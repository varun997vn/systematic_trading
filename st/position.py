"""
Position Sizing Module for Systematic Trading Framework
Based on Robert Carver's "Systematic Trading"

Core responsibilities:
- Position size calculation from forecasts
- Volatility-based position sizing
- Risk targeting and scaling
- Notional exposure calculation
- Position limits and constraints
"""

from typing import Dict, List, Optional

import polars as pl
from pydantic import BaseModel, Field, field_validator

from st.config.settings import Settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


# ---- Core Position Structures ---- #


class PositionConfig(BaseModel):
    """Configuration for position sizing."""

    volatility_target: float = Field(
        default=Settings.VOLATILITY_TARGET,
        ge=0.0,
        le=1.0,
        description="Annual volatility target (e.g., 0.20 for 20%)"
    )
    use_buffering: bool = Field(
        default=True,
        description="Apply position buffering to reduce turnover"
    )
    buffer_width: float = Field(
        default=0.10,
        ge=0.0,
        le=1.0,
        description="Buffer width as fraction of position (0.10 = 10%)"
    )
    max_leverage: float = Field(
        default=Settings.MAX_LEVERAGE,
        ge=1.0,
        description="Maximum allowed leverage"
    )
    max_forecast: float = Field(
        default=20.0,
        description="Maximum forecast value"
    )

    @field_validator("volatility_target")
    @classmethod
    def validate_vol_target(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Volatility target must be positive")
        if v > 0.50:
            logger.warning(f"High volatility target: {v:.2%}")
        return v


class Position(BaseModel):
    """Container for position information."""

    ticker: str
    forecast: float = Field(..., description="Combined scaled forecast (-20 to +20)")
    volatility: float = Field(..., ge=0.0, description="Annual instrument volatility")
    price: float = Field(..., gt=0.0, description="Current instrument price")
    capital: float = Field(..., gt=0.0, description="Allocated capital for instrument")
    contract_size: float = Field(default=1.0, gt=0.0, description="Contract multiplier")
    fx_rate: float = Field(default=1.0, gt=0.0, description="FX rate to base currency")

    # Calculated fields (set after initialization)
    notional_position: Optional[float] = Field(default=None, description="Notional exposure")
    contracts: Optional[float] = Field(default=None, description="Number of contracts")
    leverage: Optional[float] = Field(default=None, description="Position leverage")
    risk_contribution: Optional[float] = Field(default=None, description="Risk in $ terms")


class PositionSet(BaseModel):
    """Container for multiple instrument positions."""

    positions: Dict[str, Position] = Field(default_factory=dict)
    total_capital: float = Field(..., gt=0.0)
    timestamp: Optional[str] = Field(default=None)

    @property
    def total_notional(self) -> float:
        """Total notional exposure across all positions."""
        return sum(
            abs(p.notional_position) for p in self.positions.values()
            if p.notional_position is not None
        )

    @property
    def portfolio_leverage(self) -> float:
        """Portfolio-level leverage."""
        if self.total_capital <= 0:
            return 0.0
        return self.total_notional / self.total_capital

    @property
    def tickers(self) -> List[str]:
        """List of tickers in position set."""
        return list(self.positions.keys())


# ---- Position Sizer ---- #


class PositionSizer:
    """
    Calculate position sizes using Carver's methodology.
    Core formula: Position = (Capital * Volatility_Target * Forecast) / (Instrument_Vol * Multiplier * Price)
    """

    def __init__(self, config: Optional[PositionConfig] = None):
        self.config = config or PositionConfig()

    def calculate_notional_position(
            self,
            forecast: float,
            capital: float,
            instrument_volatility: float,
            price: float,
            instrument_weight: float = 1.0,
            fx_rate: float = 1.0,
    ) -> float:
        """
        Calculate notional position size in base currency.

        Carver's formula:
        Position = (Capital * Vol_Target * IDM * Instrument_Weight * Forecast) / (10 * Instrument_Vol)

        Args:
            forecast: Combined scaled forecast (-20 to +20)
            capital: Total portfolio capital
            instrument_volatility: Annual instrument volatility
            price: Current instrument price
            instrument_weight: Portfolio weight for this instrument
            fx_rate: FX rate to base currency

        Returns:
            Notional position size in base currency
        """
        # Cap forecast at maximum
        forecast = max(-self.config.max_forecast, min(forecast, self.config.max_forecast))

        # Validate inputs
        if instrument_volatility <= 0:
            logger.warning(f"Invalid volatility {instrument_volatility}, returning 0 position")
            return 0.0

        # Carver's position sizing formula
        # Notional = (Capital * Vol_Target * Weight * Forecast) / (10 * Instrument_Vol)
        numerator = capital * self.config.volatility_target * instrument_weight * forecast
        denominator = 10.0 * instrument_volatility

        notional_position = numerator / denominator

        logger.debug(
            f"Position calc: forecast={forecast:.2f}, capital=${capital:,.0f}, "
            f"vol={instrument_volatility:.2%}, weight={instrument_weight:.2%} "
            f"→ notional=${notional_position:,.0f}"
        )

        return notional_position

    def calculate_contracts(
            self,
            notional_position: float,
            price: float,
            contract_size: float = 1.0,
            fx_rate: float = 1.0,
    ) -> float:
        """
        Convert notional position to number of contracts.

        Args:
            notional_position: Notional position in base currency
            price: Current instrument price
            contract_size: Contract multiplier (e.g., 100 for options)
            fx_rate: FX rate to base currency

        Returns:
            Number of contracts (can be fractional)
        """
        if price <= 0 or contract_size <= 0:
            logger.warning(f"Invalid price ({price}) or contract size ({contract_size})")
            return 0.0

        # Contracts = Notional / (Price * Contract_Size * FX_Rate)
        contracts = notional_position / (price * contract_size * fx_rate)

        return contracts

    def calculate_position(
            self,
            forecast: float,
            capital: float,
            instrument_volatility: float,
            price: float,
            instrument_weight: float = 1.0,
            contract_size: float = 1.0,
            fx_rate: float = 1.0,
            ticker: str = "",
    ) -> Position:
        """
        Calculate complete position with all details.

        Args:
            forecast: Combined scaled forecast
            capital: Allocated capital
            instrument_volatility: Annual volatility
            price: Current price
            instrument_weight: Portfolio weight
            contract_size: Contract multiplier
            fx_rate: FX rate
            ticker: Instrument identifier

        Returns:
            Position object with all calculated fields
        """
        # Calculate notional position
        notional = self.calculate_notional_position(
            forecast, capital, instrument_volatility, price, instrument_weight, fx_rate
        )

        # Calculate contracts
        contracts = self.calculate_contracts(notional, price, contract_size, fx_rate)

        # Calculate leverage
        leverage = abs(notional) / capital if capital > 0 else 0.0

        # Calculate risk contribution (notional * volatility)
        risk_contribution = abs(notional) * instrument_volatility

        # Create position object
        position = Position(
            ticker=ticker or "unknown",
            forecast=forecast,
            volatility=instrument_volatility,
            price=price,
            capital=capital,
            contract_size=contract_size,
            fx_rate=fx_rate,
            notional_position=notional,
            contracts=contracts,
            leverage=leverage,
            risk_contribution=risk_contribution,
        )

        logger.info(
            f"{ticker}: forecast={forecast:.2f}, contracts={contracts:.2f}, "
            f"notional=${notional:,.0f}, leverage={leverage:.2f}x"
        )

        return position

    def apply_leverage_limit(self, position: Position) -> Position:
        """
        Apply maximum leverage constraint.

        Args:
            position: Position to constrain

        Returns:
            Constrained position
        """
        if position.leverage is None or position.leverage <= self.config.max_leverage:
            return position

        # Scale down position to meet leverage limit
        scale_factor = self.config.max_leverage / position.leverage

        position.notional_position *= scale_factor
        position.contracts *= scale_factor
        position.leverage = self.config.max_leverage
        position.risk_contribution *= scale_factor

        logger.warning(
            f"{position.ticker}: Leverage limit applied, "
            f"scaled to {self.config.max_leverage:.2f}x"
        )

        return position


# ---- Position Buffering ---- #


class PositionBuffer:
    """
    Implement position buffering to reduce turnover.
    Only change positions when they move outside buffer zone.
    """

    def __init__(self, buffer_width: float = 0.10):
        """
        Initialize position buffer.

        Args:
            buffer_width: Buffer width as fraction (e.g., 0.10 for 10%)
        """
        self.buffer_width = buffer_width

    def should_rebalance(
            self, current_position: float, target_position: float
    ) -> bool:
        """
        Determine if position should be rebalanced.

        Args:
            current_position: Current position size
            target_position: Target position size

        Returns:
            True if rebalance needed
        """
        if current_position == 0:
            # Always establish new positions
            return True

        # Calculate buffer boundaries
        upper_bound = current_position * (1 + self.buffer_width)
        lower_bound = current_position * (1 - self.buffer_width)

        # Rebalance if target outside buffer
        needs_rebalance = target_position > upper_bound or target_position < lower_bound

        return needs_rebalance

    def apply_buffer(
            self,
            current_positions: Dict[str, float],
            target_positions: Dict[str, float],
    ) -> Dict[str, float]:
        """
        Apply buffering to position changes.

        Args:
            current_positions: Current position sizes
            target_positions: Target position sizes

        Returns:
            Buffered positions (current or target depending on buffer check)
        """
        buffered = {}

        for ticker in target_positions.keys():
            current = current_positions.get(ticker, 0.0)
            target = target_positions[ticker]

            if self.should_rebalance(current, target):
                buffered[ticker] = target
                logger.debug(f"{ticker}: Rebalancing {current:.2f} → {target:.2f}")
            else:
                buffered[ticker] = current
                logger.debug(f"{ticker}: Within buffer, keeping {current:.2f}")

        return buffered


# ---- Volatility Scaling ---- #


class VolatilityScaler:
    """
    Scale positions based on volatility targeting.
    Core component of Carver's risk management.
    """

    def __init__(self, target_volatility: float = Settings.VOLATILITY_TARGET):
        self.target_volatility = target_volatility

    def calculate_vol_scalar(self, instrument_volatility: float) -> float:
        """
        Calculate volatility scaling factor.

        Args:
            instrument_volatility: Current instrument volatility

        Returns:
            Scaling factor
        """
        if instrument_volatility <= 0:
            logger.warning("Invalid volatility for scaling")
            return 0.0

        scalar = self.target_volatility / instrument_volatility
        return scalar

    def scale_position(
            self, base_position: float, instrument_volatility: float
    ) -> float:
        """
        Scale position to target volatility.

        Args:
            base_position: Unscaled position
            instrument_volatility: Instrument volatility

        Returns:
            Volatility-scaled position
        """
        scalar = self.calculate_vol_scalar(instrument_volatility)
        scaled_position = base_position * scalar

        logger.debug(
            f"Vol scaling: base={base_position:.2f}, vol={instrument_volatility:.2%}, "
            f"scalar={scalar:.4f} → scaled={scaled_position:.2f}"
        )

        return scaled_position


# ---- Risk Calculator ---- #


class RiskCalculator:
    """Calculate risk metrics for positions and portfolio."""

    @staticmethod
    def position_risk(position: Position) -> float:
        """
        Calculate risk contribution of a position.

        Args:
            position: Position object

        Returns:
            Risk in $ terms (notional * volatility)
        """
        if position.notional_position is None:
            return 0.0

        risk = abs(position.notional_position) * position.volatility
        return risk

    @staticmethod
    def portfolio_risk(
            positions: Dict[str, Position],
            correlation_matrix: Optional[pl.DataFrame] = None,
    ) -> float:
        """
        Calculate total portfolio risk.

        Args:
            positions: Dictionary of positions
            correlation_matrix: Optional correlation matrix

        Returns:
            Portfolio risk in $ terms
        """
        if not positions:
            return 0.0

        # Simple approach: sum of individual risks (assumes independence)
        if correlation_matrix is None:
            total_risk = sum(
                RiskCalculator.position_risk(p) for p in positions.values()
            )
            return total_risk

        # Correlation-adjusted approach
        # Risk = sqrt(sum_i sum_j w_i * w_j * vol_i * vol_j * corr_ij)
        tickers = list(positions.keys())
        risks = [RiskCalculator.position_risk(positions[t]) for t in tickers]

        # Get correlation matrix as numpy
        import numpy as np
        corr = correlation_matrix.to_numpy()

        # Portfolio variance
        risk_array = np.array(risks)
        portfolio_var = risk_array.T @ corr @ risk_array
        portfolio_risk = np.sqrt(portfolio_var)

        return portfolio_risk

    @staticmethod
    def max_position_risk(
            capital: float, volatility_target: float, max_forecast: float = 20.0
    ) -> float:
        """
        Calculate maximum possible risk from a single position.

        Args:
            capital: Portfolio capital
            volatility_target: Target volatility
            max_forecast: Maximum forecast value

        Returns:
            Maximum position risk
        """
        # Max risk occurs at max forecast
        max_risk = capital * volatility_target * (max_forecast / 10.0)
        return max_risk


# ---- Position Manager (Main Interface) ---- #


class PositionManager:
    """
    Main interface for position sizing and management.
    Coordinates sizing, buffering, and risk calculations.
    """

    def __init__(self, config: Optional[PositionConfig] = None):
        self.config = config or PositionConfig()
        self.sizer = PositionSizer(self.config)
        self.buffer = PositionBuffer(self.config.buffer_width) if self.config.use_buffering else None
        self.scaler = VolatilityScaler(self.config.volatility_target)
        self.risk_calculator = RiskCalculator()

    def calculate_position(
            self,
            ticker: str,
            forecast: float,
            capital: float,
            instrument_volatility: float,
            price: float,
            instrument_weight: float = 1.0,
            contract_size: float = 1.0,
            fx_rate: float = 1.0,
    ) -> Position:
        """
        Calculate position for a single instrument.

        Args:
            ticker: Instrument ticker
            forecast: Combined scaled forecast
            capital: Allocated capital
            instrument_volatility: Annual volatility
            price: Current price
            instrument_weight: Portfolio weight
            contract_size: Contract multiplier
            fx_rate: FX rate

        Returns:
            Position object
        """
        position = self.sizer.calculate_position(
            forecast=forecast,
            capital=capital,
            instrument_volatility=instrument_volatility,
            price=price,
            instrument_weight=instrument_weight,
            contract_size=contract_size,
            fx_rate=fx_rate,
            ticker=ticker,
        )

        # Apply leverage limit
        position = self.sizer.apply_leverage_limit(position)

        return position

    def calculate_portfolio_positions(
            self,
            forecasts: Dict[str, float],
            capital_allocation: Dict[str, float],
            volatilities: Dict[str, float],
            prices: Dict[str, float],
            contract_sizes: Optional[Dict[str, float]] = None,
            fx_rates: Optional[Dict[str, float]] = None,
    ) -> PositionSet:
        """
        Calculate positions for entire portfolio.

        Args:
            forecasts: Dictionary of instrument forecasts
            capital_allocation: Capital allocated per instrument
            volatilities: Instrument volatilities
            prices: Current prices
            contract_sizes: Optional contract sizes
            fx_rates: Optional FX rates

        Returns:
            PositionSet with all positions
        """
        positions = {}
        total_capital = sum(capital_allocation.values())

        for ticker in forecasts.keys():
            if ticker not in capital_allocation:
                logger.warning(f"No capital allocated for {ticker}, skipping")
                continue

            position = self.calculate_position(
                ticker=ticker,
                forecast=forecasts[ticker],
                capital=capital_allocation[ticker],
                instrument_volatility=volatilities.get(ticker, 0.0),
                price=prices.get(ticker, 0.0),
                contract_size=contract_sizes.get(ticker, 1.0) if contract_sizes else 1.0,
                fx_rate=fx_rates.get(ticker, 1.0) if fx_rates else 1.0,
            )

            positions[ticker] = position

        return PositionSet(positions=positions, total_capital=total_capital)

    def apply_buffering(
            self,
            current_positions: Dict[str, float],
            target_position_set: PositionSet,
    ) -> PositionSet:
        """
        Apply position buffering to reduce turnover.

        Args:
            current_positions: Current position sizes (contracts)
            target_position_set: Target positions

        Returns:
            Buffered PositionSet
        """
        if self.buffer is None:
            return target_position_set

        target_contracts = {
            t: p.contracts for t, p in target_position_set.positions.items()
            if p.contracts is not None
        }

        buffered_contracts = self.buffer.apply_buffer(
            current_positions, target_contracts
        )

        # Update position set with buffered values
        for ticker, contracts in buffered_contracts.items():
            if ticker in target_position_set.positions:
                position = target_position_set.positions[ticker]
                # Recalculate notional and leverage with buffered contracts
                position.contracts = contracts
                position.notional_position = (
                        contracts * position.price * position.contract_size * position.fx_rate
                )
                position.leverage = (
                    abs(position.notional_position) / position.capital
                    if position.capital > 0 else 0.0
                )

        return target_position_set

    def calculate_portfolio_risk(
            self,
            position_set: PositionSet,
            correlation_matrix: Optional[pl.DataFrame] = None,
    ) -> Dict[str, float]:
        """
        Calculate risk metrics for portfolio.

        Args:
            position_set: Set of positions
            correlation_matrix: Optional correlation matrix

        Returns:
            Dictionary of risk metrics
        """
        total_risk = self.risk_calculator.portfolio_risk(
            position_set.positions, correlation_matrix
        )

        portfolio_vol = total_risk / position_set.total_capital if position_set.total_capital > 0 else 0.0

        return {
            "total_risk": total_risk,
            "portfolio_volatility": portfolio_vol,
            "portfolio_leverage": position_set.portfolio_leverage,
            "total_notional": position_set.total_notional,
            "num_positions": len(position_set.positions),
        }


# ---- Utility Functions ---- #


def calculate_required_capital(
        forecast: float,
        target_volatility: float,
        instrument_volatility: float,
        price: float,
        contracts: float,
        contract_size: float = 1.0,
) -> float:
    """
    Calculate capital required for a given position.

    Args:
        forecast: Forecast value
        target_volatility: Target portfolio volatility
        instrument_volatility: Instrument volatility
        price: Current price
        contracts: Number of contracts
        contract_size: Contract multiplier

    Returns:
        Required capital
    """
    # Reverse Carver's formula
    # Capital = (10 * Instrument_Vol * Notional) / (Vol_Target * Forecast)
    notional = contracts * price * contract_size

    if forecast == 0 or target_volatility == 0:
        return 0.0

    required_capital = (10.0 * instrument_volatility * notional) / (
            target_volatility * abs(forecast)
    )

    return required_capital


def round_contracts(
        contracts: float, lot_size: float = 1.0, method: str = "round"
) -> float:
    """
    Round contracts to tradeable lot sizes.

    Args:
        contracts: Fractional contracts
        lot_size: Minimum tradeable lot
        method: 'round', 'floor', or 'ceil'

    Returns:
        Rounded contracts
    """
    import math

    if method == "floor":
        return math.floor(contracts / lot_size) * lot_size
    elif method == "ceil":
        return math.ceil(contracts / lot_size) * lot_size
    else:  # round
        return round(contracts / lot_size) * lot_size


def validate_position(position: Position, max_leverage: float = 5.0) -> bool:
    """
    Validate position is within acceptable bounds.

    Args:
        position: Position to validate
        max_leverage: Maximum leverage

    Returns:
        True if valid
    """
    if position.leverage is None:
        logger.warning(f"{position.ticker}: Leverage not calculated")
        return False

    if position.leverage > max_leverage:
        logger.warning(
            f"{position.ticker}: Leverage {position.leverage:.2f}x exceeds max {max_leverage:.2f}x"
        )
        return False

    if position.notional_position is None or position.notional_position == 0:
        logger.warning(f"{position.ticker}: Zero or invalid notional position")
        return False

    return True
