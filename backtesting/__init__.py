"""
Backtesting module for testing trading strategies on historical data.
"""

from .backtest_engine import BacktestEngine
from .performance import PerformanceAnalyzer

__all__ = ['BacktestEngine', 'PerformanceAnalyzer']
