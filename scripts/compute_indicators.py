"""
Compute technical indicators for ALL missing dates and store in the `indicators` table.

Behavior:
- Reads all stock data from `historicdata` table in historicdata.sqlite
- Computes indicators for each symbol: RSI, MACD, SMA, EMA, ATR, Bollinger Bands,
  OBV, MFI, KVO, ADX (+DI/-DI), linear regression slope, momentum acceleration,
  momentum, Chandelier Exit, Ichimoku Cloud
- Creates `indicators` table if it does not exist
- Skips dates already present in the `indicators` table (incremental backfill)
- Use this for historical backfill; for daily scheduled runs use compute_indicators_daily.py

Run: uv run python scripts/compute_indicators.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from db import get_connection
from _indicators_core import (
    ensure_indicators_table,
    get_existing_dates,
    get_incomplete_dates,
    load_historicdata,
    compute_all_indicators,
    insert_indicators,
)


def main():
    conn = get_connection()
    try:
        ensure_indicators_table(conn)
        existing_dates = get_existing_dates(conn)

        print(f"Loading stock data from historicdata...")
        df = load_historicdata(conn)
        if df.empty:
            print("No data found in historicdata table.")
            return

        all_dates = set(df['date'].unique())
        new_dates = (all_dates - existing_dates) | get_incomplete_dates(conn)

        if not new_dates:
            print("Indicators are already up to date. Nothing to compute.")
            return

        print(f"Found {len(new_dates)} new date(s) to compute indicators for.")
        result = compute_all_indicators(df)
        inserted = insert_indicators(conn, result, new_dates)
        print(f"Inserted {inserted} indicator rows for {len(new_dates)} new date(s).")
        print("Done.")
    finally:
        conn.close()


if __name__ == '__main__':
    main()
