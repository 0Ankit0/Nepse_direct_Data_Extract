"""
Import CSV files from `sharesansarAPI` into PostgreSQL database `Nepse`.

Behavior:
- Scans `sharesansarAPI` for `.csv` files
- Parses header row to detect columns
- Ensures a table `sharesansar_api` exists and has columns matching the CSV headers (TEXT)
- Adds a `date` column (DATE) and populates it with the date parsed from the filename (supports YYYY_MM_DD or YYYY-MM-DD)
- Inserts all rows from the CSV into the table
- Moves processed CSV files to `sharesansarAPI/processed/`

Configuration via environment variables:
- PGHOST (default: localhost)
- PGPORT (default: 5432)
- PGUSER
- PGPASSWORD
- PGDATABASE (default: Nepse)

Run: python import_sharesansar_to_db.py
"""

import os
import csv
import shutil
import re
import sys
from datetime import datetime

import psycopg2
from psycopg2 import sql, OperationalError

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

# Map to SQL types
COLUMN_TYPES = {
    'id': 'SERIAL PRIMARY KEY',
    'date': 'DATE',
    'symbol': 'TEXT',
    'conf': 'DECIMAL',
    'open': 'DECIMAL',
    'high': 'DECIMAL',
    'low': 'DECIMAL',
    'close': 'DECIMAL',
    'ltp': 'DECIMAL',
    'close_minus_ltp': 'DECIMAL',
    'close_minus_ltp_pct': 'DECIMAL',
    'vwap': 'DECIMAL',
    'vol': 'DECIMAL',
    'prev_close': 'DECIMAL',
    'turnover': 'DECIMAL',
    'trans': 'DECIMAL',
    'diff': 'DECIMAL',
    'range': 'DECIMAL',
    'diff_pct': 'DECIMAL',
    'range_pct': 'DECIMAL',
    'vwap_pct': 'DECIMAL',
    'weeks_52_high': 'DECIMAL',
    'weeks_52_low': 'DECIMAL',
}

TABLE_NAME = 'historicdata'

PGHOST = os.getenv('PGHOST', 'localhost')
PGPORT = int(os.getenv('PGPORT', 5432))
PGUSER = os.getenv('PGUSER', 'postgres')
PGPASSWORD = os.getenv('PGPASSWORD', 'admin')
PGDATABASE = os.getenv('PGDATABASE', 'Nepse')

os.makedirs(PROCESSED_FOLDER, exist_ok=True)



def ensure_database_exists():
    """Connect to Nepse DB, or create it if missing."""
    try:
        # Try connecting to Nepse
        conn = psycopg2.connect(host=PGHOST, port=PGPORT, user=PGUSER, password=PGPASSWORD, dbname=PGDATABASE)
        conn.close()
        print(f"Database '{PGDATABASE}' exists.")
    except OperationalError as e:
        if f'database "{PGDATABASE}" does not exist' in str(e):
            print(f"Database '{PGDATABASE}' does not exist. Creating...")
            # Connect to default 'postgres' DB and create Nepse
            conn = psycopg2.connect(host=PGHOST, port=PGPORT, user=PGUSER, password=PGPASSWORD, dbname='postgres')
            try:
                conn.autocommit = True
                with conn.cursor() as cur:
                    cur.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(PGDATABASE)))
                print(f"Database '{PGDATABASE}' created.")
            finally:
                conn.close()
        else:
            raise

def get_connection():
    return psycopg2.connect(host=PGHOST, port=PGPORT, user=PGUSER, password=PGPASSWORD, dbname=PGDATABASE)


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
    """Create table if not exists and add any missing columns."""
    with conn.cursor() as cur:
        # Check if table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = %s
            )
        """, [TABLE_NAME.lower()])
        table_exists = cur.fetchone()[0]
        
        if not table_exists:
            # Table doesn't exist, create it with all columns
            col_defs = []
            for col in COLUMN_ORDER:
                if col == 'id':
                    col_defs.append('id SERIAL PRIMARY KEY')
                else:
                    col_defs.append(f'{col} {COLUMN_TYPES[col]}')
            create_tbl = f"""
                CREATE TABLE {TABLE_NAME} (
                    {', '.join(col_defs)}
                )
            """
            cur.execute(create_tbl)
            print(f"Created table {TABLE_NAME} with all required columns")
        else:
            # Table exists, check what columns we have
            cur.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = %s AND table_schema = 'public'
                ORDER BY ordinal_position
            """, [TABLE_NAME.lower()])
            existing_columns = [row[0].lower() for row in cur.fetchall()]
            expected_columns = [col.lower() for col in COLUMN_ORDER]
            
            # Rename old columns if present
            rename_map = {
                'close_ltp': 'close_minus_ltp',
                'close_ltp_pct': 'close_minus_ltp_pct',
            }
            for old, new in rename_map.items():
                if old in existing_columns and new not in existing_columns:
                    print(f"Renaming column {old} to {new}")
                    cur.execute(f'ALTER TABLE {TABLE_NAME} RENAME COLUMN {old} TO {new}')
            # Refresh columns after renaming
            cur.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = %s AND table_schema = 'public'
                ORDER BY ordinal_position
            """, [TABLE_NAME.lower()])
            existing_columns = [row[0].lower() for row in cur.fetchall()]
            expected_columns = [col.lower() for col in COLUMN_ORDER]

            # Add missing columns
            for col in COLUMN_ORDER:
                if col.lower() not in existing_columns and col != 'id':  # id is SERIAL, don't add manually
                    col_type = COLUMN_TYPES[col]
                    print(f"Adding missing column: {col}")
                    cur.execute(f'ALTER TABLE {TABLE_NAME} ADD COLUMN {col} {col_type}')

            # Remove extra columns that aren't in our expected list
            for existing_col in existing_columns:
                if existing_col not in expected_columns:
                    print(f"Removing extra column: {existing_col}")
                    cur.execute(f'ALTER TABLE {TABLE_NAME} DROP COLUMN IF EXISTS {existing_col}')
        
        conn.commit()


def insert_rows(conn, columns, rows, file_date):
    """Insert rows into table. columns is ordered list of column names present in CSV."""
    if not rows:
        return 0
    with conn.cursor() as cur:
        all_cols = columns + ['date']
        col_identifiers = sql.SQL(', ').join(sql.Identifier(c) for c in all_cols)
        placeholders = sql.SQL(', ').join(sql.Placeholder() for _ in all_cols)
        insert_sql = sql.SQL('INSERT INTO {table} ({cols}) VALUES ({vals})').format(
            table=sql.Identifier(TABLE_NAME),
            cols=col_identifiers,
            vals=placeholders
        )
        count = 0
        batch = []
        for r in rows:
            # pad row if shorter
            vals = [v if v != '' else None for v in r]
            if len(vals) < len(columns):
                vals += [None] * (len(columns) - len(vals))
            vals.append(file_date)
            batch.append(vals)
            # execute in small batches
            if len(batch) >= 1000:
                cur.executemany(insert_sql.as_string(conn), batch)
                count += len(batch)
                batch = []
        if batch:
            cur.executemany(insert_sql.as_string(conn), batch)
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
            # Remove S.No and only use the specified columns
            data_rows = []
            for row in reader:
                # Only keep the specified columns, skip S.No
                filtered = {k.strip(): v for k, v in row.items() if k and k.strip() not in ('S.No', 'SNO', 'sno', 'Sno')}
                # Direct mapping: CSV header to canonical column name
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
            # Rename old columns if present
            rename_map = {
                'close_ltp': 'close_minus_ltp',
                'close_ltp_pct': 'close_minus_ltp_pct',
            }
            for old, new in rename_map.items():
                if old in existing_columns and new not in existing_columns:
                    print(f"Renaming column {old} to {new}")
                    cur.execute(f'ALTER TABLE {TABLE_NAME} RENAME COLUMN {old} TO {new}')
                for k, v in filtered.items():
                    if k in header_map:
                        mapped[header_map[k]] = v
                # Only add if Symbol is present
                if mapped.get('symbol'):
                    data_rows.append(mapped)
            if not data_rows:
                print('  No valid data rows, skipping')
                return False
            # Debug print removed for production
            # Check for 'No Record Found.' as the only data row
            if len(data_rows) == 1 and list(data_rows[0].values())[0].strip().lower() == 'no record found.':
                print('  No record found, skipping import')
                return False
            # ensure table and columns
            ensure_table_and_columns(conn, COLUMN_ORDER)
            num_data_rows = len(data_rows)
            file_date = parse_date_from_filename(filepath)
            # Check if already imported: compare only data rows, not header
            with conn.cursor() as cur:
                cur.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE date = %s", (file_date,))
                db_count = cur.fetchone()[0]
            if db_count == num_data_rows:
                print(f'  Skipping {filepath}: {db_count} rows already present for {file_date}')
                return False
            # Prepare rows for insert
            rows_to_insert = []
            for row in data_rows:
                vals = []
                for col in COLUMN_ORDER:
                    if col == 'id':
                        continue  # SERIAL PRIMARY KEY
                    elif col == 'date':
                        vals.append(file_date)
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
                    with conn.cursor() as cur:
                        col_names = [c for c in COLUMN_ORDER if c not in ('id',)]
                        col_identifiers = sql.SQL(', ').join(sql.Identifier(c) for c in col_names)
                        placeholders = sql.SQL(', ').join(sql.Placeholder() for _ in col_names)
                        insert_sql = sql.SQL('INSERT INTO {table} ({cols}) VALUES ({vals})').format(
                            table=sql.Identifier(TABLE_NAME),
                            cols=col_identifiers,
                            vals=placeholders
                        )
                        cur.executemany(insert_sql.as_string(conn), rows_to_insert)
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

    # Ensure Nepse database exists
    ensure_database_exists()

    # Find csv files and extract dates
    files = [os.path.join(DATA_FOLDER, f) for f in os.listdir(DATA_FOLDER) if f.lower().endswith('.csv')]
    if not files:
        print('No CSV files found in', DATA_FOLDER)
        return

    # Map: date -> filepath
    date_file_map = {}
    for fp in files:
        date = parse_date_from_filename(fp)
        if date:
            date_file_map[date] = fp

    if not date_file_map:
        print('No valid dated CSV files found.')
        return

    # Sort dates descending
    sorted_dates = sorted(date_file_map.keys(), reverse=True)

    conn = get_connection()
    try:
        # Ensure table and columns exist before querying
        ensure_table_and_columns(conn, COLUMN_ORDER)
        for d in sorted_dates:
            # Stop if we reach 2020-01-01
            if d <= datetime(2020, 1, 1).date():
                print('Reached 2020-01-01, stopping.')
                break
            # Check if date exists in DB
            with conn.cursor() as cur:
                cur.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE date = %s", (d,))
                db_count = cur.fetchone()[0]
            if db_count > 0:
                print(f"Data for {d} already exists in DB. Stopping.")
                break
            # Not in DB, import
            print(f"Importing data for {d} from {date_file_map[d]}")
            ok = process_file(conn, date_file_map[d])
            if not ok:
                print(f"Failed to import {date_file_map[d]}")
            # Continue to previous date
        print('Done.')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
