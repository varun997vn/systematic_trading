import polars as pl

from utils.logger import setup_logger

logger = setup_logger(__name__)


class TurtleStrategy:
    """
    Turtle Trading breakout strategy.
    Based on the famous Turtle Trading System using Donchian Channels.

    The strategy generates long signals when price breaks above the upper channel
    and short signals when price breaks below the lower channel.
    """

    def __init__(self, entry_window: int = 20, exit_window: int = 10):
        """
        Initialize Turtle strategy.

        Args:
            entry_window: Lookback period for entry breakout (Turtles used 20)
            exit_window: Lookback period for exit breakout (Turtles used 10)
        """
        if exit_window >= entry_window:
            logger.warning(
                f"Exit window ({exit_window}) should typically be less than "
                f"entry window ({entry_window})"
            )

        self.entry_window = entry_window
        self.exit_window = exit_window
        self.name = f"turtle_{entry_window}_{exit_window}"

    def calculate(self, prices: pl.Series, ticker: str = "") -> pl.Series:
        """
        Calculate Turtle Trading forecast.

        Args:
            prices: Series of close prices
            ticker: Instrument identifier

        Returns:
            Series of turtle signals
        """
        # Calculate Donchian Channels for entry
        upper_channel = prices.rolling_max(
            window_size=self.entry_window, min_periods=self.entry_window
        )
        lower_channel = prices.rolling_min(
            window_size=self.entry_window, min_periods=self.entry_window
        )

        # Calculate channel midpoint and width
        channel_mid = (upper_channel + lower_channel) / 2.0
        channel_width = upper_channel - lower_channel

        # Prevent division by zero
        channel_width = channel_width.fill_null(1.0)
        channel_width = pl.when(channel_width == 0).then(1.0).otherwise(
            channel_width
        )

        # Signal is distance from midpoint, normalized by channel width
        # Positive when price above midpoint (bullish)
        # Negative when price below midpoint (bearish)
        signal = (prices - channel_mid) / channel_width

        logger.debug(
            f"Turtle strategy calculated for {ticker or 'series'} "
            f"(current={signal[-1]:.4f})"
        )

        return signal

    def calculate_normalized(
            self, prices: pl.Series, price_volatility: pl.Series,
            ticker: str = ""
    ) -> pl.Series:
        """
        Calculate volatility-standardized Turtle forecast.

        Args:
            prices: Series of close prices
            price_volatility: Series of price volatility
            ticker: Instrument identifier

        Returns:
            Series of normalized turtle signals
        """
        raw_signal = self.calculate(prices, ticker)

        # Normalize by price volatility
        normalized = raw_signal / price_volatility

        return normalized

    def get_breakout_levels(
            self, prices: pl.Series
    ) -> tuple[pl.Series, pl.Series, pl.Series, pl.Series]:
        """
        Get current Donchian Channel levels.

        Args:
            prices: Series of close prices

        Returns:
            Tuple of (entry_upper, entry_lower, exit_upper, exit_lower)
        """
        # Entry levels
        entry_upper = prices.rolling_max(
            window_size=self.entry_window, min_periods=self.entry_window
        )
        entry_lower = prices.rolling_min(
            window_size=self.entry_window, min_periods=self.entry_window
        )

        # Exit levels
        exit_upper = prices.rolling_max(
            window_size=self.exit_window, min_periods=self.exit_window
        )
        exit_lower = prices.rolling_min(
            window_size=self.exit_window, min_periods=self.exit_window
        )

        return entry_upper, entry_lower, exit_upper, exit_lower
