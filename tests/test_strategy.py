"""
Unit tests for trading strategies.
"""

import pytest
import pandas as pd
import numpy as np
from strategy.trend_following import MovingAverageCrossover, EWMAC


class TestStrategies:
    """Test suite for trading strategies."""

    @pytest.fixture
    def sample_data(self):
        """Create sample OHLCV data for testing."""
        dates = pd.date_range('2020-01-01', periods=200, freq='D')
        np.random.seed(42)

        # Create trending price data
        trend = np.linspace(100, 150, 200)
        noise = np.random.randn(200) * 2
        close_prices = trend + noise

        data = pd.DataFrame({
            'Open': close_prices * 0.99,
            'High': close_prices * 1.01,
            'Low': close_prices * 0.98,
            'Close': close_prices,
            'Volume': np.random.randint(1000000, 5000000, 200)
        }, index=dates)

        return data

    def test_ma_crossover_initialization(self):
        """Test MA crossover strategy initialization."""
        strategy = MovingAverageCrossover(fast_period=10, slow_period=30)

        assert strategy.fast_period == 10
        assert strategy.slow_period == 30
        assert strategy.name == "MA_Crossover"

    def test_ma_crossover_signals(self, sample_data):
        """Test MA crossover signal generation."""
        strategy = MovingAverageCrossover(fast_period=16, slow_period=64)
        signals = strategy.generate_signals(sample_data)

        assert isinstance(signals, pd.Series)
        assert len(signals) == len(sample_data)
        assert signals.isin([-1.0, 0.0, 1.0]).all()

    def test_ewmac_initialization(self):
        """Test EWMAC strategy initialization."""
        strategy = EWMAC(fast_span=16, slow_span=64)

        assert strategy.fast_span == 16
        assert strategy.slow_span == 64
        assert strategy.name == "EWMAC"

    def test_ewmac_signals(self, sample_data):
        """Test EWMAC signal generation."""
        strategy = EWMAC(fast_span=16, slow_span=64)
        signals = strategy.generate_signals(sample_data)

        assert isinstance(signals, pd.Series)
        assert len(signals) == len(sample_data)
        # Carver's forecasts should be in range -20 to +20
        assert signals.max() <= 20
        assert signals.min() >= -20

    def test_strategy_with_empty_data(self):
        """Test strategy with empty data."""
        strategy = EWMAC()
        empty_data = pd.DataFrame()
        signals = strategy.generate_signals(empty_data)

        assert isinstance(signals, pd.Series)
        assert len(signals) == 0

    def test_strategy_with_missing_close(self):
        """Test strategy with missing Close column."""
        strategy = EWMAC()
        bad_data = pd.DataFrame({'Open': [100, 101, 102]})
        signals = strategy.generate_signals(bad_data)

        assert len(signals) == 0
