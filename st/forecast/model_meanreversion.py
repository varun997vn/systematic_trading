import pandas as pd

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

    def calculate(self, prices: pd.Series, ticker: str = "") -> pd.Series:
        """
        Calculate mean reversion forecast.

        Args:
            prices: Series of close prices
            ticker: Instrument identifier

        Returns:
            Series of mean reversion signals
        """
        # Calculate z-score
        rolling = prices.rolling(
            window=self.lookback,
            center=False
        )
        rolling_mean = rolling.mean()
        rolling_std = rolling.std()

        z_score = (prices - rolling_mean) / rolling_std

        # Mean reversion signal (inverted z-score)
        # Negative when price is above mean (sell)
        # Positive when price is below mean (buy)
        signal = -z_score

        logger.debug(
            f"Mean reversion calculated for {ticker or 'series'} "
            f"(current={signal.iloc[-1]:.4f})"
        )

        return signal

    def calculate_normalized(
            self, prices: pd.Series, price_volatility: pd.Series,
            ticker: str = ""
    ) -> pd.Series:
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
