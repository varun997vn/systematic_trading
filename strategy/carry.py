"""
Carry and value-based strategies for systematic trading.

Carry strategies profit from yield differentials and value anomalies.
For stocks, this can be implemented using dividend yield and fundamental ratios.
"""

import pandas as pd
import numpy as np
from typing import Optional

from .base_strategy import BaseStrategy
from config.settings import Settings
from utils.logger import setup_logger


logger = setup_logger(__name__)


class DividendYieldCarry(BaseStrategy):
    """
    Dividend yield carry strategy for stocks.

    Favors stocks with higher dividend yields relative to the market.
    This is an equity version of the carry trade.

    Note: This strategy requires dividend data which may need to be
    fetched separately or calculated from price adjustments.
    """

    def __init__(
        self,
        yield_lookback: int = 252,  # 1 year
        name: str = "Dividend_Carry"
    ):
        """
        Initialize dividend yield carry strategy.

        Args:
            yield_lookback: Lookback period for yield calculation
            name: Strategy name
        """
        super().__init__(name)
        self.yield_lookback = yield_lookback

        logger.info(f"Dividend Carry: lookback={self.yield_lookback}")

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate carry signals based on dividend yield.

        Args:
            data: DataFrame with 'Close' and optionally 'Dividends' column

        Returns:
            Series of trading signals
        """
        if not self.validate_data(data):
            return pd.Series(index=data.index, dtype=float)

        prices = data['Close']

        # Check if dividend data is available
        if 'Dividends' in data.columns:
            dividends = data['Dividends']
            # Calculate rolling dividend yield
            rolling_dividends = dividends.rolling(window=self.yield_lookback).sum()
            dividend_yield = rolling_dividends / prices
        else:
            # Estimate from price stability (stocks with stable prices may pay dividends)
            # This is a rough proxy and not ideal
            logger.warning("No dividend data available, using price-based proxy")
            returns_vol = prices.pct_change().rolling(window=self.yield_lookback).std()
            # Lower volatility = higher signal (proxy for dividend payers)
            dividend_yield = 1 / (1 + returns_vol * 100)

        # Normalize yield to generate signals
        yield_mean = dividend_yield.rolling(window=self.yield_lookback).mean()
        yield_std = dividend_yield.rolling(window=self.yield_lookback).std()

        # Z-score of dividend yield
        yield_zscore = (dividend_yield - yield_mean) / yield_std

        # Higher yield = positive signal
        signals = yield_zscore.clip(-2, 2) / 2 * 10
        signals = signals.fillna(0.0)

        logger.debug(f"Generated Dividend Carry signals: mean={signals.mean():.2f}")

        return signals


class ValueStrategy(BaseStrategy):
    """
    Value-based strategy using price ratios.

    Identifies undervalued stocks using price-to-moving-average ratios
    as a proxy for value. Lower ratios suggest better value.

    In production, this would use fundamental data (P/E, P/B ratios).
    """

    def __init__(
        self,
        lookback_period: int = 252,
        name: str = "Value_Strategy"
    ):
        """
        Initialize value strategy.

        Args:
            lookback_period: Lookback period for value assessment
            name: Strategy name
        """
        super().__init__(name)
        self.lookback_period = lookback_period

        logger.info(f"Value Strategy: lookback={self.lookback_period}")

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate value-based signals.

        Args:
            data: DataFrame with 'Close' prices

        Returns:
            Series of trading signals
        """
        if not self.validate_data(data):
            return pd.Series(index=data.index, dtype=float)

        prices = data['Close']

        # Calculate long-term moving average as "fair value" proxy
        fair_value = prices.rolling(window=self.lookback_period).mean()

        # Calculate price-to-value ratio
        price_to_value = prices / fair_value

        # Lower ratio = undervalued = buy signal
        # Higher ratio = overvalued = sell signal
        value_score = 2 - price_to_value  # Inverted ratio

        # Normalize using rolling statistics
        score_mean = value_score.rolling(window=100).mean()
        score_std = value_score.rolling(window=100).std()
        normalized_score = (value_score - score_mean) / score_std

        # Scale to forecast range
        signals = normalized_score.clip(-2, 2) / 2 * 10
        signals = signals.fillna(0.0)

        logger.debug(f"Generated Value signals: mean={signals.mean():.2f}")

        return signals


class YieldCurveCarry(BaseStrategy):
    """
    Yield curve carry strategy.

    For stocks, this can be implemented as the slope of the moving average curve.
    A steeper upward slope suggests positive carry.
    """

    def __init__(
        self,
        short_period: int = 20,
        long_period: int = 200,
        name: str = "Yield_Curve_Carry"
    ):
        """
        Initialize yield curve carry strategy.

        Args:
            short_period: Short-term moving average period
            long_period: Long-term moving average period
            name: Strategy name
        """
        super().__init__(name)
        self.short_period = short_period
        self.long_period = long_period

        logger.info(
            f"Yield Curve Carry: short={self.short_period}, long={self.long_period}"
        )

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate carry signals based on moving average slope.

        Args:
            data: DataFrame with 'Close' prices

        Returns:
            Series of trading signals
        """
        if not self.validate_data(data):
            return pd.Series(index=data.index, dtype=float)

        prices = data['Close']

        # Calculate short and long-term moving averages
        ma_short = prices.rolling(window=self.short_period).mean()
        ma_long = prices.rolling(window=self.long_period).mean()

        # Calculate the "slope" or spread
        spread = (ma_short - ma_long) / ma_long

        # Normalize the spread
        spread_mean = spread.rolling(window=100).mean()
        spread_std = spread.rolling(window=100).std()
        normalized_spread = (spread - spread_mean) / spread_std

        # Positive spread = positive carry signal
        signals = normalized_spread.clip(-2, 2) / 2 * 10
        signals = signals.fillna(0.0)

        logger.debug(f"Generated Yield Curve signals: mean={signals.mean():.2f}")

        return signals


class SeasonalityCarry(BaseStrategy):
    """
    Seasonality-based carry strategy.

    Exploits seasonal patterns in stock prices.
    Common patterns include:
    - January effect
    - Summer lull
    - Year-end rallies
    """

    def __init__(
        self,
        lookback_years: int = 3,
        name: str = "Seasonality_Carry"
    ):
        """
        Initialize seasonality carry strategy.

        Args:
            lookback_years: Years of historical data to analyze seasonality
            name: Strategy name
        """
        super().__init__(name)
        self.lookback_years = lookback_years

        logger.info(f"Seasonality Carry: lookback_years={self.lookback_years}")

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate carry signals based on seasonal patterns.

        Args:
            data: DataFrame with 'Close' prices

        Returns:
            Series of trading signals
        """
        if not self.validate_data(data):
            return pd.Series(index=data.index, dtype=float)

        prices = data['Close']
        returns = prices.pct_change()

        # Calculate average returns by month
        monthly_returns = returns.groupby(returns.index.month).mean()

        # Create signal based on current month's historical performance
        signals = pd.Series(0.0, index=data.index)

        for month in range(1, 13):
            if month in monthly_returns.index:
                month_mask = data.index.month == month
                # Positive historical returns = positive signal
                signals[month_mask] = monthly_returns[month] * 100

        # Normalize signals
        if signals.std() > 0:
            signals = (signals - signals.mean()) / signals.std()
            signals = signals.clip(-2, 2) / 2 * 10

        signals = signals.fillna(0.0)

        logger.debug(f"Generated Seasonality signals: mean={signals.mean():.2f}")

        return signals
