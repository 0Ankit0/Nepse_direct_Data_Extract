"""
Commodity Channel Index (CCI).

CCI = (Typical Price - SMA(TP, period)) / (0.015 * Mean Absolute Deviation(TP, period))

Typical Price (TP) = (High + Low + Close) / 3
The constant 0.015 ensures ~75% of values fall between ±100.
"""

import pandas as pd
import numpy as np

def cci(df, period: int = 20):
    def _group(g):
        tp  = (g['high'] + g['low'] + g['close']) / 3
        sma = tp.rolling(period).mean()
        mad = tp.rolling(period).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)
        return (tp - sma) / (0.015 * mad.replace(0, float('nan')))

    return df.groupby('symbol', group_keys=False).apply(_group)
