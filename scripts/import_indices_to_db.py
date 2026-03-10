import os
import csv
import re
from datetime import datetime
import sys
import psycopg2

sys.path.insert(0, os.path.dirname(__file__))
from db import get_connection

# Configuration
INDICES_FOLDER = 'Indices'
TABLE_NAME = 'indices'

# Columns based on your header
COLUMN_ORDER = [
    'id', 'date', 'index', 'current', 'point_change', 'pct_change', 'turnover'
]

COLUMN_TYPES = {
    'id': 'BIGSERIAL PRIMARY KEY',
    'date': 'TEXT',
    'index': 'TEXT',
    'current': 'REAL',
    'point_change': 'REAL',
    'pct_change': 'REAL',
    'turnover': 'REAL',
}

def parse_date_from_filename(filename: str):
    base = os.path.splitext(os.path.basename(filename))[0]
    candidates = [base.replace('_', '-'), base.replace('-', '-'), base]
    for c in candidates:
        for fmt in ('%Y-%m-%d', '%Y%m%d', '%Y_%m_%d'):
            try:
                return datetime.strptime(c, fmt).date()
            except Exception:
                pass
    return None

def ensure_table_and_columns(conn):
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
            col_defs.append(f'"{col}" {COLUMN_TYPES[col]}')
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
                cur.execute(f'ALTER TABLE {TABLE_NAME} ADD COLUMN "{col}" {col_type}')
    conn.commit()

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
                mapped = {
                    'index': row.get('Index', row.get('index', None)),
                    'current': row.get('Current', row.get('current', None)),
                    'point_change': row.get('Point Change', row.get('point_change', None)),
                    'pct_change': row.get('% Change', row.get('pct_change', None)),
                    'turnover': row.get('Turnover', row.get('turnover', None)),
                    'date': str(file_date)
                }
                data_rows.append(mapped)
            if not data_rows:
                print('  No valid data rows, skipping')
                return False
            ensure_table_and_columns(conn)
            cur = conn.cursor()
            cur.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE date = %s", (str(file_date),))
            db_count = cur.fetchone()[0]
            if db_count == len(data_rows):
                print(f'  Skipping {filepath}: {db_count} rows already present for {file_date}')
                return False
            rows_to_insert = []
            for row in data_rows:
                vals = []
                for col in COLUMN_ORDER:
                    if col == 'id':
                        continue
                    elif col == 'date':
                        vals.append(row.get('date'))
                    elif col in ['index', 'current', 'point_change', 'pct_change', 'turnover']:
                        val = row.get(col, None)
                        if val is not None and val != '':
                            try:
                                vals.append(float(val.replace(',', '')))
                            except Exception:
                                vals.append(val)
                        else:
                            vals.append(None)
                rows_to_insert.append(vals)
            if rows_to_insert:
                col_names = [c for c in COLUMN_ORDER if c != 'id']
                col_str = ', '.join([f'"{c}"' for c in col_names])
                placeholders = ', '.join(['%s'] * len(col_names))
                insert_sql = f'INSERT INTO {TABLE_NAME} ({col_str}) VALUES ({placeholders})'
                cur.executemany(insert_sql, rows_to_insert)
                conn.commit()
                print(f'  Inserted {len(rows_to_insert)} rows')
        return True
    except Exception as e:
        conn.rollback()
        print(f'  Error processing file {filepath}: {e}')
        return False

def main():
    files = [os.path.join(INDICES_FOLDER, f) for f in os.listdir(INDICES_FOLDER) if f.lower().endswith('.csv')]
    if not files:
        print('No CSV files found in', INDICES_FOLDER)
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
        ensure_table_and_columns(conn)
        for d in sorted_dates:
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
