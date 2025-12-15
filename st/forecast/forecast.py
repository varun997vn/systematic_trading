"""
Forecasting Module for Systematic Trading Framework
Based on Robert Carver's "Systematic Trading"

Core responsibilities:
- Trading rule implementation (EWMAC, Carry, Mean Reversion, Turtle)
- Volatility standardization (enabled by default for all strategies)
- Forecast scaling to standardized range (-20 to +20)
- Forecast combination and weighting
- Signal generation
"""

from typing import Dict, List, Optional, Tuple

import polars as pl
import pandas as pd
from pydantic import BaseModel, Field, field_validator

from utils.logger import setup_logger

logger = setup_logger(__name__)

from .model_carry import Carry
from .model_ewmac import EWMAC
from .model_turtle import TurtleStrategy
from .model_meanreversion import MeanReversion


# ---- Core Forecast Structures ---- #


class ForecastConfig(BaseModel):
    """Configuration for forecast generation."""

    target_abs_forecast: float = Field(
        default=10.0,
        description="Target average absolute forecast (Carver uses 10)"
    )
    min_forecast: float = Field(
        default=-20.0, description="Minimum forecast value"
    )
    max_forecast: float = Field(
        default=20.0, description="Maximum forecast value"
    )
    cap_forecasts: bool = Field(
        default=True, description="Apply min/max capping to forecasts"
    )

    @field_validator("target_abs_forecast")
    @classmethod
    def validate_target(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Target absolute forecast must be positive")
        if v > 20:
            logger.warning(
                f"Unusual target forecast: {v}. Carver recommends 10."
            )
        return v


class Forecast(BaseModel):
    """Container for forecast results."""

    model_config = {"arbitrary_types_allowed": True}

    rule_name: str
    ticker: str
    raw_forecast: pd.Series
    scaled_forecast: pd.Series
    params: Dict = Field(default_factory=dict)

    @property
    def current_forecast(self) -> Optional[float]:
        """Get most recent forecast value."""
        if len(self.scaled_forecast) == 0:
            return None
        return self.scaled_forecast.iloc[-1]


# ---- Forecast Scaler ---- #


class ForecastScaler:
    """
    Scale forecasts to standardized range.
    Carver's approach: scale to average absolute forecast of 10.
    """

    def __init__(self, config: Optional[ForecastConfig] = None):
        self.config = config or ForecastConfig()

    def calculate_scalar(self, raw_forecast: pd.Series) -> float:
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
            logger.warning(
                "Zero average absolute forecast, returning 0 scalar"
            )
            return 0.0

        # Scalar to achieve target average
        scalar = self.config.target_abs_forecast / avg_abs

        logger.debug(
            f"Forecast scalar: avg_abs={avg_abs:.4f}, "
            f"target={self.config.target_abs_forecast}, scalar={scalar:.4f}"
        )

        return scalar

    def scale(self, raw_forecast: pd.Series) -> pd.Series:
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
            scaled = scaled.clip(
                self.config.min_forecast, self.config.max_forecast
            )

        return scaled

    def scale_with_fixed_scalar(
            self, raw_forecast: pd.Series, scalar: float
    ) -> pd.Series:
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
            scaled = scaled.clip(
                self.config.min_forecast, self.config.max_forecast
            )

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
            self, forecasts: Dict[str, pd.Series], weights: Dict[str, float]
    ) -> pd.Series:
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
            logger.warning(
                f"Weights sum to {weight_sum:.4f}, normalizing to 1.0"
            )
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
            combined = combined.clip(
                self.config.min_forecast, self.config.max_forecast
            )

        logger.info(
            f"Combined {len(forecasts)} forecasts "
            f"(current={combined.iloc[-1]:.4f})"
        )

        return combined

    def equal_weight(self, forecasts: Dict[str, pd.Series]) -> pd.Series:
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
            prices: pd.Series,
            price_volatility: Optional[pd.Series] = None,
            fast_span: int = 16,
            slow_span: int = 64,
            ticker: str = "",
            use_volatility_standardization: bool = True,
    ) -> Forecast:
        """
        Generate EWMAC forecast with optional volatility standardization.

        Args:
            prices: Price series
            price_volatility: Price volatility series (required if use_volatility_standardization=True)
            fast_span: Fast EWMA span
            slow_span: Slow EWMA span
            ticker: Instrument identifier
            use_volatility_standardization: Use volatility standardization (default True)

        Returns:
            Forecast object
        """
        ewmac = EWMAC(fast_span, slow_span)

        if use_volatility_standardization:
            if price_volatility is None:
                raise ValueError(
                    "price_volatility required when use_volatility_standardization=True"
                )
            raw = ewmac.calculate_normalized(prices, price_volatility, ticker)
            rule_name = f"{ewmac.name}_normalized"
            normalized = True
        else:
            raw = ewmac.calculate(prices, ticker)
            rule_name = ewmac.name
            normalized = False

        scaled = self.scaler.scale(raw)

        return Forecast(
            rule_name=rule_name,
            ticker=ticker or "unknown",
            raw_forecast=raw,
            scaled_forecast=scaled,
            params={
                "fast_span":  fast_span,
                "slow_span":  slow_span,
                "normalized": normalized,
            },
        )

    def generate_ewmac_normalized(
            self,
            prices: pd.Series,
            price_volatility: pd.Series,
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
                "fast_span":  fast_span,
                "slow_span":  slow_span,
                "normalized": True,
            },
        )

    def generate_carry(
            self,
            spot_prices: pd.Series,
            forward_prices: pd.Series,
            price_volatility: Optional[pd.Series] = None,
            smoothing_span: int = 30,
            ticker: str = "",
            use_volatility_standardization: bool = True,
    ) -> Forecast:
        """
        Generate carry forecast with optional volatility standardization.

        Args:
            spot_prices: Spot price series
            forward_prices: Forward price series
            price_volatility: Price volatility series (required if use_volatility_standardization=True)
            smoothing_span: EWMA smoothing span
            ticker: Instrument identifier
            use_volatility_standardization: Use volatility standardization (default True)

        Returns:
            Forecast object
        """
        carry = Carry(smoothing_span)

        if use_volatility_standardization:
            if price_volatility is None:
                raise ValueError(
                    "price_volatility required when use_volatility_standardization=True"
                )
            raw = carry.calculate_from_prices_normalized(
                spot_prices, forward_prices, price_volatility, ticker
            )
            rule_name = f"{carry.name}_normalized"
            normalized = True
        else:
            raw = carry.calculate_from_prices(
                spot_prices, forward_prices, ticker
            )
            rule_name = carry.name
            normalized = False

        scaled = self.scaler.scale(raw)

        return Forecast(
            rule_name=rule_name,
            ticker=ticker or "unknown",
            raw_forecast=raw,
            scaled_forecast=scaled,
            params={
                "smoothing_span": smoothing_span, "normalized": normalized
            },
        )

    def generate_mean_reversion(
            self,
            prices: pd.Series,
            price_volatility: Optional[pd.Series] = None,
            lookback: int = 30,
            entry_threshold: float = 2.0,
            ticker: str = "",
            use_volatility_standardization: bool = True,
    ) -> Forecast:
        """
        Generate mean reversion forecast with optional volatility standardization.

        Args:
            prices: Price series
            price_volatility: Price volatility series (required if use_volatility_standardization=True)
            lookback: Lookback period
            entry_threshold: Entry threshold in std devs
            ticker: Instrument identifier
            use_volatility_standardization: Use volatility standardization (default True)

        Returns:
            Forecast object
        """
        mean_rev = MeanReversion(lookback, entry_threshold)

        if use_volatility_standardization:
            if price_volatility is None:
                raise ValueError(
                    "price_volatility required when use_volatility_standardization=True"
                )
            raw = mean_rev.calculate_normalized(
                prices, price_volatility, ticker
            )
            rule_name = f"{mean_rev.name}_normalized"
            normalized = True
        else:
            raw = mean_rev.calculate(prices, ticker)
            rule_name = mean_rev.name
            normalized = False

        scaled = self.scaler.scale(raw)

        return Forecast(
            rule_name=rule_name,
            ticker=ticker or "unknown",
            raw_forecast=raw,
            scaled_forecast=scaled,
            params={
                "lookback":        lookback,
                "entry_threshold": entry_threshold,
                "normalized":      normalized,
            },
        )

    def generate_turtle(
            self,
            prices: pd.Series,
            price_volatility: Optional[pd.Series] = None,
            entry_window: int = 20,
            exit_window: int = 10,
            ticker: str = "",
            use_volatility_standardization: bool = True,
    ) -> Forecast:
        """
        Generate Turtle Trading forecast with optional volatility standardization.

        Args:
            prices: Price series
            price_volatility: Price volatility series (required if use_volatility_standardization=True)
            entry_window: Entry breakout window
            exit_window: Exit breakout window
            ticker: Instrument identifier
            use_volatility_standardization: Use volatility standardization (default True)

        Returns:
            Forecast object
        """
        turtle = TurtleStrategy(entry_window, exit_window)

        if use_volatility_standardization:
            if price_volatility is None:
                raise ValueError(
                    "price_volatility required when use_volatility_standardization=True"
                )
            raw = turtle.calculate_normalized(prices, price_volatility, ticker)
            rule_name = f"{turtle.name}_normalized"
            normalized = True
        else:
            raw = turtle.calculate(prices, ticker)
            rule_name = turtle.name
            normalized = False

        scaled = self.scaler.scale(raw)

        return Forecast(
            rule_name=rule_name,
            ticker=ticker or "unknown",
            raw_forecast=raw,
            scaled_forecast=scaled,
            params={
                "entry_window": entry_window,
                "exit_window":  exit_window,
                "normalized":   normalized,
            },
        )

    def combine_forecasts(
            self, forecasts: List[Forecast],
            weights: Optional[Dict[str, float]] = None
    ) -> Tuple[pd.Series, float]:
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
            self,
            prices: pd.Series,
            price_volatility: Optional[pd.Series] = None,
            ticker: str = "",
            use_volatility_standardization: bool = True,
    ) -> Dict[str, Forecast]:
        """
        Generate Carver's standard suite of EWMAC forecasts with optional volatility standardization.

        Args:
            prices: Price series
            price_volatility: Price volatility series (required if use_volatility_standardization=True)
            ticker: Instrument identifier
            use_volatility_standardization: Use volatility standardization (default True)

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
            forecast = self.generate_ewmac(
                prices,
                price_volatility=price_volatility,
                fast_span=fast,
                slow_span=slow,
                ticker=ticker,
                use_volatility_standardization=use_volatility_standardization,
            )
            forecasts[forecast.rule_name] = forecast

        logger.info(
            f"Generated {len(forecasts)} EWMAC forecasts for {ticker or 'series'}"
        )

        return forecasts


# ---- Utility Functions ---- #


def calculate_forecast_correlation(
        forecast1: pd.Series, forecast2: pd.Series
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


def calculate_forecast_diversity(
        forecasts: Dict[str, pd.Series]
) -> pl.DataFrame:
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


def validate_forecast(forecast: pd.Series, config: ForecastConfig) -> bool:
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
