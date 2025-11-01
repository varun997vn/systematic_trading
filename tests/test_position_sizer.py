"""
Unit tests for position sizing.
"""

import pytest
import pandas as pd
import numpy as np
from risk_management.position_sizer import PositionSizer


class TestPositionSizer:
    """Test suite for position sizing."""

    def test_initialization(self):
        """Test position sizer initialization."""
        sizer = PositionSizer(
            capital=100000,
            volatility_target=0.20,
            max_position_size=0.10
        )

        assert sizer.capital == 100000
        assert sizer.volatility_target == 0.20
        assert sizer.max_position_size == 0.10

    def test_calculate_instrument_weight(self):
        """Test instrument weight calculation."""
        sizer = PositionSizer(capital=100000, volatility_target=0.20)

        # Test with typical values
        shares = sizer.calculate_instrument_weight(
            price=100.0,
            volatility=0.25,
            forecast=10.0
        )

        assert isinstance(shares, float)
        assert shares > 0  # Should be positive for positive forecast

    def test_calculate_instrument_weight_negative_forecast(self):
        """Test with negative forecast (short position)."""
        sizer = PositionSizer(capital=100000, volatility_target=0.20)

        shares = sizer.calculate_instrument_weight(
            price=100.0,
            volatility=0.25,
            forecast=-10.0
        )

        assert shares < 0  # Should be negative for short position

    def test_position_size_limits(self):
        """Test that position sizes respect maximum limits."""
        sizer = PositionSizer(
            capital=100000,
            volatility_target=0.20,
            max_position_size=0.10
        )

        # Try to create a very large position with low volatility
        shares = sizer.calculate_instrument_weight(
            price=10.0,
            volatility=0.01,  # Very low volatility
            forecast=20.0  # Strong signal
        )

        # Position value should not exceed max_position_size * capital
        position_value = abs(shares * 10.0)
        assert position_value <= sizer.capital * sizer.max_position_size * 1.01  # Allow small rounding

    def test_invalid_inputs(self):
        """Test handling of invalid inputs."""
        sizer = PositionSizer(capital=100000)

        # Zero volatility
        shares = sizer.calculate_instrument_weight(
            price=100.0,
            volatility=0.0,
            forecast=10.0
        )
        assert shares == 0.0

        # Zero price
        shares = sizer.calculate_instrument_weight(
            price=0.0,
            volatility=0.25,
            forecast=10.0
        )
        assert shares == 0.0

    def test_fixed_fractional(self):
        """Test fixed fractional position sizing."""
        sizer = PositionSizer(capital=100000)

        shares = sizer.calculate_fixed_fractional(price=100.0, fraction=0.02)

        expected_shares = (100000 * 0.02) / 100.0
        assert abs(shares - expected_shares) < 0.01

    def test_portfolio_leverage(self):
        """Test portfolio leverage calculation."""
        sizer = PositionSizer(capital=100000)

        positions = {
            'STOCK1': 100,
            'STOCK2': 50,
            'STOCK3': -30
        }

        prices = {
            'STOCK1': 100.0,
            'STOCK2': 200.0,
            'STOCK3': 50.0
        }

        leverage = sizer.calculate_portfolio_leverage(positions, prices)

        # Total notional = |100*100| + |50*200| + |-30*50| = 10000 + 10000 + 1500 = 21500
        expected_leverage = 21500 / 100000
        assert abs(leverage - expected_leverage) < 0.01
