from typing import Any, Literal

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from st.config import Settings
from utils.logger import setup_logger
from .data import ReturnsDTO

logger = setup_logger(__name__)


# ---- Volatility Estimators ---- #

class VolatilityDTO(BaseModel):
    returns: ReturnsDTO
    annualization_factor: int = Field(
        default=Settings.BUSINESS_DAYS_PER_YEAR,
        description="Trading days per year (256 for Carver)",
    )
    daily_vol: pd.Series = None
    annul_vol: pd.Series = None

    def __str__(self):
        return f"{self.__class__.__name__}({self.daily_vol})"


class StandardVolatilityDTO(VolatilityDTO):
    window: int = Field(default=36, description="Rolling window size")
    min_periods: int = Field(default=10, description="Minimum observations required")

    class Config:
        arbitrary_types_allowed = True

    def model_post_init(self, __context: Any):
        self.daily_vol = self.returns.returns.rolling(window=self.window, min_periods=self.min_periods).std()
        self.annul_vol = self.daily_vol * (self.annualization_factor ** 0.5)
        logger.info(f"Creation Complete: {self}")


class EWMAVolatilityDTO(VolatilityDTO):
    span: int = Field(
        default=36, ge=2, description="EWMA span (Carver recommends 32-36)"
    )
    min_periods: int = Field(default=10, description="Minimum observations required")

    class Config:
        arbitrary_types_allowed = True

    def model_post_init(self, __context: Any):
        if self.span < 2:
            raise ValueError("Span must be at least 2")

        # EWMA of squared returns
        squared_returns = self.returns.returns ** 2
        ewma_var = squared_returns.ewm(
            span=self.span,
            min_periods=self.min_periods
        ).mean()

        # Volatility is square root of variance
        self.daily_vol = ewma_var ** 0.5

        # Annualize
        self.annul_vol = self.daily_vol * (self.annualization_factor ** 0.5)
        logger.info(f"Creation Complete: {self}")


class RobustVolatilityDTO(VolatilityDTO):
    window: int = Field(default=36, description="Rolling window size")
    scale_factor: float = Field(default=1.4826, description="Scale to match std dev (1.4826 for normal distribution)")

    class Config:
        arbitrary_types_allowed = True

    def rolling_mad(self, series: pd.Series) -> float:
        """Calculate median absolute deviation."""
        median = series.median()
        if median is None:
            return None
        mad = (series - median).abs().median()
        return mad * self.scale_factor if mad is not None else None

    def model_post_init(self, __context: Any):
        self.daily_vol = self.returns.returns.rolling(window=self.window).apply(self.rolling_mad, raw=False)
        self.annul_vol = self.daily_vol * (self.annualization_factor ** 0.5)
        logger.info(f"Creation Complete: {self}")


# ---- Volatility Forecasting ---- #

class VolatilityForecastDTO(BaseModel):
    volatility: VolatilityDTO
    forecast: pd.Series = None

    def __str__(self):
        return f"{self.__class__.__name__}({self.volatility})"


class SimpleVolatilityForecastDTO(VolatilityForecastDTO):
    horizon: int = Field(default=1, description="Forecast horizon (days)")
    method: Literal["last", "mean"] = Field(default="last", description="Forecast method")

    class Config:
        arbitrary_types_allowed = True

    def model_post_init(self, __context: Any):
        if self.method == "last":
            # Use last observation (Carver's simple approach)
            self.forecast = self.volatility.daily_vol.copy()
        elif self.method == "mean":
            # Rolling mean forecast
            self.forecast = self.volatility.daily_vol.rolling(window=10, min_periods=1).mean()
        else:
            raise ValueError(f"Unknown method: {self.method}")

        # Scale by sqrt(horizon) for multi-day forecasts
        if self.horizon > 1:
            self.forecast = self.forecast * (self.horizon ** 0.5)
        logger.info(f"Creation Complete: {self}")


class EWMAVolatilityForecastDTO(VolatilityForecastDTO):
    span: int = Field(default=10, description="EWMA span for forecasting")
    horizon: int = Field(default=1, description="Forecast horizon (days)")

    class Config:
        arbitrary_types_allowed = True

    def model_post_init(self, __context: Any):
        self.forecast = self.volatility.daily_vol.ewm(span=self.span, min_periods=1).mean()
        if self.horizon > 1:
            self.forecast = self.forecast * (self.horizon ** 0.5)
        logger.info(f"Creation Complete: {self}")


# ---- Volatility Targeting ---- #
class VolatilityTargeter(BaseModel):
    volatility: VolatilityDTO
    target_vol: float = Field(default=Settings.VOLATILITY_TARGET,
                              description="Target annual volatility (e.g., 0.20 for 20%)")
    scalars: pd.Series = None

    class Config:
        arbitrary_types_allowed = True

    def model_post_init(self, __context: Any):
        self.scalars = self.target_vol / self.volatility.annul_vol
        self.scalars.fillna(value=0.0, inplace=True)
        self.scalars[np.isinf(self.scalars)] = 0.0
        logger.info(f"Creation Complete: {self}")

    def __str__(self):
        return f"{self.__class__.__name__}({self.volatility})"
