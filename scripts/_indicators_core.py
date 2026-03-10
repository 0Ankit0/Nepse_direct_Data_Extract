"""
Shared core logic for indicator computation.

Used by:
  compute_indicators.py       - backfill all missing dates
  compute_indicators_daily.py - today's date only
"""

import os
import sys
import psycopg2
import psycopg2.extensions

import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

from db import get_connection

from indicators.momentum.rsi import rsi
from indicators.momentum.macd import macd
from indicators.momentum.momentum import momentum
from indicators.momentum.stochastic import stochastic
from indicators.momentum.cci import cci
from indicators.momentum.williams_r import williams_r
from indicators.trend.moving_averages import sma, ema
from indicators.trend.adx import calculate_adx
from indicators.trend.trend_strength import calculate_slope, calculate_acceleration
from indicators.volatility.atr import atr
from indicators.volatility.bollinger import bollinger_bands
from indicators.volatility.ichimoku import ichimoku
from indicators.volatility.exits import calculate_chandelier_exit
from indicators.volume.volume_flow import calculate_obv, calculate_mfi, calculate_kvo

SOURCE_TABLE = 'historicdata'
INDICATORS_TABLE = 'indicators'

COLUMN_TYPES = {
    # identifiers
    'id':                   'BIGSERIAL PRIMARY KEY',
    'date':                 'TEXT NOT NULL',
    'symbol':               'TEXT NOT NULL',
    # momentum
    'rsi_14':               'REAL',
    'macd_line':            'REAL',
    'macd_signal':          'REAL',
    'macd_hist':            'REAL',
    'stoch_k':              'REAL',   # Stochastic %K (14)
    'stoch_d':              'REAL',   # Stochastic %D (3-period SMA of %K)
    'cci_20':               'REAL',   # Commodity Channel Index (20)
    'williams_r':           'REAL',   # Williams %R (14)
    'momentum_5':           'REAL',   # Rate of change over 5 periods
    # trend – moving averages
    'sma_5':                'REAL',
    'sma_10':               'REAL',
    'sma_20':               'REAL',
    'sma_50':               'REAL',
    'sma_200':              'REAL',   # Long-term trend (golden/death cross with sma_50)
    'ema_9':                'REAL',   # Short-term signal line
    'ema_12':               'REAL',
    'ema_26':               'REAL',
    'ema_200':              'REAL',   # Long-term exponential trend
    # trend – directional / strength
    'adx_14':               'REAL',
    'plus_di':              'REAL',
    'minus_di':             'REAL',
    'slope_20':             'REAL',
    'acceleration':         'REAL',
    # volatility
    'atr_14':               'REAL',
    'bb_upper':             'REAL',
    'bb_lower':             'REAL',
    'ichimoku_conversion':  'REAL',
    'ichimoku_base':        'REAL',
    'ichimoku_span_a':      'REAL',
    'ichimoku_span_b':      'REAL',
    'chandelier_long':      'REAL',
    'chandelier_short':     'REAL',
    # volume
    'obv':                  'REAL',
    'mfi_14':               'REAL',
    'kvo':                  'REAL',
}

COLUMN_ORDER = list(COLUMN_TYPES.keys())

# Columns used in UPSERT conflict resolution (the unique index columns)
_UPSERT_CONFLICT_COLS = '(date, symbol)'


def ensure_indicators_table(conn: psycopg2.extensions.connection):
    """Create indicators table if it does not exist; add any missing columns."""
    cur = conn.cursor()
    cur.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema='public' AND table_name=%s",
        (INDICATORS_TABLE,)
    )
    if cur.fetchone() is None:
        col_defs = ', '.join(f'{col} {typ}' for col, typ in COLUMN_TYPES.items())
        cur.execute(f'CREATE TABLE {INDICATORS_TABLE} ({col_defs})')
        cur.execute(
            f'CREATE UNIQUE INDEX IF NOT EXISTS idx_indicators_date_symbol '
            f'ON {INDICATORS_TABLE} (date, symbol)'
        )
        print(f"Created table '{INDICATORS_TABLE}'")
    else:
        cur.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name=%s",
            (INDICATORS_TABLE,)
        )
        existing = {row[0].lower() for row in cur.fetchall()}
        added = []
        for col, typ in COLUMN_TYPES.items():
            if col not in existing and col != 'id':
                cur.execute(f'ALTER TABLE {INDICATORS_TABLE} ADD COLUMN {col} {typ}')
                added.append(col)
        if added:
            print(f"  Added missing columns: {', '.join(added)}")
    conn.commit()


def get_existing_dates(conn: psycopg2.extensions.connection) -> set:
    cur = conn.cursor()
    cur.execute(f'SELECT DISTINCT date FROM {INDICATORS_TABLE}')
    return {row[0] for row in cur.fetchall()}


def get_incomplete_dates(conn: psycopg2.extensions.connection) -> set:
    """Return dates that exist in indicators but have NULLs in any indicator column."""
    probe_cols = ['rsi_14', 'stoch_k', 'cci_20', 'williams_r', 'sma_200', 'ema_9', 'ema_200']
    cur = conn.cursor()
    cur.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema='public' AND table_name=%s",
        (INDICATORS_TABLE,)
    )
    existing = {row[0] for row in cur.fetchall()}
    checks = [f'{col} IS NULL' for col in probe_cols if col in existing]
    if not checks:
        return set()
    where = ' OR '.join(checks)
    cur.execute(f'SELECT DISTINCT date FROM {INDICATORS_TABLE} WHERE {where}')
    return {row[0] for row in cur.fetchall()}


def load_historicdata(conn: psycopg2.extensions.connection) -> pd.DataFrame:
    """Load all rows from historicdata, sorted by symbol then date."""
    df = pd.read_sql_query(
        f'SELECT date, symbol, open, high, low, close, ltp, vol '
        f'FROM {SOURCE_TABLE} '
        f'WHERE symbol IS NOT NULL AND close IS NOT NULL '
        f'ORDER BY symbol, date',
        conn
    )
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    for col in ('open', 'high', 'low', 'close', 'ltp', 'vol'):
        df[col] = pd.to_numeric(df[col], errors='coerce')
    return df


def compute_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Compute all technical indicators over the full DataFrame.

    NOTE: Rolling indicators require the full history even when only a subset
    of dates will be inserted, so always pass the complete dataset.
    """
    print(f"  Computing indicators for {df['symbol'].nunique()} symbols "
          f"over {df['date'].nunique()} dates...")

    result = df[['date', 'symbol']].copy()

    # ── Momentum ──────────────────────────────────────────────────────────────
    result['rsi_14'] = rsi(df, period=14)

    _macd_line, _macd_signal, _macd_hist = macd(df)
    result['macd_line']   = _macd_line.values
    result['macd_signal'] = _macd_signal.values
    result['macd_hist']   = _macd_hist.values

    _stoch_k, _stoch_d = stochastic(df, k_period=14, d_period=3)
    result['stoch_k'] = _stoch_k.values
    result['stoch_d'] = _stoch_d.values

    result['cci_20']     = cci(df, period=20).values
    result['williams_r'] = williams_r(df, period=14).values
    result['momentum_5'] = momentum(df, period=5)

    # ── Trend – Moving Averages ───────────────────────────────────────────────
    result['sma_5']   = sma(df, period=5)
    result['sma_10']  = sma(df, period=10)
    result['sma_20']  = sma(df, period=20)
    result['sma_50']  = sma(df, period=50)
    result['sma_200'] = sma(df, period=200)
    result['ema_9']   = ema(df, period=9)
    result['ema_12']  = ema(df, period=12)
    result['ema_26']  = ema(df, period=26)
    result['ema_200'] = ema(df, period=200)

    # ── Trend – Directional / Strength ───────────────────────────────────────
    adx_df = calculate_adx(df, window=14)
    result['adx_14']   = adx_df['adx'].values
    result['plus_di']  = adx_df['plus_di'].values
    result['minus_di'] = adx_df['minus_di'].values

    result['slope_20']     = calculate_slope(df, window=20)
    result['acceleration'] = calculate_acceleration(df)

    # ── Volatility ────────────────────────────────────────────────────────────
    result['atr_14'] = atr(df, period=14).values

    _bb_upper, _bb_lower = bollinger_bands(df, period=20)
    result['bb_upper'] = _bb_upper.values
    result['bb_lower'] = _bb_lower.values

    _ich_conv, _ich_base, _ich_span_a, _ich_span_b = ichimoku(df)
    result['ichimoku_conversion'] = _ich_conv.values
    result['ichimoku_base']       = _ich_base.values
    result['ichimoku_span_a']     = _ich_span_a.values
    result['ichimoku_span_b']     = _ich_span_b.values

    _chan_df = calculate_chandelier_exit(df, period=22)
    result['chandelier_long']  = _chan_df['chandelier_long'].values
    result['chandelier_short'] = _chan_df['chandelier_short'].values

    # ── Volume ────────────────────────────────────────────────────────────────
    result['obv']    = calculate_obv(df).values
    result['mfi_14'] = calculate_mfi(df, period=14).values
    result['kvo']    = calculate_kvo(df).values

    return result


def insert_indicators(conn: psycopg2.extensions.connection, df: pd.DataFrame, target_dates: set) -> int:
    """Upsert computed indicator rows for target_dates."""
    df_new = df[df['date'].isin(target_dates)].copy()
    if df_new.empty:
        print("  No rows to insert.")
        return 0

    cols = [c for c in COLUMN_ORDER if c != 'id']
    col_str      = ', '.join(cols)
    placeholders = ', '.join(['%s'] * len(cols))

    update_set = ', '.join(
        f'{c}=EXCLUDED.{c}' for c in cols if c not in ('date', 'symbol')
    )
    upsert_sql = (
        f'INSERT INTO {INDICATORS_TABLE} ({col_str}) VALUES ({placeholders}) '
        f'ON CONFLICT {_UPSERT_CONFLICT_COLS} DO UPDATE SET {update_set}'
    )

    def _val(v):
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return None
        return float(v) if isinstance(v, (np.floating, float)) else v

    rows = []
    for _, row in df_new.iterrows():
        vals = [
            row.get(col) if col in ('date', 'symbol') else _val(row.get(col))
            for col in cols
        ]
        rows.append(vals)

    cur = conn.cursor()
    cur.executemany(upsert_sql, rows)
    conn.commit()
    return len(rows)
