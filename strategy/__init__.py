"""
Trading strategy module implementing systematic trading strategies.
"""

from .base_strategy import BaseStrategy
from .trend_following import MovingAverageCrossover, EWMAC

__all__ = ['BaseStrategy', 'MovingAverageCrossover', 'EWMAC']
