"""
Momentum strategies for systematic trading.

Momentum strategies profit from the continuation of existing trends.
They buy assets that have performed well and sell assets that have performed poorly.
"""

import pandas as pd
import numpy as np
from typing import Optional, List

from .base_strategy import BaseStrategy
from config.settings import Settings
from utils.logger import setup_logger


logger = setup_logger(__name__)


class RateOfChange(BaseStrategy):
    """
    Rate of Change (ROC) momentum strategy.

    Measures the percentage change in price over a given period.
    Positive ROC suggests upward momentum, negative ROC suggests downward momentum.
    """

    def __init__(
        self,
        period: int = 12,
        name: str = "ROC_Momentum"
    ):
        """
        Initialize ROC momentum strategy.

        Args:
            period: Lookback period for ROC calculation
            name: Strategy name
        """
        super().__init__(name)
        self.period = period

        logger.info(f"ROC Momentum: period={self.period}")

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate momentum signals based on Rate of Change.

        Args:
            data: DataFrame with 'Close' prices

        Returns:
            Series of trading signals
        """
        if not self.validate_data(data):
            return pd.Series(index=data.index, dtype=float)

        prices = data['Close']

        # Calculate ROC: (current_price / price_n_periods_ago - 1) * 100
        roc = ((prices / prices.shift(self.period)) - 1) * 100

        # Normalize ROC to generate signals
        # Using rolling z-score for normalization
        roc_mean = roc.rolling(window=50).mean()
        roc_std = roc.rolling(window=50).std()
        normalized_roc = (roc - roc_mean) / roc_std

        # Scale to forecast range
        signals = normalized_roc.clip(-2, 2) / 2 * 10
        signals = signals.fillna(0.0)

        logger.debug(f"Generated ROC signals: mean={signals.mean():.2f}")

        return signals


class RelativeStrength(BaseStrategy):
    """
    Relative Strength momentum strategy.

    Compares an asset's performance to a benchmark or its own historical performance.
    """

    def __init__(
        self,
        short_period: int = 20,
        long_period: int = 60,
        name: str = "Relative_Strength"
    ):
        """
        Initialize Relative Strength strategy.

        Args:
            short_period: Short-term performance period
            long_period: Long-term performance period
            name: Strategy name
        """
        super().__init__(name)
        self.short_period = short_period
        self.long_period = long_period

        logger.info(
            f"Relative Strength: short={self.short_period}, long={self.long_period}"
        )

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate momentum signals based on relative strength.

        Args:
            data: DataFrame with 'Close' prices

        Returns:
            Series of trading signals
        """
        if not self.validate_data(data):
            return pd.Series(index=data.index, dtype=float)

        prices = data['Close']

        # Calculate returns over different periods
        short_return = prices.pct_change(self.short_period)
        long_return = prices.pct_change(self.long_period)

        # Relative strength: compare short-term to long-term momentum
        relative_strength = short_return - long_return

        # Normalize using rolling statistics
        rs_mean = relative_strength.rolling(window=50).mean()
        rs_std = relative_strength.rolling(window=50).std()
        normalized_rs = (relative_strength - rs_mean) / rs_std

        # Scale to forecast range
        signals = normalized_rs.clip(-2, 2) / 2 * 10
        signals = signals.fillna(0.0)

        logger.debug(f"Generated Relative Strength signals: mean={signals.mean():.2f}")

        return signals


class DualMomentum(BaseStrategy):
    """
    Dual Momentum strategy combining absolute and relative momentum.

    Absolute momentum: Is the asset trending up or down?
    Relative momentum: How does it compare to other assets?

    This implementation focuses on absolute momentum with multiple timeframes.
    """

    def __init__(
        self,
        periods: List[int] = None,
        name: str = "Dual_Momentum"
    ):
        """
        Initialize Dual Momentum strategy.

        Args:
            periods: List of lookback periods for momentum calculation
            name: Strategy name
        """
        super().__init__(name)
        self.periods = periods or [20, 60, 120]

        logger.info(f"Dual Momentum: periods={self.periods}")

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate momentum signals using multiple timeframes.

        Args:
            data: DataFrame with 'Close' prices

        Returns:
            Series of trading signals
        """
        if not self.validate_data(data):
            return pd.Series(index=data.index, dtype=float)

        prices = data['Close']

        # Calculate momentum for each period
        momentum_signals = []

        for period in self.periods:
            # Calculate return over period
            returns = prices.pct_change(period)

            # Normalize
            returns_mean = returns.rolling(window=100).mean()
            returns_std = returns.rolling(window=100).std()
            normalized = (returns - returns_mean) / returns_std

            # Clip and scale
            signal = normalized.clip(-2, 2) / 2
            momentum_signals.append(signal)

        # Combine signals from all periods (equal weighting)
        combined_signals = pd.concat(momentum_signals, axis=1).mean(axis=1)

        # Scale to forecast range
        combined_signals = combined_signals * 10
        combined_signals = combined_signals.fillna(0.0)

        logger.debug(
            f"Generated Dual Momentum signals: mean={combined_signals.mean():.2f}"
        )

        return combined_signals


class MACD(BaseStrategy):
    """
    Moving Average Convergence Divergence (MACD) momentum strategy.

    MACD measures the relationship between two moving averages.
    Signal line crossovers indicate momentum shifts.
    """

    def __init__(
        self,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        name: str = "MACD"
    ):
        """
        Initialize MACD strategy.

        Args:
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line EMA period
            name: Strategy name
        """
        super().__init__(name)
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period

        logger.info(
            f"MACD: fast={self.fast_period}, slow={self.slow_period}, "
            f"signal={self.signal_period}"
        )

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate momentum signals based on MACD.

        Args:
            data: DataFrame with 'Close' prices

        Returns:
            Series of trading signals
        """
        if not self.validate_data(data):
            return pd.Series(index=data.index, dtype=float)

        prices = data['Close']

        # Calculate MACD
        ema_fast = prices.ewm(span=self.fast_period, adjust=False).mean()
        ema_slow = prices.ewm(span=self.slow_period, adjust=False).mean()
        macd_line = ema_fast - ema_slow

        # Calculate signal line
        signal_line = macd_line.ewm(span=self.signal_period, adjust=False).mean()

        # MACD histogram (difference between MACD and signal line)
        macd_histogram = macd_line - signal_line

        # Normalize by price for scale independence
        normalized_histogram = macd_histogram / prices

        # Scale to forecast range
        histogram_std = normalized_histogram.rolling(window=50).std()
        signals = (normalized_histogram / histogram_std).clip(-2, 2) / 2 * 10
        signals = signals.fillna(0.0)

        logger.debug(f"Generated MACD signals: mean={signals.mean():.2f}")

        return signals
