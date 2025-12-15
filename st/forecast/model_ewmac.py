import polars as pl
import pandas as pd
from utils.logger import setup_logger

logger = setup_logger(__name__)


class EWMAC:
    """
    EWMAC trend following strategy.
    Carver's primary trend-following approach.
    """

    def __init__(self, fast_span: int = 16, slow_span: int = 64):
        """
        Initialize EWMAC strategy.

        Args:
            fast_span: Fast EWMA span (Carver uses 2, 4, 8, 16, 32, 64)
            slow_span: Slow EWMA span (must be > fast_span)
        """
        if slow_span <= fast_span:
            raise ValueError("Slow span must be greater than fast span")

        self.fast_span = fast_span
        self.slow_span = slow_span
        self.name = f"ewmac_{fast_span}_{slow_span}"

    def calculate(self, prices: pd.Series, ticker: str = "") -> pd.Series:
        """
        Calculate raw EWMAC forecast.

        Args:
            prices: Series of close prices
            ticker: Instrument identifier

        Returns:
            Series of raw EWMAC values
        """
        # Calculate EMAs
        fast_ema = prices.ewm(
            span=self.fast_span, min_periods=self.fast_span
        ).mean()
        slow_ema = prices.ewm(
            span=self.slow_span, min_periods=self.slow_span
        ).mean()

        # Raw forecast is the difference
        raw_ewmac = fast_ema - slow_ema

        logger.debug(
            f"EWMAC {self.name} calculated for {ticker or 'series'} "
            f"(current={raw_ewmac.iloc[-1]:.4f})"
        )

        return raw_ewmac

    def calculate_normalized(
            self, prices: pd.Series, price_volatility: pd.Series,
            ticker: str = ""
    ) -> pd.Series:
        """
        Calculate risk-adjusted EWMAC forecast.

        Args:
            prices: Series of close prices
            price_volatility: Series of price volatility
            ticker: Instrument identifier

        Returns:
            Series of normalized EWMAC values
        """
        raw_ewmac = self.calculate(prices, ticker)

        # Normalize by price volatility
        normalized = raw_ewmac / price_volatility

        return normalized
