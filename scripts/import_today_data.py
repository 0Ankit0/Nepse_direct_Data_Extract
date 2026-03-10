import os
from datetime import datetime
import sqlite3
from import_sharesansar_to_db import process_file as process_api_file, ensure_table_and_columns as ensure_api_table, COLUMN_ORDER as API_COLUMN_ORDER
from import_indices_to_db import process_file as process_indices_file, ensure_table_and_columns as ensure_indices_table, COLUMN_ORDER as INDICES_COLUMN_ORDER

DATA_FOLDER = 'sharesansarAPI'
INDICES_FOLDER = 'Indices'
SQLITE_DB_PATH = 'historicdata.sqlite'

# Today's date in YYYY_MM_DD and YYYY-MM-DD
now = datetime.now()
today_str_underscore = now.strftime('%Y_%m_%d')
today_str_dash = now.strftime('%Y-%m-%d')

api_file = None
indices_file = None

# Find today's API file
for fname in os.listdir(DATA_FOLDER):
    if fname.lower().endswith('.csv') and (today_str_underscore in fname or today_str_dash in fname):
        api_file = os.path.join(DATA_FOLDER, fname)
        break

# Find today's Indices file
for fname in os.listdir(INDICES_FOLDER):
    if fname.lower().endswith('.csv') and (today_str_underscore in fname or today_str_dash in fname):
        indices_file = os.path.join(INDICES_FOLDER, fname)
        break

conn = sqlite3.connect(SQLITE_DB_PATH)
try:
    # Import API file if found
    if api_file:
        print(f"Importing API data from {api_file}")
        ensure_api_table(conn, API_COLUMN_ORDER)
        process_api_file(conn, api_file)
    else:
        print("No API CSV file found for today.")
    # Import Indices file if found
    if indices_file:
        print(f"Importing Indices data from {indices_file}")
        ensure_indices_table(conn)
        process_indices_file(conn, indices_file)
    else:
        print("No Indices CSV file found for today.")
finally:
    conn.close()
