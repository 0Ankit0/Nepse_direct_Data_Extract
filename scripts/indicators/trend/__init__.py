# Trend indicators package
from .moving_averages import sma, ema
from .adx import calculate_adx
from .trend_strength import calculate_slope, calculate_acceleration

__all__ = [
    'sma', 'ema',
    'calculate_adx',
    'calculate_slope', 'calculate_acceleration',
]