from datetime import datetime
from typing import Dict, Optional

import pandas as pd
from pydantic import BaseModel, Field

from utils.logger import setup_logger
from .ticker_collection import TickerCollection

logger = setup_logger(__name__)


# ==========================================
# Portfolio Components
# ==========================================

class PortfolioPosition(BaseModel):
    """Represents a single position in the portfolio."""
    ticker: str
    quantity: float = Field(gt=0, description="Number of shares")
    avg_entry_price: float = Field(gt=0, description="Average entry price")
    current_price: Optional[float] = None
    last_updated: Optional[datetime] = None

    @property
    def market_value(self) -> float:
        """Current market value of the position."""
        if self.current_price is None:
            return 0.0
        return self.quantity * self.current_price

    @property
    def cost_basis(self) -> float:
        """Total cost basis of the position."""
        return self.quantity * self.avg_entry_price

    @property
    def unrealized_pnl(self) -> float:
        """Unrealized profit/loss."""
        if self.current_price is None:
            return 0.0
        return self.market_value - self.cost_basis

    @property
    def unrealized_pnl_pct(self) -> float:
        """Unrealized profit/loss as percentage."""
        if self.cost_basis == 0:
            return 0.0
        return (self.unrealized_pnl / self.cost_basis) * 100

    def update_price(self, price: float) -> None:
        """Update current price."""
        self.current_price = price
        self.last_updated = datetime.now()

    def add_shares(self, quantity: float, price: float) -> None:
        """Add shares and update average entry price."""
        total_cost = self.cost_basis + (quantity * price)
        self.quantity += quantity
        self.avg_entry_price = total_cost / self.quantity
        logger.info(f"Added {quantity} shares of {self.ticker} at ${price:.2f}")

    def remove_shares(self, quantity: float) -> None:
        """Remove shares (for partial position close)."""
        if quantity > self.quantity:
            raise ValueError(f"Cannot remove {quantity} shares, only {self.quantity} available")
        self.quantity -= quantity
        logger.info(f"Removed {quantity} shares of {self.ticker}")


class Portfolio(TickerCollection):
    """
    Portfolio management class handling positions, cash, and P&L tracking.
    """
    positions: Dict[str, PortfolioPosition] = Field(default_factory=dict)
    cash: float = Field(default=100000.0, ge=0, description="Available cash")
    initial_cash: float = Field(default=100000.0, ge=0, description="Initial capital")

    def __init__(self, **data):
        """Initialize portfolio."""
        super().__init__(**data)
        if 'initial_cash' not in data and 'cash' in data:
            self.initial_cash = data['cash']
        # Sync tickers list with positions
        if self.positions:
            self.tickers = list(self.positions.keys())

    def add_position(
            self,
            ticker: str,
            quantity: float,
            price: float,
            update_cash: bool = True
    ) -> None:
        """
        Add a new position or increase existing position.

        Args:
            ticker: Stock ticker
            quantity: Number of shares
            price: Price per share
            update_cash: Whether to deduct cost from cash
        """
        ticker = ticker.upper()
        cost = quantity * price

        if update_cash:
            if cost > self.cash:
                raise ValueError(f"Insufficient cash: need ${cost:.2f}, have ${self.cash:.2f}")
            self.cash -= cost

        if ticker in self.positions:
            self.positions[ticker].add_shares(quantity, price)
        else:
            self.positions[ticker] = PortfolioPosition(
                ticker=ticker,
                quantity=quantity,
                avg_entry_price=price,
                current_price=price,
                last_updated=datetime.now()
            )
            self.add_ticker(ticker)

        logger.info(f"Added position: {quantity} shares of {ticker} at ${price:.2f}")

    def remove_position(
            self,
            ticker: str,
            quantity: Optional[float] = None,
            price: Optional[float] = None,
            update_cash: bool = True
    ) -> Optional[float]:
        """
        Remove a position (full or partial).

        Args:
            ticker: Stock ticker
            quantity: Number of shares to sell (None = sell all)
            price: Sale price (if None, uses current_price)
            update_cash: Whether to add proceeds to cash

        Returns:
            Realized P&L from the sale
        """
        ticker = ticker.upper()

        if ticker not in self.positions:
            logger.warning(f"Position {ticker} not found")
            return None

        position = self.positions[ticker]
        sell_quantity = quantity if quantity is not None else position.quantity
        sell_price = price if price is not None else position.current_price

        if sell_price is None:
            raise ValueError(f"No price available for {ticker}")

        if sell_quantity > position.quantity:
            raise ValueError(
                f"Cannot sell {sell_quantity} shares of {ticker}, only {position.quantity} available"
            )

        # Calculate P&L
        proceeds = sell_quantity * sell_price
        cost = sell_quantity * position.avg_entry_price
        realized_pnl = proceeds - cost

        if update_cash:
            self.cash += proceeds

        # Remove shares or entire position
        if sell_quantity >= position.quantity:
            del self.positions[ticker]
            self.remove_ticker(ticker)
            logger.info(f"Closed position in {ticker}, realized P&L: ${realized_pnl:.2f}")
        else:
            position.remove_shares(sell_quantity)
            logger.info(
                f"Reduced position in {ticker} by {sell_quantity} shares, "
                f"realized P&L: ${realized_pnl:.2f}"
            )

        return realized_pnl

    def update_prices(self, prices: Dict[str, float]) -> None:
        """
        Update current prices for all positions.

        Args:
            prices: Dict mapping ticker to current price
        """
        for ticker, price in prices.items():
            if ticker in self.positions:
                self.positions[ticker].update_price(price)

        logger.info(f"Updated prices for {len(prices)} positions")

    def update_price(self, ticker: str, price: float) -> None:
        """Update price for a single position."""
        ticker = ticker.upper()
        if ticker in self.positions:
            self.positions[ticker].update_price(price)

    def get_position(self, ticker: str) -> Optional[PortfolioPosition]:
        """Get a specific position."""
        return self.positions.get(ticker.upper())

    def get_all_positions(self) -> Dict[str, PortfolioPosition]:
        """Get all positions."""
        return self.positions.copy()

    @property
    def positions_value(self) -> float:
        """Total market value of all positions."""
        return sum(pos.market_value for pos in self.positions.values())

    @property
    def total_value(self) -> float:
        """Total portfolio value (positions + cash)."""
        return self.positions_value + self.cash

    @property
    def total_unrealized_pnl(self) -> float:
        """Total unrealized P&L across all positions."""
        return sum(pos.unrealized_pnl for pos in self.positions.values())

    @property
    def total_return(self) -> float:
        """Total return as percentage of initial capital."""
        if self.initial_cash == 0:
            return 0.0
        return ((self.total_value - self.initial_cash) / self.initial_cash) * 100

    @property
    def cash_weight(self) -> float:
        """Cash as percentage of total portfolio value."""
        if self.total_value == 0:
            return 0.0
        return (self.cash / self.total_value) * 100

    def get_position_weights(self) -> Dict[str, float]:
        """Get weight of each position as percentage of total value."""
        if self.total_value == 0:
            return {ticker: 0.0 for ticker in self.positions.keys()}

        return {
            ticker: (pos.market_value / self.total_value * 100)
            for ticker, pos in self.positions.items()
        }

    def get_summary(self) -> Dict:
        """Get comprehensive portfolio summary."""
        weights = self.get_position_weights()

        summary = {
            "total_value": self.total_value,
            "cash": self.cash,
            "positions_value": self.positions_value,
            "num_positions": len(self.positions),
            "cash_weight": self.cash_weight,
            "total_unrealized_pnl": self.total_unrealized_pnl,
            "total_return": self.total_return,
            "positions": {}
        }

        for ticker, pos in self.positions.items():
            summary["positions"][ticker] = {
                "quantity": pos.quantity,
                "avg_entry": pos.avg_entry_price,
                "current_price": pos.current_price,
                "market_value": pos.market_value,
                "cost_basis": pos.cost_basis,
                "unrealized_pnl": pos.unrealized_pnl,
                "unrealized_pnl_pct": pos.unrealized_pnl_pct,
                "weight": weights[ticker],
                "last_updated": pos.last_updated
            }

        return summary

    def to_dataframe(self) -> pd.DataFrame:
        """Convert portfolio to a DataFrame."""
        if not self.positions:
            return pd.DataFrame()

        data = []
        weights = self.get_position_weights()

        for ticker, pos in self.positions.items():
            data.append({
                "ticker": ticker,
                "quantity": pos.quantity,
                "avg_entry_price": pos.avg_entry_price,
                "current_price": pos.current_price,
                "market_value": pos.market_value,
                "cost_basis": pos.cost_basis,
                "unrealized_pnl": pos.unrealized_pnl,
                "unrealized_pnl_pct": pos.unrealized_pnl_pct,
                "weight": weights[ticker],
                "last_updated": pos.last_updated
            })

        return pd.DataFrame(data)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"Portfolio(positions={len(self.positions)}, "
            f"value=${self.total_value:,.2f}, cash=${self.cash:,.2f})"
        )
