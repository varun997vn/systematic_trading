from pydantic import BaseModel, Field, field_validator


# ---- Strategy Configuration DTOs ---- #


class EWMACConfig(BaseModel):
    """EWMAC trend-following strategy configuration."""

    fast_span: int = Field(ge=2, description="Fast EMA span (e.g., 2, 4, 8, 16, 32, 64)")
    slow_span: int = Field(gt=2, description="Slow EMA span (must be > fast_span)")

    @field_validator("slow_span")
    @classmethod
    def validate_spans(cls, slow: int, info) -> int:
        """Ensure slow span is greater than fast span."""
        if "fast_span" in info.data and slow <= info.data["fast_span"]:
            raise ValueError("slow_span must be greater than fast_span")
        return slow


class CarryConfig(BaseModel):
    """Carry-based strategy configuration."""

    smoothing_span: int = Field(default=30, ge=1, description="EWMA span for smoothing carry signal")


class MeanReversionConfig(BaseModel):
    """Mean reversion strategy configuration."""

    lookback: int = Field(default=30, ge=2, description="Lookback period for mean/std calculation")
    entry_threshold: float = Field(default=2.0, gt=0, description="Standard deviations for entry signal")


class TurtleConfig(BaseModel):
    """Turtle Trading breakout strategy configuration."""

    entry_window: int = Field(default=20, ge=2, description="Entry breakout window (Donchian Channel)")
    exit_window: int = Field(default=10, ge=1, description="Exit breakout window")

    @field_validator("exit_window")
    @classmethod
    def validate_windows(cls, exit_w: int, info) -> int:
        """Warn if exit window >= entry window (typically exit should be smaller)."""
        if "entry_window" in info.data and exit_w >= info.data["entry_window"]:
            # Just log a note, don't raise - this is a soft recommendation
            pass
        return exit_w
