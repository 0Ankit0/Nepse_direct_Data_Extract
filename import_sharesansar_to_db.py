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
TABLE_NAME = 'sharesansar_api'

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
    name = name.strip()
    name = name.lower()
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"[^a-z0-9_]+", "", name)
    if not name:
        name = 'col'
    # ensure not starting with digit
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
        # Create table if not exists with id serial primary key and date column
        create_tbl = sql.SQL("""
            CREATE TABLE IF NOT EXISTS {table} (
                id SERIAL PRIMARY KEY,
                date DATE
            )
        """).format(table=sql.Identifier(TABLE_NAME))
        cur.execute(create_tbl)
        # Get existing columns
        cur.execute(sql.SQL("SELECT column_name FROM information_schema.columns WHERE table_name = %s"), [TABLE_NAME])
        existing = {r[0] for r in cur.fetchall()}
        # Add missing columns
        for col in columns:
            if col not in existing:
                q = sql.SQL('ALTER TABLE {table} ADD COLUMN {col} TEXT').format(
                    table=sql.Identifier(TABLE_NAME),
                    col=sql.Identifier(col)
                )
                cur.execute(q)
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
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            print('  Empty file, skipping')
            return False
        cols_raw = [h.strip() for h in header if h.strip()]
        if not cols_raw:
            print('  No headers found, skipping')
            return False
        # Check for 'No Record Found.' as the only data row
        data_rows = [row for row in reader]
        if len(data_rows) == 1 and len(data_rows[0]) == 1 and data_rows[0][0].strip().lower() == 'no record found.':
            print('  No record found, skipping import')
            dest = os.path.join(PROCESSED_FOLDER, os.path.basename(filepath))
            shutil.move(filepath, dest)
            print(f'  Moved file to {dest}')
            return False
        cols = [normalize_col(c) for c in cols_raw]
        # ensure table and columns
        ensure_table_and_columns(conn, cols)
        # filter out empty rows
        rows = [row for row in data_rows if any(cell.strip() for cell in row)]
        inserted = insert_rows(conn, cols, rows, file_date)
        print(f'  Inserted {inserted} rows')
    # move file to processed
    dest = os.path.join(PROCESSED_FOLDER, os.path.basename(filepath))
    shutil.move(filepath, dest)
    print(f'  Moved file to {dest}')
    return True


def main():

    # Ensure Nepse database exists
    ensure_database_exists()

    # find csv files
    files = [os.path.join(DATA_FOLDER, f) for f in os.listdir(DATA_FOLDER) if f.lower().endswith('.csv')]
    if not files:
        print('No CSV files found in', DATA_FOLDER)
        return
    conn = get_connection()
    try:
        total = 0
        for fp in sorted(files):
            try:
                ok = process_file(conn, fp)
                if ok:
                    total += 1
            except Exception as e:
                print('Error processing', fp, e)
        print(f'Done. Processed {total} files.')
    finally:
        conn.close()


if __name__ == '__main__':
    main()
