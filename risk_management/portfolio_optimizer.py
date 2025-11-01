"""
Portfolio optimization for systematic trading.

Implements various portfolio construction techniques including:
- Equal weighting
- Risk parity
- Minimum variance
- Maximum Sharpe ratio
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from scipy.optimize import minimize

from config.settings import Settings
from utils.logger import setup_logger


logger = setup_logger(__name__)


class PortfolioOptimizer:
    """
    Portfolio optimization using modern portfolio theory.

    Supports multiple optimization methods following Carver's principles
    of diversification and risk management.
    """

    def __init__(
        self,
        risk_free_rate: float = None
    ):
        """
        Initialize portfolio optimizer.

        Args:
            risk_free_rate: Risk-free rate for Sharpe ratio calculation
        """
        self.risk_free_rate = risk_free_rate or Settings.RISK_FREE_RATE

        logger.info(f"PortfolioOptimizer initialized: rf_rate={self.risk_free_rate}")

    def equal_weight(self, n_assets: int) -> np.ndarray:
        """
        Calculate equal weight allocation.

        Args:
            n_assets: Number of assets

        Returns:
            Array of weights (equal weights)
        """
        weights = np.ones(n_assets) / n_assets
        logger.debug(f"Equal weight allocation: {weights}")
        return weights

    def risk_parity(
        self,
        returns: pd.DataFrame,
        target_risk: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Calculate risk parity allocation.

        Each asset contributes equally to portfolio risk.
        This is Carver's preferred approach for diversification.

        Args:
            returns: DataFrame of asset returns
            target_risk: Optional target risk contribution for each asset

        Returns:
            Array of optimal weights
        """
        # Calculate covariance matrix
        cov_matrix = returns.cov().values
        n_assets = len(returns.columns)

        # Target equal risk contribution if not specified
        if target_risk is None:
            target_risk = np.ones(n_assets) / n_assets

        # Objective function: minimize difference from target risk contributions
        def risk_parity_objective(weights):
            portfolio_var = np.dot(weights, np.dot(cov_matrix, weights))
            portfolio_std = np.sqrt(portfolio_var)

            # Marginal contribution to risk
            marginal_contrib = np.dot(cov_matrix, weights)
            risk_contrib = weights * marginal_contrib / portfolio_std

            # Normalize risk contributions
            risk_contrib_pct = risk_contrib / np.sum(risk_contrib)

            # Minimize squared difference from target
            return np.sum((risk_contrib_pct - target_risk) ** 2)

        # Constraints: weights sum to 1, all weights >= 0
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}
        ]
        bounds = tuple((0, 1) for _ in range(n_assets))

        # Initial guess: equal weights
        x0 = np.ones(n_assets) / n_assets

        # Optimize
        result = minimize(
            risk_parity_objective,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )

        if result.success:
            logger.debug(f"Risk parity weights: {result.x}")
            return result.x
        else:
            logger.warning("Risk parity optimization failed, using equal weights")
            return self.equal_weight(n_assets)

    def minimum_variance(
        self,
        returns: pd.DataFrame
    ) -> np.ndarray:
        """
        Calculate minimum variance portfolio allocation.

        Minimizes portfolio volatility without considering returns.

        Args:
            returns: DataFrame of asset returns

        Returns:
            Array of optimal weights
        """
        cov_matrix = returns.cov().values
        n_assets = len(returns.columns)

        # Objective: minimize portfolio variance
        def portfolio_variance(weights):
            return np.dot(weights, np.dot(cov_matrix, weights))

        # Constraints
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}
        ]
        bounds = tuple((0, 1) for _ in range(n_assets))

        # Initial guess
        x0 = np.ones(n_assets) / n_assets

        # Optimize
        result = minimize(
            portfolio_variance,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )

        if result.success:
            logger.debug(f"Minimum variance weights: {result.x}")
            return result.x
        else:
            logger.warning("Min variance optimization failed, using equal weights")
            return self.equal_weight(n_assets)

    def maximum_sharpe(
        self,
        returns: pd.DataFrame
    ) -> np.ndarray:
        """
        Calculate maximum Sharpe ratio portfolio allocation.

        Maximizes risk-adjusted returns.

        Args:
            returns: DataFrame of asset returns

        Returns:
            Array of optimal weights
        """
        mean_returns = returns.mean().values
        cov_matrix = returns.cov().values
        n_assets = len(returns.columns)

        # Objective: maximize Sharpe ratio (minimize negative Sharpe)
        def negative_sharpe(weights):
            portfolio_return = np.dot(weights, mean_returns)
            portfolio_std = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))

            if portfolio_std == 0:
                return np.inf

            sharpe = (portfolio_return - self.risk_free_rate / 252) / portfolio_std
            return -sharpe  # Negative because we minimize

        # Constraints
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}
        ]
        bounds = tuple((0, 1) for _ in range(n_assets))

        # Initial guess
        x0 = np.ones(n_assets) / n_assets

        # Optimize
        result = minimize(
            negative_sharpe,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )

        if result.success:
            logger.debug(f"Maximum Sharpe weights: {result.x}")
            return result.x
        else:
            logger.warning("Max Sharpe optimization failed, using equal weights")
            return self.equal_weight(n_assets)

    def inverse_volatility(
        self,
        returns: pd.DataFrame
    ) -> np.ndarray:
        """
        Calculate inverse volatility weights.

        Weight inversely proportional to asset volatility.
        This is a simpler alternative to risk parity.

        Args:
            returns: DataFrame of asset returns

        Returns:
            Array of weights
        """
        volatilities = returns.std().values

        # Inverse volatility
        inv_vol = 1 / volatilities

        # Normalize to sum to 1
        weights = inv_vol / np.sum(inv_vol)

        logger.debug(f"Inverse volatility weights: {weights}")

        return weights

    def optimize_portfolio(
        self,
        returns: pd.DataFrame,
        method: str = 'risk_parity'
    ) -> Dict:
        """
        Optimize portfolio using specified method.

        Args:
            returns: DataFrame of asset returns
            method: Optimization method ('equal', 'risk_parity', 'min_variance',
                   'max_sharpe', 'inverse_vol')

        Returns:
            Dictionary with weights and portfolio statistics
        """
        logger.info(f"Optimizing portfolio using {method} method")

        # Get weights based on method
        if method == 'equal':
            weights = self.equal_weight(len(returns.columns))
        elif method == 'risk_parity':
            weights = self.risk_parity(returns)
        elif method == 'min_variance':
            weights = self.minimum_variance(returns)
        elif method == 'max_sharpe':
            weights = self.maximum_sharpe(returns)
        elif method == 'inverse_vol':
            weights = self.inverse_volatility(returns)
        else:
            logger.warning(f"Unknown method {method}, using equal weights")
            weights = self.equal_weight(len(returns.columns))

        # Calculate portfolio statistics
        portfolio_return = np.dot(weights, returns.mean().values)
        portfolio_std = np.sqrt(
            np.dot(weights, np.dot(returns.cov().values, weights))
        )

        # Annualize
        annual_return = portfolio_return * 252
        annual_std = portfolio_std * np.sqrt(252)
        sharpe = (annual_return - self.risk_free_rate) / annual_std if annual_std > 0 else 0

        results = {
            'weights': dict(zip(returns.columns, weights)),
            'expected_return': annual_return,
            'volatility': annual_std,
            'sharpe_ratio': sharpe,
        }

        logger.info(f"Portfolio optimized: Sharpe={sharpe:.2f}, Vol={annual_std:.2%}")

        return results

    def rebalance_threshold(
        self,
        current_weights: Dict[str, float],
        target_weights: Dict[str, float],
        threshold: float = 0.05
    ) -> bool:
        """
        Determine if portfolio needs rebalancing.

        Args:
            current_weights: Current portfolio weights
            target_weights: Target portfolio weights
            threshold: Rebalancing threshold (e.g., 0.05 for 5%)

        Returns:
            True if rebalancing is needed
        """
        # Calculate maximum deviation
        max_deviation = 0.0

        for asset in target_weights:
            if asset in current_weights:
                deviation = abs(current_weights[asset] - target_weights[asset])
                max_deviation = max(max_deviation, deviation)

        needs_rebalance = max_deviation > threshold

        logger.debug(
            f"Rebalance check: max_deviation={max_deviation:.2%}, "
            f"threshold={threshold:.2%}, needs_rebalance={needs_rebalance}"
        )

        return needs_rebalance
