"""
Base strategy class for systematic trading strategies.

All strategies should inherit from this class and implement the generate_signals method.
"""

from abc import ABC, abstractmethod
import pandas as pd
from typing import Optional

from utils.logger import setup_logger


logger = setup_logger(__name__)


class BaseStrategy(ABC):
    """
    Abstract base class for trading strategies.

    Carver's approach emphasizes:
    1. Clear signal generation
    2. Continuous forecasts (not just binary long/short)
    3. Multiple timeframes and diversification
    """

    def __init__(self, name: str = "BaseStrategy"):
        """
        Initialize base strategy.

        Args:
            name: Strategy name
        """
        self.name = name
        logger.info(f"Initialized strategy: {self.name}")

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals from price data.

        Args:
            data: DataFrame with price data (must include 'Close' column)

        Returns:
            Series of trading signals (typically -1 to 1 or -20 to 20 in Carver's framework)
        """
        pass

    def validate_data(self, data: pd.DataFrame) -> bool:
        """
        Validate input data format.

        Args:
            data: Input DataFrame

        Returns:
            True if data is valid
        """
        if data is None or data.empty:
            logger.error("Data is None or empty")
            return False

        if 'Close' not in data.columns:
            logger.error("Data must contain 'Close' column")
            return False

        return True

    def calculate_forecast_scalar(
        self,
        raw_forecast: pd.Series,
        target_abs_forecast: float = 10.0
    ) -> pd.Series:
        """
        Scale raw forecasts to Carver's standard forecast range.

        Carver uses forecasts in the range of -20 to +20, with 10 being
        the average absolute forecast. This method scales raw signals accordingly.

        Args:
            raw_forecast: Raw forecast series
            target_abs_forecast: Target average absolute forecast (default 10)

        Returns:
            Scaled forecast series
        """
        # Calculate average absolute forecast
        avg_abs_forecast = raw_forecast.abs().mean()

        if avg_abs_forecast == 0:
            logger.warning("Average absolute forecast is zero")
            return raw_forecast

        # Calculate scaling factor
        scalar = target_abs_forecast / avg_abs_forecast

        # Scale and cap forecasts
        scaled_forecast = raw_forecast * scalar
        scaled_forecast = scaled_forecast.clip(-20, 20)

        logger.debug(
            f"Forecast scalar: {scalar:.2f}, "
            f"avg abs before: {avg_abs_forecast:.2f}, "
            f"avg abs after: {scaled_forecast.abs().mean():.2f}"
        )

        return scaled_forecast

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
