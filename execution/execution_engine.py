"""
Execution engine for managing order flow and execution.

Coordinates between strategy signals, position sizing, and broker execution.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime

from .mock_broker import MockBroker
from .order import Order, OrderType
from strategy.base_strategy import BaseStrategy
from risk_management.position_sizer import PositionSizer
from config.settings import Settings
from utils.logger import setup_logger


logger = setup_logger(__name__)


class ExecutionEngine:
    """
    Execution engine for systematic trading.

    Manages the complete execution workflow:
    1. Receive strategy signals
    2. Calculate position sizes
    3. Generate orders
    4. Execute through broker
    5. Track performance
    """

    def __init__(
        self,
        broker: MockBroker,
        position_sizer: Optional[PositionSizer] = None,
        rebalance_threshold: float = 0.05,
    ):
        """
        Initialize execution engine.

        Args:
            broker: Broker instance for order execution
            position_sizer: Position sizing instance
            rebalance_threshold: Threshold for position adjustment (e.g., 0.05 for 5%)
        """
        self.broker = broker
        self.position_sizer = position_sizer or PositionSizer()
        self.rebalance_threshold = rebalance_threshold

        self.execution_history: List[Dict] = []

        logger.info(
            f"ExecutionEngine initialized with rebalance_threshold={rebalance_threshold}"
        )

    def calculate_target_positions(
        self,
        signals: Dict[str, float],
        prices: Dict[str, float],
        volatilities: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Calculate target positions from signals.

        Args:
            signals: Dictionary of symbol -> signal strength
            prices: Dictionary of symbol -> current price
            volatilities: Dictionary of symbol -> annualized volatility

        Returns:
            Dictionary of symbol -> target position size
        """
        target_positions = {}

        for symbol, signal in signals.items():
            if symbol not in prices or symbol not in volatilities:
                logger.warning(f"Missing price or volatility data for {symbol}")
                continue

            # Calculate position size
            position = self.position_sizer.calculate_instrument_weight(
                price=prices[symbol],
                volatility=volatilities[symbol],
                forecast=signal
            )

            target_positions[symbol] = position

        return target_positions

    def generate_orders(
        self,
        target_positions: Dict[str, float],
        current_positions: Dict[str, float],
        prices: Dict[str, float]
    ) -> List[Order]:
        """
        Generate orders to reach target positions from current positions.

        Args:
            target_positions: Target positions
            current_positions: Current positions
            prices: Current prices

        Returns:
            List of orders to execute
        """
        orders = []

        # Get all symbols (union of target and current)
        all_symbols = set(target_positions.keys()) | set(current_positions.keys())

        for symbol in all_symbols:
            target = target_positions.get(symbol, 0.0)
            current = current_positions.get(symbol, 0.0)

            # Calculate required trade
            trade_quantity = target - current

            # Check if trade exceeds rebalance threshold
            if symbol in prices and prices[symbol] > 0:
                trade_value = abs(trade_quantity) * prices[symbol]
                threshold_value = abs(current) * prices[symbol] * self.rebalance_threshold

                if trade_value < threshold_value:
                    # Trade too small, skip
                    continue

            # Round to lot size (assume 1 share lots)
            trade_quantity = round(trade_quantity)

            if trade_quantity != 0:
                # Create order
                order = Order(
                    symbol=symbol,
                    quantity=trade_quantity,
                    order_type=OrderType.MARKET
                )
                orders.append(order)

        logger.info(f"Generated {len(orders)} orders")

        return orders

    def execute_signals(
        self,
        signals: Dict[str, float],
        prices: Dict[str, float],
        volatilities: Dict[str, float],
        volumes: Optional[Dict[str, float]] = None
    ) -> List[Order]:
        """
        Execute trading signals.

        Complete workflow from signals to order execution.

        Args:
            signals: Dictionary of symbol -> signal strength
            prices: Dictionary of symbol -> current price
            volatilities: Dictionary of symbol -> annualized volatility
            volumes: Optional dictionary of symbol -> daily volume

        Returns:
            List of executed orders
        """
        logger.info(f"Executing signals for {len(signals)} symbols")

        # Calculate target positions
        target_positions = self.calculate_target_positions(signals, prices, volatilities)

        # Get current positions
        current_positions = self.broker.positions.copy()

        # Generate orders
        orders = self.generate_orders(target_positions, current_positions, prices)

        # Execute orders through broker
        executed_orders = []

        for order in orders:
            # Submit order
            submitted_order = self.broker.submit_order(
                symbol=order.symbol,
                quantity=order.quantity,
                order_type=order.order_type
            )

            # Execute immediately (market order in simulation)
            if order.symbol in prices:
                volume = volumes.get(order.symbol) if volumes else None
                success = self.broker.execute_order(
                    submitted_order,
                    current_price=prices[order.symbol],
                    volume=volume
                )

                if success:
                    executed_orders.append(submitted_order)

        # Record execution
        self.execution_history.append({
            'timestamp': datetime.now(),
            'num_signals': len(signals),
            'num_orders': len(orders),
            'num_executed': len(executed_orders),
            'account_value': self.broker.get_portfolio_value(prices),
        })

        logger.info(f"Executed {len(executed_orders)} out of {len(orders)} orders")

        return executed_orders

    def run_backtest(
        self,
        strategy: BaseStrategy,
        data_dict: Dict[str, pd.DataFrame],
        start_index: int = 0,
        end_index: Optional[int] = None
    ) -> Dict:
        """
        Run backtest with realistic execution.

        Args:
            strategy: Trading strategy
            data_dict: Dictionary of symbol -> price data
            start_index: Starting index for backtest
            end_index: Ending index for backtest

        Returns:
            Dictionary with backtest results
        """
        logger.info(f"Starting backtest with ExecutionEngine")

        # Reset broker
        self.broker.reset()

        # Initialize results tracking
        equity_curve = []
        timestamps = []

        # Get common date range
        all_dates = None
        for symbol, data in data_dict.items():
            if all_dates is None:
                all_dates = data.index
            else:
                all_dates = all_dates.intersection(data.index)

        if end_index is None:
            end_index = len(all_dates)

        all_dates = all_dates[start_index:end_index]

        # Generate signals for all symbols
        signals_dict = {}
        for symbol, data in data_dict.items():
            signals = strategy.generate_signals(data)
            signals_dict[symbol] = signals

        # Simulate trading day by day
        for date in all_dates:
            # Get current data
            prices = {}
            volatilities = {}
            volumes = {}
            signals = {}

            for symbol in data_dict.keys():
                try:
                    prices[symbol] = data_dict[symbol].loc[date, 'Close']

                    # Calculate volatility
                    returns = data_dict[symbol]['Close'].pct_change()
                    vol = returns.loc[:date].rolling(window=25).std().iloc[-1] * np.sqrt(252)
                    volatilities[symbol] = vol if not pd.isna(vol) else 0.20

                    # Get volume if available
                    if 'Volume' in data_dict[symbol].columns:
                        volumes[symbol] = data_dict[symbol].loc[date, 'Volume']

                    # Get signal
                    if date in signals_dict[symbol].index:
                        signals[symbol] = signals_dict[symbol].loc[date]
                except (KeyError, IndexError):
                    continue

            # Execute signals
            if signals:
                self.execute_signals(signals, prices, volatilities, volumes)

            # Record equity
            portfolio_value = self.broker.get_portfolio_value(prices)
            equity_curve.append(portfolio_value)
            timestamps.append(date)

        # Calculate performance metrics
        equity_series = pd.Series(equity_curve, index=timestamps)
        returns = equity_series.pct_change()

        total_return = (equity_series.iloc[-1] / equity_series.iloc[0]) - 1
        years = len(equity_series) / 252
        annual_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
        annual_vol = returns.std() * np.sqrt(252)
        sharpe = annual_return / annual_vol if annual_vol > 0 else 0

        # Get trading statistics
        trade_stats = self.broker.get_trade_statistics()

        results = {
            'equity_curve': equity_series,
            'returns': returns,
            'total_return': total_return,
            'annualized_return': annual_return,
            'annualized_volatility': annual_vol,
            'sharpe_ratio': sharpe,
            'final_value': equity_series.iloc[-1],
            'final_equity': equity_series.iloc[-1],
            'start_date': str(equity_series.index[0].date()) if len(equity_series) > 0 else None,
            'end_date': str(equity_series.index[-1].date()) if len(equity_series) > 0 else None,
            'total_trades': trade_stats.get('total_trades', 0),
            'total_costs': trade_stats.get('total_costs', 0),
            'trade_statistics': trade_stats,
            'broker_state': self.broker.get_account_summary(prices),
        }

        logger.info(
            f"Backtest complete: Return={total_return:.2%}, "
            f"Sharpe={sharpe:.2f}, Trades={trade_stats.get('total_trades', 0)}"
        )

        return results

    def get_execution_summary(self) -> pd.DataFrame:
        """
        Get summary of execution history.

        Returns:
            DataFrame with execution history
        """
        if not self.execution_history:
            return pd.DataFrame()

        return pd.DataFrame(self.execution_history)
