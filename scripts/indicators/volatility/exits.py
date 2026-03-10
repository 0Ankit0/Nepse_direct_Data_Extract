"""
Exit indicators: Chandelier Exit
"""
import pandas as pd
import numpy as np

def calculate_chandelier_exit(df: pd.DataFrame, period: int = 22, multiplier: float = 3.0) -> pd.DataFrame:
    """
    Calculate Chandelier Exit for trailing stop placement.
    
    Ref: Chapter 13.4.3
    """
    def _chandelier_group(group):
        high = group['high']
        low = group['low']
        close = group['close']
        prev_close = close.shift(1)
        
        # True Range
        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # ATR (Simple Moving Average of TR)
        atr_val = tr.rolling(period).mean()
        
        highest_high = high.rolling(period).max()
        lowest_low = low.rolling(period).min()
        
        long_exit = highest_high - (atr_val * multiplier)
        short_exit = lowest_low + (atr_val * multiplier)
        
        return pd.DataFrame({
            'chandelier_long': long_exit,
            'chandelier_short': short_exit
        }, index=group.index)

    return df.groupby('symbol', group_keys=False).apply(_chandelier_group)
