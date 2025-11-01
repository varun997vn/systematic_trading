"""
Order management for trading execution.

Defines order types, status, and order objects.
"""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


class OrderType(Enum):
    """Order types supported by the execution engine."""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class OrderStatus(Enum):
    """Order status lifecycle."""
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    PARTIAL_FILL = "PARTIAL_FILL"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


@dataclass
class Order:
    """
    Represents a trading order.

    Attributes:
        symbol: Trading symbol
        quantity: Number of shares (positive for buy, negative for sell)
        order_type: Type of order
        limit_price: Limit price for limit orders
        stop_price: Stop price for stop orders
        timestamp: Order creation timestamp
        order_id: Unique order identifier
        status: Current order status
        filled_quantity: Number of shares filled
        filled_price: Average fill price
        commission: Commission paid
        slippage: Slippage experienced
    """
    symbol: str
    quantity: float
    order_type: OrderType = OrderType.MARKET
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    timestamp: datetime = None
    order_id: Optional[str] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    filled_price: Optional[float] = None
    commission: float = 0.0
    slippage: float = 0.0

    def __post_init__(self):
        """Initialize timestamp and order_id if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.order_id is None:
            self.order_id = f"{self.symbol}_{self.timestamp.strftime('%Y%m%d%H%M%S%f')}"

    @property
    def is_buy(self) -> bool:
        """Check if this is a buy order."""
        return self.quantity > 0

    @property
    def is_sell(self) -> bool:
        """Check if this is a sell order."""
        return self.quantity < 0

    @property
    def is_filled(self) -> bool:
        """Check if order is completely filled."""
        return self.status == OrderStatus.FILLED

    @property
    def is_active(self) -> bool:
        """Check if order is still active."""
        return self.status in [OrderStatus.PENDING, OrderStatus.SUBMITTED, OrderStatus.PARTIAL_FILL]

    @property
    def remaining_quantity(self) -> float:
        """Calculate remaining unfilled quantity."""
        return abs(self.quantity) - abs(self.filled_quantity)

    def update_fill(
        self,
        fill_quantity: float,
        fill_price: float,
        commission: float = 0.0,
        slippage: float = 0.0
    ):
        """
        Update order with fill information.

        Args:
            fill_quantity: Quantity filled
            fill_price: Price of fill
            commission: Commission charged
            slippage: Slippage experienced
        """
        # Update filled quantity
        self.filled_quantity += fill_quantity

        # Update average fill price
        if self.filled_price is None:
            self.filled_price = fill_price
        else:
            total_value = (self.filled_price * (self.filled_quantity - fill_quantity) +
                          fill_price * fill_quantity)
            self.filled_price = total_value / self.filled_quantity

        # Update costs
        self.commission += commission
        self.slippage += slippage

        # Update status
        if abs(self.filled_quantity) >= abs(self.quantity):
            self.status = OrderStatus.FILLED
        elif self.filled_quantity > 0:
            self.status = OrderStatus.PARTIAL_FILL
        else:
            self.status = OrderStatus.SUBMITTED

    def cancel(self):
        """Cancel this order."""
        if self.is_active:
            self.status = OrderStatus.CANCELLED

    def reject(self):
        """Mark this order as rejected."""
        self.status = OrderStatus.REJECTED

    def __repr__(self) -> str:
        """String representation of order."""
        direction = "BUY" if self.is_buy else "SELL"
        return (
            f"Order({self.order_id}, {direction} {abs(self.quantity)} {self.symbol} "
            f"@ {self.order_type.value}, Status: {self.status.value})"
        )
