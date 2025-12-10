"""
Trading strategy module implementing systematic trading strategies.
"""

from .base_strategy import BaseStrategy
from .breakout import (
    DonchianBreakout,
    RangeBreakout,
    SupportResistanceBreakout,
    VolatilityBreakout,
)
from .carry import DividendYieldCarry, SeasonalityCarry, ValueStrategy, YieldCurveCarry
from .mean_reversion import BollingerBands, RSIMeanReversion, ZScoreMeanReversion
from .momentum import MACD, DualMomentum, RateOfChange, RelativeStrength
from .trend_following import EWMAC, MovingAverageCrossover, MultipleEWMAC

__all__ = [
    "BaseStrategy",
    # Trend Following
    "MovingAverageCrossover",
    "EWMAC",
    "MultipleEWMAC",
    # Mean Reversion
    "BollingerBands",
    "RSIMeanReversion",
    "ZScoreMeanReversion",
    # Momentum
    "RateOfChange",
    "RelativeStrength",
    "DualMomentum",
    "MACD",
    # Breakout
    "DonchianBreakout",
    "VolatilityBreakout",
    "SupportResistanceBreakout",
    "RangeBreakout",
    # Carry
    "DividendYieldCarry",
    "ValueStrategy",
    "YieldCurveCarry",
    "SeasonalityCarry",
]
