"""
MACD indicator — signal line is EWM of the MACD line, not of price.
"""

import pandas as pd
from ..trend.moving_averages import ema

def macd(df, fast: int = 12, slow: int = 26, signal: int = 9, column: str = 'close'):
    ema_fast = ema(df, period=fast, column=column)
    ema_slow = ema(df, period=slow, column=column)
    macd_line = ema_fast - ema_slow

    # Signal line: EWM of the MACD line, grouped per symbol
    macd_s = macd_line.copy()
    macd_s.name = '_macd'
    tmp = df[['symbol']].copy()
    tmp['_macd'] = macd_s
    signal_line = tmp.groupby('symbol')['_macd'].transform(
        lambda x: x.ewm(span=signal, adjust=False).mean()
    )

    hist = macd_line - signal_line
    return macd_line, signal_line, hist
