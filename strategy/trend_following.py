"""
Trend-following strategies based on Robert Carver's methods.

Carver emphasizes trend-following as the core of systematic trading,
using multiple timeframes and exponential moving averages.
"""

import pandas as pd
import numpy as np
from typing import Optional

from .base_strategy import BaseStrategy
from config.settings import Settings
from utils.logger import setup_logger


logger = setup_logger(__name__)


class MovingAverageCrossover(BaseStrategy):
    """
    Simple moving average crossover strategy.

    This is a classic trend-following approach:
    - Buy when fast MA crosses above slow MA
    - Sell when fast MA crosses below slow MA

    While simpler than Carver's EWMAC, it's a good starting point.
    """

    def __init__(
        self,
        fast_period: int = None,
        slow_period: int = None,
        name: str = "MA_Crossover"
    ):
        """
        Initialize MA crossover strategy.

        Args:
            fast_period: Fast moving average period
            slow_period: Slow moving average period
            name: Strategy name
        """
        super().__init__(name)
        self.fast_period = fast_period or Settings.MA_FAST
        self.slow_period = slow_period or Settings.MA_SLOW

        logger.info(
            f"MA Crossover: fast={self.fast_period}, slow={self.slow_period}"
        )

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on MA crossover.

        Args:
            data: DataFrame with 'Close' prices

        Returns:
            Series of trading signals (-1, 0, or 1)
        """
        if not self.validate_data(data):
            return pd.Series(index=data.index, dtype=float)

        # Calculate moving averages
        ma_fast = data['Close'].rolling(window=self.fast_period).mean()
        ma_slow = data['Close'].rolling(window=self.slow_period).mean()

        # Generate raw signals
        # 1 when fast > slow (uptrend), -1 when fast < slow (downtrend)
        signals = pd.Series(index=data.index, dtype=float)
        signals[ma_fast > ma_slow] = 1.0
        signals[ma_fast < ma_slow] = -1.0
        signals[ma_fast == ma_slow] = 0.0

        # Forward fill NaN values
        signals = signals.fillna(0.0)

        logger.debug(f"Generated {len(signals)} signals for MA crossover")

        return signals


class EWMAC(BaseStrategy):
    """
    Exponentially Weighted Moving Average Crossover (EWMAC).

    This is one of Carver's core trading rules. EWMAC uses exponential
    moving averages, which are more responsive to recent prices.

    Carver typically uses multiple EWMAC rules with different speeds
    (e.g., EWMAC 16/64, EWMAC 32/128, EWMAC 64/256) and combines them.
    """

    def __init__(
        self,
        fast_span: int = None,
        slow_span: int = None,
        name: str = "EWMAC"
    ):
        """
        Initialize EWMAC strategy.

        Args:
            fast_span: Fast EMA span (Carver uses 16, 32, 64)
            slow_span: Slow EMA span (Carver uses 64, 128, 256)
            name: Strategy name
        """
        super().__init__(name)
        self.fast_span = fast_span or Settings.MA_FAST
        self.slow_span = slow_span or Settings.MA_SLOW

        logger.info(
            f"EWMAC initialized: fast={self.fast_span}, slow={self.slow_span}"
        )

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate EWMAC trading signals.

        The signal is the difference between fast and slow EMAs,
        normalized by price volatility (as per Carver's method).

        Args:
            data: DataFrame with 'Close' prices

        Returns:
            Series of continuous trading forecasts
        """
        if not self.validate_data(data):
            return pd.Series(index=data.index, dtype=float)

        prices = data['Close']

        # Calculate exponential moving averages
        ema_fast = prices.ewm(span=self.fast_span, adjust=False).mean()
        ema_slow = prices.ewm(span=self.slow_span, adjust=False).mean()

        # Raw forecast: difference between fast and slow EMAs
        raw_forecast = ema_fast - ema_slow

        # Normalize by price level (Carver divides by price)
        # This makes the signal comparable across different price levels
        normalized_forecast = raw_forecast / prices

        # Scale to Carver's standard forecast range (-20 to +20, avg abs = 10)
        scaled_forecast = self.calculate_forecast_scalar(normalized_forecast)

        logger.debug(
            f"Generated EWMAC signals: "
            f"mean={scaled_forecast.mean():.2f}, "
            f"std={scaled_forecast.std():.2f}"
        )

        return scaled_forecast


class MultipleEWMAC(BaseStrategy):
    """
    Multiple EWMAC rules combined together.

    Carver combines multiple trading rules with different speeds to achieve
    better diversification. This class implements a simple equal-weighted
    combination of EWMAC rules.
    """

    def __init__(
        self,
        rule_configs: list = None,
        name: str = "Multiple_EWMAC"
    ):
        """
        Initialize multiple EWMAC strategy.

        Args:
            rule_configs: List of (fast, slow) tuples for different EWMAC rules
            name: Strategy name
        """
        super().__init__(name)

        # Default: Carver's typical combinations
        if rule_configs is None:
            rule_configs = [
                (16, 64),   # Fast rule
                (32, 128),  # Medium rule
                (64, 256),  # Slow rule
            ]

        self.rules = [
            EWMAC(fast, slow, name=f"EWMAC_{fast}_{slow}")
            for fast, slow in rule_configs
        ]

        logger.info(f"Multiple EWMAC with {len(self.rules)} rules")

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate combined signals from multiple EWMAC rules.

        Args:
            data: DataFrame with 'Close' prices

        Returns:
            Series of combined forecasts
        """
        if not self.validate_data(data):
            return pd.Series(index=data.index, dtype=float)

        # Generate signals for each rule
        all_signals = []
        for rule in self.rules:
            signals = rule.generate_signals(data)
            all_signals.append(signals)

        # Combine signals (equal weighting)
        combined_signals = pd.concat(all_signals, axis=1).mean(axis=1)

        # Ensure combined signals stay in valid range
        combined_signals = combined_signals.clip(-20, 20)

        logger.debug(
            f"Combined {len(self.rules)} EWMAC rules: "
            f"mean={combined_signals.mean():.2f}"
        )

        return combined_signals
