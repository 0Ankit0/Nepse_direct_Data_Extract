"""
Stochastic Oscillator — %K and %D (slow stochastic).

%K = (Close - Lowest Low[k_period]) / (Highest High[k_period] - Lowest Low[k_period]) * 100
%D = SMA(%K, d_period)
"""

import pandas as pd

def stochastic(df, k_period: int = 14, d_period: int = 3):
    def _group(g):
        low_min  = g['low'].rolling(k_period).min()
        high_max = g['high'].rolling(k_period).max()
        denom = (high_max - low_min).replace(0, float('nan'))
        k = (g['close'] - low_min) / denom * 100
        d = k.rolling(d_period).mean()
        return pd.DataFrame({'stoch_k': k, 'stoch_d': d}, index=g.index)

    result = df.groupby('symbol', group_keys=False).apply(_group)
    return result['stoch_k'], result['stoch_d']
