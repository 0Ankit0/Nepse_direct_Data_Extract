"""
Compute technical indicators for TODAY'S date only and store in the `indicators` table.

Behavior:
- Checks that today's data exists in the `historicdata` table
- Skips if indicators for today are already present in the `indicators` table
- Loads full historical stock data (required for rolling-window indicators)
- Computes all indicators (RSI, MACD, SMA, EMA, ATR, Bollinger Bands, OBV, MFI,
  KVO, ADX, slope, acceleration, momentum, Chandelier Exit, Ichimoku Cloud)
- Inserts only today's rows into the `indicators` table
- Creates the `indicators` table if it does not exist
- Run this after import_today_data.py in the daily GitHub Actions workflow

Run: uv run python scripts/compute_indicators_daily.py
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from db import get_connection
from _indicators_core import (
    SOURCE_TABLE,
    INDICATORS_TABLE,
    ensure_indicators_table,
    get_existing_dates,
    load_historicdata,
    compute_and_insert_indicators_incremental,
)


def main():
    today = datetime.now().strftime('%Y-%m-%d')
    print(f"Running daily indicator computation for {today}...")

    conn = get_connection()
    try:
        ensure_indicators_table(conn)

        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM {SOURCE_TABLE} WHERE date = %s", (today,))
        result = cur.fetchone()
        if result is None:
            print(f"No stock data found for {today} in '{SOURCE_TABLE}'. Nothing to compute.")
            return
        count = result[0]
        if count == 0:
            print(f"No stock data found for {today} in '{SOURCE_TABLE}'. Nothing to compute.")
            return

        # Skip if already computed
        existing_dates = get_existing_dates(conn)
        if today in existing_dates:
            print(f"Indicators for {today} already exist. Nothing to do.")
            return

        print(f"Found {count} stock rows for {today}. Loading full history for rolling calculations...")
        df = load_historicdata(conn)
        if df.empty:
            print("No data found in historicdata table.")
            return

        inserted = compute_and_insert_indicators_incremental(conn, df, {today})
        print(f"Inserted {inserted} indicator rows for {today}.")
        print("Done.")
    finally:
        conn.close()


if __name__ == '__main__':
    main()
