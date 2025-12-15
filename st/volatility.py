"""
Volatility Module for Systematic Trading Framework
Based on Robert Carver's "Systematic Trading"

Core responsibilities:
- Volatility estimation (EWMA, Standard Deviation)
- Volatility forecasting
- Volatility targeting for position sizing
- Risk normalization
"""

from typing import Optional

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field, field_validator

from st.config.settings import Settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


# ---- Core Volatility Structures ---- #


class VolatilityConfig(BaseModel):
    """Configuration for volatility calculations."""

    span: int = Field(
        default=36, ge=2, description="EWMA span (Carver recommends 32-36)"
    )
    min_periods: int = Field(
        default=10, ge=1, description="Minimum periods for calculation"
    )
    annualization_factor: int = Field(
        default=Settings.BUSINESS_DAYS_PER_YEAR,
        description="Trading days per year (256 for Carver)",
    )

    @field_validator("span")
    @classmethod
    def validate_span(cls, v: int) -> int:
        """Ensure span is reasonable for trading."""
        if v < 2:
            raise ValueError("Span must be at least 2")
        if v > 200:
            logger.warning(
                f"Unusual span value: {v}. Carver recommends 32-36."
            )
        return v


class VolatilityResult(BaseModel):
    """Container for volatility calculation results."""

    model_config = {"arbitrary_types_allowed": True}

    ticker: str
    daily_vol: pd.Series
    annual_vol: pd.Series
    config: VolatilityConfig

    @property
    def current_daily_vol(self) -> Optional[float]:
        """Get most recent daily volatility."""
        if len(self.daily_vol) == 0:
            return None
        return self.daily_vol.iloc[-1]

    @property
    def current_annual_vol(self) -> Optional[float]:
        """Get most recent annual volatility."""
        if len(self.annual_vol) == 0:
            return None
        return self.annual_vol.iloc[-1]


# ---- Volatility Estimators ---- #


class StandardVolatility:
    """Standard deviation-based volatility estimation."""

    @staticmethod
    def calculate(
            returns: pd.Series, window: int = 36, min_periods: int = 10
    ) -> pd.Series:
        """
        Calculate rolling standard deviation of returns.

        Args:
            returns: Series of returns (log or percentage)
            window: Rolling window size
            min_periods: Minimum observations required

        Returns:
            Series of volatility estimates
        """
        vol = returns.rolling().std(
            window_size=window,
            min_periods=min_periods
        )
        return vol

    @staticmethod
    def annualize(daily_vol: pd.Series, factor: int = 256) -> pd.Series:
        """Convert daily volatility to annual."""
        return daily_vol * (factor ** 0.5)


class EWMAVolatility:
    """
    Exponentially Weighted Moving Average volatility estimation.
    Carver's preferred method for systematic trading.
    """

    def __init__(self, config: Optional[VolatilityConfig] = None):
        self.config = config or VolatilityConfig()

    def calculate(
            self, returns: pd.Series, ticker: str = ""
    ) -> VolatilityResult:
        """
        Calculate EWMA volatility.

        Args:
            returns: Series of returns
            ticker: Instrument identifier

        Returns:
            VolatilityResult with daily and annual volatility
        """
        # EWMA of squared returns
        squared_returns = returns ** 2
        ewma_var = squared_returns.ewm(
            span=self.config.span,
            min_periods=self.config.min_periods
        ).mean()

        # Volatility is square root of variance
        daily_vol = ewma_var ** 0.5

        # Annualize
        annual_vol = daily_vol * (self.config.annualization_factor ** 0.5)

        logger.info(
            f"Calculated EWMA volatility for {ticker or 'series'} "
            f"(span={self.config.span}, current={daily_vol.iloc[-1]:.4f})"
        )

        return VolatilityResult(
            ticker=ticker or "unknown",
            daily_vol=daily_vol,
            annual_vol=annual_vol,
            config=self.config,
        )

    def calculate_from_prices(
            self, prices: pd.Series, ticker: str = ""
    ) -> VolatilityResult:
        """
        Calculate EWMA volatility from price series.

        Args:
            prices: Series of close prices
            ticker: Instrument identifier

        Returns:
            VolatilityResult
        """
        # Calculate log returns
        log_returns = np.log(prices / prices.shift(1))

        return self.calculate(log_returns, ticker)


class RobustVolatility:
    """
    Robust volatility estimation using median absolute deviation.
    Useful for data with outliers.
    """

    @staticmethod
    def calculate(
            returns: pd.Series, window: int = 36, scale_factor: float = 1.4826
    ) -> pd.Series:
        """
        Calculate rolling MAD-based volatility.

        Args:
            returns: Series of returns
            window: Rolling window size
            scale_factor: Scale to match std dev (1.4826 for normal distribution)

        Returns:
            Series of volatility estimates
        """

        def rolling_mad(series: pd.Series) -> float:
            """Calculate median absolute deviation."""
            median = series.median()
            if median is None:
                return None
            mad = (series - median).abs().median()
            return mad * scale_factor if mad is not None else None

        # Use rolling_map for custom aggregation
        vol = returns.rolling().apply(rolling_mad, window_size=window)

        return vol


# ---- Volatility Forecasting ---- #


class VolatilityForecaster:
    """Forecast future volatility using recent estimates."""

    @staticmethod
    def simple_forecast(
            volatility: pd.Series, horizon: int = 1, method: str = "last"
    ) -> pd.Series:
        """
        Simple volatility forecast.

        Args:
            volatility: Historical volatility series
            horizon: Forecast horizon (days)
            method: 'last' or 'mean'

        Returns:
            Forecasted volatility
        """
        if method == "last":
            # Use last observation (Carver's simple approach)
            forecast = volatility
        elif method == "mean":
            # Rolling mean forecast
            forecast = volatility.rolling().mean(window_size=10, min_periods=1)
        else:
            raise ValueError(f"Unknown method: {method}")

        # Scale by sqrt(horizon) for multi-day forecasts
        if horizon > 1:
            forecast = forecast * (horizon ** 0.5)

        return forecast

    @staticmethod
    def ewma_forecast(
            volatility: pd.Series, span: int = 10, horizon: int = 1
    ) -> pd.Series:
        """
        EWMA-based volatility forecast.

        Args:
            volatility: Historical volatility
            span: EWMA span for forecasting
            horizon: Forecast horizon

        Returns:
            Forecasted volatility
        """
        forecast = volatility.ewm_mean(span=span, min_periods=1)

        if horizon > 1:
            forecast = forecast * (horizon ** 0.5)

        return forecast


# ---- Volatility Targeting ---- #


class VolatilityTargeter:
    """
    Volatility targeting for position sizing.
    Core component of Carver's risk management.
    """

    def __init__(self, target_vol: float = Settings.VOLATILITY_TARGET):
        """
        Initialize volatility targeter.

        Args:
            target_vol: Target annual volatility (e.g., 0.20 for 20%)
        """
        self.target_vol = target_vol

    def calculate_scalar(self, current_vol: float) -> float:
        """
        Calculate volatility scaling factor.

        Args:
            current_vol: Current annual volatility

        Returns:
            Scaling factor (target_vol / current_vol)
        """
        if current_vol <= 0:
            logger.warning(
                f"Invalid volatility: {current_vol}, returning 0 scalar"
            )
            return 0.0

        scalar = self.target_vol / current_vol

        logger.debug(
            f"Vol scalar: target={self.target_vol:.2%}, "
            f"current={current_vol:.2%}, scalar={scalar:.4f}"
        )

        return scalar

    def calculate_scalars(self, volatilities: pd.Series) -> pd.Series:
        """
        Calculate scaling factors for a series of volatilities.

        Args:
            volatilities: Series of annual volatilities

        Returns:
            Series of scaling factors
        """
        scalars = self.target_vol / volatilities

        # Handle invalid values
        scalars = scalars.fillna(0.0)
        scalars[np.isinf(scalars)] = 0.0
        return scalars

    def target_position(
            self, base_position: float, current_vol: float
    ) -> float:
        """
        Scale position to target volatility.

        Args:
            base_position: Unscaled position size
            current_vol: Current annual volatility

        Returns:
            Volatility-targeted position
        """
        scalar = self.calculate_scalar(current_vol)
        return base_position * scalar


# ---- Volatility Manager (Main Interface) ---- #


class VolatilityManager:
    """
    Main interface for volatility calculations.
    Coordinates estimation, forecasting, and targeting.
    """

    def __init__(
            self,
            config: Optional[VolatilityConfig] = None,
            target_vol: float = Settings.VOLATILITY_TARGET,
    ):
        self.config = config or VolatilityConfig()
        self.estimator = EWMAVolatility(self.config)
        self.targeter = VolatilityTargeter(target_vol)
        self.forecaster = VolatilityForecaster()

    def estimate_from_returns(
            self, returns: pd.Series, ticker: str = ""
    ) -> VolatilityResult:
        """
        Estimate volatility from returns.

        Args:
            returns: Series of returns
            ticker: Instrument identifier

        Returns:
            VolatilityResult
        """
        return self.estimator.calculate(returns, ticker)

    def estimate_from_prices(
            self, prices: pd.Series, ticker: str = ""
    ) -> VolatilityResult:
        """
        Estimate volatility from prices.

        Args:
            prices: Series of close prices
            ticker: Instrument identifier

        Returns:
            VolatilityResult
        """
        return self.estimator.calculate_from_prices(prices, ticker)

    def forecast(
            self, volatility_result: VolatilityResult, horizon: int = 1
    ) -> pd.Series:
        """
        Forecast future volatility.

        Args:
            volatility_result: Historical volatility
            horizon: Forecast horizon (days)

        Returns:
            Forecasted annual volatility
        """
        return self.forecaster.simple_forecast(
            volatility_result.annual_vol, horizon, method="last"
        )

    def get_position_scalar(
            self, volatility_result: VolatilityResult
    ) -> float:
        """
        Get current position scaling factor.

        Args:
            volatility_result: Volatility estimate

        Returns:
            Scaling factor for position sizing
        """
        current_vol = volatility_result.current_annual_vol
        if current_vol is None:
            logger.warning("No volatility data available")
            return 0.0

        return self.targeter.calculate_scalar(current_vol)

    def calculate_multi_instrument_vols(
            self, returns_df: pd.DataFrame
    ) -> dict[str, VolatilityResult]:
        """
        Calculate volatilities for multiple instruments.

        Args:
            returns_df: DataFrame with returns for each instrument (columns)

        Returns:
            Dictionary mapping ticker to VolatilityResult
        """
        results = {}

        for col in returns_df.columns:
            returns = returns_df[col]
            vol_result = self.estimate_from_returns(returns, ticker=col)
            results[col] = vol_result

            logger.info(
                f"{col}: Current vol = {vol_result.current_annual_vol:.2%}"
            )

        return results


# ---- Utility Functions ---- #


def calculate_correlation_adjusted_vol(
        volatilities: pd.Series, correlation_matrix: pd.DataFrame
) -> float:
    """
    Calculate portfolio volatility accounting for correlations.

    Args:
        volatilities: Series of instrument volatilities
        correlation_matrix: Correlation matrix

    Returns:
        Portfolio volatility
    """
    # Convert to numpy for matrix operations
    vols = volatilities.to_numpy()
    corr = correlation_matrix.to_numpy()

    # Portfolio variance = w^T * Σ * w (assuming equal weights)
    n = len(vols)
    weights = pd.Series([1.0 / n] * n)
    w = weights.to_numpy().reshape(-1, 1)

    # Covariance matrix
    cov = corr * (vols.reshape(-1, 1) @ vols.reshape(1, -1))

    # Portfolio variance
    portfolio_var = (w.T @ cov @ w)[0, 0]
    portfolio_vol = portfolio_var ** 0.5

    return portfolio_vol


def validate_volatility(
        vol: float, min_vol: float = 0.01, max_vol: float = 2.0
) -> bool:
    """
    Validate volatility is within reasonable bounds.

    Args:
        vol: Volatility to validate
        min_vol: Minimum acceptable volatility (default 1%)
        max_vol: Maximum acceptable volatility (default 200%)

    Returns:
        True if valid
    """
    if vol < min_vol:
        logger.warning(f"Volatility too low: {vol:.2%} < {min_vol:.2%}")
        return False

    if vol > max_vol:
        logger.warning(f"Volatility too high: {vol:.2%} > {max_vol:.2%}")
        return False

    return True
