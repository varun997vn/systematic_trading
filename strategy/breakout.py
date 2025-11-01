"""
Breakout strategies for systematic trading.

Breakout strategies attempt to capture moves when price breaks through
support/resistance levels or trading ranges.
"""

import pandas as pd
import numpy as np
from typing import Optional

from .base_strategy import BaseStrategy
from config.settings import Settings
from utils.logger import setup_logger


logger = setup_logger(__name__)


class DonchianBreakout(BaseStrategy):
    """
    Donchian Channel breakout strategy.

    Trades breakouts of the highest high or lowest low over a given period.
    This is similar to the famous Turtle Trading system.

    Buy when price breaks above the highest high.
    Sell when price breaks below the lowest low.
    """

    def __init__(
        self,
        entry_period: int = 20,
        exit_period: int = 10,
        name: str = "Donchian_Breakout"
    ):
        """
        Initialize Donchian breakout strategy.

        Args:
            entry_period: Period for entry breakout
            exit_period: Period for exit breakout
            name: Strategy name
        """
        super().__init__(name)
        self.entry_period = entry_period
        self.exit_period = exit_period

        logger.info(
            f"Donchian Breakout: entry={self.entry_period}, exit={self.exit_period}"
        )

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate breakout signals based on Donchian Channels.

        Args:
            data: DataFrame with 'High', 'Low', 'Close' prices

        Returns:
            Series of trading signals
        """
        if not self.validate_data(data):
            return pd.Series(index=data.index, dtype=float)

        # Use High/Low if available, otherwise use Close
        if 'High' in data.columns and 'Low' in data.columns:
            high = data['High']
            low = data['Low']
        else:
            high = data['Close']
            low = data['Close']

        prices = data['Close']

        # Calculate Donchian channels
        upper_channel = high.rolling(window=self.entry_period).max()
        lower_channel = low.rolling(window=self.entry_period).min()

        # Calculate channel width for normalization
        channel_width = upper_channel - lower_channel

        # Calculate position within channel
        # 0 = at lower channel, 1 = at upper channel
        position_in_channel = (prices - lower_channel) / channel_width

        # Generate signals
        # Strong buy when breaking above upper channel
        # Strong sell when breaking below lower channel
        signals = pd.Series(0.0, index=data.index)

        # Breakout signals
        signals[prices >= upper_channel] = 1.0
        signals[prices <= lower_channel] = -1.0

        # Gradual signal strength based on position in channel
        neutral_zone = (position_in_channel > 0.3) & (position_in_channel < 0.7)
        signals[neutral_zone] = (position_in_channel[neutral_zone] - 0.5) * 2

        # Scale to forecast range
        signals = signals * 10
        signals = signals.fillna(0.0)

        logger.debug(f"Generated Donchian signals: mean={signals.mean():.2f}")

        return signals


class VolatilityBreakout(BaseStrategy):
    """
    Volatility-adjusted breakout strategy.

    Identifies breakouts that are significant relative to recent volatility.
    This helps filter out false breakouts in low volatility periods.
    """

    def __init__(
        self,
        lookback: int = 20,
        threshold: float = 1.5,
        name: str = "Volatility_Breakout"
    ):
        """
        Initialize volatility breakout strategy.

        Args:
            lookback: Lookback period for volatility calculation
            threshold: Number of standard deviations for breakout
            name: Strategy name
        """
        super().__init__(name)
        self.lookback = lookback
        self.threshold = threshold

        logger.info(
            f"Volatility Breakout: lookback={self.lookback}, threshold={self.threshold}"
        )

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate volatility-adjusted breakout signals.

        Args:
            data: DataFrame with 'Close' prices

        Returns:
            Series of trading signals
        """
        if not self.validate_data(data):
            return pd.Series(index=data.index, dtype=float)

        prices = data['Close']

        # Calculate rolling mean and volatility
        rolling_mean = prices.rolling(window=self.lookback).mean()
        rolling_std = prices.rolling(window=self.lookback).std()

        # Calculate breakout bands
        upper_band = rolling_mean + (rolling_std * self.threshold)
        lower_band = rolling_mean - (rolling_std * self.threshold)

        # Calculate z-score (standardized distance from mean)
        z_score = (prices - rolling_mean) / rolling_std

        # Generate signals based on z-score
        # Strong signal when price is beyond threshold
        signals = z_score / self.threshold

        # Clip to reasonable range
        signals = signals.clip(-1.5, 1.5) / 1.5 * 10
        signals = signals.fillna(0.0)

        logger.debug(
            f"Generated Volatility Breakout signals: mean={signals.mean():.2f}"
        )

        return signals


class SupportResistanceBreakout(BaseStrategy):
    """
    Support and Resistance level breakout strategy.

    Identifies key support and resistance levels using pivot points
    and generates signals when price breaks through these levels.
    """

    def __init__(
        self,
        pivot_lookback: int = 20,
        breakout_threshold: float = 0.02,
        name: str = "SR_Breakout"
    ):
        """
        Initialize support/resistance breakout strategy.

        Args:
            pivot_lookback: Lookback period for pivot calculation
            breakout_threshold: Percentage threshold for breakout confirmation
            name: Strategy name
        """
        super().__init__(name)
        self.pivot_lookback = pivot_lookback
        self.breakout_threshold = breakout_threshold

        logger.info(
            f"SR Breakout: lookback={self.pivot_lookback}, "
            f"threshold={self.breakout_threshold}"
        )

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate support/resistance breakout signals.

        Args:
            data: DataFrame with 'High', 'Low', 'Close' prices

        Returns:
            Series of trading signals
        """
        if not self.validate_data(data):
            return pd.Series(index=data.index, dtype=float)

        # Use High/Low if available
        if 'High' in data.columns and 'Low' in data.columns:
            high = data['High']
            low = data['Low']
        else:
            high = data['Close']
            low = data['Close']

        prices = data['Close']

        # Calculate pivot points (simplified version)
        pivot = (high + low + prices) / 3
        pivot_rolling = pivot.rolling(window=self.pivot_lookback).mean()

        # Calculate resistance and support levels
        resistance = pivot_rolling * (1 + self.breakout_threshold)
        support = pivot_rolling * (1 - self.breakout_threshold)

        # Calculate distance from support/resistance
        dist_to_resistance = (prices - resistance) / resistance
        dist_to_support = (prices - support) / support

        # Generate signals
        signals = pd.Series(0.0, index=data.index)

        # Bullish breakout above resistance
        signals[prices > resistance] = (dist_to_resistance[prices > resistance] / self.breakout_threshold).clip(0, 2)

        # Bearish breakout below support
        signals[prices < support] = (dist_to_support[prices < support] / self.breakout_threshold).clip(-2, 0)

        # Scale to forecast range
        signals = signals * 5
        signals = signals.fillna(0.0)

        logger.debug(f"Generated SR Breakout signals: mean={signals.mean():.2f}")

        return signals


class RangeBreakout(BaseStrategy):
    """
    Trading range breakout strategy.

    Identifies consolidation periods (trading ranges) and trades breakouts
    from these ranges with increased volatility.
    """

    def __init__(
        self,
        range_period: int = 20,
        volatility_factor: float = 1.5,
        name: str = "Range_Breakout"
    ):
        """
        Initialize range breakout strategy.

        Args:
            range_period: Period to identify trading range
            volatility_factor: Factor for volatility expansion detection
            name: Strategy name
        """
        super().__init__(name)
        self.range_period = range_period
        self.volatility_factor = volatility_factor

        logger.info(
            f"Range Breakout: period={self.range_period}, "
            f"vol_factor={self.volatility_factor}"
        )

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate range breakout signals.

        Args:
            data: DataFrame with 'Close' prices

        Returns:
            Series of trading signals
        """
        if not self.validate_data(data):
            return pd.Series(index=data.index, dtype=float)

        prices = data['Close']

        # Calculate range boundaries
        range_high = prices.rolling(window=self.range_period).max()
        range_low = prices.rolling(window=self.range_period).min()
        range_mid = (range_high + range_low) / 2

        # Calculate current volatility vs historical
        returns = prices.pct_change()
        current_vol = returns.rolling(window=5).std()
        historical_vol = returns.rolling(window=self.range_period).std()

        # Detect volatility expansion (breakout confirmation)
        vol_expansion = current_vol / historical_vol

        # Calculate position relative to range
        range_position = (prices - range_mid) / (range_high - range_low)

        # Generate signals: position * volatility confirmation
        signals = range_position * vol_expansion.clip(0, self.volatility_factor) / self.volatility_factor

        # Scale to forecast range
        signals = signals.clip(-1, 1) * 10
        signals = signals.fillna(0.0)

        logger.debug(f"Generated Range Breakout signals: mean={signals.mean():.2f}")

        return signals
