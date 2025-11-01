"""
Position sizing based on Robert Carver's volatility targeting approach.

Carver's key principles:
1. Target a consistent level of volatility across instruments
2. Scale positions based on instrument volatility
3. Account for forecast strength (signal confidence)
"""

import numpy as np
import pandas as pd
from typing import Union, Optional

from config.settings import Settings
from utils.calculations import calculate_volatility
from utils.logger import setup_logger


logger = setup_logger(__name__)


class PositionSizer:
    """
    Position sizing using Carver's volatility-targeting approach.

    The core idea: positions should be inversely proportional to volatility
    to achieve consistent risk exposure across all instruments.
    """

    def __init__(
        self,
        capital: float = None,
        volatility_target: float = None,
        max_position_size: float = None,
    ):
        """
        Initialize position sizer.

        Args:
            capital: Total trading capital
            volatility_target: Target annual volatility (e.g., 0.20 for 20%)
            max_position_size: Maximum position size as fraction of capital
        """
        self.capital = capital or Settings.INITIAL_CAPITAL
        self.volatility_target = volatility_target or Settings.VOLATILITY_TARGET
        self.max_position_size = max_position_size or Settings.MAX_POSITION_SIZE

        logger.info(
            f"PositionSizer initialized: capital={self.capital}, "
            f"vol_target={self.volatility_target}, max_size={self.max_position_size}"
        )

    def calculate_instrument_weight(
        self,
        price: float,
        volatility: float,
        forecast: float = 10.0,
    ) -> float:
        """
        Calculate position size using Carver's volatility targeting.

        Carver's formula:
        position = (target_vol / instrument_vol) * (forecast / 10) * capital / price

        Args:
            price: Current price of instrument
            volatility: Annualized volatility (as decimal, e.g., 0.25 for 25%)
            forecast: Trading signal forecast (Carver uses -20 to +20, scaled to 10)

        Returns:
            Number of shares/contracts to hold
        """
        if volatility <= 0 or price <= 0:
            logger.warning("Invalid volatility or price, returning zero position")
            return 0.0

        # Carver's volatility scalar
        # This adjusts position size to achieve target volatility
        vol_scalar = self.volatility_target / volatility

        # Scale by forecast strength (normalized to 10)
        forecast_scalar = forecast / 10.0

        # Capital allocated to this position
        notional_position = vol_scalar * forecast_scalar * self.capital

        # Convert to number of shares
        shares = notional_position / price

        # Apply position size limits
        max_shares = (self.capital * self.max_position_size) / price
        shares = np.clip(shares, -max_shares, max_shares)

        return shares

    def calculate_position_from_signal(
        self,
        prices: pd.Series,
        signal: pd.Series,
        volatility_window: int = 25,
    ) -> pd.Series:
        """
        Calculate position sizes for a backtest based on trading signals.

        Args:
            prices: Price series
            signal: Trading signal series (typically -1 to 1 or -20 to 20)
            volatility_window: Window for volatility calculation

        Returns:
            Series of position sizes (number of shares)
        """
        # Calculate returns and volatility
        returns = prices.pct_change()
        volatility = calculate_volatility(
            returns,
            window=volatility_window,
            annualize=True
        )

        # Initialize position series
        positions = pd.Series(index=prices.index, dtype=float)

        # Calculate positions for each time point
        for i in range(len(prices)):
            if pd.isna(volatility.iloc[i]) or pd.isna(signal.iloc[i]):
                positions.iloc[i] = 0.0
            else:
                positions.iloc[i] = self.calculate_instrument_weight(
                    price=prices.iloc[i],
                    volatility=volatility.iloc[i],
                    forecast=signal.iloc[i] * 10,  # Scale signal to Carver's forecast range
                )

        return positions

    def calculate_fixed_fractional(
        self,
        price: float,
        fraction: float = 0.02,
    ) -> float:
        """
        Simple fixed fractional position sizing (alternative method).

        This is simpler than Carver's approach but less sophisticated.
        Good for beginners or as a comparison baseline.

        Args:
            price: Current price
            fraction: Fraction of capital to risk (e.g., 0.02 for 2%)

        Returns:
            Number of shares
        """
        if price <= 0:
            return 0.0

        position_value = self.capital * fraction
        shares = position_value / price

        return shares

    def calculate_portfolio_leverage(
        self,
        positions: dict,
        prices: dict,
    ) -> float:
        """
        Calculate current portfolio leverage.

        Carver monitors leverage to ensure it stays within reasonable bounds.

        Args:
            positions: Dictionary of {ticker: position_size}
            prices: Dictionary of {ticker: current_price}

        Returns:
            Portfolio leverage (total notional / capital)
        """
        total_notional = 0.0

        for ticker, position in positions.items():
            if ticker in prices:
                notional = abs(position * prices[ticker])
                total_notional += notional

        leverage = total_notional / self.capital if self.capital > 0 else 0.0

        return leverage

    def adjust_for_costs(
        self,
        shares: float,
        current_position: float,
        price: float,
        cost_per_trade: float = None,
    ) -> float:
        """
        Adjust position size accounting for transaction costs.

        Carver emphasizes being cost-aware and avoiding excessive trading.

        Args:
            shares: Target position size
            current_position: Current position size
            price: Current price
            cost_per_trade: Transaction cost as fraction

        Returns:
            Adjusted position size
        """
        cost = cost_per_trade or Settings.TRANSACTION_COST

        # Calculate trade size
        trade_size = abs(shares - current_position)
        trade_value = trade_size * price

        # Estimate trading cost
        trading_cost = trade_value * cost

        # If trading cost is too high relative to position, don't trade
        # This is a simple threshold; Carver uses more sophisticated rules
        if trade_value > 0:
            cost_ratio = trading_cost / trade_value
            if cost_ratio > 0.05:  # If costs exceed 5%, skip trade
                logger.debug(f"Skipping trade due to high costs: {cost_ratio:.2%}")
                return current_position

        return shares
