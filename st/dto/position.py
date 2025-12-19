from copy import deepcopy
from typing import Any, Optional

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from st.config import Settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


# ============================================================================
# Risk Target (Portfolio-Level Configuration)
# ============================================================================

class PortfolioRiskTargetDTO(BaseModel):
    """
    Portfolio-level risk parameters.

    This defines the risk budget for the entire portfolio, not individual instruments.
    Each instrument gets a portion of this risk budget based on its weight.

    Attributes:
        annual_volatility_target: Target portfolio volatility (e.g., 0.25 for 25%)
        notional_trading_capital: Total trading capital in account currency

    Note: FX conversion is handled at instrument level, not here.
    """
    annual_volatility_target: float = Field(
        default=Settings.VOLATILITY_TARGET,
        gt=0,
        le=0.50,
        description="Target annualized portfolio volatility (0.25 = 25%)"
    )
    notional_trading_capital: float = Field(
        gt=0,
        description="Total trading capital in account currency"
    )

    class Config:
        arbitrary_types_allowed = True

    def __str__(self):
        return (
            f"PortfolioRiskTarget("
            f"vol_target={self.annual_volatility_target:.1%}, "
            f"capital={self.notional_trading_capital:,.0f})"
        )

    __repr__ = __str__


# ============================================================================
# Instrument Position Sizing
# ============================================================================

class InstrumentPositionDTO(BaseModel):
    """
    Calculate position sizes for a single instrument using Carver's method.

    Carver's formula (Systematic Trading, Ch 11):
        Position = (forecast / 10) * instrument_weight * IDM * volatility_scalar

    Where:
        - forecast: Combined forecast, typically capped at [-20, +20]
        - instrument_weight: This instrument's allocation in portfolio (0-1)
        - IDM: Instrument Diversification Multiplier (from portfolio)
        - volatility_scalar: Position that would hit risk target for forecast=10

    The volatility scalar is:
        (portfolio_vol_target * capital) / (instrument_vol * price * FX)

    Inputs:
        combined_forecast: Combined forecast signal (typically [-20, +20])
        instrument_volatility: Annualized price volatility (% of price)
        price: Instrument price in instrument currency
        portfolio_risk_target: Portfolio risk parameters
        instrument_weight: Allocation to this instrument (must be set by portfolio)
        idm: Instrument Diversification Multiplier (must be set by portfolio)
        fx_rate: FX rate to convert instrument currency to account currency

    Outputs:
        position: Fractional position sizes (pre-rounding)
        volatility_scalar: Position for forecast of 10
    """
    combined_forecast: pd.Series
    instrument_volatility: pd.Series  # Annualized % volatility
    price: pd.Series
    portfolio_risk_target: PortfolioRiskTargetDTO
    instrument_weight: float = Field(
        default=1.0,
        gt=0,
        le=1.0,
        description="Portfolio allocation to this instrument (should sum to 1 across all)"
    )
    idm: float = Field(
        default=1.0,
        gt=0,
        le=3.0,
        description="Instrument Diversification Multiplier (from portfolio correlations)"
    )
    fx_rate: float = Field(
        default=1.0,
        gt=0,
        description="FX rate: instrument_currency per account_currency"
    )

    # Computed fields
    volatility_scalar: pd.Series = None
    position: pd.Series = None

    class Config:
        arbitrary_types_allowed = True

    def model_post_init(self, __context: Any):
        # Deep copy to avoid mutations
        self.combined_forecast = deepcopy(self.combined_forecast)
        self.instrument_volatility = deepcopy(self.instrument_volatility)
        self.price = deepcopy(self.price)

        # Validate alignment
        self._validate_aligned()

        # Calculate volatility scalar
        self.volatility_scalar = self._calculate_volatility_scalar()

        # Calculate position
        # Position = (forecast / 10) * weight * IDM * vol_scalar
        self.position = (
                (self.combined_forecast / 10.0)
                * self.instrument_weight
                * self.idm
                * self.volatility_scalar
        )

        # scale according to available capital
        required_curr_capital = self.position * self.price
        avaliable_capital = self.portfolio_risk_target.notional_trading_capital * self.instrument_weight
        self.position = self.position * avaliable_capital / required_curr_capital


        logger.info(f"Creation completed: {self}")

    def _validate_aligned(self) -> None:
        """Ensure all series have identical indices."""
        base_index = self.combined_forecast.index

        for name, series in [
            ('instrument_volatility', self.instrument_volatility),
            ('price', self.price)
        ]:
            if not series.index.equals(base_index):
                # Attempt to align
                self.combined_forecast, series_aligned = \
                    self.combined_forecast.align(series, join='inner')

                if name == 'instrument_volatility':
                    self.instrument_volatility = series_aligned
                else:
                    self.price = series_aligned

        logger.warning(f"Aligned to {len(self.combined_forecast)} common dates")

    def _calculate_volatility_scalar(self) -> pd.Series:
        """
        Calculate volatility scalar: position for forecast of +10.

        Carver: "The volatility scalar tells us what position we would hold
        for a forecast of +10, which is our average forecast."

        Formula:
            (vol_target * capital) / (instrument_vol * price * FX)

        Where instrument_vol is annualized % volatility of price.
        """
        # Convert percentage volatility to price volatility
        # If vol = 20% and price = 100, price_vol = 20
        price_volatility = (self.instrument_volatility / 100.0) * self.price

        # Target risk contribution in account currency
        risk_capital = (
                self.portfolio_risk_target.annual_volatility_target
                * self.portfolio_risk_target.notional_trading_capital
        )

        # Volatility scalar: how many contracts to hit risk target?
        # Divide by price_vol (in instrument currency) times FX rate
        vol_scalar = risk_capital / (price_volatility * self.fx_rate)

        return vol_scalar

    def __str__(self):
        return (
            f"InstrumentPosition("
            f"weight={self.instrument_weight:.2f}, "
            f"IDM={self.idm:.2f}, "
            f"shape={self.position.shape})"
        )

    __repr__ = __str__


# ============================================================================
# Position Buffering
# ============================================================================

class BufferedPositionDTO(BaseModel):
    """
    Apply Carver's buffering logic to reduce excessive trading.

    Carver's rule (Systematic Trading, Ch 14):
        Only trade if position change exceeds 10% of current position.

    This reduces turnover while maintaining responsiveness to signals.

    Inputs:
        optimal_position: Unbuffered position from InstrumentPositionDTO
        current_position: Current holdings (None if starting from zero)
        buffer_fraction: Minimum fractional change to trigger trade (default 0.10)

    Outputs:
        buffered_position: Position after applying buffer logic
    """
    optimal_position: pd.Series
    current_position: Optional[pd.Series] = None
    buffer_fraction: float = Field(
        default=0.10,
        gt=0,
        lt=1.0,
        description="Minimum fractional change to trigger rebalance"
    )

    # Computed field
    buffered_position: pd.Series = None

    class Config:
        arbitrary_types_allowed = True

    def model_post_init(self, __context: Any):
        self.optimal_position = deepcopy(self.optimal_position)

        if self.current_position is None:
            # First position: no buffering needed
            self.buffered_position = self.optimal_position
            logger.info("Initial position - no buffering applied")
        else:
            self.current_position = deepcopy(self.current_position)
            self.buffered_position = self._apply_buffer()

        logger.info(f"Creation completed: {self}")

    def _apply_buffer(self) -> pd.Series:
        """
        Apply buffer logic: only change position if delta exceeds threshold.

        Buffer = buffer_fraction * |current_position|
        Update position only if |optimal - current| > buffer
        """
        # Align series (inner join to only trade where we have both)
        optimal, current = self.optimal_position.align(
            self.current_position,
            join='inner'
        )

        # Calculate buffer size (absolute value)
        buffer_size = self.buffer_fraction * current.abs()

        # Calculate delta
        delta = optimal - current

        # Start with current position
        buffered = current.copy()

        # Update where threshold exceeded
        threshold_exceeded = delta.abs() > buffer_size
        buffered[threshold_exceeded] = optimal[threshold_exceeded]

        # Log buffering statistics
        n_total = len(buffered)
        n_changed = threshold_exceeded.sum()
        logger.info(
            f"Buffering: {n_changed}/{n_total} positions changed "
            f"({n_changed / n_total * 100:.1f}%)"
        )

        return buffered

    def __str__(self):
        n_positions = len(self.buffered_position)
        if self.current_position is not None:
            n_changed = (self.buffered_position != self.current_position).sum()
            change_pct = n_changed / n_positions * 100
            return (
                f"BufferedPosition("
                f"buffer={self.buffer_fraction:.1%}, "
                f"changed={n_changed}/{n_positions} ({change_pct:.1f}%))"
            )
        return f"BufferedPosition(buffer={self.buffer_fraction:.1%}, initial_position)"

    __repr__ = __str__


# ============================================================================
# Position Rounding
# ============================================================================

class RoundedPositionDTO(BaseModel):
    """
    Round fractional positions to tradeable integers.

    Carver: Round positions to nearest integer, but zero out positions
    below a minimum size threshold.

    Inputs:
        fractional_position: Position before rounding (from BufferedPositionDTO)
        min_position_size: Minimum position size (default 1.0 contract)

    Outputs:
        rounded_position: Integer positions ready for execution
    """
    fractional_position: pd.Series
    min_position_size: float = Field(
        default=1.0,
        gt=0,
        description="Minimum position size threshold"
    )

    # Computed field
    rounded_position: pd.Series = None

    class Config:
        arbitrary_types_allowed = True

    def model_post_init(self, __context: Any):
        self.fractional_position = deepcopy(self.fractional_position)

        # Round to nearest integer
        rounded = self.fractional_position.apply(np.floor)

        # Zero out positions below minimum size
        rounded[rounded.abs() < self.min_position_size] = 0

        self.rounded_position = rounded

        # Log rounding statistics
        n_nonzero = (self.rounded_position != 0).sum()
        mean_abs = self.rounded_position.abs().mean()
        logger.info(
            f"Rounding: {n_nonzero} non-zero positions, "
            f"mean |position| = {mean_abs:.2f}"
        )

        logger.info(f"Creation completed: {self}")

    def __str__(self):
        n_total = len(self.rounded_position)
        n_nonzero = (self.rounded_position != 0).sum()
        mean_abs = self.rounded_position.abs().mean()
        return (
            f"RoundedPosition("
            f"non_zero={n_nonzero}/{n_total}, "
            f"mean_|pos|={mean_abs:.2f})"
        )

    __repr__ = __str__


# ============================================================================
# Complete Position Pipeline
# ============================================================================

class PositionPipelineDTO(BaseModel):
    """
    Complete position sizing pipeline for a single instrument.

    Combines all position sizing steps:
    1. Calculate optimal fractional position
    2. Apply buffering to reduce turnover
    3. Round to tradeable integers

    This is a convenience wrapper that chains together the individual DTOs.

    Inputs:
        combined_forecast: Combined forecast signal
        instrument_volatility: Annualized volatility (% of price)
        price: Instrument price
        portfolio_risk_target: Portfolio risk parameters
        instrument_weight: Allocation to this instrument
        idm: Instrument Diversification Multiplier
        fx_rate: FX conversion rate
        current_position: Current holdings (None if starting fresh)
        buffer_fraction: Buffering threshold (default 0.10)
        min_position_size: Minimum tradeable size (default 1.0)

    Outputs:
        instrument_position: Optimal fractional position
        buffered_position: Position after buffering
        rounded_position: Final tradeable position
    """
    combined_forecast: pd.Series
    instrument_volatility: pd.Series
    price: pd.Series
    portfolio_risk_target: PortfolioRiskTargetDTO
    instrument_weight: float = Field(default=1.0, gt=0, le=1.0)
    idm: float = Field(default=1.0, gt=0, le=3.0)
    fx_rate: float = Field(default=1.0, gt=0)
    current_position: Optional[pd.Series] = None
    buffer_fraction: float = Field(default=0.10, gt=0, lt=1.0)
    min_position_size: float = Field(default=1.0, gt=0)

    # Computed fields
    instrument_position: InstrumentPositionDTO = None
    buffered: BufferedPositionDTO = None
    rounded: RoundedPositionDTO = None
    rescaled_to_available_capital: RoundedPositionDTO = None

    class Config:
        arbitrary_types_allowed = True

    def model_post_init(self, __context: Any):
        # Step 1: Calculate optimal position
        self.instrument_position = InstrumentPositionDTO(
            combined_forecast=self.combined_forecast,
            instrument_volatility=self.instrument_volatility,
            price=self.price,
            portfolio_risk_target=self.portfolio_risk_target,
            instrument_weight=self.instrument_weight,
            idm=self.idm,
            fx_rate=self.fx_rate
        )

        # Step 2: Apply buffering
        self.buffered = BufferedPositionDTO(
            optimal_position=self.instrument_position.position,
            current_position=self.current_position,
            buffer_fraction=self.buffer_fraction
        )

        # Step 3: Round to integers
        self.rounded = RoundedPositionDTO(
            fractional_position=self.buffered.buffered_position,
            min_position_size=self.min_position_size
        )

        logger.info(f"Creation completed: {self}")

    @property
    def final_position(self) -> pd.Series:
        """Get the final tradeable position (convenience property)."""
        return self.rounded.rounded_position

    def get_trades(self) -> pd.Series:
        """
        Calculate trades needed to move from current to final position.

        Returns:
            Series of position changes (positive = buy, negative = sell)
        """
        if self.current_position is None:
            # All positions are new trades
            return self.final_position

        # Calculate delta
        current_aligned = self.current_position.reindex(
            self.final_position.index,
            fill_value=0
        )
        trades = self.final_position - current_aligned

        return trades

    def __str__(self):
        n_trades = (self.get_trades() != 0).sum()
        return (
            f"PositionPipeline("
            f"weight={self.instrument_weight:.2f}, "
            f"IDM={self.idm:.2f}, "
            f"trades={n_trades})"
        )

    __repr__ = __str__


# ============================================================================
# Helper Functions
# ============================================================================

def calculate_turnover(
        old_positions: pd.Series,
        new_positions: pd.Series
) -> float:
    """
    Calculate turnover as fraction of position changes.

    Turnover = sum(|position_change|) / average_position_size

    Args:
        old_positions: Previous positions
        new_positions: New positions

    Returns:
        Turnover ratio (higher = more trading)
    """
    # Align series
    old, new = old_positions.align(new_positions, join='inner')

    # Calculate changes
    changes = (new - old).abs()

    # Average position size
    avg_position = (old.abs() + new.abs()).mean() / 2

    if avg_position == 0:
        return 0.0

    turnover = changes.sum() / (len(changes) * avg_position)

    return turnover


def compare_buffering_impact(
        position_pipeline: PositionPipelineDTO,
        unbuffered_position: pd.Series
) -> dict:
    """
    Compare buffered vs unbuffered positions to measure buffer impact.

    Args:
        position_pipeline: Pipeline with buffering
        unbuffered_position: Position without buffering

    Returns:
        Dictionary with comparison metrics
    """
    buffered = position_pipeline.buffered.buffered_position

    # Align for comparison
    buffered_aligned, unbuffered_aligned = buffered.align(
        unbuffered_position,
        join='inner'
    )

    # Count differences
    n_different = (buffered_aligned != unbuffered_aligned).sum()
    n_total = len(buffered_aligned)

    # Calculate turnover difference
    if position_pipeline.current_position is not None:
        turnover_unbuffered = calculate_turnover(
            position_pipeline.current_position,
            unbuffered_aligned
        )
        turnover_buffered = calculate_turnover(
            position_pipeline.current_position,
            buffered_aligned
        )
        turnover_reduction = (
                1 - turnover_buffered / turnover_unbuffered
        ) if turnover_unbuffered > 0 else 0
    else:
        turnover_unbuffered = None
        turnover_buffered = None
        turnover_reduction = None

    return {
        'positions_changed': n_different,
        'total_positions': n_total,
        'change_percentage': n_different / n_total * 100,
        'turnover_unbuffered': turnover_unbuffered,
        'turnover_buffered': turnover_buffered,
        'turnover_reduction_pct': (
            turnover_reduction * 100 if turnover_reduction else None
        )
    }
