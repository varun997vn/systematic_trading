"""
Base Strategy Class
All trading strategies inherit from this class
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import polars as pl


class Strategy(ABC):
    """
    Base class for all trading strategies
    Signal scale: -20 to 20
    - Negative: Sell signals (-20 strongest, -5 weakest)
    - Zero: Neutral
    - Positive: Buy signals (5 weakest, 20 strongest)
    """

    def __init__(self, name: str, parameters: Dict[str, Any] = None):
        self.name = name
        self.parameters = parameters or {}

    @abstractmethod
    def calculate_signal(self, df: pl.DataFrame, index: int) -> int:
        """
        Calculate trading signal for a given index

        Args:
            df: DataFrame with OHLCV data and calculated indicators
            index: Current row index

        Returns:
            int: Signal from -20 to 20
        """
        pass

    @abstractmethod
    def add_indicators(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Add technical indicators required by this strategy

        Args:
            df: DataFrame with OHLCV data

        Returns:
            DataFrame with added indicator columns
        """
        pass

    def validate_signal(self, signal: int) -> int:
        """Ensure signal is within valid range"""
        return max(-20, min(20, signal))

    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}')"