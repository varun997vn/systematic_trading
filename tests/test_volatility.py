"""
Unit tests for the Volatility module.
Tests all key functionality with edge cases.
"""

import polars as pl
import pytest

from st.volatility import (
    VolatilityConfig,
    VolatilityResult,
    EWMAVolatility,
    StandardVolatility,
    VolatilityTargeter,
    VolatilityForecaster,
    VolatilityManager,
    validate_volatility,
)


class TestVolatilityConfig:
    """Test VolatilityConfig validation."""

    def test_default_config(self):
        """Test default configuration."""
        config = VolatilityConfig()
        assert config.span == 36
        assert config.min_periods == 10
        assert config.annualization_factor == 256

    def test_custom_config(self):
        """Test custom configuration."""
        config = VolatilityConfig(span=32, min_periods=5)
        assert config.span == 32
        assert config.min_periods == 5

    def test_invalid_span(self):
        """Test invalid span raises error."""
        with pytest.raises(ValueError):
            VolatilityConfig(span=1)


class TestEWMAVolatility:
    """Test EWMA volatility calculations."""

    def test_basic_calculation(self):
        """Test basic EWMA calculation."""
        returns = pl.Series([0.01, -0.02, 0.015, -0.01, 0.008] * 20)

        estimator = EWMAVolatility()
        result = estimator.calculate(returns, ticker="TEST")

        assert isinstance(result, VolatilityResult)
        assert result.ticker == "TEST"
        assert len(result.daily_vol) == len(returns)
        assert result.current_daily_vol is not None
        assert result.current_annual_vol is not None

    def test_from_prices(self):
        """Test calculation from prices."""
        prices = pl.Series([100.0, 101.0, 99.5, 102.0, 100.5] * 20)

        estimator = EWMAVolatility()
        result = estimator.calculate_from_prices(prices, ticker="AAPL")

        assert result.ticker == "AAPL"
        assert result.current_annual_vol is not None

    def test_annualization(self):
        """Test volatility annualization."""
        returns = pl.Series([0.01] * 100)

        estimator = EWMAVolatility(VolatilityConfig(span=36))
        result = estimator.calculate(returns)

        # Annual vol should be daily vol * sqrt(256)
        expected_ratio = 256 ** 0.5
        actual_ratio = result.current_annual_vol / result.current_daily_vol

        assert abs(actual_ratio - expected_ratio) < 0.01

    def test_different_spans(self):
        """Test different EWMA spans."""
        returns = pl.Series([0.01, -0.02, 0.015] * 50)

        spans = [16, 32, 64]
        results = []

        for span in spans:
            config = VolatilityConfig(span=span)
            estimator = EWMAVolatility(config)
            result = estimator.calculate(returns)
            results.append(result.current_annual_vol)

        # Results should be different
        assert len(set(results)) == len(results)


class TestStandardVolatility:
    """Test standard deviation volatility."""

    def test_rolling_std(self):
        """Test rolling standard deviation."""
        returns = pl.Series([0.01, -0.01] * 50)

        vol = StandardVolatility.calculate(returns, window=20)
        assert len(vol) == len(returns)

    def test_annualization(self):
        """Test annualization factor."""
        daily_vol = pl.Series([0.01] * 10)
        annual_vol = StandardVolatility.annualize(daily_vol)

        expected = 0.01 * (256 ** 0.5)
        assert abs(annual_vol[0] - expected) < 0.001


class TestVolatilityTargeter:
    """Test volatility targeting."""

    def test_calculate_scalar(self):
        """Test scalar calculation."""
        targeter = VolatilityTargeter(target_vol=0.20)

        scalar = targeter.calculate_scalar(current_vol=0.10)
        assert scalar == 2.0  # 0.20 / 0.10

        scalar = targeter.calculate_scalar(current_vol=0.40)
        assert scalar == 0.5  # 0.20 / 0.40

    def test_zero_volatility(self):
        """Test handling of zero volatility."""
        targeter = VolatilityTargeter(target_vol=0.20)
        scalar = targeter.calculate_scalar(current_vol=0.0)
        assert scalar == 0.0

    def test_target_position(self):
        """Test position targeting."""
        targeter = VolatilityTargeter(target_vol=0.20)

        position = targeter.target_position(base_position=100, current_vol=0.10)
        assert position == 200.0  # Scaled up

        position = targeter.target_position(base_position=100, current_vol=0.40)
        assert position == 50.0  # Scaled down

    def test_calculate_scalars_series(self):
        """Test scalar calculation for series."""
        targeter = VolatilityTargeter(target_vol=0.20)
        vols = pl.Series([0.10, 0.20, 0.40])

        scalars = targeter.calculate_scalars(vols)
        expected = pl.Series([2.0, 1.0, 0.5])

        assert scalars.to_list() == expected.to_list()


class TestVolatilityForecaster:
    """Test volatility forecasting."""

    def test_simple_forecast_last(self):
        """Test simple forecast using last value."""
        vol = pl.Series([0.15, 0.16, 0.18, 0.17, 0.19])

        forecaster = VolatilityForecaster()
        forecast = forecaster.simple_forecast(vol, horizon=1, method="last")

        assert forecast[-1] == vol[-1]

    def test_multi_period_forecast(self):
        """Test multi-period forecast."""
        vol = pl.Series([0.20] * 10)

        forecaster = VolatilityForecaster()
        forecast_5d = forecaster.simple_forecast(vol, horizon=5)

        expected = 0.20 * (5 ** 0.5)
        assert abs(forecast_5d[-1] - expected) < 0.001

    def test_ewma_forecast(self):
        """Test EWMA forecast."""
        vol = pl.Series([0.15, 0.16, 0.18, 0.17, 0.19])

        forecaster = VolatilityForecaster()
        forecast = forecaster.ewma_forecast(vol, span=3)

        assert len(forecast) == len(vol)


class TestVolatilityManager:
    """Test VolatilityManager integration."""

    def test_estimate_from_returns(self):
        """Test estimation from returns."""
        returns = pl.Series([0.01, -0.02, 0.015] * 40)

        manager = VolatilityManager()
        result = manager.estimate_from_returns(returns, ticker="TEST")

        assert isinstance(result, VolatilityResult)
        assert result.ticker == "TEST"

    def test_estimate_from_prices(self):
        """Test estimation from prices."""
        prices = pl.Series([100.0 + i * 0.1 for i in range(100)])

        manager = VolatilityManager()
        result = manager.estimate_from_prices(prices, ticker="AAPL")

        assert result.ticker == "AAPL"

    def test_get_position_scalar(self):
        """Test getting position scalar."""
        returns = pl.Series([0.01, -0.02] * 50)

        manager = VolatilityManager(target_vol=0.20)
        result = manager.estimate_from_returns(returns)
        scalar = manager.get_position_scalar(result)

        assert scalar > 0

    def test_multi_instrument(self):
        """Test multi-instrument calculation."""
        data = {
            "AAPL": [0.01, -0.02, 0.015] * 40,
            "GOOGL": [0.012, -0.015, 0.008] * 40,
        }
        returns_df = pl.DataFrame(data)

        manager = VolatilityManager()
        results = manager.calculate_multi_instrument_vols(returns_df)

        assert len(results) == 2
        assert "AAPL" in results
        assert "GOOGL" in results


class TestUtilityFunctions:
    """Test utility functions."""

    def test_validate_volatility(self):
        """Test volatility validation."""
        assert validate_volatility(0.15) is True
        assert validate_volatility(0.005) is False  # Too low
        assert validate_volatility(2.5) is False  # Too high

    def test_validate_custom_bounds(self):
        """Test validation with custom bounds."""
        assert validate_volatility(0.05, min_vol=0.01, max_vol=0.50) is True
        assert validate_volatility(0.60, min_vol=0.01, max_vol=0.50) is False


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_series(self):
        """Test with empty series."""
        returns = pl.Series([], dtype=pl.Float64)

        estimator = EWMAVolatility()
        result = estimator.calculate(returns)

        assert result.current_daily_vol is None

    def test_single_value(self):
        """Test with single value."""
        returns = pl.Series([0.01])

        estimator = EWMAVolatility()
        result = estimator.calculate(returns)

        # Should handle gracefully
        assert result is not None

    def test_all_zeros(self):
        """Test with all zero returns."""
        returns = pl.Series([0.0] * 100)

        estimator = EWMAVolatility()
        result = estimator.calculate(returns)

        # Vol should be near zero
        assert result.current_daily_vol < 0.001

    def test_extreme_volatility(self):
        """Test with extreme volatility."""
        returns = pl.Series([0.5, -0.5] * 50)

        estimator = EWMAVolatility()
        result = estimator.calculate(returns)

        # Should calculate high volatility
        assert result.current_annual_vol > 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
