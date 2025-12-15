import polars as pl

from utils.logger import setup_logger

logger = setup_logger(__name__)


class MeanReversion:
    """
    Mean reversion trading strategy.
    Counter-trend approach.
    """

    def __init__(self, lookback: int = 30, entry_threshold: float = 2.0):
        """
        Initialize mean reversion strategy.

        Args:
            lookback: Lookback period for mean/std calculation
            entry_threshold: Standard deviations for entry signal
        """
        self.lookback = lookback
        self.entry_threshold = entry_threshold
        self.name = f"mean_reversion_{lookback}"

    def calculate(self, prices: pl.Series, ticker: str = "") -> pl.Series:
        """
        Calculate mean reversion forecast.

        Args:
            prices: Series of close prices
            ticker: Instrument identifier

        Returns:
            Series of mean reversion signals
        """
        # Calculate z-score
        rolling_mean = prices.rolling_mean(
            window_size=self.lookback, min_periods=self.lookback
        )
        rolling_std = prices.rolling_std(
            window_size=self.lookback, min_periods=self.lookback
        )

        z_score = (prices - rolling_mean) / rolling_std

        # Mean reversion signal (inverted z-score)
        # Negative when price is above mean (sell)
        # Positive when price is below mean (buy)
        signal = -z_score

        logger.debug(
            f"Mean reversion calculated for {ticker or 'series'} "
            f"(current={signal[-1]:.4f})"
        )

        return signal

    def calculate_normalized(
            self, prices: pl.Series, price_volatility: pl.Series,
            ticker: str = ""
    ) -> pl.Series:
        """
        Calculate volatility-standardized mean reversion forecast.

        Args:
            prices: Series of close prices
            price_volatility: Series of price volatility
            ticker: Instrument identifier

        Returns:
            Series of normalized mean reversion signals
        """
        raw_signal = self.calculate(prices, ticker)

        # Normalize by price volatility
        normalized = raw_signal / price_volatility

        return normalized
