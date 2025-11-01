"""
Mean reversion strategies for systematic trading.

Mean reversion strategies profit when prices return to their average after
moving away from it. These strategies work well in ranging markets.
"""

import pandas as pd
import numpy as np
from typing import Optional

from .base_strategy import BaseStrategy
from config.settings import Settings
from utils.logger import setup_logger


logger = setup_logger(__name__)


class BollingerBands(BaseStrategy):
    """
    Bollinger Bands mean reversion strategy.

    Buy when price crosses below lower band (oversold).
    Sell when price crosses above upper band (overbought).
    Exit when price returns to middle band.
    """

    def __init__(
        self,
        period: int = 20,
        num_std: float = 2.0,
        name: str = "Bollinger_Bands"
    ):
        """
        Initialize Bollinger Bands strategy.

        Args:
            period: Period for moving average
            num_std: Number of standard deviations for bands
            name: Strategy name
        """
        super().__init__(name)
        self.period = period
        self.num_std = num_std

        logger.info(
            f"Bollinger Bands: period={self.period}, std={self.num_std}"
        )

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate mean reversion signals based on Bollinger Bands.

        Args:
            data: DataFrame with 'Close' prices

        Returns:
            Series of trading signals (-1 to 1)
        """
        if not self.validate_data(data):
            return pd.Series(index=data.index, dtype=float)

        prices = data['Close']

        # Calculate Bollinger Bands
        middle_band = prices.rolling(window=self.period).mean()
        std = prices.rolling(window=self.period).std()
        upper_band = middle_band + (std * self.num_std)
        lower_band = middle_band - (std * self.num_std)

        # Calculate position of price within bands
        # -1 when below lower band, 0 at middle, +1 when above upper band
        band_position = (prices - middle_band) / (std * self.num_std)

        # Generate signals (inverted for mean reversion)
        # Buy (positive signal) when price is low (oversold)
        # Sell (negative signal) when price is high (overbought)
        signals = -band_position.clip(-1, 1)

        # Scale to forecast range
        signals = signals * 10  # Scale to -10 to +10
        signals = signals.fillna(0.0)

        logger.debug(f"Generated Bollinger Bands signals: mean={signals.mean():.2f}")

        return signals


class RSIMeanReversion(BaseStrategy):
    """
    RSI-based mean reversion strategy.

    Uses Relative Strength Index to identify overbought/oversold conditions.
    RSI > 70 typically indicates overbought (sell signal).
    RSI < 30 typically indicates oversold (buy signal).
    """

    def __init__(
        self,
        period: int = 14,
        overbought: float = 70.0,
        oversold: float = 30.0,
        name: str = "RSI_Mean_Reversion"
    ):
        """
        Initialize RSI mean reversion strategy.

        Args:
            period: RSI calculation period
            overbought: Overbought threshold (default 70)
            oversold: Oversold threshold (default 30)
            name: Strategy name
        """
        super().__init__(name)
        self.period = period
        self.overbought = overbought
        self.oversold = oversold

        logger.info(
            f"RSI Mean Reversion: period={self.period}, "
            f"OB={self.overbought}, OS={self.oversold}"
        )

    def calculate_rsi(self, prices: pd.Series) -> pd.Series:
        """
        Calculate Relative Strength Index.

        Args:
            prices: Price series

        Returns:
            RSI series (0-100)
        """
        # Calculate price changes
        delta = prices.diff()

        # Separate gains and losses
        gains = delta.where(delta > 0, 0.0)
        losses = -delta.where(delta < 0, 0.0)

        # Calculate average gains and losses
        avg_gains = gains.rolling(window=self.period).mean()
        avg_losses = losses.rolling(window=self.period).mean()

        # Calculate RS and RSI
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate mean reversion signals based on RSI.

        Args:
            data: DataFrame with 'Close' prices

        Returns:
            Series of trading signals (-1 to 1)
        """
        if not self.validate_data(data):
            return pd.Series(index=data.index, dtype=float)

        prices = data['Close']

        # Calculate RSI
        rsi = self.calculate_rsi(prices)

        # Generate signals based on RSI
        signals = pd.Series(index=data.index, dtype=float)

        # Buy signal when oversold (RSI < 30)
        # Sell signal when overbought (RSI > 70)
        # Linear interpolation in between
        signals = pd.Series(0.0, index=data.index)

        # Below oversold: strong buy signal
        signals[rsi < self.oversold] = (self.oversold - rsi[rsi < self.oversold]) / self.oversold

        # Above overbought: strong sell signal
        signals[rsi > self.overbought] = (self.overbought - rsi[rsi > self.overbought]) / (100 - self.overbought)

        # Clip and scale
        signals = signals.clip(-1, 1) * 10
        signals = signals.fillna(0.0)

        logger.debug(f"Generated RSI signals: mean={signals.mean():.2f}")

        return signals


class ZScoreMeanReversion(BaseStrategy):
    """
    Z-Score mean reversion strategy.

    Uses z-score to measure how far price has deviated from its mean.
    Z-score = (price - mean) / std

    Trade when price is significantly away from mean (high absolute z-score).
    """

    def __init__(
        self,
        lookback: int = 20,
        entry_threshold: float = 2.0,
        exit_threshold: float = 0.5,
        name: str = "ZScore_Mean_Reversion"
    ):
        """
        Initialize Z-Score mean reversion strategy.

        Args:
            lookback: Lookback period for mean and std calculation
            entry_threshold: Z-score threshold for entry
            exit_threshold: Z-score threshold for exit
            name: Strategy name
        """
        super().__init__(name)
        self.lookback = lookback
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold

        logger.info(
            f"Z-Score Mean Reversion: lookback={self.lookback}, "
            f"entry={self.entry_threshold}, exit={self.exit_threshold}"
        )

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate mean reversion signals based on Z-Score.

        Args:
            data: DataFrame with 'Close' prices

        Returns:
            Series of trading signals (-1 to 1)
        """
        if not self.validate_data(data):
            return pd.Series(index=data.index, dtype=float)

        prices = data['Close']

        # Calculate rolling mean and std
        rolling_mean = prices.rolling(window=self.lookback).mean()
        rolling_std = prices.rolling(window=self.lookback).std()

        # Calculate z-score
        z_score = (prices - rolling_mean) / rolling_std

        # Generate signals (inverted for mean reversion)
        # When z-score is high (price above mean), sell
        # When z-score is low (price below mean), buy
        signals = -z_score / self.entry_threshold

        # Clip and scale to forecast range
        signals = signals.clip(-1, 1) * 10
        signals = signals.fillna(0.0)

        logger.debug(
            f"Generated Z-Score signals: mean={signals.mean():.2f}, "
            f"avg_zscore={z_score.abs().mean():.2f}"
        )

        return signals
