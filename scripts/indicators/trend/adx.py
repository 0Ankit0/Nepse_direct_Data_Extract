"""
Average Directional Index (ADX) indicator
"""
import pandas as pd
import numpy as np

def calculate_adx(df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    """
    Calculate Average Directional Index (ADX), Plus DI, and Minus DI.
    
    Ref: Chapter 13.2.3
    """
    def _adx_series(group):
        high = group['high']
        low = group['low']
        close = group['close']
        
        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Directional Movement
        high_diff = high.diff()
        low_diff = (low.shift(1) - low)
        
        plus_dm = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0)
        minus_dm = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0)
        
        plus_dm = pd.Series(plus_dm, index=group.index)
        minus_dm = pd.Series(minus_dm, index=group.index)
        
        # Wilder's Smoothing (alpha = 1/period)
        def wilders_smoothing(series, period):
            return series.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
        
        atr = wilders_smoothing(tr, window)
        smooth_plus_dm = wilders_smoothing(plus_dm, window)
        smooth_minus_dm = wilders_smoothing(minus_dm, window)
        
        plus_di = 100 * (smooth_plus_dm / atr)
        minus_di = 100 * (smooth_minus_dm / atr)
        
        dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di))
        adx = wilders_smoothing(dx, window)
        
        return pd.DataFrame({
            'adx': adx,
            'plus_di': plus_di,
            'minus_di': minus_di
        }, index=group.index)

    return df.groupby('symbol', group_keys=False).apply(_adx_series)
