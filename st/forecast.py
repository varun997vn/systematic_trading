"""
Forecasting Module for Systematic Trading Framework
Based on Robert Carver's "Systematic Trading"

Core responsibilities:
- Trading rule implementation (EWMAC, Carry, Mean Reversion)
- Forecast scaling to standardized range (-20 to +20)
- Forecast combination and weighting
- Signal generation
"""

from typing import Dict, List, Optional, Tuple

import polars as pl
from pydantic import BaseModel, Field, field_validator

from utils.logger import setup_logger

logger = setup_logger(__name__)


# ---- Core Forecast Structures ---- #


class ForecastConfig(BaseModel):
    """Configuration for forecast generation."""

    target_abs_forecast: float = Field(
        default=10.0, description="Target average absolute forecast (Carver uses 10)"
    )
    min_forecast: float = Field(default=-20.0, description="Minimum forecast value")
    max_forecast: float = Field(default=20.0, description="Maximum forecast value")
    cap_forecasts: bool = Field(
        default=True, description="Apply min/max capping to forecasts"
    )

    @field_validator("target_abs_forecast")
    @classmethod
    def validate_target(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Target absolute forecast must be positive")
        if v > 20:
            logger.warning(f"Unusual target forecast: {v}. Carver recommends 10.")
        return v


class Forecast(BaseModel):
    """Container for forecast results."""

    model_config = {"arbitrary_types_allowed": True}

    rule_name: str
    ticker: str
    raw_forecast: pl.Series
    scaled_forecast: pl.Series
    params: Dict = Field(default_factory=dict)

    @property
    def current_forecast(self) -> Optional[float]:
        """Get most recent forecast value."""
        if len(self.scaled_forecast) == 0:
            return None
        return self.scaled_forecast[-1]


# ---- EWMAC (Exponentially Weighted Moving Average Crossover) ---- #


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

    def calculate(self, prices: pl.Series, ticker: str = "") -> pl.Series:
        """
        Calculate raw EWMAC forecast.

        Args:
            prices: Series of close prices
            ticker: Instrument identifier

        Returns:
            Series of raw EWMAC values
        """
        # Calculate EMAs
        fast_ema = prices.ewm_mean(span=self.fast_span, min_periods=self.fast_span)
        slow_ema = prices.ewm_mean(span=self.slow_span, min_periods=self.slow_span)

        # Raw forecast is the difference
        raw_ewmac = fast_ema - slow_ema

        logger.debug(
            f"EWMAC {self.name} calculated for {ticker or 'series'} "
            f"(current={raw_ewmac[-1]:.4f})"
        )

        return raw_ewmac

    def calculate_normalized(
            self, prices: pl.Series, price_volatility: pl.Series, ticker: str = ""
    ) -> pl.Series:
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


# ---- Carry Strategy ---- #


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
            self, current_yield: pl.Series, expected_yield: pl.Series, ticker: str = ""
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


# ---- Mean Reversion Strategy ---- #


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


# ---- Forecast Scaler ---- #


class ForecastScaler:
    """
    Scale forecasts to standardized range.
    Carver's approach: scale to average absolute forecast of 10.
    """

    def __init__(self, config: Optional[ForecastConfig] = None):
        self.config = config or ForecastConfig()

    def calculate_scalar(self, raw_forecast: pl.Series) -> float:
        """
        Calculate scaling factor for forecast.

        Args:
            raw_forecast: Raw forecast values

        Returns:
            Scaling factor
        """
        # Calculate average absolute forecast
        avg_abs = raw_forecast.abs().mean()

        if avg_abs == 0 or avg_abs is None:
            logger.warning("Zero average absolute forecast, returning 0 scalar")
            return 0.0

        # Scalar to achieve target average
        scalar = self.config.target_abs_forecast / avg_abs

        logger.debug(
            f"Forecast scalar: avg_abs={avg_abs:.4f}, "
            f"target={self.config.target_abs_forecast}, scalar={scalar:.4f}"
        )

        return scalar

    def scale(self, raw_forecast: pl.Series) -> pl.Series:
        """
        Scale forecast to target range.

        Args:
            raw_forecast: Raw forecast values

        Returns:
            Scaled forecast
        """
        scalar = self.calculate_scalar(raw_forecast)
        scaled = raw_forecast * scalar

        # Apply caps if configured
        if self.config.cap_forecasts:
            scaled = scaled.clip(self.config.min_forecast, self.config.max_forecast)

        return scaled

    def scale_with_fixed_scalar(
            self, raw_forecast: pl.Series, scalar: float
    ) -> pl.Series:
        """
        Scale forecast using pre-calculated scalar.

        Args:
            raw_forecast: Raw forecast values
            scalar: Pre-calculated scaling factor

        Returns:
            Scaled forecast
        """
        scaled = raw_forecast * scalar

        if self.config.cap_forecasts:
            scaled = scaled.clip(self.config.min_forecast, self.config.max_forecast)

        return scaled


# ---- Forecast Combiner ---- #


class ForecastCombiner:
    """
    Combine multiple forecasts with weights.
    Implements Carver's forecast diversification.
    """

    def __init__(self, config: Optional[ForecastConfig] = None):
        self.config = config or ForecastConfig()

    def weighted_average(
            self, forecasts: Dict[str, pl.Series], weights: Dict[str, float]
    ) -> pl.Series:
        """
        Combine forecasts using weighted average.

        Args:
            forecasts: Dictionary mapping rule name to forecast series
            weights: Dictionary mapping rule name to weight (must sum to 1)

        Returns:
            Combined forecast
        """
        # Validate weights
        weight_sum = sum(weights.values())
        if not (0.99 <= weight_sum <= 1.01):
            logger.warning(f"Weights sum to {weight_sum:.4f}, normalizing to 1.0")
            weights = {k: v / weight_sum for k, v in weights.items()}

        # Combine forecasts
        combined = None
        for rule_name, forecast in forecasts.items():
            weight = weights.get(rule_name, 0.0)
            weighted = forecast * weight

            if combined is None:
                combined = weighted
            else:
                combined = combined + weighted

        # Apply caps
        if self.config.cap_forecasts:
            combined = combined.clip(self.config.min_forecast, self.config.max_forecast)

        logger.info(
            f"Combined {len(forecasts)} forecasts "
            f"(current={combined[-1]:.4f})"
        )

        return combined

    def equal_weight(self, forecasts: Dict[str, pl.Series]) -> pl.Series:
        """
        Combine forecasts with equal weights.

        Args:
            forecasts: Dictionary mapping rule name to forecast series

        Returns:
            Combined forecast
        """
        n = len(forecasts)
        weights = {name: 1.0 / n for name in forecasts.keys()}
        return self.weighted_average(forecasts, weights)

    def diversification_multiplier(self, weights: Dict[str, float]) -> float:
        """
        Calculate diversification multiplier (FDM).

        Args:
            weights: Dictionary of forecast weights

        Returns:
            Diversification multiplier
        """
        # FDM = 1 / sqrt(sum of squared weights)
        # Carver's approach to account for forecast diversification
        sum_squared_weights = sum(w ** 2 for w in weights.values())
        fdm = 1.0 / (sum_squared_weights ** 0.5)

        logger.debug(f"Diversification multiplier: {fdm:.4f}")
        return fdm


# ---- Forecast Manager (Main Interface) ---- #


class ForecastManager:
    """
    Main interface for forecast generation.
    Coordinates trading rules, scaling, and combination.
    """

    def __init__(self, config: Optional[ForecastConfig] = None):
        self.config = config or ForecastConfig()
        self.scaler = ForecastScaler(self.config)
        self.combiner = ForecastCombiner(self.config)

    def generate_ewmac(
            self,
            prices: pl.Series,
            fast_span: int = 16,
            slow_span: int = 64,
            ticker: str = "",
    ) -> Forecast:
        """
        Generate EWMAC forecast.

        Args:
            prices: Price series
            fast_span: Fast EWMA span
            slow_span: Slow EWMA span
            ticker: Instrument identifier

        Returns:
            Forecast object
        """
        ewmac = EWMAC(fast_span, slow_span)
        raw = ewmac.calculate(prices, ticker)
        scaled = self.scaler.scale(raw)

        return Forecast(
            rule_name=ewmac.name,
            ticker=ticker or "unknown",
            raw_forecast=raw,
            scaled_forecast=scaled,
            params={"fast_span": fast_span, "slow_span": slow_span},
        )

    def generate_ewmac_normalized(
            self,
            prices: pl.Series,
            price_volatility: pl.Series,
            fast_span: int = 16,
            slow_span: int = 64,
            ticker: str = "",
    ) -> Forecast:
        """
        Generate risk-adjusted EWMAC forecast.

        Args:
            prices: Price series
            price_volatility: Price volatility series
            fast_span: Fast EWMA span
            slow_span: Slow EWMA span
            ticker: Instrument identifier

        Returns:
            Forecast object
        """
        ewmac = EWMAC(fast_span, slow_span)
        raw = ewmac.calculate_normalized(prices, price_volatility, ticker)
        scaled = self.scaler.scale(raw)

        return Forecast(
            rule_name=f"{ewmac.name}_normalized",
            ticker=ticker or "unknown",
            raw_forecast=raw,
            scaled_forecast=scaled,
            params={
                "fast_span": fast_span,
                "slow_span": slow_span,
                "normalized": True,
            },
        )

    def generate_carry(
            self,
            spot_prices: pl.Series,
            forward_prices: pl.Series,
            smoothing_span: int = 30,
            ticker: str = "",
    ) -> Forecast:
        """
        Generate carry forecast.

        Args:
            spot_prices: Spot price series
            forward_prices: Forward price series
            smoothing_span: EWMA smoothing span
            ticker: Instrument identifier

        Returns:
            Forecast object
        """
        carry = Carry(smoothing_span)
        raw = carry.calculate_from_prices(spot_prices, forward_prices, ticker)
        scaled = self.scaler.scale(raw)

        return Forecast(
            rule_name=carry.name,
            ticker=ticker or "unknown",
            raw_forecast=raw,
            scaled_forecast=scaled,
            params={"smoothing_span": smoothing_span},
        )

    def generate_mean_reversion(
            self,
            prices: pl.Series,
            lookback: int = 30,
            entry_threshold: float = 2.0,
            ticker: str = "",
    ) -> Forecast:
        """
        Generate mean reversion forecast.

        Args:
            prices: Price series
            lookback: Lookback period
            entry_threshold: Entry threshold in std devs
            ticker: Instrument identifier

        Returns:
            Forecast object
        """
        mean_rev = MeanReversion(lookback, entry_threshold)
        raw = mean_rev.calculate(prices, ticker)
        scaled = self.scaler.scale(raw)

        return Forecast(
            rule_name=mean_rev.name,
            ticker=ticker or "unknown",
            raw_forecast=raw,
            scaled_forecast=scaled,
            params={"lookback": lookback, "entry_threshold": entry_threshold},
        )

    def combine_forecasts(
            self, forecasts: List[Forecast], weights: Optional[Dict[str, float]] = None
    ) -> Tuple[pl.Series, float]:
        """
        Combine multiple forecasts.

        Args:
            forecasts: List of Forecast objects
            weights: Optional weights dictionary (equal weights if None)

        Returns:
            Tuple of (combined forecast series, diversification multiplier)
        """
        forecast_dict = {f.rule_name: f.scaled_forecast for f in forecasts}

        if weights is None:
            combined = self.combiner.equal_weight(forecast_dict)
            n = len(forecasts)
            weights = {f.rule_name: 1.0 / n for f in forecasts}
        else:
            combined = self.combiner.weighted_average(forecast_dict, weights)

        fdm = self.combiner.diversification_multiplier(weights)

        return combined, fdm

    def generate_standard_suite(
            self, prices: pl.Series, ticker: str = ""
    ) -> Dict[str, Forecast]:
        """
        Generate Carver's standard suite of EWMAC forecasts.

        Args:
            prices: Price series
            ticker: Instrument identifier

        Returns:
            Dictionary of Forecast objects
        """
        # Carver's standard EWMAC variations
        ewmac_pairs = [
            (2, 8),
            (4, 16),
            (8, 32),
            (16, 64),
            (32, 128),
            (64, 256),
        ]

        forecasts = {}
        for fast, slow in ewmac_pairs:
            forecast = self.generate_ewmac(prices, fast, slow, ticker)
            forecasts[forecast.rule_name] = forecast

        logger.info(
            f"Generated {len(forecasts)} EWMAC forecasts for {ticker or 'series'}"
        )

        return forecasts


# ---- Utility Functions ---- #


def calculate_forecast_correlation(
        forecast1: pl.Series, forecast2: pl.Series
) -> float:
    """
    Calculate correlation between two forecasts.

    Args:
        forecast1: First forecast series
        forecast2: Second forecast series

    Returns:
        Correlation coefficient
    """
    # Create DataFrame for correlation calculation
    df = pl.DataFrame({"f1": forecast1, "f2": forecast2})
    corr_matrix = df.corr()
    correlation = corr_matrix[0, 1]

    return correlation


def calculate_forecast_diversity(forecasts: Dict[str, pl.Series]) -> pl.DataFrame:
    """
    Calculate pairwise correlations between forecasts.

    Args:
        forecasts: Dictionary of forecast series

    Returns:
        Correlation matrix
    """
    df = pl.DataFrame(forecasts)
    corr_matrix = df.corr()

    return corr_matrix


def validate_forecast(forecast: pl.Series, config: ForecastConfig) -> bool:
    """
    Validate forecast values are within expected range.

    Args:
        forecast: Forecast series
        config: Forecast configuration

    Returns:
        True if valid
    """
    min_val = forecast.min()
    max_val = forecast.max()

    if min_val < config.min_forecast - 0.01:
        logger.warning(
            f"Forecast below minimum: {min_val:.2f} < {config.min_forecast}"
        )
        return False

    if max_val > config.max_forecast + 0.01:
        logger.warning(
            f"Forecast above maximum: {max_val:.2f} > {config.max_forecast}"
        )
        return False

    return True
