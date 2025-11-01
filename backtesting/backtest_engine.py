"""
Backtesting engine for systematic trading strategies.

Implements realistic simulation accounting for:
- Transaction costs
- Slippage
- Position sizing
- Capital constraints
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict

from strategy.base_strategy import BaseStrategy
from risk_management.position_sizer import PositionSizer
from config.settings import Settings
from utils.logger import setup_logger


logger = setup_logger(__name__)


class BacktestEngine:
    """
    Backtesting engine for systematic trading strategies.

    Follows Carver's emphasis on realistic cost modeling and
    proper position sizing.
    """

    def __init__(
        self,
        initial_capital: float = None,
        transaction_cost: float = None,
        slippage: float = None,
    ):
        """
        Initialize backtest engine.

        Args:
            initial_capital: Starting capital
            transaction_cost: Transaction cost as fraction (e.g., 0.001 for 0.1%)
            slippage: Slippage as fraction
        """
        self.initial_capital = initial_capital or Settings.INITIAL_CAPITAL
        self.transaction_cost = transaction_cost or Settings.TRANSACTION_COST
        self.slippage = slippage or Settings.SLIPPAGE

        logger.info(
            f"BacktestEngine initialized: capital={self.initial_capital}, "
            f"costs={self.transaction_cost:.4f}, slippage={self.slippage:.4f}"
        )

    def run(
        self,
        strategy: BaseStrategy,
        data: pd.DataFrame,
        position_sizer: Optional[PositionSizer] = None,
    ) -> Dict:
        """
        Run backtest for a strategy on historical data.

        Args:
            strategy: Trading strategy to test
            data: Historical price data
            position_sizer: Position sizing instance (creates default if None)

        Returns:
            Dictionary with backtest results
        """
        logger.info(f"Starting backtest for {strategy.name}")

        # Validate data
        if not strategy.validate_data(data):
            logger.error("Invalid data for backtesting")
            return {}

        # Initialize position sizer
        if position_sizer is None:
            position_sizer = PositionSizer(capital=self.initial_capital)

        # Generate trading signals
        signals = strategy.generate_signals(data)

        # Calculate positions
        positions = position_sizer.calculate_position_from_signal(
            prices=data['Close'],
            signal=signals,
        )

        # Calculate returns and equity curve
        results = self._calculate_performance(
            data=data,
            positions=positions,
            signals=signals,
        )

        logger.info(f"Backtest completed for {strategy.name}")

        return results

    def _calculate_performance(
        self,
        data: pd.DataFrame,
        positions: pd.Series,
        signals: pd.Series,
    ) -> Dict:
        """
        Calculate backtest performance metrics.

        Args:
            data: Price data
            positions: Position sizes over time
            signals: Trading signals

        Returns:
            Dictionary with performance metrics
        """
        prices = data['Close']

        # Calculate position changes (trades)
        position_diff = positions.diff()

        # Calculate trading costs
        # Cost = |position change| * price * (transaction cost + slippage)
        total_cost_rate = self.transaction_cost + self.slippage
        costs = position_diff.abs() * prices * total_cost_rate

        # Calculate returns from price changes
        price_returns = prices.pct_change()

        # Calculate strategy returns
        # Return = position (from previous day) * price return - costs
        strategy_returns = positions.shift(1) * price_returns * prices.shift(1)

        # Convert to percentage returns
        strategy_returns_pct = strategy_returns / self.initial_capital

        # Subtract costs (as percentage of capital)
        strategy_returns_pct = strategy_returns_pct - (costs / self.initial_capital)

        # Calculate equity curve
        equity_curve = self.initial_capital * (1 + strategy_returns_pct).cumprod()
        equity_curve.iloc[0] = self.initial_capital

        # Calculate performance metrics
        total_return = (equity_curve.iloc[-1] / self.initial_capital) - 1
        total_costs = costs.sum()

        # Count trades
        trades = (position_diff != 0).sum()

        # Calculate annualized metrics
        trading_days = len(equity_curve)
        years = trading_days / Settings.BUSINESS_DAYS_PER_YEAR

        annualized_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
        annualized_vol = strategy_returns_pct.std() * np.sqrt(Settings.BUSINESS_DAYS_PER_YEAR)

        # Sharpe ratio
        excess_returns = strategy_returns_pct - (Settings.RISK_FREE_RATE / Settings.BUSINESS_DAYS_PER_YEAR)
        sharpe_ratio = (
            excess_returns.mean() / strategy_returns_pct.std() * np.sqrt(Settings.BUSINESS_DAYS_PER_YEAR)
            if strategy_returns_pct.std() > 0 else 0
        )

        # Prepare results
        results = {
            'equity_curve': equity_curve,
            'returns': strategy_returns_pct,
            'positions': positions,
            'signals': signals,
            'total_return': total_return,
            'annualized_return': annualized_return,
            'annualized_volatility': annualized_vol,
            'sharpe_ratio': sharpe_ratio,
            'total_trades': trades,
            'total_costs': total_costs,
            'final_equity': equity_curve.iloc[-1],
            'start_date': equity_curve.index[0],
            'end_date': equity_curve.index[-1],
        }

        return results

    def run_multiple_assets(
        self,
        strategy: BaseStrategy,
        data_dict: Dict[str, pd.DataFrame],
        position_sizer: Optional[PositionSizer] = None,
    ) -> Dict:
        """
        Run backtest across multiple assets (portfolio approach).

        This is Carver's multi-asset portfolio approach.

        Args:
            strategy: Trading strategy
            data_dict: Dictionary of {ticker: DataFrame}
            position_sizer: Position sizing instance

        Returns:
            Dictionary with portfolio backtest results
        """
        logger.info(f"Starting multi-asset backtest with {len(data_dict)} assets")

        # Run individual backtests
        individual_results = {}
        for ticker, data in data_dict.items():
            logger.info(f"Backtesting {ticker}")
            result = self.run(strategy, data, position_sizer)
            individual_results[ticker] = result

        # Combine into portfolio
        portfolio_equity = pd.DataFrame({
            ticker: result['equity_curve']
            for ticker, result in individual_results.items()
            if 'equity_curve' in result
        })

        # Sum equity curves (equal weighting)
        # In production, Carver uses more sophisticated weighting
        combined_equity = portfolio_equity.sum(axis=1)

        # Calculate portfolio metrics
        portfolio_returns = combined_equity.pct_change()
        total_return = (combined_equity.iloc[-1] / (self.initial_capital * len(data_dict))) - 1

        years = len(combined_equity) / Settings.BUSINESS_DAYS_PER_YEAR
        annualized_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
        annualized_vol = portfolio_returns.std() * np.sqrt(Settings.BUSINESS_DAYS_PER_YEAR)

        sharpe = (
            annualized_return / annualized_vol
            if annualized_vol > 0 else 0
        )

        results = {
            'individual_results': individual_results,
            'portfolio_equity': combined_equity,
            'portfolio_returns': portfolio_returns,
            'total_return': total_return,
            'annualized_return': annualized_return,
            'annualized_volatility': annualized_vol,
            'sharpe_ratio': sharpe,
        }

        logger.info(f"Multi-asset backtest completed")

        return results
