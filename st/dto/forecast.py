"""
Data Transfer Objects for Systematic Trading Framework

Minimal Pydantic models for configuration and data transfer.
Follows Robert Carver's "Systematic Trading" methodology.
"""

from typing import Dict, Optional

from pydantic import BaseModel, Field, field_validator

from .strategy import EWMACConfig


# ---- Forecast Configuration DTO ---- #


class ForecastConfig(BaseModel):
    """Forecast generation and scaling configuration."""

    target_abs_forecast: float = Field(
        default=10.0,
        gt=0,
        description="Target average absolute forecast (Carver standard: 10)"
    )
    min_forecast: float = Field(default=-20.0, description="Minimum forecast value")
    max_forecast: float = Field(default=20.0, description="Maximum forecast value")
    cap_forecasts: bool = Field(default=True, description="Apply min/max capping")
    use_volatility_standardization: bool = Field(
        default=True,
        description="Normalize forecasts by price volatility"
    )

    @field_validator("target_abs_forecast")
    @classmethod
    def validate_target(cls, v: float) -> float:
        """Validate target forecast is reasonable (Carver uses 10)."""
        if v > 20:
            # Log warning but don't fail - user may have good reason
            pass
        return v

    @field_validator("max_forecast")
    @classmethod
    def validate_range(cls, max_f: float, info) -> float:
        """Ensure max > min forecast."""
        if "min_forecast" in info.data and max_f <= info.data["min_forecast"]:
            raise ValueError("max_forecast must be greater than min_forecast")
        return max_f


# ---- Position Sizing DTO ---- #


class PositionSizingConfig(BaseModel):
    """Position sizing and risk management configuration."""

    instrument_weight: float = Field(
        default=1.0,
        ge=0,
        le=1.0,
        description="Portfolio weight for this instrument (0-1)"
    )
    volatility_target: float = Field(
        default=0.16,
        gt=0,
        description="Annual volatility target (e.g., 16% = 0.16)"
    )
    notional_exposure_per_contract: Optional[float] = Field(
        default=None,
        description="Notional value per contract (for futures)"
    )


# ---- Forecast Weights DTO ---- #


class ForecastWeights(BaseModel):
    """Weights for combining multiple forecasts."""

    weights: Dict[str, float] = Field(description="Map of rule_name to weight")

    @field_validator("weights")
    @classmethod
    def validate_weights(cls, w: Dict[str, float]) -> Dict[str, float]:
        """Ensure weights are positive and sum to ~1.0."""
        if not w:
            raise ValueError("weights dictionary cannot be empty")

        for rule, weight in w.items():
            if weight < 0:
                raise ValueError(f"Negative weight for {rule}: {weight}")

        weight_sum = sum(w.values())
        if not (0.99 <= weight_sum <= 1.01):
            raise ValueError(
                f"Weights must sum to 1.0, got {weight_sum:.4f}. "
                "Use normalize=True or adjust weights."
            )
        return w

    def normalize(self) -> "ForecastWeights":
        """Return a new ForecastWeights with normalized weights summing to 1.0."""
        total = sum(self.weights.values())
        if total == 0:
            raise ValueError("Cannot normalize - weights sum to zero")

        normalized = {k: v / total for k, v in self.weights.items()}
        return ForecastWeights(weights=normalized)


# ---- Trading Signal DTO ---- #


class TradingSignal(BaseModel):
    """Output trading signal with all necessary information."""

    ticker: str = Field(description="Instrument identifier")
    timestamp: str = Field(description="Signal timestamp (ISO format)")

    # Forecast information
    combined_forecast: float = Field(description="Combined scaled forecast (-20 to +20)")
    forecast_components: Dict[str, float] = Field(
        default_factory=dict,
        description="Individual forecast contributions"
    )

    # Position information
    target_position: float = Field(description="Target position in contracts/units")
    current_position: Optional[float] = Field(
        default=None,
        description="Current position (if known)"
    )

    # Risk metrics
    position_risk: Optional[float] = Field(
        default=None,
        description="Position risk as % of capital"
    )
    volatility_scalar: Optional[float] = Field(
        default=None,
        description="Volatility adjustment scalar"
    )

    # Metadata
    signal_strength: str = Field(
        default="neutral",
        description="Signal strength: 'strong_long', 'long', 'neutral', 'short', 'strong_short'"
    )

    @field_validator("signal_strength")
    @classmethod
    def validate_strength(cls, v: str) -> str:
        """Ensure valid signal strength."""
        valid = {"strong_long", "long", "neutral", "short", "strong_short"}
        if v not in valid:
            raise ValueError(f"signal_strength must be one of {valid}")
        return v


# ---- Preset Configurations ---- #


class PresetConfigs:
    """Common preset configurations following Carver's recommendations."""

    # Carver's standard EWMAC suite
    EWMAC_SUITE = [
        EWMACConfig(fast_span=2, slow_span=8),
        EWMACConfig(fast_span=4, slow_span=16),
        EWMACConfig(fast_span=8, slow_span=32),
        EWMACConfig(fast_span=16, slow_span=64),
        EWMACConfig(fast_span=32, slow_span=128),
        EWMACConfig(fast_span=64, slow_span=256),
    ]

    # Default forecast weights (equal weight)
    EQUAL_WEIGHTS = {
        "ewmac_2_8": 1 / 6,
        "ewmac_4_16": 1 / 6,
        "ewmac_8_32": 1 / 6,
        "ewmac_16_64": 1 / 6,
        "ewmac_32_128": 1 / 6,
        "ewmac_64_256": 1 / 6,
    }

    # Conservative forecast config
    CONSERVATIVE = ForecastConfig(
        target_abs_forecast=8.0,  # Lower target
        min_forecast=-15.0,
        max_forecast=15.0,
        cap_forecasts=True,
        use_volatility_standardization=True,
    )

    # Aggressive forecast config
    AGGRESSIVE = ForecastConfig(
        target_abs_forecast=12.0,  # Higher target
        min_forecast=-20.0,
        max_forecast=20.0,
        cap_forecasts=True,
        use_volatility_standardization=True,
    )
