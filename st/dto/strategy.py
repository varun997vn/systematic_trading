from abc import ABC, abstractmethod
from typing import Any

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from utils.logger import setup_logger
from .data import PriceDataDTO, ReturnsDTO
from .volatility import VolatilityStandardizationDTO

logger = setup_logger(__name__)


class ForecastConfig(BaseModel):
    """Forecast generation and scaling configuration."""

    target_abs_forecast: float = Field(
        default=10.0,
        gt=0,
        description="Target average absolute forecast (Carver standard: 10)"
    )
    min_forecast: float = Field(
        default=-20.0, description="Minimum forecast value"
    )
    max_forecast: float = Field(
        default=20.0, description="Maximum forecast value"
    )
    cap_forecasts: bool = Field(
        default=True, description="Apply min/max capping"
    )
    use_volatility_standardization: bool = Field(
        default=True,
        description="Normalize forecasts by price volatility"
    )

    def model_post_init(self, context: Any, /) -> None:
        if self.max_forecast < self.min_forecast:
            raise ValueError(
                f"max_forecast {self.max_forecast} must be greater than min_forecast {self.min_forecast}"
            )

    def __str__(self):
        return (f"ForecastConfig(target={self.target_abs_forecast}, "
                f"range=[{self.min_forecast}, {self.max_forecast}])")

    __repr__ = __str__


# ---- Base Strategy DTO ---- #


class StrategyDTO(BaseModel, ABC):
    """Base class for all trading strategies."""

    price_data: PriceDataDTO
    volatility_model: str = Field(
        default="ewma",
        description="Volatility model: 'standard', 'ewma', 'robust'"
    )
    volatility_params: dict = Field(
        default_factory=dict, description="Parameters for volatility model"
    )
    forecast_config: ForecastConfig = Field(
        default_factory=ForecastConfig, description="Forecast configuration"
    )

    # Computed fields
    returns: ReturnsDTO = None
    vol_standardization: VolatilityStandardizationDTO = None
    forecasts_raw: pd.Series = None
    forecasts_vol_normalized: pd.Series = None
    forecasts_scaled: pd.Series = None

    class Config:
        arbitrary_types_allowed = True

    def model_post_init(self, context: Any, /) -> None:
        # Volatility standardization (common to all strategies)
        if self.forecast_config.use_volatility_standardization:
            self.vol_standardization = VolatilityStandardizationDTO(
                price_data=self.price_data,
                model=self.volatility_model,
                parameters=self.volatility_params
            )
            self.returns = self.vol_standardization.returns

        # Strategy-specific forecast calculation
        self._calculate_forecasts()

        # Normalize forecasts by volatility (if enabled)
        if self.forecast_config.use_volatility_standardization and self.vol_standardization is not None:
            # Calculate instrument currency volatility (price volatility, not % volatility)
            # ICVol = daily_vol (%) * price / 100
            price_vol = (self.vol_standardization.volatility.daily_vol *
                         self.price_data.data['Close'] / 100)

            # Normalize forecast by price volatility
            # This makes forecasts comparable across instruments
            self.forecasts_vol_normalized = self.forecasts_raw / price_vol

            # Fill NaN with 0 (can't trade if no volatility estimate)
            self.forecasts_vol_normalized = self.forecasts_vol_normalized.fillna(0)
        else:
            self.forecasts_vol_normalized = self.forecasts_raw.fillna(0)

        # Scale and cap forecasts
        self._scale_forecasts()

        logger.info(f"Creation Completed: {self}")

    def _scale_forecasts(self) -> None:
        """
        Scale forecasts to target absolute forecast and apply capping.

        CRITICAL: Must avoid lookahead bias by using only past data for scaling.
        """
        # Calculate scaling factor using ONLY past data
        # Shift first, then calculate rolling mean to ensure no lookahead
        past_abs_forecast = (
            self.forecasts_vol_normalized.abs()
            .shift(1)  # Use yesterday's forecast to scale today
            .rolling(window=36, min_periods=10)
            .mean()
        )

        # Calculate scaling factor
        scaling_factor = self.forecast_config.target_abs_forecast / past_abs_forecast

        # Handle division by zero / NaN / Inf
        scaling_factor = scaling_factor.replace([np.inf, -np.inf], np.nan)
        scaling_factor = scaling_factor.fillna(1.0)  # Default to no scaling if no history

        # Apply scaling
        self.forecasts_scaled = self.forecasts_vol_normalized * scaling_factor

        # Cap forecasts if enabled
        if self.forecast_config.cap_forecasts:
            self.forecasts_scaled = self.forecasts_scaled.clip(
                lower=self.forecast_config.min_forecast,
                upper=self.forecast_config.max_forecast
            )

        # Fill any remaining NaN with 0
        self.forecasts_scaled = self.forecasts_scaled.fillna(0)

    @abstractmethod
    def _calculate_forecasts(self) -> None:
        """Calculate raw forecasts. Must be implemented by subclasses."""
        pass

    def __str__(self):
        return f"{self.__class__.__name__}(ticker={self.price_data.ticker}, vol_model={self.volatility_model})"

    __repr__ = __str__


# ---- Strategy Configuration DTOs ---- #


class EWMACStrategyDTO(StrategyDTO):
    """EWMAC trend-following strategy configuration."""

    fast_span: int = Field(
        default=16,
        ge=2, description="Fast EMA span (e.g., 2, 4, 8, 16, 32, 64)"
    )
    slow_span: int = Field(
        default=64,
        gt=2, description="Slow EMA span (must be > fast_span)"
    )

    def _calculate_forecasts(self) -> None:
        """Calculate EWMAC raw forecasts."""
        if self.slow_span <= self.fast_span:
            raise ValueError(
                f"slow_span: {self.slow_span} must be greater than fast_span: {self.fast_span}"
            )

        data = self.price_data.data.copy()
        fast_ema = data['Close'].ewm(span=self.fast_span, adjust=False).mean()
        slow_ema = data['Close'].ewm(span=self.slow_span, adjust=False).mean()

        # Raw forecast = (fast_ema - slow_ema)
        self.forecasts_raw = (fast_ema - slow_ema).fillna(0)

    def __str__(self):
        return f"EWMACStrategy(ticker={self.price_data.ticker}, {self.fast_span}/{self.slow_span}, vol_model={self.volatility_model})"

    __repr__ = __str__


class CarryStrategyDTO(StrategyDTO):
    """Carry-based strategy configuration."""

    smoothing_span: int = Field(
        default=30, ge=1, description="EWMA span for smoothing carry signal"
    )

    def _calculate_forecasts(self) -> None:
        """Calculate carry raw forecasts."""
        data = self.price_data.data.copy()

        # Rolling return as proxy for carry
        rolling_return = data['Close'].pct_change(periods=self.smoothing_span)

        # Smooth the carry signal
        self.forecasts_raw = rolling_return.ewm(
            span=self.smoothing_span, adjust=False
        ).mean().fillna(0)

    def __str__(self):
        return f"CarryStrategy(ticker={self.price_data.ticker}, smoothing={self.smoothing_span}, vol_model={self.volatility_model})"

    __repr__ = __str__


class MeanReversionStrategyDTO(StrategyDTO):
    """Mean reversion strategy configuration."""

    lookback: int = Field(
        default=30, ge=2,
        description="Lookback period for mean/std calculation"
    )
    entry_threshold: float = Field(
        default=2.0, gt=0, description="Standard deviations for entry signal"
    )

    def _calculate_forecasts(self) -> None:
        """Calculate mean reversion raw forecasts."""
        data = self.price_data.data.copy()
        rolling_mean = data['Close'].rolling(window=self.lookback).mean()
        rolling_std = data['Close'].rolling(window=self.lookback).std()

        # Z-score: negative when price is above mean (sell signal)
        z_score = (data['Close'] - rolling_mean) / rolling_std

        # Raw forecast based on z-score scaled by entry threshold
        # Multiply by -1 so that high prices give negative signal (mean reversion)
        self.forecasts_raw = (-z_score / self.entry_threshold).fillna(0)

    def __str__(self):
        return f"MeanReversionStrategy(ticker={self.price_data.ticker}, lookback={self.lookback}, std={self.entry_threshold}, vol_model={self.volatility_model})"

    __repr__ = __str__


class TurtleStrategyDTO(StrategyDTO):
    """Turtle Trading breakout strategy configuration."""

    entry_window: int = Field(
        default=20, ge=2,
        description="Entry breakout window (Donchian Channel)"
    )
    exit_window: int = Field(
        default=10, ge=1, description="Exit breakout window"
    )

    def _calculate_forecasts(self) -> None:
        """Calculate Turtle Trading raw forecasts."""
        data = self.price_data.data.copy()
        upper_band = data['High'].rolling(window=self.entry_window).max()
        lower_band = data['Low'].rolling(window=self.entry_window).min()
        middle_band = (upper_band + lower_band) / 2

        # Raw forecast: position relative to channel
        # +1 when at upper band, -1 when at lower band
        channel_width = upper_band - lower_band

        # Avoid division by zero
        channel_width = channel_width.replace(0, np.nan)

        price_position = (data['Close'] - middle_band) / (channel_width / 2)
        price_position = price_position.clip(-1, 1)

        self.forecasts_raw = price_position.fillna(0)

    def __str__(self):
        return f"TurtleStrategy(ticker={self.price_data.ticker}, entry_window={self.entry_window}, exit_window={self.exit_window}, vol_model={self.volatility_model})"

    __repr__ = __str__
