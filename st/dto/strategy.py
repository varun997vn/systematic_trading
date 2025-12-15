from typing import Any

from pydantic import BaseModel, Field

from utils.logger import setup_logger

logger = setup_logger(__name__)


# ---- Strategy Configuration DTOs ---- #


class EWMACStrategyDTO(BaseModel):
    """EWMAC trend-following strategy configuration."""

    fast_span: int = Field(ge=2, description="Fast EMA span (e.g., 2, 4, 8, 16, 32, 64)")
    slow_span: int = Field(gt=2, description="Slow EMA span (must be > fast_span)")

    def model_post_init(self, context: Any, /) -> None:
        if self.slow_span >= self.fast_span:
            raise ValueError(f"slow_span: {self.slow_span} must be smaller than fast_span: {self.fast_span}")
        logger.info(f"Creation Completed: {self}")

    def __str__(self):
        return f"EWMACStrategy(slow={self.slow_span}, fast={self.fast_span})"


class CarryStrategyDTO(BaseModel):
    """Carry-based strategy configuration."""

    smoothing_span: int = Field(default=30, ge=1, description="EWMA span for smoothing carry signal")

    def model_post_init(self, context: Any, /) -> None:
        logger.info(f"Creation Completed: {self}")

    def __str__(self):
        return f"CarryStrategy(smoothening={self.smoothing_span})"


class MeanReversionStrategyDTO(BaseModel):
    """Mean reversion strategy configuration."""

    lookback: int = Field(default=30, ge=2, description="Lookback period for mean/std calculation")
    entry_threshold: float = Field(default=2.0, gt=0, description="Standard deviations for entry signal")

    def model_post_init(self, context: Any, /) -> None:
        logger.info(f"Creation Completed: {self}")

    def __str__(self):
        return f"MeanReversionStrategy(lookback={self.lookback}, std={self.entry_threshold})"


class TurtleStrategy(BaseModel):
    """Turtle Trading breakout strategy configuration."""

    entry_window: int = Field(default=20, ge=2, description="Entry breakout window (Donchian Channel)")
    exit_window: int = Field(default=10, ge=1, description="Exit breakout window")

    def model_post_init(self, context: Any, /) -> None:
        logger.info(f"Creation Completed: {self}")

    def __str__(self):
        return f"TurtleStrategy(entry_window={self.entry_window}, exit_window={self.exit_window})"
