"""
Average True Range (ATR) — Wilder's smoothing, grouped per symbol.
"""

import pandas as pd

def atr(df, period: int = 14):
    def _atr_group(group):
        high = group['high']
        low = group['low']
        close = group['close']
        prev_close = close.shift(1)
        tr = pd.concat([
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ], axis=1).max(axis=1)
        # Wilder's smoothing: alpha = 1/period
        return tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    return df.groupby('symbol', group_keys=False).apply(_atr_group)
