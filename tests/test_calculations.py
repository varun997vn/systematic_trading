"""
Unit tests for utility calculations.
"""

import pytest
import pandas as pd
import numpy as np
from utils.calculations import (
    calculate_returns,
    calculate_volatility,
    calculate_sharpe_ratio,
    calculate_max_drawdown,
)


class TestCalculations:
    """Test suite for financial calculations."""

    @pytest.fixture
    def sample_prices(self):
        """Create sample price data for testing."""
        dates = pd.date_range('2020-01-01', periods=100, freq='D')
        prices = pd.Series(
            100 * (1 + np.random.randn(100).cumsum() * 0.01),
            index=dates
        )
        return prices

    def test_calculate_returns_log(self, sample_prices):
        """Test log returns calculation."""
        returns = calculate_returns(sample_prices, method='log')

        assert isinstance(returns, pd.Series)
        assert len(returns) == len(sample_prices)
        assert pd.isna(returns.iloc[0])  # First return should be NaN
        assert not returns.iloc[1:].isna().all()  # Rest should have values

    def test_calculate_returns_simple(self, sample_prices):
        """Test simple returns calculation."""
        returns = calculate_returns(sample_prices, method='simple')

        assert isinstance(returns, pd.Series)
        assert len(returns) == len(sample_prices)

    def test_calculate_volatility(self, sample_prices):
        """Test volatility calculation."""
        returns = calculate_returns(sample_prices)
        vol = calculate_volatility(returns, window=25, annualize=True)

        assert isinstance(vol, pd.Series)
        assert len(vol) == len(returns)
        assert vol.iloc[25:].min() >= 0  # Volatility should be non-negative

    def test_calculate_sharpe_ratio(self, sample_prices):
        """Test Sharpe ratio calculation."""
        returns = calculate_returns(sample_prices)
        sharpe = calculate_sharpe_ratio(returns.dropna(), risk_free_rate=0.02)

        assert isinstance(sharpe, float)
        assert not np.isnan(sharpe)

    def test_calculate_max_drawdown(self, sample_prices):
        """Test maximum drawdown calculation."""
        # Create equity curve
        equity = sample_prices * 1000  # Scale up to simulate equity

        dd_stats = calculate_max_drawdown(equity)

        assert 'max_drawdown' in dd_stats
        assert 'peak_date' in dd_stats
        assert 'trough_date' in dd_stats
        assert dd_stats['max_drawdown'] <= 0  # Drawdown should be negative or zero

    def test_invalid_returns_method(self, sample_prices):
        """Test that invalid method raises error."""
        with pytest.raises(ValueError):
            calculate_returns(sample_prices, method='invalid')
