"""
Ichimoku Cloud indicator components — grouped per symbol.
"""

import pandas as pd


def ichimoku(df,
             conversion_period: int = 9,
             base_period: int = 26,
             span_b_period: int = 52):
    """Compute Ichimoku cloud lines grouped per symbol.

    Returns (conversion, base, span_a, span_b) Series.
    Span A and Span B are shifted forward by `base_period` periods (standard plot offset).
    """
    def _group(g):
        high = g['high']
        low  = g['low']
        conversion = (high.rolling(conversion_period).max() + low.rolling(conversion_period).min()) / 2
        base       = (high.rolling(base_period).max()       + low.rolling(base_period).min())       / 2
        span_a     = ((conversion + base) / 2).shift(base_period)
        span_b     = ((high.rolling(span_b_period).max() + low.rolling(span_b_period).min()) / 2).shift(base_period)
        return pd.DataFrame({
            'conversion': conversion,
            'base':       base,
            'span_a':     span_a,
            'span_b':     span_b,
        }, index=g.index)

    result = df.groupby('symbol', group_keys=False).apply(_group)
    return result['conversion'], result['base'], result['span_a'], result['span_b']
