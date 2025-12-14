"""
Portfolio Module for Systematic Trading Framework
Based on Robert Carver's "Systematic Trading"

Core responsibilities:
- Forecast combination across instruments
- Portfolio optimization and weight calculation
- Diversification multiplier calculation
- Instrument weight management
- Capital allocation across instruments
"""

from typing import Dict, List, Optional

import numpy as np
import polars as pl
from pydantic import BaseModel, Field, field_validator

from utils.logger import setup_logger

logger = setup_logger(__name__)


# ---- Core Portfolio Structures ---- #


class PortfolioConfig(BaseModel):
    """Configuration for portfolio management."""

    use_instrument_weights: bool = Field(
        default=True, description="Use instrument-specific weights"
    )
    use_forecast_div_multiplier: bool = Field(
        default=True, description="Apply forecast diversification multiplier"
    )
    use_instrument_div_multiplier: bool = Field(
        default=True, description="Apply instrument diversification multiplier"
    )
    max_instruments: int = Field(
        default=50, ge=1, description="Maximum number of instruments"
    )
    min_instrument_weight: float = Field(
        default=0.01, ge=0.0, le=1.0, description="Minimum weight per instrument"
    )


class InstrumentForecast(BaseModel):
    """Container for instrument-level combined forecast."""

    model_config = {"arbitrary_types_allowed": True}

    ticker: str
    combined_forecast: pl.Series
    forecast_weights: Dict[str, float]
    diversification_multiplier: float

    @property
    def current_forecast(self) -> Optional[float]:
        """Get most recent combined forecast."""
        if len(self.combined_forecast) == 0:
            return None
        return self.combined_forecast[-1]


class PortfolioWeights(BaseModel):
    """Container for portfolio-level instrument weights."""

    weights: Dict[str, float] = Field(..., description="Instrument weights")
    diversification_multiplier: float = Field(
        default=1.0, description="Instrument diversification multiplier (IDM)"
    )
    method: str = Field(default="equal", description="Weight calculation method")

    @field_validator("weights")
    @classmethod
    def validate_weights(cls, v: Dict[str, float]) -> Dict[str, float]:
        """Ensure weights sum to approximately 1.0."""
        total = sum(v.values())
        if abs(total - 1.0) > 0.01:
            logger.warning(f"Weights sum to {total:.4f}, normalizing to 1.0")
            return {k: w / total for k, w in v.items()}
        return v


# ---- Instrument Diversification Multiplier ---- #


class InstrumentDiversificationMultiplier:
    """
    Calculate Instrument Diversification Multiplier (IDM).
    Carver's approach to account for portfolio diversification.
    """

    @staticmethod
    def calculate(weights: Dict[str, float]) -> float:
        """
        Calculate IDM from instrument weights.

        IDM = 1 / sqrt(sum of squared weights)

        Args:
            weights: Dictionary of instrument weights

        Returns:
            Instrument diversification multiplier
        """
        sum_squared = sum(w ** 2 for w in weights.values())
        if sum_squared <= 0:
            logger.warning("Invalid weights for IDM calculation")
            return 1.0

        idm = 1.0 / (sum_squared ** 0.5)

        logger.debug(f"IDM calculated: {idm:.4f} for {len(weights)} instruments")
        return idm

    @staticmethod
    def calculate_from_correlation(
            weights: Dict[str, float], correlation_matrix: pl.DataFrame
    ) -> float:
        """
        Calculate IDM accounting for correlations.

        IDM = 1 / sqrt(w^T * Corr * w)

        Args:
            weights: Dictionary of instrument weights
            correlation_matrix: Correlation matrix (DataFrame)

        Returns:
            Correlation-adjusted IDM
        """
        # Convert weights to array
        tickers = list(weights.keys())
        w = np.array([weights[t] for t in tickers])

        # Get correlation matrix as numpy array
        corr = correlation_matrix.to_numpy()

        # Portfolio variance in correlation space
        portfolio_var = w.T @ corr @ w

        if portfolio_var <= 0:
            logger.warning("Invalid portfolio variance for IDM")
            return 1.0

        idm = 1.0 / np.sqrt(portfolio_var)

        logger.debug(f"Correlation-adjusted IDM: {idm:.4f}")
        return idm


# ---- Instrument Weight Calculator ---- #


class InstrumentWeightCalculator:
    """Calculate optimal weights for instruments in portfolio."""

    @staticmethod
    def equal_weights(tickers: List[str]) -> Dict[str, float]:
        """
        Calculate equal weights for all instruments.

        Args:
            tickers: List of instrument tickers

        Returns:
            Dictionary of equal weights
        """
        n = len(tickers)
        if n == 0:
            return {}

        weight = 1.0 / n
        weights = {ticker: weight for ticker in tickers}

        logger.info(f"Equal weights calculated for {n} instruments: {weight:.4f} each")
        return weights

    @staticmethod
    def handcrafted_weights(weight_dict: Dict[str, float]) -> Dict[str, float]:
        """
        Use user-specified weights.

        Args:
            weight_dict: Dictionary of desired weights

        Returns:
            Normalized weights dictionary
        """
        total = sum(weight_dict.values())
        if abs(total - 1.0) > 0.01:
            logger.warning(f"Handcrafted weights sum to {total:.4f}, normalizing")
            normalized = {k: v / total for k, v in weight_dict.items()}
        else:
            normalized = weight_dict

        return normalized

    @staticmethod
    def inverse_volatility_weights(
            tickers: List[str], volatilities: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Weight instruments by inverse volatility.

        Args:
            tickers: List of tickers
            volatilities: Dictionary of instrument volatilities

        Returns:
            Inverse volatility weights
        """
        # Calculate inverse volatilities
        inv_vols = {t: 1.0 / volatilities[t] for t in tickers if volatilities[t] > 0}

        # Normalize to sum to 1
        total = sum(inv_vols.values())
        weights = {t: v / total for t, v in inv_vols.items()}

        logger.info(f"Inverse volatility weights calculated for {len(weights)} instruments")
        return weights

    @staticmethod
    def risk_parity_weights(
            tickers: List[str],
            volatilities: Dict[str, float],
            correlation_matrix: pl.DataFrame,
    ) -> Dict[str, float]:
        """
        Calculate risk parity weights (simplified approach).

        Args:
            tickers: List of tickers
            volatilities: Dictionary of volatilities
            correlation_matrix: Correlation matrix

        Returns:
            Risk parity weights
        """
        # Simplified: inverse vol adjusted for average correlation
        avg_corr = {}

        corr_np = correlation_matrix.to_numpy()
        for i, ticker in enumerate(tickers):
            # Average correlation with other instruments (excluding self)
            corr_vals = [corr_np[i, j] for j in range(len(tickers)) if i != j]
            avg_corr[ticker] = np.mean(corr_vals) if corr_vals else 0.0

        # Weight = 1 / (vol * sqrt(avg_correlation))
        weights_raw = {}
        for ticker in tickers:
            vol = volatilities.get(ticker, 0.0)
            if vol > 0:
                correlation_factor = max(avg_corr[ticker], 0.1)  # Floor at 0.1
                weights_raw[ticker] = 1.0 / (vol * np.sqrt(correlation_factor))

        # Normalize
        total = sum(weights_raw.values())
        weights = {t: w / total for t, w in weights_raw.items()}

        logger.info(f"Risk parity weights calculated for {len(weights)} instruments")
        return weights


# ---- Portfolio Optimizer ---- #


class PortfolioOptimizer:
    """
    Portfolio optimization using various methods.
    Carver prefers simple, robust methods over complex optimization.
    """

    def __init__(self, config: Optional[PortfolioConfig] = None):
        self.config = config or PortfolioConfig()

    def optimize_equal_weights(self, tickers: List[str]) -> PortfolioWeights:
        """
        Equal weight portfolio (Carver's default).

        Args:
            tickers: List of instrument tickers

        Returns:
            PortfolioWeights object
        """
        weights = InstrumentWeightCalculator.equal_weights(tickers)
        idm = InstrumentDiversificationMultiplier.calculate(weights)

        return PortfolioWeights(
            weights=weights,
            diversification_multiplier=idm,
            method="equal"
        )

    def optimize_inverse_volatility(
            self, tickers: List[str], volatilities: Dict[str, float]
    ) -> PortfolioWeights:
        """
        Inverse volatility weighting.

        Args:
            tickers: List of tickers
            volatilities: Dictionary of instrument volatilities

        Returns:
            PortfolioWeights object
        """
        weights = InstrumentWeightCalculator.inverse_volatility_weights(
            tickers, volatilities
        )
        idm = InstrumentDiversificationMultiplier.calculate(weights)

        return PortfolioWeights(
            weights=weights,
            diversification_multiplier=idm,
            method="inverse_volatility"
        )

    def optimize_risk_parity(
            self,
            tickers: List[str],
            volatilities: Dict[str, float],
            correlation_matrix: pl.DataFrame,
    ) -> PortfolioWeights:
        """
        Risk parity weighting.

        Args:
            tickers: List of tickers
            volatilities: Dictionary of volatilities
            correlation_matrix: Correlation matrix

        Returns:
            PortfolioWeights object
        """
        weights = InstrumentWeightCalculator.risk_parity_weights(
            tickers, volatilities, correlation_matrix
        )
        idm = InstrumentDiversificationMultiplier.calculate_from_correlation(
            weights, correlation_matrix
        )

        return PortfolioWeights(
            weights=weights,
            diversification_multiplier=idm,
            method="risk_parity"
        )

    def optimize_handcrafted(
            self, weight_dict: Dict[str, float], correlation_matrix: Optional[pl.DataFrame] = None
    ) -> PortfolioWeights:
        """
        Use handcrafted/manual weights.

        Args:
            weight_dict: Dictionary of desired weights
            correlation_matrix: Optional correlation matrix for IDM calculation

        Returns:
            PortfolioWeights object
        """
        weights = InstrumentWeightCalculator.handcrafted_weights(weight_dict)

        if correlation_matrix is not None:
            idm = InstrumentDiversificationMultiplier.calculate_from_correlation(
                weights, correlation_matrix
            )
        else:
            idm = InstrumentDiversificationMultiplier.calculate(weights)

        return PortfolioWeights(
            weights=weights,
            diversification_multiplier=idm,
            method="handcrafted"
        )


# ---- Correlation Estimator ---- #


class CorrelationEstimator:
    """Estimate correlations between instrument returns."""

    @staticmethod
    def calculate_from_returns(
            returns_df: pl.DataFrame, min_periods: int = 20
    ) -> pl.DataFrame:
        """
        Calculate correlation matrix from returns.

        Args:
            returns_df: DataFrame with returns for each instrument (columns)
            min_periods: Minimum observations required

        Returns:
            Correlation matrix as DataFrame
        """
        if len(returns_df) < min_periods:
            logger.warning(
                f"Insufficient data for correlation: {len(returns_df)} < {min_periods}"
            )
            # Return identity matrix
            n = len(returns_df.columns)
            return pl.DataFrame(np.eye(n), schema=returns_df.columns)

        corr_matrix = returns_df.corr()

        logger.info(f"Correlation matrix calculated for {len(returns_df.columns)} instruments")
        return corr_matrix

    @staticmethod
    def ewma_correlation(
            returns_df: pl.DataFrame, span: int = 60, min_periods: int = 20
    ) -> pl.DataFrame:
        """
        Calculate EWMA correlation matrix.

        Args:
            returns_df: DataFrame with returns
            span: EWMA span
            min_periods: Minimum periods

        Returns:
            EWMA correlation matrix
        """
        # Calculate EWMA covariance, then convert to correlation
        # Simplified: use standard correlation as approximation
        # Full EWMA covariance requires more complex calculation
        corr = CorrelationEstimator.calculate_from_returns(returns_df, min_periods)

        logger.info(f"EWMA correlation matrix calculated (span={span})")
        return corr

    @staticmethod
    def shrink_correlation(
            corr_matrix: pl.DataFrame, shrinkage_factor: float = 0.5
    ) -> pl.DataFrame:
        """
        Apply shrinkage to correlation matrix (towards identity).

        Args:
            corr_matrix: Original correlation matrix
            shrinkage_factor: Shrinkage intensity (0=no shrink, 1=full shrink to identity)

        Returns:
            Shrunk correlation matrix
        """
        n = len(corr_matrix.columns)
        identity = pl.DataFrame(np.eye(n), schema=corr_matrix.columns)

        # Linear combination: shrunk = (1-λ)*corr + λ*I
        corr_np = corr_matrix.to_numpy()
        identity_np = identity.to_numpy()

        shrunk_np = (1 - shrinkage_factor) * corr_np + shrinkage_factor * identity_np

        shrunk = pl.DataFrame(shrunk_np, schema=corr_matrix.columns)

        logger.info(f"Correlation matrix shrunk with factor {shrinkage_factor:.2f}")
        return shrunk


# ---- Capital Allocation ---- #


class CapitalAllocator:
    """Allocate capital across instruments based on weights."""

    @staticmethod
    def allocate(
            total_capital: float,
            portfolio_weights: PortfolioWeights,
            apply_idm: bool = True,
    ) -> Dict[str, float]:
        """
        Allocate capital to each instrument.

        Args:
            total_capital: Total portfolio capital
            portfolio_weights: PortfolioWeights object
            apply_idm: Whether to apply IDM

        Returns:
            Dictionary of capital allocation per instrument
        """
        weights = portfolio_weights.weights

        if apply_idm:
            # Scale capital by IDM
            effective_capital = total_capital * portfolio_weights.diversification_multiplier
            logger.debug(
                f"Applying IDM {portfolio_weights.diversification_multiplier:.4f}: "
                f"${total_capital:,.0f} → ${effective_capital:,.0f}"
            )
        else:
            effective_capital = total_capital

        allocation = {
            ticker: effective_capital * weight
            for ticker, weight in weights.items()
        }

        logger.info(
            f"Capital allocated across {len(allocation)} instruments "
            f"(total: ${sum(allocation.values()):,.0f})"
        )

        return allocation


# ---- Portfolio Manager (Main Interface) ---- #


class PortfolioManager:
    """
    Main interface for portfolio management.
    Coordinates forecast combination, optimization, and capital allocation.
    """

    def __init__(self, config: Optional[PortfolioConfig] = None):
        self.config = config or PortfolioConfig()
        self.optimizer = PortfolioOptimizer(self.config)
        self.correlation_estimator = CorrelationEstimator()

    def calculate_portfolio_weights(
            self,
            tickers: List[str],
            method: str = "equal",
            volatilities: Optional[Dict[str, float]] = None,
            correlation_matrix: Optional[pl.DataFrame] = None,
            handcrafted_weights: Optional[Dict[str, float]] = None,
    ) -> PortfolioWeights:
        """
        Calculate optimal portfolio weights.

        Args:
            tickers: List of instrument tickers
            method: 'equal', 'inverse_volatility', 'risk_parity', or 'handcrafted'
            volatilities: Optional dictionary of instrument volatilities
            correlation_matrix: Optional correlation matrix
            handcrafted_weights: Optional manual weights

        Returns:
            PortfolioWeights object
        """
        if method == "equal":
            return self.optimizer.optimize_equal_weights(tickers)

        elif method == "inverse_volatility":
            if volatilities is None:
                raise ValueError("Volatilities required for inverse_volatility method")
            return self.optimizer.optimize_inverse_volatility(tickers, volatilities)

        elif method == "risk_parity":
            if volatilities is None or correlation_matrix is None:
                raise ValueError(
                    "Volatilities and correlation matrix required for risk_parity"
                )
            return self.optimizer.optimize_risk_parity(
                tickers, volatilities, correlation_matrix
            )

        elif method == "handcrafted":
            if handcrafted_weights is None:
                raise ValueError("Handcrafted weights required for handcrafted method")
            return self.optimizer.optimize_handcrafted(
                handcrafted_weights, correlation_matrix
            )

        else:
            raise ValueError(f"Unknown method: {method}")

    def estimate_correlations(
            self,
            returns_df: pl.DataFrame,
            method: str = "standard",
            span: int = 60,
            shrinkage: float = 0.0,
    ) -> pl.DataFrame:
        """
        Estimate correlation matrix from returns.

        Args:
            returns_df: DataFrame with returns
            method: 'standard' or 'ewma'
            span: EWMA span (if using ewma method)
            shrinkage: Shrinkage factor (0=no shrink, 1=full shrink)

        Returns:
            Correlation matrix
        """
        if method == "standard":
            corr = self.correlation_estimator.calculate_from_returns(returns_df)
        elif method == "ewma":
            corr = self.correlation_estimator.ewma_correlation(returns_df, span)
        else:
            raise ValueError(f"Unknown correlation method: {method}")

        if shrinkage > 0:
            corr = self.correlation_estimator.shrink_correlation(corr, shrinkage)

        return corr

    def allocate_capital(
            self,
            total_capital: float,
            portfolio_weights: PortfolioWeights,
            apply_idm: bool = True,
    ) -> Dict[str, float]:
        """
        Allocate capital across instruments.

        Args:
            total_capital: Total portfolio capital
            portfolio_weights: Portfolio weights
            apply_idm: Apply instrument diversification multiplier

        Returns:
            Dictionary of capital per instrument
        """
        return CapitalAllocator.allocate(total_capital, portfolio_weights, apply_idm)


# ---- Utility Functions ---- #


def calculate_portfolio_forecast(
        instrument_forecasts: Dict[str, float],
        instrument_weights: Dict[str, float],
) -> float:
    """
    Calculate aggregate portfolio forecast.

    Args:
        instrument_forecasts: Dictionary of instrument forecasts
        instrument_weights: Dictionary of instrument weights

    Returns:
        Weighted average portfolio forecast
    """
    portfolio_forecast = sum(
        instrument_forecasts[ticker] * instrument_weights[ticker]
        for ticker in instrument_forecasts.keys()
        if ticker in instrument_weights
    )

    return portfolio_forecast


def validate_weights(weights: Dict[str, float], tolerance: float = 0.01) -> bool:
    """
    Validate that weights sum to approximately 1.0.

    Args:
        weights: Dictionary of weights
        tolerance: Acceptable deviation from 1.0

    Returns:
        True if valid
    """
    total = sum(weights.values())

    if abs(total - 1.0) > tolerance:
        logger.warning(f"Weights sum to {total:.4f}, outside tolerance {tolerance}")
        return False

    if any(w < 0 for w in weights.values()):
        logger.warning("Negative weights detected")
        return False

    return True
