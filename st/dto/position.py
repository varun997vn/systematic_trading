from typing import Optional

import pandas as pd
from pydantic import BaseModel, Field


class RiskTarget(BaseModel):
    """Target risk parameters for position sizing.

    Attributes:
        annual_volatility_target: Target annualized portfolio volatility (e.g., 0.25 for 25%)
        notional_trading_capital: Trading capital in currency units
        fx_rate: FX rate to convert instrument currency to account currency (default 1.0)
    """
    annual_volatility_target: float = Field(
        gt=0, le=0.5, default=0.25,
        description="Annualized volatility target. Above 50% is unrealistic."
    )
    notional_trading_capital: float = Field(gt=0)
    fx_rate: float = Field(gt=0, default=1.0)

    def __str__(self):
        return (f"RistTarget(annual_volatility_target="
                f"{self.annual_volatility_target}, "
                f"notional_trading_capital={self.notional_trading_capital}, "
                f"fx_rate={self.fx_rate})")

    __repr__ = __str__


class InstrumentPositionSizer(BaseModel):
    """Calculate position sizes for a single instrument using Carver's method.

    Position = (forecast / 10) * instrument_weight * IDM * volatility_scalar

    Where volatility_scalar = (risk_target * capital) / (instrument_vol * price * FX)

    risk_target: Risk targeting parameters
    instrument_weight: Portfolio weight for this instrument (0-1, should sum to 1 across portfolio)
    idm: Instrument diversification multiplier (typically 1.0 - 2.5)
    """

    risk_target: RiskTarget
    instrument_weight: float = Field(default=1.0, gt=0, le=1)
    idm: float = Field(default=1.0, gt=0, le=3)

    def calculate_position(
            self,
            combined_forecast: pd.Series,
            instrument_volatility: pd.Series,
            price: pd.Series,
    ) -> pd.Series:
        """Calculate position sizes (in contracts) from forecast and volatility.

        Args:
            combined_forecast: Combined, capped forecast (typically -20 to +20)
            instrument_volatility: Annualized price volatility (% of price)
            price: Instrument price (for contract value calculation)

        Returns:
            Position sizes in contracts (fractional, pre-rounding)

        Notes:
            - All series must be aligned by date
            - Volatility should be annualized (daily vol * sqrt(252))
            - Returns NaN where any input is NaN (no forward filling)
        """
        self._validate_aligned(
            [combined_forecast, instrument_volatility, price]
        )

        # Carver: "The volatility scalar tells us what position we would hold
        # for a forecast of +10, which is our average forecast"
        volatility_scalar = self._calculate_volatility_scalar(
            instrument_volatility=instrument_volatility,
            price=price,
        )

        # Position = (forecast / 10) * weight * IDM * vol_scalar
        # Forecast of 10 = 100% of target position
        # Forecast of 20 = 200% of target position (max)
        position = (
                (combined_forecast / 10.0)
                * self.instrument_weight
                * self.idm
                * volatility_scalar
        )

        return position

    def _calculate_volatility_scalar(
            self,
            instrument_volatility: pd.Series,
            price: pd.Series,
    ) -> pd.Series:
        """Calculate the volatility scalar for position sizing.

        This is the position we would hold for a forecast of +10.

        Formula: (risk_target * capital) / (instrument_vol * price * FX)

        Where:
        - instrument_vol is annualized % volatility of price
        - price is in instrument currency
        - FX converts instrument currency to account currency
        """
        # Convert percentage volatility to price volatility
        # If vol = 20% and price = 100, price vol = 20
        price_volatility = (instrument_volatility / 100.0) * price

        # Notional value of 1 contract in account currency
        notional_per_contract = price * self.risk_target.fx_rate

        # Target risk contribution in account currency
        risk_capital = (
                self.risk_target.annual_volatility_target
                * self.risk_target.notional_trading_capital
        )

        # Position for forecast of 10: how many contracts to hit risk target?
        volatility_scalar = risk_capital / (
                price_volatility * self.risk_target.fx_rate
        )

        return volatility_scalar

    @staticmethod
    def _validate_aligned(series_list: list[pd.Series]) -> None:
        """Ensure all series have the same index."""
        if not series_list:
            return

        first_index = series_list[0].index
        for i, series in enumerate(series_list[1:], 1):
            if not series.index.equals(first_index):
                raise ValueError(
                    f"Series {i} has misaligned index with series 0. "
                    "Align all inputs before calling calculate_position."
                )

    def __str__(self) -> str:
        return (
            f"InstrumentPositionSizer("
            f"risk_target={self.risk_target.annual_volatility_target:.1%}, "
            f"weight={self.instrument_weight:.2f}, "
            f"IDM={self.idm:.2f})"
        )

    __repr__ = __str__


class BufferedPositionSizer:
    """Add Carver's buffering logic to reduce excessive trading.

    Carver's rule: only trade if position change exceeds 10% of current position.
    This reduces turnover while maintaining responsiveness.
    """

    def __init__(
            self,
            base_sizer: InstrumentPositionSizer,
            buffer_fraction: float = 0.10,
    ):
        """Initialize buffered position sizer.

        Args:
            base_sizer: Underlying position sizer
            buffer_fraction: Minimum fractional change to trigger rebalance (default 0.10)
        """
        if not 0 < buffer_fraction < 1.0:
            raise ValueError(
                f"Buffer fraction must be in (0, 1), got {buffer_fraction}"
            )

        self.base_sizer = base_sizer
        self.buffer_fraction = buffer_fraction

    def calculate_buffered_position(
            self,
            combined_forecast: pd.Series,
            instrument_volatility: pd.Series,
            price: pd.Series,
            current_position: Optional[pd.Series] = None,
    ) -> pd.Series:
        """Calculate position with buffering applied.

        Args:
            combined_forecast: Combined forecast signal
            instrument_volatility: Annualized volatility
            price: Instrument price
            current_position: Current holdings (if None, assumes starting from zero)

        Returns:
            Buffered position series (only changes when buffer threshold exceeded)
        """
        # Get optimal position from base sizer
        optimal_position = self.base_sizer.calculate_position(
            combined_forecast=combined_forecast,
            instrument_volatility=instrument_volatility,
            price=price,
        )

        if current_position is None:
            # First position: no buffering
            return optimal_position

        # Apply buffering logic
        buffered_position = self._apply_buffer(
            optimal=optimal_position,
            current=current_position,
        )

        return buffered_position

    def _apply_buffer(
            self,
            optimal: pd.Series,
            current: pd.Series,
    ) -> pd.Series:
        """Apply buffer logic: only change position if delta exceeds threshold.

        Buffer = buffer_fraction * current_position
        Change position only if |optimal - current| > buffer
        """
        # Align series
        optimal, current = optimal.align(current, join='inner')

        # Calculate buffer size (absolute value)
        buffer_size = self.buffer_fraction * current.abs()

        # Calculate delta
        delta = optimal - current

        # Only update where delta exceeds buffer
        # Start with current position
        buffered = current.copy()

        # Update where threshold exceeded
        threshold_exceeded = delta.abs() > buffer_size
        buffered[threshold_exceeded] = optimal[threshold_exceeded]

        return buffered

    def __str__(self) -> str:
        return f"BufferedPositionSizer(buffer={self.buffer_fraction:.1%}, {self.base_sizer})"

    __repr__ = __str__


def round_positions(
        positions: pd.Series,
        min_position_size: float = 1.0,
) -> pd.Series:
    """Round fractional positions to tradeable integers.

    Args:
        positions: Fractional position sizes
        min_position_size: Minimum position size (default 1.0 contract)

    Returns:
        Rounded positions

    Notes:
        - Positions with |position| < min_position_size become 0
        - Otherwise round to nearest integer
    """
    rounded = positions.round()

    # Zero out positions below minimum size
    rounded[rounded.abs() < min_position_size] = 0

    return rounded


# ============================================================================
# Usage Example
# ============================================================================

def example_usage():
    """Demonstrate position sizing pipeline."""
    import numpy as np

    # Create sample data
    dates = pd.date_range('2020-01-01', '2020-12-31', freq='D')
    n = len(dates)

    # Sample forecast (oscillating around 0, capped at ±20)
    forecast = pd.Series(
        np.clip(10 * np.sin(np.linspace(0, 4 * np.pi, n)), -20, 20),
        index=dates,
    )

    # Sample volatility (20% annualized, with some variation)
    volatility = pd.Series(
        20 + 5 * np.sin(np.linspace(0, 2 * np.pi, n)),
        index=dates,
    )

    # Sample price (trending up with noise)
    price = pd.Series(
        100 + np.linspace(0, 20, n) + 5 * np.random.randn(n).cumsum(),
        index=dates,
    )

    # Setup position sizer
    risk_target = RiskTarget(
        annual_volatility_target=0.25,  # 25% target vol
        notional_trading_capital=100_000,  # $100k account
        fx_rate=1.0,
    )

    sizer = InstrumentPositionSizer(
        risk_target=risk_target,
        instrument_weight=0.10,  # 10% of portfolio
        idm=1.5,  # Some diversification benefit
    )

    # Calculate positions
    positions_fractional = sizer.calculate_position(
        combined_forecast=forecast,
        instrument_volatility=volatility,
        price=price,
    )

    # Round to tradeable sizes
    positions_rounded = round_positions(positions_fractional)

    print(f"\nPosition Sizer: {sizer}")
    print(f"\nFractional positions (first 5):")
    print(positions_fractional.head())
    print(f"\nRounded positions (first 5):")
    print(positions_rounded.head())

    # Demonstrate buffering
    buffered_sizer = BufferedPositionSizer(sizer, buffer_fraction=0.10)

    # Simulate starting with current position
    current_position = positions_rounded.shift(1).fillna(0)

    positions_buffered = buffered_sizer.calculate_buffered_position(
        combined_forecast=forecast,
        instrument_volatility=volatility,
        price=price,
        current_position=current_position,
    )

    positions_buffered_rounded = round_positions(positions_buffered)

    print(f"\nBuffered & rounded positions (first 10):")
    print(positions_buffered_rounded.head(10))

    # Compare turnover
    unbuffered_trades = (positions_rounded.diff().abs() > 0).sum()
    buffered_trades = (positions_buffered_rounded.diff().abs() > 0).sum()

    print(f"\nTrades without buffering: {unbuffered_trades}")
    print(f"Trades with buffering: {buffered_trades}")
    print(f"Reduction: {(1 - buffered_trades / unbuffered_trades) * 100:.1f}%")


if __name__ == "__main__":
    example_usage()
