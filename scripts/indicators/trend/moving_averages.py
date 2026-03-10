"""
Moving averages utilities
"""

def sma(df, period: int = 5, column: str = 'close'):
    return df.groupby('symbol')[column].transform(lambda x: x.rolling(period).mean())

def ema(df, period: int = 12, column: str = 'close'):
    # exponential moving average; Pandas ewm handles min_periods
    return df.groupby('symbol')[column].transform(lambda x: x.ewm(span=period, adjust=False).mean())
