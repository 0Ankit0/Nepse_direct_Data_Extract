"""
Trend strength indicators: Linear Regression Slope and Momentum Acceleration
"""
import pandas as pd
import numpy as np
from scipy import stats

def calculate_slope(df: pd.DataFrame, window: int = 20, column: str = 'close') -> pd.Series:
    """
    Calculate the rolling linear regression slope.
    
    Ref: Chapter 13.2.3
    """
    def _linreg_slope(x):
        if len(x) < 2:
            return 0.0
        slope, _, _, _, _ = stats.linregress(np.arange(len(x)), x)
        return slope

    return df.groupby('symbol')[column].transform(lambda x: x.rolling(window=window).apply(_linreg_slope, raw=True))

def calculate_acceleration(df: pd.DataFrame, window: int = 12, smooth: int = 3, column: str = 'close') -> pd.Series:
    """
    Calculate momentum acceleration (Rate of Change of ROC).
    
    Ref: Chapter 13.3.3
    """
    def _accel_group(group_series):
        # ROC (First Momentum)
        roc = group_series.pct_change(periods=window) * 100
        # Acceleration (Change in ROC)
        return roc.diff(periods=smooth)
        
    return df.groupby('symbol')[column].transform(_accel_group)
