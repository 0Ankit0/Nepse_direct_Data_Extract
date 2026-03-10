"""
Momentum indicators
"""

def momentum(df, period: int = 5, column: str = 'close'):
    """Return a series representing percent change over `period` steps."""
    return df.groupby('symbol')[column].transform(lambda x: x.pct_change(period))
