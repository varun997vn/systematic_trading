"""
Mock broker for simulating realistic trade execution.

Implements realistic trading costs, slippage, and market impact.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime

from .order import Order, OrderType, OrderStatus
from config.settings import Settings
from utils.logger import setup_logger


logger = setup_logger(__name__)


class MockBroker:
    """
    Simulated broker for backtesting and paper trading.

    Implements:
    - Realistic transaction costs
    - Market impact and slippage
    - Order execution with fills
    - Position tracking
    - P&L calculation
    """

    def __init__(
        self,
        initial_capital: float = None,
        commission_rate: float = None,
        slippage_rate: float = None,
        min_commission: float = 1.0,
        market_impact_factor: float = 0.001,
    ):
        """
        Initialize mock broker.

        Args:
            initial_capital: Starting capital
            commission_rate: Commission as fraction of trade value
            slippage_rate: Base slippage rate
            min_commission: Minimum commission per trade
            market_impact_factor: Market impact factor based on order size
        """
        self.initial_capital = initial_capital or Settings.INITIAL_CAPITAL
        self.commission_rate = commission_rate or Settings.TRANSACTION_COST
        self.slippage_rate = slippage_rate or Settings.SLIPPAGE
        self.min_commission = min_commission
        self.market_impact_factor = market_impact_factor

        # Account state
        self.cash = self.initial_capital
        self.positions: Dict[str, float] = {}  # symbol -> quantity
        self.orders: List[Order] = []
        self.filled_orders: List[Order] = []
        self.trade_history: List[Dict] = []

        logger.info(
            f"MockBroker initialized: capital=${self.initial_capital:,.0f}, "
            f"commission={self.commission_rate:.4f}, slippage={self.slippage_rate:.4f}"
        )

    def get_position(self, symbol: str) -> float:
        """
        Get current position for symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Current position quantity (positive for long, negative for short)
        """
        return self.positions.get(symbol, 0.0)

    def get_portfolio_value(self, prices: Dict[str, float]) -> float:
        """
        Calculate total portfolio value.

        Args:
            prices: Dictionary of symbol -> current price

        Returns:
            Total portfolio value
        """
        position_value = sum(
            self.positions.get(symbol, 0) * prices.get(symbol, 0)
            for symbol in self.positions
        )
        return self.cash + position_value

    def calculate_slippage(
        self,
        symbol: str,
        quantity: float,
        price: float,
        volume: Optional[float] = None
    ) -> float:
        """
        Calculate realistic slippage based on order size and market conditions.

        Args:
            symbol: Trading symbol
            quantity: Order quantity
            price: Current price
            volume: Daily volume (optional)

        Returns:
            Slippage as fraction of price
        """
        # Base slippage
        slippage = self.slippage_rate

        # Add market impact based on order size
        if volume is not None and volume > 0:
            # Order size relative to daily volume
            volume_fraction = abs(quantity) / volume
            market_impact = volume_fraction * self.market_impact_factor
            slippage += market_impact

        # Add random component (bid-ask bounce)
        random_slippage = np.random.uniform(0, self.slippage_rate * 0.5)
        slippage += random_slippage

        return slippage

    def calculate_commission(
        self,
        quantity: float,
        price: float
    ) -> float:
        """
        Calculate commission for trade.

        Args:
            quantity: Order quantity
            price: Execution price

        Returns:
            Commission amount
        """
        trade_value = abs(quantity) * price
        commission = max(trade_value * self.commission_rate, self.min_commission)
        return commission

    def submit_order(
        self,
        symbol: str,
        quantity: float,
        order_type: OrderType = OrderType.MARKET,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
    ) -> Order:
        """
        Submit an order to the broker.

        Args:
            symbol: Trading symbol
            quantity: Order quantity (positive for buy, negative for sell)
            order_type: Type of order
            limit_price: Limit price for limit orders
            stop_price: Stop price for stop orders

        Returns:
            Created order object
        """
        order = Order(
            symbol=symbol,
            quantity=quantity,
            order_type=order_type,
            limit_price=limit_price,
            stop_price=stop_price,
            status=OrderStatus.SUBMITTED
        )

        self.orders.append(order)

        logger.info(f"Order submitted: {order}")

        return order

    def execute_order(
        self,
        order: Order,
        current_price: float,
        volume: Optional[float] = None
    ) -> bool:
        """
        Execute an order at current market conditions.

        Args:
            order: Order to execute
            current_price: Current market price
            volume: Daily volume (optional)

        Returns:
            True if order was filled
        """
        if not order.is_active:
            return False

        # Check if order should be filled based on type
        should_fill = False
        fill_price = current_price

        if order.order_type == OrderType.MARKET:
            should_fill = True
        elif order.order_type == OrderType.LIMIT:
            if order.is_buy and current_price <= order.limit_price:
                should_fill = True
                fill_price = order.limit_price
            elif order.is_sell and current_price >= order.limit_price:
                should_fill = True
                fill_price = order.limit_price
        elif order.order_type == OrderType.STOP:
            if order.is_buy and current_price >= order.stop_price:
                should_fill = True
            elif order.is_sell and current_price <= order.stop_price:
                should_fill = True

        if not should_fill:
            return False

        # Calculate slippage
        slippage_fraction = self.calculate_slippage(
            order.symbol, order.quantity, fill_price, volume
        )

        # Apply slippage (worse price for trader)
        if order.is_buy:
            fill_price *= (1 + slippage_fraction)
        else:
            fill_price *= (1 - slippage_fraction)

        # Calculate commission
        commission = self.calculate_commission(abs(order.quantity), fill_price)

        # Check if we have enough cash for buy orders
        if order.is_buy:
            required_cash = abs(order.quantity) * fill_price + commission
            if required_cash > self.cash:
                logger.warning(
                    f"Insufficient cash for order {order.order_id}. "
                    f"Required: ${required_cash:,.0f}, Available: ${self.cash:,.0f}"
                )
                order.reject()
                return False

        # Execute the fill
        fill_quantity = order.remaining_quantity
        if order.is_sell:
            fill_quantity = -fill_quantity

        order.update_fill(
            fill_quantity=fill_quantity,
            fill_price=fill_price,
            commission=commission,
            slippage=slippage_fraction * fill_price * abs(fill_quantity)
        )

        # Update positions and cash
        self.positions[order.symbol] = self.positions.get(order.symbol, 0.0) + fill_quantity

        if order.is_buy:
            self.cash -= (abs(fill_quantity) * fill_price + commission)
        else:
            self.cash += (abs(fill_quantity) * fill_price - commission)

        # Record trade
        trade = {
            'timestamp': datetime.now(),
            'symbol': order.symbol,
            'quantity': fill_quantity,
            'price': fill_price,
            'commission': commission,
            'slippage': order.slippage,
            'order_id': order.order_id,
        }
        self.trade_history.append(trade)

        # Move to filled orders
        if order.is_filled:
            self.filled_orders.append(order)
            self.orders.remove(order)

        logger.info(
            f"Order filled: {order.symbol} {fill_quantity:+.2f} shares @ ${fill_price:.2f}, "
            f"commission=${commission:.2f}, slippage=${order.slippage:.2f}"
        )

        return True

    def cancel_order(self, order: Order):
        """
        Cancel an active order.

        Args:
            order: Order to cancel
        """
        if order.is_active:
            order.cancel()
            if order in self.orders:
                self.orders.remove(order)
            logger.info(f"Order cancelled: {order.order_id}")

    def get_account_summary(self, prices: Dict[str, float]) -> Dict:
        """
        Get account summary.

        Args:
            prices: Current prices for all positions

        Returns:
            Dictionary with account information
        """
        position_value = sum(
            qty * prices.get(symbol, 0)
            for symbol, qty in self.positions.items()
        )

        total_value = self.cash + position_value

        return {
            'cash': self.cash,
            'position_value': position_value,
            'total_value': total_value,
            'positions': self.positions.copy(),
            'active_orders': len(self.orders),
            'filled_orders': len(self.filled_orders),
            'total_trades': len(self.trade_history),
        }

    def get_trade_statistics(self) -> Dict:
        """
        Calculate trading statistics.

        Returns:
            Dictionary with trading statistics
        """
        if not self.trade_history:
            return {}

        trades_df = pd.DataFrame(self.trade_history)

        total_commission = trades_df['commission'].sum()
        total_slippage = trades_df['slippage'].sum()
        total_costs = total_commission + total_slippage

        avg_commission = trades_df['commission'].mean()
        avg_slippage = trades_df['slippage'].mean()

        trade_value = (trades_df['quantity'].abs() * trades_df['price']).sum()
        cost_percentage = total_costs / trade_value if trade_value > 0 else 0

        return {
            'total_trades': len(self.trade_history),
            'total_commission': total_commission,
            'total_slippage': total_slippage,
            'total_costs': total_costs,
            'avg_commission_per_trade': avg_commission,
            'avg_slippage_per_trade': avg_slippage,
            'cost_as_percentage': cost_percentage,
        }

    def reset(self):
        """Reset broker to initial state."""
        self.cash = self.initial_capital
        self.positions = {}
        self.orders = []
        self.filled_orders = []
        self.trade_history = []
        logger.info("Broker reset to initial state")
