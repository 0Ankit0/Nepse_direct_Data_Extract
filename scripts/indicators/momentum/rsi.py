"""
Relative Strength Index (RSI) — Wilder's smoothing method.
"""

import pandas as pd

def rsi(df, period: int = 14, column: str = 'close'):
    def compute(s):
        delta = s.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        # Wilder's smoothing: alpha = 1/period, require at least `period` observations
        avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, float('nan'))
        return 100 - (100 / (1 + rs))

    return df.groupby('symbol')[column].transform(compute)
