from typing import Any

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from utils.logger import setup_logger
from .strategy import StrategyDTO, ForecastConfig

logger = setup_logger(__name__)


class ForecastWeights(BaseModel):
    """
    Forecast weights configuration.
    
    Carver uses equal weights as default, but allows handcrafted or optimized weights.
    """
    strategy_names: list[str]
    weights: dict[str, float] = Field(default_factory=dict)
    auto_equal_weight: bool = Field(
        default=True,
        description="Automatically assign equal weights if weights not provided"
    )

    class Config:
        arbitrary_types_allowed = True

    def model_post_init(self, context: Any, /) -> None:
        if self.auto_equal_weight and not self.weights:
            # Equal weighting - Carver's default
            equal_weight = 1.0 / len(self.strategy_names)
            self.weights = {name: equal_weight for name in self.strategy_names}

        # Validation
        if set(self.weights.keys()) != set(self.strategy_names):
            raise ValueError(
                f"Weights keys {set(self.weights.keys())} don't match "
                f"strategy names {set(self.strategy_names)}"
            )

        total_weight = sum(self.weights.values())
        if not np.isclose(total_weight, 1.0):
            raise ValueError(
                f"Weights must sum to 1.0, got {total_weight}"
            )

    def __str__(self):
        return f"ForecastWeights({self.weights})"

    __repr__ = __str__


class ForecastDiversificationMultiplier(BaseModel):
    """
    Calculate Forecast Diversification Multiplier (FDM) from forecast correlations.
    
    Carver: FDM = 1/sqrt(sum of weighted correlation matrix)
    This accounts for diversification benefit when combining forecasts.
    """
    forecast_weights: ForecastWeights
    correlation_matrix: pd.DataFrame = None  # Forecast correlations
    fdm: float = Field(default=1.0, description="Calculated FDM")

    class Config:
        arbitrary_types_allowed = True

    def model_post_init(self, context: Any, /) -> None:
        if self.correlation_matrix is None or self.correlation_matrix.empty:
            logger.warning("No correlation matrix provided - using FDM = 1.0")
            self.fdm = 1.0
            return

        # Carver's FDM formula
        weights = np.array(
            [
                self.forecast_weights.weights[name]
                for name in self.correlation_matrix.columns
            ]
        )

        # Weighted correlation: w^T * Corr * w
        weighted_corr = weights @ self.correlation_matrix.values @ weights

        # FDM = 1 / sqrt(weighted_correlation)
        self.fdm = 1.0 / np.sqrt(weighted_corr)

        logger.info(f"Calculated FDM: {self.fdm:.4f}")

    def __str__(self):
        return f"FDM(value={self.fdm:.4f})"

    __repr__ = __str__


class CombinedForecastDTO(BaseModel):
    """
    Combine multiple strategy forecasts into a single forecast.
    
    Carver's process:
    1. Weight individual scaled forecasts
    2. Sum weighted forecasts
    3. Apply Forecast Diversification Multiplier (FDM)
    4. Cap combined forecast to [-20, 20]
    """
    strategies: dict[str, StrategyDTO]  # Name -> StrategyDTO
    forecast_weights: ForecastWeights = None
    fdm_calculator: ForecastDiversificationMultiplier = None
    forecast_config: ForecastConfig = Field(
        default_factory=ForecastConfig,
        description="Config for combined forecast (typically inherits from strategies)"
    )

    # Computed fields
    combined_forecast_raw: pd.Series = None  # Before FDM
    combined_forecast: pd.Series = None  # After FDM and capping
    forecast_correlation: pd.DataFrame = None  # Correlation between strategy forecasts

    class Config:
        arbitrary_types_allowed = True

    def model_post_init(self, context: Any, /) -> None:
        if not self.strategies:
            raise ValueError("No strategies provided for combination")

        strategy_names = list(self.strategies.keys())

        # Auto-create equal weights if not provided
        if self.forecast_weights is None:
            self.forecast_weights = ForecastWeights(
                strategy_names=strategy_names
                )

        # Collect scaled forecasts from each strategy
        forecast_dict = {}
        for name, strategy in self.strategies.items():
            if strategy.forecasts_scaled is None:
                raise ValueError(f"Strategy '{name}' has no scaled forecasts")
            forecast_dict[name] = strategy.forecasts_scaled

        # Create DataFrame of all forecasts (aligned by index)
        forecasts_df = pd.DataFrame(forecast_dict)

        # Calculate forecast correlations (for FDM calculation)
        self.forecast_correlation = forecasts_df.corr()

        # Calculate FDM if not provided
        if self.fdm_calculator is None:
            self.fdm_calculator = ForecastDiversificationMultiplier(
                forecast_weights=self.forecast_weights,
                correlation_matrix=self.forecast_correlation
            )

        # Step 1: Weight individual forecasts
        weighted_forecasts = pd.DataFrame()
        for name in strategy_names:
            weight = self.forecast_weights.weights[name]
            weighted_forecasts[name] = forecasts_df[name] * weight

        # Step 2: Sum weighted forecasts
        self.combined_forecast_raw = weighted_forecasts.sum(axis=1)

        # Step 3: Apply FDM
        self.combined_forecast = self.combined_forecast_raw * self.fdm_calculator.fdm

        # Step 4: Cap to [-20, 20] (or custom range)
        if self.forecast_config.cap_forecasts:
            self.combined_forecast = self.combined_forecast.clip(
                lower=self.forecast_config.min_forecast,
                upper=self.forecast_config.max_forecast
            )

        logger.info(f"Creation completed: {self}")

    def __str__(self):
        ticker = list(self.strategies.values())[0].price_data.ticker
        fdm = self.fdm_calculator.fdm
        return (f"CombinedForecast(ticker={ticker}, "
                f"strategies={list(self.strategies.keys())}, "
                f"FDM={fdm:.4f})")

    __repr__ = __str__
