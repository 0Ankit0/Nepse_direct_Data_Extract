"""
Import CSV files from `sharesansarAPI` into Supabase (PostgreSQL).

Behavior:
- Scans `sharesansarAPI` for `.csv` files
- Parses header row to detect columns
- Ensures a table `historicdata` exists with the required schema
- Adds a `date` column and populates it from the filename (YYYY_MM_DD or YYYY-MM-DD)
- Inserts all rows from the CSV into the table

Configuration via environment variables (GitHub Actions secrets):
- PGHOST      - Supabase database host
- PGPORT      - Database port (default: 5432)
- PGUSER      - Database user
- PGPASSWORD  - Database password
- PGDATABASE  - Database name (default: postgres)

Run: python import_sharesansar_to_db.py
"""

import os
import csv
import shutil
import re
import sys
from datetime import datetime

import psycopg2

# Configuration
DATA_FOLDER = 'sharesansarAPI'
PROCESSED_FOLDER = os.path.join(DATA_FOLDER, 'processed')

# Only use these columns, in this order
COLUMN_ORDER = [
    'id', 'date', 'symbol', 'conf', 'open', 'high', 'low', 'close', 'ltp',
    'close_minus_ltp', 'close_minus_ltp_pct', 'vwap', 'vol', 'prev_close', 'turnover',
    'trans', 'diff', 'range', 'diff_pct', 'range_pct', 'vwap_pct',
    'weeks_52_high', 'weeks_52_low'
]

COLUMN_TYPES = {
    'id': 'BIGSERIAL PRIMARY KEY',
    'date': 'TEXT',
    'symbol': 'TEXT',
    'conf': 'REAL',
    'open': 'REAL',
    'high': 'REAL',
    'low': 'REAL',
    'close': 'REAL',
    'ltp': 'REAL',
    'close_minus_ltp': 'REAL',
    'close_minus_ltp_pct': 'REAL',
    'vwap': 'REAL',
    'vol': 'REAL',
    'prev_close': 'REAL',
    'turnover': 'REAL',
    'trans': 'REAL',
    'diff': 'REAL',
    'range': 'REAL',
    'diff_pct': 'REAL',
    'range_pct': 'REAL',
    'vwap_pct': 'REAL',
    'weeks_52_high': 'REAL',
    'weeks_52_low': 'REAL',
}

TABLE_NAME = 'historicdata'
os.makedirs(PROCESSED_FOLDER, exist_ok=True)



def get_connection():
    sys.path.insert(0, os.path.dirname(__file__))
    from db import get_connection as _get_conn
    return _get_conn()


def normalize_col(name: str) -> str:
    orig = name.strip()
    name = orig.lower().strip()
    # Remove dots and extra spaces
    name = name.replace('.', '').replace(',', '').replace('  ', ' ')
    name = re.sub(r"\s+", "_", name)
    # Robust mapping for all known variants
    mapping = {
        'sno': 'sno',
        'symbol': 'symbol',
        'conf': 'conf',
        'conf.': 'conf',
        'open': 'open',
        'high': 'high',
        'low': 'low',
        'close': 'close',
        'ltp': 'ltp',
        'close_-_ltp': 'close_minus_ltp',
        'close_ltp': 'close_minus_ltp',
        'close_ltp_': 'close_minus_ltp',
        'close_ltp__': 'close_minus_ltp',
        'close_-_ltp_': 'close_minus_ltp',
        'close_-_ltp_pct': 'close_minus_ltp_pct',
        'close_-_ltp_%': 'close_minus_ltp_pct',
        'close_ltp_pct': 'close_minus_ltp_pct',
        'close_ltp__pct': 'close_minus_ltp_pct',
        'vwap': 'vwap',
        'vol': 'vol',
        'prev_close': 'prev_close',
        'prev_close.': 'prev_close',
        'turnover': 'turnover',
        'trans': 'trans',
        'diff': 'diff',
        'range': 'range',
        'diff_pct': 'diff_pct',
        'diff_%': 'diff_pct',
        'diff__': 'diff_pct',
        'diff__%': 'diff_pct',
        'range_pct': 'range_pct',
        'range_%': 'range_pct',
        'range__%': 'range_pct',
        'vwap_pct': 'vwap_pct',
        'vwap_%': 'vwap_pct',
        'vwap__%': 'vwap_pct',
        'weeks_52_high': 'weeks_52_high',
        '52_weeks_high': 'weeks_52_high',
        '52_weeks_high.': 'weeks_52_high',
        '52_weeks_high_': 'weeks_52_high',
        '52_weeks_high__': 'weeks_52_high',
        '52_weeks_high__': 'weeks_52_high',
        '52_weeks_high__': 'weeks_52_high',
        '52_weeks_low': 'weeks_52_low',
        '52_weeks_low.': 'weeks_52_low',
        '52_weeks_low_': 'weeks_52_low',
        '52_weeks_low__': 'weeks_52_low',
        '52_weeks_low__': 'weeks_52_low',
        '52_weeks_low__': 'weeks_52_low',
    }
    # Handle special cases for headers with spaces and symbols
    if orig.strip().lower() in ['close - ltp', 'close-ltp']:
        return 'close_minus_ltp'
    if orig.strip().lower() in ['close - ltp %', 'close-ltp %', 'close - ltp%', 'close-ltp%']:
        return 'close_minus_ltp_pct'
    if orig.strip().lower() in ['diff %', 'diff%', 'diff percent', 'diff percentage']:
        return 'diff_pct'
    if orig.strip().lower() in ['range %', 'range%', 'range percent', 'range percentage']:
        return 'range_pct'
    if orig.strip().lower() in ['vwap %', 'vwap%', 'vwap percent', 'vwap percentage']:
        return 'vwap_pct'
    if orig.strip().lower() in ['52 weeks high', '52weeks high', '52 week high', '52week high']:
        return 'weeks_52_high'
    if orig.strip().lower() in ['52 weeks low', '52weeks low', '52 week low', '52week low']:
        return 'weeks_52_low'
    # Fallback to mapping dict
    if name in mapping:
        name = mapping[name]
    if not name:
        name = 'col'
    if re.match(r"^[0-9]", name):
        name = '_' + name
    return name


def parse_date_from_filename(filename: str):
    base = os.path.splitext(os.path.basename(filename))[0]
    # support YYYY_MM_DD or YYYY-MM-DD or YYYYMMDD
    candidates = [base.replace('_', '-'), base.replace('-', '-'), base]
    for c in candidates:
        # try formats
        for fmt in ('%Y-%m-%d', '%Y%m%d', '%Y_%m_%d'):
            try:
                return datetime.strptime(c, fmt).date()
            except Exception:
                pass
    # fallback: return None
    return None


def ensure_table_and_columns(conn, columns):
    """Create table if not exists and add any missing columns (PostgreSQL)."""
    cur = conn.cursor()
    cur.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema='public' AND table_name=%s",
        (TABLE_NAME,)
    )
    table_exists = cur.fetchone() is not None
    if not table_exists:
        col_defs = []
        for col in COLUMN_ORDER:
            col_defs.append(f'{col} {COLUMN_TYPES[col]}')
        create_tbl = f"CREATE TABLE {TABLE_NAME} ({', '.join(col_defs)})"
        cur.execute(create_tbl)
        print(f"Created table {TABLE_NAME} with all required columns")
    else:
        cur.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name=%s",
            (TABLE_NAME,)
        )
        existing_columns = [row[0].lower() for row in cur.fetchall()]
        for col in COLUMN_ORDER:
            if col.lower() not in existing_columns and col != 'id':
                col_type = COLUMN_TYPES[col]
                print(f"Adding missing column: {col}")
                cur.execute(f'ALTER TABLE {TABLE_NAME} ADD COLUMN {col} {col_type}')
    conn.commit()


def insert_rows(conn, columns, rows, file_date):
    """Insert rows into table. columns is ordered list of column names present in CSV."""
    if not rows:
        return 0
    cur = conn.cursor()
    all_cols = columns + ['date']
    col_names = ', '.join(all_cols)
    placeholders = ', '.join(['%s'] * len(all_cols))
    insert_sql = f'INSERT INTO {TABLE_NAME} ({col_names}) VALUES ({placeholders})'
    count = 0
    batch = []
    for r in rows:
        vals = [v if v != '' else None for v in r]
        if len(vals) < len(columns):
            vals += [None] * (len(columns) - len(vals))
        vals.append(file_date)
        batch.append(vals)
        if len(batch) >= 1000:
            cur.executemany(insert_sql, batch)
            count += len(batch)
            batch = []
    if batch:
        cur.executemany(insert_sql, batch)
        count += len(batch)
    conn.commit()
    return count


def process_file(conn, filepath):
    print(f'Processing {filepath}')
    file_date = parse_date_from_filename(filepath)
    if not file_date:
        print(f'  Warning: could not parse date from filename, skipping: {filepath}')
        return False
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            data_rows = []
            for row in reader:
                filtered = {k.strip(): v for k, v in row.items() if k and k.strip() not in ('S.No', 'SNO', 'sno', 'Sno')}
                mapped = {}
                header_map = {
                    'Symbol': 'symbol',
                    'Conf.': 'conf',
                    'Open': 'open',
                    'High': 'high',
                    'Low': 'low',
                    'Close': 'close',
                    'LTP': 'ltp',
                    'Close - LTP': 'close_minus_ltp',
                    'Close - LTP %': 'close_minus_ltp_pct',
                    'VWAP': 'vwap',
                    'Vol': 'vol',
                    'Prev. Close': 'prev_close',
                    'Turnover': 'turnover',
                    'Trans.': 'trans',
                    'Diff': 'diff',
                    'Range': 'range',
                    'Diff %': 'diff_pct',
                    'Range %': 'range_pct',
                    'VWAP %': 'vwap_pct',
                    '52 Weeks High': 'weeks_52_high',
                    '52 Weeks Low': 'weeks_52_low',
                }
                for k, v in filtered.items():
                    if k in header_map:
                        mapped[header_map[k]] = v
                if mapped.get('symbol'):
                    data_rows.append(mapped)
            if not data_rows:
                print('  No valid data rows, skipping')
                return False
            if len(data_rows) == 1 and list(data_rows[0].values())[0].strip().lower() == 'no record found.':
                print('  No record found, skipping import')
                return False
            ensure_table_and_columns(conn, COLUMN_ORDER)
            num_data_rows = len(data_rows)
            file_date = parse_date_from_filename(filepath)
            cur = conn.cursor()
            cur.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE date = %s", (str(file_date),))
            db_count = cur.fetchone()[0]
            if db_count == num_data_rows:
                print(f'  Skipping {filepath}: {db_count} rows already present for {file_date}')
                return False
            rows_to_insert = []
            for row in data_rows:
                vals = []
                for col in COLUMN_ORDER:
                    if col == 'id':
                        continue
                    elif col == 'date':
                        vals.append(str(file_date))
                    elif col == 'symbol':
                        vals.append(row.get('symbol', None))
                    else:
                        val = row.get(col, None)
                        if val is not None and val != '':
                            try:
                                vals.append(float(val.replace(',', '')))
                            except Exception:
                                vals.append(None)
                        else:
                            vals.append(None)
                rows_to_insert.append(vals)
            inserted = 0
            if rows_to_insert:
                try:
                    col_names = [c for c in COLUMN_ORDER if c != 'id']
                    col_str = ', '.join(col_names)
                    placeholders = ', '.join(['%s'] * len(col_names))
                    insert_sql = f'INSERT INTO {TABLE_NAME} ({col_str}) VALUES ({placeholders})'
                    cur.executemany(insert_sql, rows_to_insert)
                    conn.commit()
                    inserted = len(rows_to_insert)
                except Exception as e:
                    conn.rollback()
                    print(f'  Error inserting rows for file {filepath}: {e}')
                    print('  Skipping this file due to error.')
                    return False
            print(f'  Inserted {inserted} rows')
        return True
    except Exception as e:
        conn.rollback()
        print(f'  Error processing file {filepath}: {e}')
        return False



def main():
    files = [os.path.join(DATA_FOLDER, f) for f in os.listdir(DATA_FOLDER) if f.lower().endswith('.csv')]
    if not files:
        print('No CSV files found in', DATA_FOLDER)
        return

    date_file_map = {}
    for fp in files:
        date = parse_date_from_filename(fp)
        if date:
            date_file_map[date] = fp

    if not date_file_map:
        print('No valid dated CSV files found.')
        return

    sorted_dates = sorted(date_file_map.keys(), reverse=True)

    conn = get_connection()
    try:
        ensure_table_and_columns(conn, COLUMN_ORDER)
        for d in sorted_dates:
            if d <= datetime(2020, 1, 1).date():
                print('Reached 2020-01-01, stopping.')
                break
            cur = conn.cursor()
            cur.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE date = %s", (str(d),))
            db_count = cur.fetchone()[0]
            if db_count > 0:
                print(f"Data for {d} already exists in DB. Skipping.")
                continue
            print(f"Importing data for {d} from {date_file_map[d]}")
            ok = process_file(conn, date_file_map[d])
            if not ok:
                print(f"Failed to import {date_file_map[d]}")
        print('Done.')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
