import polars as pl

from utils.logger import setup_logger

logger = setup_logger(__name__)


class Carry:
    """
    Carry-based trading strategy.
    Works for futures, FX, and fixed income.
    """

    def __init__(self, smoothing_span: int = 30):
        """
        Initialize Carry strategy.

        Args:
            smoothing_span: EWMA span for smoothing carry signal
        """
        self.smoothing_span = smoothing_span
        self.name = f"carry_{smoothing_span}"

    def calculate_from_prices(
            self,
            spot_prices: pl.Series,
            forward_prices: pl.Series,
            ticker: str = "",
    ) -> pl.Series:
        """
        Calculate carry from spot and forward prices.

        Args:
            spot_prices: Current spot prices
            forward_prices: Forward/futures prices
            ticker: Instrument identifier

        Returns:
            Series of carry values
        """
        # Raw carry = (Forward - Spot) / Spot
        raw_carry = (forward_prices - spot_prices) / spot_prices

        # Smooth the carry signal
        smoothed = raw_carry.ewm_mean(
            span=self.smoothing_span, min_periods=self.smoothing_span
        )

        logger.debug(
            f"Carry calculated for {ticker or 'series'} (current={smoothed[-1]:.4f})"
        )

        return smoothed

    def calculate_from_yields(
            self, current_yield: pl.Series, expected_yield: pl.Series,
            ticker: str = ""
    ) -> pl.Series:
        """
        Calculate carry from yield differential.

        Args:
            current_yield: Current instrument yield
            expected_yield: Expected/fair yield
            ticker: Instrument identifier

        Returns:
            Series of carry values
        """
        # Carry = current yield - expected yield
        raw_carry = current_yield - expected_yield

        smoothed = raw_carry.ewm_mean(
            span=self.smoothing_span, min_periods=self.smoothing_span
        )

        return smoothed

    def calculate_from_prices_normalized(
            self,
            spot_prices: pl.Series,
            forward_prices: pl.Series,
            price_volatility: pl.Series,
            ticker: str = "",
    ) -> pl.Series:
        """
        Calculate volatility-standardized carry from spot and forward prices.

        Args:
            spot_prices: Current spot prices
            forward_prices: Forward/futures prices
            price_volatility: Series of price volatility
            ticker: Instrument identifier

        Returns:
            Series of normalized carry values
        """
        raw_carry = self.calculate_from_prices(
            spot_prices, forward_prices, ticker
        )

        # Normalize by price volatility
        normalized = raw_carry / price_volatility

        return normalized

    def calculate_from_yields_normalized(
            self,
            current_yield: pl.Series,
            expected_yield: pl.Series,
            price_volatility: pl.Series,
            ticker: str = "",
    ) -> pl.Series:
        """
        Calculate volatility-standardized carry from yield differential.

        Args:
            current_yield: Current instrument yield
            expected_yield: Expected/fair yield
            price_volatility: Series of price volatility
            ticker: Instrument identifier

        Returns:
            Series of normalized carry values
        """
        raw_carry = self.calculate_from_yields(
            current_yield, expected_yield, ticker
        )

        # Normalize by price volatility
        normalized = raw_carry / price_volatility

        return normalized
