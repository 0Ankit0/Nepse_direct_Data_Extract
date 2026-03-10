"""
Bollinger Bands — uses population standard deviation (ddof=0) per Bollinger's definition.
"""

def bollinger_bands(df, period: int = 20, stddev: float = 2.0, column: str = 'close'):
    mid    = df.groupby('symbol')[column].transform(lambda x: x.rolling(period).mean())
    std    = df.groupby('symbol')[column].transform(lambda x: x.rolling(period).std(ddof=0))
    upper  = mid + stddev * std
    lower  = mid - stddev * std
    return upper, lower
