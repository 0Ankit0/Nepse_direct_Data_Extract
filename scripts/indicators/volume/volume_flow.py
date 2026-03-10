"""
Volume-based indicators: OBV, MFI, and Klinger Oscillator
"""
import pandas as pd
import numpy as np

def calculate_obv(df: pd.DataFrame) -> pd.Series:
    """
    Calculate On-Balance Volume (OBV).
    
    """
    def _obv_group(group):
        close = group['close']
        vol = group['vol']
        # Direction: +1 if close > previous close, -1 if less, 0 if equal
        direction = np.sign(close.diff()).fillna(0)
        return (vol * direction).cumsum()
        
    # `include_groups=False` prevents the group labels being included
    # in the result when pandas deprecates current behaviour.
    return df.groupby('symbol', group_keys=False).apply(_obv_group, include_groups=False)

def calculate_mfi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Money Flow Index (MFI).
    
    """
    def _mfi_group(group):
        tp = (group['high'] + group['low'] + group['close']) / 3
        rmf = tp * group['vol']
        
        diff = tp.diff()
        pos_mf = np.where(diff > 0, rmf, 0)
        neg_mf = np.where(diff < 0, rmf, 0)
        
        pos_mf_sum = pd.Series(pos_mf, index=group.index).rolling(period).sum()
        neg_mf_sum = pd.Series(neg_mf, index=group.index).rolling(period).sum()
        
        # Avoid division by zero
        mfr = pos_mf_sum / neg_mf_sum.replace(0, np.nan)
        mfi = 100 - (100 / (1 + mfr))
        return mfi.fillna(50) # Neutral value
        
    return df.groupby('symbol', group_keys=False).apply(_mfi_group, include_groups=False)

def calculate_kvo(df: pd.DataFrame, fast: int = 34, slow: int = 55) -> pd.Series:
    """
    Calculate Klinger Volume Oscillator (KVO).
    
    """
    def _kvo_group(group):
        tp = (group['high'] + group['low'] + group['close']) / 3
        dm = tp.diff()
        # Volume Force (VF)
        vf = group['vol'] * np.where(dm > 0, 1, -1) * abs(dm)
        vf = pd.Series(vf, index=group.index)
        
        kvo = vf.ewm(span=fast, adjust=False).mean() - vf.ewm(span=slow, adjust=False).mean()
        return kvo
        
    return df.groupby('symbol', group_keys=False).apply(_kvo_group, include_groups=False)
