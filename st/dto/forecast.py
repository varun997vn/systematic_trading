from typing import Any, Literal

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


class ForecastCorrelationAnalysis(BaseModel):
    """
    Analyze forecast correlations and recommend which forecasts to keep.

    Carver's guidance (Systematic Trading, Chapter 8):
    - Correlations > 0.9: Almost identical, remove one
    - Correlations 0.7-0.9: Very similar, consider removing
    - Correlations 0.5-0.7: Moderately correlated, probably fine
    - Correlations < 0.5: Good diversification

    Negative correlations are actually useful for diversification.
    """
    correlation_matrix: pd.DataFrame
    high_correlation_threshold: float = Field(
        default=0.9,
        ge=0.5,
        le=1.0,
        description="Threshold for flagging highly correlated forecasts"
    )
    moderate_correlation_threshold: float = Field(
        default=0.7,
        ge=0.3,
        le=1.0,
        description="Threshold for flagging moderately correlated forecasts"
    )

    # Analysis results
    highly_correlated_pairs: list[tuple[str, str, float]] = Field(
        default_factory=list
    )
    moderately_correlated_pairs: list[tuple[str, str, float]] = Field(
        default_factory=list
    )
    recommendations: dict[str, str] = Field(default_factory=dict)
    forecasts_to_remove: list[str] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True

    def model_post_init(self, context: Any, /) -> None:
        if self.moderate_correlation_threshold >= self.high_correlation_threshold:
            raise ValueError(
                f"moderate_correlation_threshold ({self.moderate_correlation_threshold}) "
                f"must be < high_correlation_threshold ({self.high_correlation_threshold})"
            )

        self._analyze_correlations()
        self._generate_recommendations()

    def _analyze_correlations(self) -> None:
        """Find highly and moderately correlated forecast pairs."""
        strategies = self.correlation_matrix.columns

        for i, strategy_a in enumerate(strategies):
            for strategy_b in strategies[i + 1:]:
                corr = self.correlation_matrix.loc[strategy_a, strategy_b]

                # Only care about positive correlations
                # Negative correlations are good for diversification
                if corr >= self.high_correlation_threshold:
                    self.highly_correlated_pairs.append(
                        (strategy_a, strategy_b, corr)
                    )
                elif corr >= self.moderate_correlation_threshold:
                    self.moderately_correlated_pairs.append(
                        (strategy_a, strategy_b, corr)
                    )

    def _generate_recommendations(self) -> None:
        """
        Generate recommendations based on Carver's guidance.

        Strategy for removing forecasts:
        1. Identify clusters of highly correlated forecasts
        2. Within each cluster, keep the one with the best diversification to others
        3. Remove the rest
        """
        if not self.highly_correlated_pairs and not self.moderately_correlated_pairs:
            self.recommendations["overall"] = (
                "✓ All forecasts have good diversification (correlations < 0.7). "
                "No changes needed."
            )
            return

        # Track which forecasts are problematic
        problematic_forecasts = set()

        # Handle highly correlated pairs (>0.9)
        if self.highly_correlated_pairs:
            self.recommendations["high_correlation"] = (
                f" Found {len(self.highly_correlated_pairs)} highly correlated pairs "
                f"(correlation > {self.high_correlation_threshold}):"
            )

            for strategy_a, strategy_b, corr in self.highly_correlated_pairs:
                self.recommendations[f"{strategy_a}_vs_{strategy_b}"] = (
                    f"  • {strategy_a} <-> {strategy_b}: {corr:.3f} - "
                    "These are nearly identical. Remove one."
                )
                problematic_forecasts.add(strategy_a)
                problematic_forecasts.add(strategy_b)

        # Handle moderately correlated pairs (0.7-0.9)
        if self.moderately_correlated_pairs:
            self.recommendations["moderate_correlation"] = (
                f" Found {len(self.moderately_correlated_pairs)} moderately correlated pairs "
                f"(correlation {self.moderate_correlation_threshold}-{self.high_correlation_threshold}):"
            )

            for strategy_a, strategy_b, corr in self.moderately_correlated_pairs:
                self.recommendations[f"{strategy_a}_vs_{strategy_b}"] = (
                    f"  • {strategy_a} <-> {strategy_b}: {corr:.3f} - "
                    "Consider removing one for better diversification."
                )
                problematic_forecasts.add(strategy_a)
                problematic_forecasts.add(strategy_b)

        # Determine which forecasts to remove
        # Use a greedy approach: remove forecasts that appear most frequently in high-corr pairs
        if self.highly_correlated_pairs:
            forecast_counts = {}
            for strategy_a, strategy_b, _ in self.highly_correlated_pairs:
                forecast_counts[strategy_a] = forecast_counts.get(
                    strategy_a, 0
                ) + 1
                forecast_counts[strategy_b] = forecast_counts.get(
                    strategy_b, 0
                ) + 1

            # Sort by count (most problematic first)
            sorted_forecasts = sorted(
                forecast_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )

            # Remove forecasts until no highly correlated pairs remain
            remaining_pairs = set(self.highly_correlated_pairs)
            for forecast, _ in sorted_forecasts:
                if not remaining_pairs:
                    break

                self.forecasts_to_remove.append(forecast)

                # Remove all pairs involving this forecast
                remaining_pairs = {
                    (a, b, c) for a, b, c in remaining_pairs
                    if a != forecast and b != forecast
                }

        # Generate final recommendation
        if self.forecasts_to_remove:
            self.recommendations["action"] = (
                f"\n RECOMMENDED ACTION: Remove these forecasts:\n"
                f"   {', '.join(self.forecasts_to_remove)}\n"
                f"   This will eliminate high correlations and improve diversification."
            )
        elif self.moderately_correlated_pairs:
            self.recommendations["action"] = (
                "\n OPTIONAL: You have moderate correlations (0.7-0.9). "
                "System will work, but removing one from each pair would improve diversification."
            )

    def get_filtered_strategies(
            self,
            strategies: dict[str, StrategyDTO],
            action: Literal["auto", "manual"] = "auto"
    ) -> dict[str, StrategyDTO]:
        """
        Return filtered strategy dictionary with problematic forecasts removed.

        Args:
            strategies: Original strategy dictionary
            action: 'auto' applies recommendations automatically,
                   'manual' requires user to decide

        Returns:
            Filtered strategy dictionary
        """
        if action == "manual":
            logger.info(
                "Manual mode: Review recommendations and filter strategies yourself.\n"
                f"{self.get_recommendation_summary()}"
            )
            return strategies

        if not self.forecasts_to_remove:
            logger.info("No forecasts need to be removed.")
            return strategies

        filtered = {
            name: strat for name, strat in strategies.items()
            if name not in self.forecasts_to_remove
        }

        logger.info(
            f"Auto-removed {len(self.forecasts_to_remove)} forecasts: "
            f"{self.forecasts_to_remove}"
        )

        return filtered

    def get_recommendation_summary(self) -> str:
        """Get a formatted summary of all recommendations."""
        if not self.recommendations:
            return "No correlation issues found. All forecasts are well-diversified."

        lines = ["\n" + "=" * 70]
        lines.append("FORECAST CORRELATION ANALYSIS")
        lines.append("=" * 70)

        for key, value in self.recommendations.items():
            lines.append(value)

        lines.append("=" * 70 + "\n")

        return "\n".join(lines)

    def __str__(self):
        n_strategies = len(self.correlation_matrix.columns)
        n_high = len(self.highly_correlated_pairs)
        n_mod = len(self.moderately_correlated_pairs)
        return (
            f"ForecastCorrelationAnalysis("
            f"strategies={n_strategies}, "
            f"high_corr_pairs={n_high}, "
            f"mod_corr_pairs={n_mod})"
        )

    __repr__ = __str__


class CombinedForecastDTO(BaseModel):
    """
    Combine multiple strategy forecasts into a single forecast.

    Carver's process:
    1. Check forecast correlations and remove redundant strategies
    2. Weight individual scaled forecasts
    3. Sum weighted forecasts
    4. Apply Forecast Diversification Multiplier (FDM)
    5. Cap combined forecast to [-20, 20]
    """
    strategies: dict[str, StrategyDTO]  # Name -> StrategyDTO
    forecast_weights: ForecastWeights = None
    fdm_calculator: ForecastDiversificationMultiplier = None
    forecast_config: ForecastConfig = Field(
        default_factory=ForecastConfig,
        description="Config for combined forecast (typically inherits from strategies)"
    )
    auto_filter_correlated: bool = Field(
        default=False,
        description="Automatically remove highly correlated forecasts"
    )
    correlation_analysis: ForecastCorrelationAnalysis = None

    # Computed fields
    combined_forecast_raw: pd.Series = None  # Before FDM
    combined_forecast: pd.Series = None  # After FDM and capping
    forecast_correlation: pd.DataFrame = None  # Correlation between strategy forecasts

    class Config:
        arbitrary_types_allowed = True

    def model_post_init(self, context: Any, /) -> None:
        if not self.strategies:
            raise ValueError("No strategies provided for combination")

        # Collect scaled forecasts from each strategy
        forecast_dict = {}
        for name, strategy in self.strategies.items():
            if strategy.forecasts_scaled is None:
                raise ValueError(f"Strategy '{name}' has no scaled forecasts")
            forecast_dict[name] = strategy.forecasts_scaled

        # Create DataFrame of all forecasts (aligned by index)
        forecasts_df = pd.DataFrame(forecast_dict)

        # Calculate forecast correlations
        self.forecast_correlation = forecasts_df.corr()

        # Analyze correlations
        self.correlation_analysis = ForecastCorrelationAnalysis(
            correlation_matrix=self.forecast_correlation
        )

        # Log recommendations
        logger.info(self.correlation_analysis.get_recommendation_summary())

        # Auto-filter if enabled
        if self.auto_filter_correlated:
            original_count = len(self.strategies)
            self.strategies = self.correlation_analysis.get_filtered_strategies(
                self.strategies,
                action="auto"
            )
            new_count = len(self.strategies)

            if new_count < original_count:
                logger.warning(
                    f"Auto-filtered {original_count - new_count} highly correlated forecasts. "
                    f"Remaining: {list(self.strategies.keys())}"
                )

                # Recalculate correlations with filtered strategies
                forecast_dict = {
                    name: strategy.forecasts_scaled
                    for name, strategy in self.strategies.items()
                }
                forecasts_df = pd.DataFrame(forecast_dict)
                self.forecast_correlation = forecasts_df.corr()

        strategy_names = list(self.strategies.keys())

        # Auto-create equal weights if not provided
        if self.forecast_weights is None:
            self.forecast_weights = ForecastWeights(
                strategy_names=strategy_names
            )

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

    def print_correlation_analysis(self) -> None:
        """Pretty-print the correlation analysis."""
        print(self.correlation_analysis.get_recommendation_summary())

    def get_filtered_strategies(self) -> dict[str, StrategyDTO]:
        """Get strategy dictionary with recommended forecasts removed."""
        return self.correlation_analysis.get_filtered_strategies(
            self.strategies,
            action="auto"
        )

    def __str__(self):
        ticker = list(self.strategies.values())[0].price_data.ticker
        fdm = self.fdm_calculator.fdm
        n_high_corr = len(self.correlation_analysis.highly_correlated_pairs)
        return (f"CombinedForecast(ticker={ticker}, "
                f"strategies={list(self.strategies.keys())}, "
                f"FDM={fdm:.4f}, high_corr_pairs={n_high_corr})")

    __repr__ = __str__
