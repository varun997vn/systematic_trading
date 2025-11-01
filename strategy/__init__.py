"""
Trading strategy module implementing systematic trading strategies.
"""

from .base_strategy import BaseStrategy
from .trend_following import MovingAverageCrossover, EWMAC, MultipleEWMAC
from .mean_reversion import BollingerBands, RSIMeanReversion, ZScoreMeanReversion
from .momentum import RateOfChange, RelativeStrength, DualMomentum, MACD
from .breakout import (
    DonchianBreakout,
    VolatilityBreakout,
    SupportResistanceBreakout,
    RangeBreakout
)
from .carry import (
    DividendYieldCarry,
    ValueStrategy,
    YieldCurveCarry,
    SeasonalityCarry
)

__all__ = [
    'BaseStrategy',
    # Trend Following
    'MovingAverageCrossover',
    'EWMAC',
    'MultipleEWMAC',
    # Mean Reversion
    'BollingerBands',
    'RSIMeanReversion',
    'ZScoreMeanReversion',
    # Momentum
    'RateOfChange',
    'RelativeStrength',
    'DualMomentum',
    'MACD',
    # Breakout
    'DonchianBreakout',
    'VolatilityBreakout',
    'SupportResistanceBreakout',
    'RangeBreakout',
    # Carry
    'DividendYieldCarry',
    'ValueStrategy',
    'YieldCurveCarry',
    'SeasonalityCarry',
]
