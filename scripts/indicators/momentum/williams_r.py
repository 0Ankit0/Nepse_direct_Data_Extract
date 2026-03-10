"""
Williams %R indicator.

%R = (Highest High[period] - Close) / (Highest High[period] - Lowest Low[period]) * -100

Oscillates between -100 (oversold) and 0 (overbought).
"""

import pandas as pd

def williams_r(df, period: int = 14):
    def _group(g):
        high_max = g['high'].rolling(period).max()
        low_min  = g['low'].rolling(period).min()
        denom = (high_max - low_min).replace(0, float('nan'))
        return (high_max - g['close']) / denom * -100

    return df.groupby('symbol', group_keys=False).apply(_group)
