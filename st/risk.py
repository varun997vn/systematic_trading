"""
Risk Management Module for Systematic Trading Framework
Based on Robert Carver's "Systematic Trading"

Core responsibilities:
- Portfolio risk calculation
- Correlation estimation
- Position limits and constraints
- Diversification multiplier
- Capital allocation
- Risk monitoring and reporting
"""

from typing import Dict, List, Optional, Tuple

import numpy as np
import polars as pl
from pydantic import BaseModel, Field, field_validator

from st.config.settings import Settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


# ---- Core Risk Structures ---- #


class RiskConfig(BaseModel):
    """Configuration for risk management."""

    max_instrument_risk: float = Field(
        default=0.20,
        ge=0.01,
        le=1.0,
        description="Maximum risk per instrument (e.g., 0.20 for 20%)",
    )
    max_portfolio_risk: float = Field(
        default=0.25,
        ge=0.01,
        le=1.0,
        description="Maximum portfolio risk (e.g., 0.25 for 25%)",
    )
    max_forecast: float = Field(
        default=20.0, ge=1.0, description="Maximum forecast scalar (Carver uses 20)"
    )
    max_leverage: float = Field(
        default=2.0, ge=1.0, description="Maximum portfolio leverage"
    )
    correlation_lookback: int = Field(
        default=120, ge=20, description="Days for correlation estimation"
    )
    min_correlation_samples: int = Field(
        default=30, ge=10, description="Minimum samples for correlation"
    )

    @field_validator("max_portfolio_risk")
    @classmethod
    def validate_portfolio_risk(cls, v: float, info) -> float:
        """Ensure portfolio risk >= instrument risk."""
        data = info.data
        if "max_instrument_risk" in data and v < data["max_instrument_risk"]:
            raise ValueError(
                "max_portfolio_risk must be >= max_instrument_risk"
            )
        return v


class PositionRisk(BaseModel):
    """Risk metrics for a single position."""

    ticker: str
    position_size: float
    volatility: float
    capital_allocated: float
    position_risk: float = Field(
        description="Position risk as % of capital"
    )
    leverage: float = Field(description="Position leverage")

    @property
    def notional_exposure(self) -> float:
        """Calculate notional exposure."""
        return abs(self.position_size * self.capital_allocated)


class PortfolioRisk(BaseModel):
    """Aggregate portfolio risk metrics."""

    total_capital: float
    gross_exposure: float
    net_exposure: float
    portfolio_volatility: float
    portfolio_risk: float = Field(
        description="Portfolio risk as % of capital"
    )
    diversification_multiplier: float
    leverage: float
    num_instruments: int
    instrument_risks: Dict[str, float] = Field(
        description="Risk contribution by instrument"
    )

    @property
    def concentration_ratio(self) -> float:
        """Calculate concentration (1 = fully concentrated, 1/N = equal weight)."""
        if not self.instrument_risks:
            return 0.0
        risks = list(self.instrument_risks.values())
        hhi = sum(r ** 2 for r in risks)
        return hhi ** 0.5


# ---- Correlation Estimation ---- #


class CorrelationEstimator:
    """
    Estimate correlations between instruments.
    Carver uses exponentially weighted correlations.
    """

    def __init__(self, lookback: int = 120, min_samples: int = 30):
        """
        Initialize correlation estimator.

        Args:
            lookback: Days of historical data
            min_samples: Minimum samples required
        """
        self.lookback = lookback
        self.min_samples = min_samples

    def estimate(self, returns_df: pl.DataFrame) -> pl.DataFrame:
        """
        Calculate correlation matrix from returns.

        Args:
            returns_df: DataFrame with instrument returns (columns = tickers)

        Returns:
            Correlation matrix as polars DataFrame
        """
        # Limit to lookback period
        if len(returns_df) > self.lookback:
            returns_df = returns_df.tail(self.lookback)

        if len(returns_df) < self.min_samples:
            logger.warning(
                f"Insufficient data for correlation: {len(returns_df)} < {self.min_samples}"
            )
            # Return identity matrix
            tickers = returns_df.columns
            return pl.DataFrame(
                np.eye(len(tickers)), schema=tickers
            )

        # Calculate correlation using numpy (polars doesn't have native corr)
        numpy_data = returns_df.to_numpy()
        corr_matrix = np.corrcoef(numpy_data.T)

        # Handle NaN (replace with 0 correlation, 1 on diagonal)
        np.nan_to_num(corr_matrix, copy=False, nan=0.0)
        np.fill_diagonal(corr_matrix, 1.0)

        # Convert back to polars
        corr_df = pl.DataFrame(corr_matrix, schema=returns_df.columns)

        logger.info(
            f"Calculated correlation matrix: {len(returns_df.columns)} instruments, "
            f"avg corr = {self._avg_correlation(corr_matrix):.3f}"
        )

        return corr_df

    def ewma_correlation(
            self, returns_df: pl.DataFrame, span: int = 60
    ) -> pl.DataFrame:
        """
        Calculate exponentially weighted correlation matrix.

        Args:
            returns_df: DataFrame with returns
            span: EWMA span

        Returns:
            EWMA correlation matrix
        """
        # Limit to lookback
        if len(returns_df) > self.lookback:
            returns_df = returns_df.tail(self.lookback)

        if len(returns_df) < self.min_samples:
            logger.warning("Insufficient data for EWMA correlation")
            tickers = returns_df.columns
            return pl.DataFrame(np.eye(len(tickers)), schema=tickers)

        # Calculate EWMA covariance manually
        n_assets = len(returns_df.columns)
        numpy_returns = returns_df.to_numpy()

        # EWMA weights
        alpha = 2 / (span + 1)
        weights = np.array(
            [(1 - alpha) ** i for i in range(len(numpy_returns) - 1, -1, -1)]
        )
        weights = weights / weights.sum()

        # Weighted mean
        weighted_mean = np.average(numpy_returns, axis=0, weights=weights)

        # Centered returns
        centered = numpy_returns - weighted_mean

        # EWMA covariance
        cov_matrix = np.zeros((n_assets, n_assets))
        for i in range(len(centered)):
            outer = np.outer(centered[i], centered[i])
            cov_matrix += weights[i] * outer

        # Convert to correlation
        std_devs = np.sqrt(np.diag(cov_matrix))
        corr_matrix = cov_matrix / np.outer(std_devs, std_devs)

        # Clean up
        np.nan_to_num(corr_matrix, copy=False, nan=0.0)
        np.fill_diagonal(corr_matrix, 1.0)

        corr_df = pl.DataFrame(corr_matrix, schema=returns_df.columns)

        logger.info(
            f"EWMA correlation (span={span}): avg = {self._avg_correlation(corr_matrix):.3f}"
        )

        return corr_df

    @staticmethod
    def _avg_correlation(corr_matrix: np.ndarray) -> float:
        """Calculate average off-diagonal correlation."""
        n = len(corr_matrix)
        if n <= 1:
            return 0.0
        mask = ~np.eye(n, dtype=bool)
        return corr_matrix[mask].mean()


# ---- Diversification Multiplier ---- #


class DiversificationMultiplier:
    """
    Calculate diversification multiplier (IDM).
    Accounts for benefit of combining multiple instruments.

    Carver's formula: IDM = 1 / sqrt(instrument_weight^T * correlation_matrix * instrument_weight)
    """

    @staticmethod
    def calculate(
            weights: pl.Series,
            correlation_matrix: pl.DataFrame,
    ) -> float:
        """
        Calculate instrument diversification multiplier.

        Args:
            weights: Instrument weights (must sum to 1)
            correlation_matrix: Correlation matrix

        Returns:
            Diversification multiplier
        """
        w = weights.to_numpy().reshape(-1, 1)
        corr = correlation_matrix.to_numpy()

        # Portfolio variance (assuming equal volatilities)
        portfolio_var = (w.T @ corr @ w)[0, 0]

        if portfolio_var <= 0:
            logger.warning("Non-positive portfolio variance, returning IDM=1")
            return 1.0

        # IDM is inverse of portfolio volatility (when individual vols = 1)
        idm = 1 / np.sqrt(portfolio_var)

        logger.debug(
            f"IDM calculation: portfolio_var={portfolio_var:.4f}, IDM={idm:.4f}"
        )

        return float(idm)

    @staticmethod
    def calculate_equal_weights(
            n_instruments: int,
            avg_correlation: float,
    ) -> float:
        """
        Calculate IDM assuming equal weights and constant correlation.

        Args:
            n_instruments: Number of instruments
            avg_correlation: Average pairwise correlation

        Returns:
            Approximate diversification multiplier
        """
        if n_instruments <= 0:
            return 1.0

        # Simplified formula for equal weights and constant correlation
        # IDM ≈ sqrt(N) / sqrt(1 + (N-1)*avg_corr)
        numerator = np.sqrt(n_instruments)
        denominator = np.sqrt(1 + (n_instruments - 1) * avg_correlation)

        idm = numerator / denominator if denominator > 0 else 1.0

        logger.debug(
            f"Equal weight IDM: N={n_instruments}, "
            f"avg_corr={avg_correlation:.3f}, IDM={idm:.4f}"
        )

        return float(idm)


# ---- Risk Calculator ---- #


class RiskCalculator:
    """
    Calculate position and portfolio risk metrics.
    Core risk measurement for Carver's system.
    """

    def __init__(self, config: Optional[RiskConfig] = None):
        self.config = config or RiskConfig()

    def position_risk(
            self,
            position_size: float,
            instrument_price: float,
            volatility: float,
            capital: float,
    ) -> float:
        """
        Calculate position risk as percentage of capital.

        Args:
            position_size: Number of contracts/shares
            instrument_price: Current price
            volatility: Annual volatility (decimal)
            capital: Total capital

        Returns:
            Position risk as decimal (e.g., 0.15 for 15%)
        """
        if capital <= 0:
            logger.warning("Invalid capital for risk calculation")
            return 0.0

        notional = abs(position_size * instrument_price)
        position_risk_pct = (notional * volatility) / capital

        return position_risk_pct

    def portfolio_risk(
            self,
            positions: Dict[str, float],
            prices: Dict[str, float],
            volatilities: Dict[str, float],
            correlation_matrix: pl.DataFrame,
            capital: float,
    ) -> PortfolioRisk:
        """
        Calculate comprehensive portfolio risk metrics.

        Args:
            positions: Dict of ticker -> position size
            prices: Dict of ticker -> current price
            volatilities: Dict of ticker -> annual volatility
            correlation_matrix: Correlation matrix
            capital: Total capital

        Returns:
            PortfolioRisk object
        """
        if capital <= 0:
            raise ValueError("Capital must be positive")

        tickers = list(positions.keys())
        n_instruments = len(tickers)

        # Calculate individual position risks
        position_risks = {}
        position_values = []

        for ticker in tickers:
            pos_size = positions[ticker]
            price = prices.get(ticker, 0)
            vol = volatilities.get(ticker, 0)

            risk = self.position_risk(pos_size, price, vol, capital)
            position_risks[ticker] = risk
            position_values.append(abs(pos_size * price))

        # Calculate exposures
        gross_exposure = sum(position_values)
        net_exposure = sum(
            positions[t] * prices.get(t, 0) for t in tickers
        )

        # Portfolio volatility (correlation-adjusted)
        portfolio_vol = self._calculate_portfolio_volatility(
            position_risks, correlation_matrix, tickers
        )

        # Diversification multiplier
        weights = self._calculate_weights(position_values)
        idm = DiversificationMultiplier.calculate(
            pl.Series(weights), correlation_matrix
        )

        # Portfolio risk
        portfolio_risk_pct = portfolio_vol

        # Leverage
        leverage = gross_exposure / capital if capital > 0 else 0

        return PortfolioRisk(
            total_capital=capital,
            gross_exposure=gross_exposure,
            net_exposure=net_exposure,
            portfolio_volatility=portfolio_vol,
            portfolio_risk=portfolio_risk_pct,
            diversification_multiplier=idm,
            leverage=leverage,
            num_instruments=n_instruments,
            instrument_risks=position_risks,
        )

    def _calculate_portfolio_volatility(
            self,
            position_risks: Dict[str, float],
            correlation_matrix: pl.DataFrame,
            tickers: List[str],
    ) -> float:
        """Calculate portfolio volatility from position risks and correlations."""
        if not position_risks:
            return 0.0

        # Position risks as vector
        risks = np.array([position_risks[t] for t in tickers])

        # Correlation matrix
        corr = correlation_matrix.to_numpy()

        # Portfolio variance = r^T * C * r
        portfolio_var = risks @ corr @ risks.T

        return np.sqrt(portfolio_var) if portfolio_var > 0 else 0.0

    @staticmethod
    def _calculate_weights(position_values: List[float]) -> List[float]:
        """Calculate normalized weights from position values."""
        total = sum(position_values)
        if total <= 0:
            return [0.0] * len(position_values)
        return [v / total for v in position_values]


# ---- Position Limits ---- #


class PositionLimits:
    """
    Apply position limits and constraints.
    Prevents excessive risk concentration.
    """

    def __init__(self, config: Optional[RiskConfig] = None):
        self.config = config or RiskConfig()

    def check_forecast_limit(self, forecast: float) -> Tuple[bool, float]:
        """
        Check if forecast exceeds limits.

        Args:
            forecast: Forecast value

        Returns:
            (is_valid, capped_forecast)
        """
        max_f = self.config.max_forecast

        if abs(forecast) > max_f:
            capped = np.sign(forecast) * max_f
            logger.warning(
                f"Forecast {forecast:.2f} exceeds limit ±{max_f:.2f}, "
                f"capped to {capped:.2f}"
            )
            return False, capped

        return True, forecast

    def check_instrument_risk(
            self, position_risk: float, ticker: str = ""
    ) -> bool:
        """
        Check if position risk exceeds instrument limit.

        Args:
            position_risk: Position risk as decimal
            ticker: Instrument identifier

        Returns:
            True if within limits
        """
        max_risk = self.config.max_instrument_risk

        if position_risk > max_risk:
            logger.warning(
                f"{ticker or 'Position'} risk {position_risk:.2%} "
                f"exceeds limit {max_risk:.2%}"
            )
            return False

        return True

    def check_portfolio_risk(self, portfolio_risk: float) -> bool:
        """
        Check if portfolio risk exceeds limit.

        Args:
            portfolio_risk: Portfolio risk as decimal

        Returns:
            True if within limits
        """
        max_risk = self.config.max_portfolio_risk

        if portfolio_risk > max_risk:
            logger.warning(
                f"Portfolio risk {portfolio_risk:.2%} exceeds limit {max_risk:.2%}"
            )
            return False

        return True

    def check_leverage(self, leverage: float) -> bool:
        """
        Check if leverage exceeds limit.

        Args:
            leverage: Portfolio leverage

        Returns:
            True if within limits
        """
        max_lev = self.config.max_leverage

        if leverage > max_lev:
            logger.warning(
                f"Leverage {leverage:.2f}x exceeds limit {max_lev:.2f}x"
            )
            return False

        return True

    def scale_for_risk_limit(
            self,
            current_risk: float,
            target_risk: float,
            position_size: float,
    ) -> float:
        """
        Scale position to meet risk target.

        Args:
            current_risk: Current position risk
            target_risk: Target risk level
            position_size: Current position size

        Returns:
            Scaled position size
        """
        if current_risk <= 0:
            return position_size

        scale_factor = target_risk / current_risk
        scaled_position = position_size * scale_factor

        logger.debug(
            f"Risk scaling: {current_risk:.2%} -> {target_risk:.2%}, "
            f"factor={scale_factor:.4f}"
        )

        return scaled_position


# ---- Capital Allocation ---- #


class CapitalAllocator:
    """
    Allocate capital across instruments.
    Supports equal weighting, risk parity, and custom allocations.
    """

    @staticmethod
    def equal_weight(tickers: List[str], total_capital: float) -> Dict[str, float]:
        """
        Allocate capital equally across instruments.

        Args:
            tickers: List of instrument tickers
            total_capital: Total capital to allocate

        Returns:
            Dict mapping ticker to allocated capital
        """
        n = len(tickers)
        if n == 0:
            return {}

        per_instrument = total_capital / n

        allocation = {ticker: per_instrument for ticker in tickers}

        logger.info(
            f"Equal weight allocation: {n} instruments, "
            f"{per_instrument:.2f} each"
        )

        return allocation

    @staticmethod
    def risk_parity(
            tickers: List[str],
            volatilities: Dict[str, float],
            total_capital: float,
    ) -> Dict[str, float]:
        """
        Allocate capital for equal risk contribution (inverse volatility weighting).

        Args:
            tickers: List of tickers
            volatilities: Dict of ticker -> volatility
            total_capital: Total capital

        Returns:
            Dict of capital allocations
        """
        # Inverse volatility weights
        inv_vols = [1 / volatilities.get(t, 1.0) for t in tickers]
        total_inv_vol = sum(inv_vols)

        if total_inv_vol <= 0:
            logger.warning("Invalid volatilities for risk parity, using equal weight")
            return CapitalAllocator.equal_weight(tickers, total_capital)

        # Normalize to weights
        weights = [iv / total_inv_vol for iv in inv_vols]

        # Allocate capital
        allocation = {
            ticker: total_capital * weight
            for ticker, weight in zip(tickers, weights)
        }

        logger.info(f"Risk parity allocation: {len(tickers)} instruments")

        return allocation

    @staticmethod
    def custom_weights(
            weights: Dict[str, float],
            total_capital: float,
    ) -> Dict[str, float]:
        """
        Allocate capital using custom weights.

        Args:
            weights: Dict of ticker -> weight (should sum to 1)
            total_capital: Total capital

        Returns:
            Dict of capital allocations
        """
        # Normalize weights
        total_weight = sum(weights.values())
        if total_weight <= 0:
            logger.warning("Invalid weights, using equal allocation")
            return CapitalAllocator.equal_weight(
                list(weights.keys()), total_capital
            )

        normalized = {
            ticker: w / total_weight for ticker, w in weights.items()
        }

        allocation = {
            ticker: total_capital * weight
            for ticker, weight in normalized.items()
        }

        logger.info(f"Custom allocation: {len(weights)} instruments")

        return allocation


# ---- Risk Monitor ---- #


class RiskMonitor:
    """
    Monitor and report on portfolio risk in real-time.
    """

    def __init__(self, config: Optional[RiskConfig] = None):
        self.config = config or RiskConfig()
        self.calculator = RiskCalculator(config)
        self.limits = PositionLimits(config)

    def check_all_limits(
            self, portfolio_risk: PortfolioRisk
    ) -> Dict[str, bool]:
        """
        Check all risk limits.

        Args:
            portfolio_risk: Portfolio risk metrics

        Returns:
            Dict of check_name -> passed
        """
        checks = {}

        # Portfolio risk
        checks["portfolio_risk"] = self.limits.check_portfolio_risk(
            portfolio_risk.portfolio_risk
        )

        # Leverage
        checks["leverage"] = self.limits.check_leverage(
            portfolio_risk.leverage
        )

        # Instrument risks
        for ticker, risk in portfolio_risk.instrument_risks.items():
            checks[f"instrument_risk_{ticker}"] = (
                self.limits.check_instrument_risk(risk, ticker)
            )

        return checks

    def generate_report(self, portfolio_risk: PortfolioRisk) -> str:
        """
        Generate risk report.

        Args:
            portfolio_risk: Portfolio risk metrics

        Returns:
            Formatted risk report
        """
        report_lines = [
            "=" * 60,
            "PORTFOLIO RISK REPORT",
            "=" * 60,
            f"Capital: ${portfolio_risk.total_capital:,.2f}",
            f"Gross Exposure: ${portfolio_risk.gross_exposure:,.2f}",
            f"Net Exposure: ${portfolio_risk.net_exposure:,.2f}",
            f"Leverage: {portfolio_risk.leverage:.2f}x",
            f"Portfolio Risk: {portfolio_risk.portfolio_risk:.2%}",
            f"Portfolio Volatility: {portfolio_risk.portfolio_volatility:.2%}",
            f"Diversification Multiplier: {portfolio_risk.diversification_multiplier:.3f}",
            f"Number of Instruments: {portfolio_risk.num_instruments}",
            f"Concentration Ratio: {portfolio_risk.concentration_ratio:.3f}",
            "",
            "Instrument Risk Breakdown:",
            "-" * 60,
        ]

        for ticker, risk in sorted(
                portfolio_risk.instrument_risks.items(),
                key=lambda x: x[1],
                reverse=True,
        ):
            status = "✓" if risk <= self.config.max_instrument_risk else "✗"
            report_lines.append(f"{status} {ticker:10s}: {risk:6.2%}")

        report_lines.extend([
            "",
            "Risk Limits:",
            "-" * 60,
            f"Max Instrument Risk: {self.config.max_instrument_risk:.2%}",
            f"Max Portfolio Risk: {self.config.max_portfolio_risk:.2%}",
            f"Max Leverage: {self.config.max_leverage:.2f}x",
            "=" * 60,
        ])

        return "\n".join(report_lines)


# ---- Risk Manager (Main Interface) ---- #


class RiskManager:
    """
    Main interface for risk management.
    Coordinates correlation estimation, risk calculation, and monitoring.
    """

    def __init__(self, config: Optional[RiskConfig] = None):
        self.config = config or RiskConfig()
        self.correlation_estimator = CorrelationEstimator(
            lookback=self.config.correlation_lookback,
            min_samples=self.config.min_correlation_samples,
        )
        self.calculator = RiskCalculator(self.config)
        self.limits = PositionLimits(self.config)
        self.monitor = RiskMonitor(self.config)
        self.allocator = CapitalAllocator()

    def estimate_correlations(
            self, returns_df: pl.DataFrame, method: str = "standard"
    ) -> pl.DataFrame:
        """
        Estimate correlation matrix.

        Args:
            returns_df: DataFrame of returns
            method: 'standard' or 'ewma'

        Returns:
            Correlation matrix
        """
        if method == "ewma":
            return self.correlation_estimator.ewma_correlation(returns_df)
        else:
            return self.correlation_estimator.estimate(returns_df)

    def calculate_portfolio_risk(
            self,
            positions: Dict[str, float],
            prices: Dict[str, float],
            volatilities: Dict[str, float],
            correlation_matrix: pl.DataFrame,
            capital: float,
    ) -> PortfolioRisk:
        """
        Calculate comprehensive portfolio risk.

        Args:
            positions: Dict of ticker -> position size
            prices: Dict of ticker -> price
            volatilities: Dict of ticker -> annual volatility
            correlation_matrix: Correlation matrix
            capital: Total capital

        Returns:
            PortfolioRisk object
        """
        return self.calculator.portfolio_risk(
            positions, prices, volatilities, correlation_matrix, capital
        )

    def allocate_capital(
            self,
            tickers: List[str],
            total_capital: float,
            method: str = "equal",
            volatilities: Optional[Dict[str, float]] = None,
            custom_weights: Optional[Dict[str, float]] = None,
    ) -> Dict[str, float]:
        """
        Allocate capital across instruments.

        Args:
            tickers: List of tickers
            total_capital: Total capital to allocate
            method: 'equal', 'risk_parity', or 'custom'
            volatilities: Required for risk_parity
            custom_weights: Required for custom allocation

        Returns:
            Dict of capital allocations
        """
        if method == "equal":
            return self.allocator.equal_weight(tickers, total_capital)
        elif method == "risk_parity":
            if not volatilities:
                raise ValueError("Volatilities required for risk parity")
            return self.allocator.risk_parity(
                tickers, volatilities, total_capital
            )
        elif method == "custom":
            if not custom_weights:
                raise ValueError("Custom weights required for custom allocation")
            return self.allocator.custom_weights(custom_weights, total_capital)
        else:
            raise ValueError(f"Unknown allocation method: {method}")

    def check_limits(
            self, portfolio_risk: PortfolioRisk
    ) -> Tuple[bool, Dict[str, bool]]:
        """
        Check all risk limits.

        Args:
            portfolio_risk: Portfolio risk metrics

        Returns:
            (all_passed, detailed_checks)
        """
        checks = self.monitor.check_all_limits(portfolio_risk)
        all_passed = all(checks.values())
        return all_passed, checks

    def get_risk_report(self, portfolio_risk: PortfolioRisk) -> str:
        """
        Generate formatted risk report.

        Args:
            portfolio_risk: Portfolio risk metrics

        Returns:
            Risk report string
        """
        return self.monitor.generate_report(portfolio_risk)


# ---- Utility Functions ---- #


def calculate_var(
        returns: pl.Series, confidence_level: float = 0.95
) -> float:
    """
    Calculate Value at Risk (VaR).

    Args:
        returns: Series of returns
        confidence_level: Confidence level (e.g., 0.95 for 95%)

    Returns:
        VaR as positive number (potential loss)
    """
    if len(returns) == 0:
        return 0.0

    quantile = 1 - confidence_level
    var = -returns.quantile(quantile)

    return float(var) if var is not None else 0.0


def calculate_cvar(
        returns: pl.Series, confidence_level: float = 0.95
) -> float:
    """
    Calculate Conditional Value at Risk (CVaR / Expected Shortfall).

    Args:
        returns: Series of returns
        confidence_level: Confidence level

    Returns:
        CVaR as positive number
    """
    if len(returns) == 0:
        return 0.0

    var = calculate_var(returns, confidence_level)
    # Average of returns worse than VaR
    tail_returns = returns.filter(returns <= -var)

    if len(tail_returns) == 0:
        return var

    cvar = -tail_returns.mean()

    return float(cvar) if cvar is not None else var


def calculate_sharpe_ratio(
        returns: pl.Series, risk_free_rate: float = 0.0
) -> float:
    """
    Calculate Sharpe ratio.

    Args:
        returns: Series of returns
        risk_free_rate: Annual risk-free rate

    Returns:
        Sharpe ratio
    """
    if len(returns) == 0:
        return 0.0

    mean_return = returns.mean()
    std_return = returns.std()

    if std_return is None or std_return <= 0:
        return 0.0

    # Annualize (assuming daily returns)
    annual_return = mean_return * Settings.BUSINESS_DAYS_PER_YEAR
    annual_vol = std_return * np.sqrt(Settings.BUSINESS_DAYS_PER_YEAR)

    sharpe = (annual_return - risk_free_rate) / annual_vol

    return float(sharpe) if sharpe is not None else 0.0


def calculate_max_drawdown(prices: pl.Series) -> Tuple[float, int, int]:
    """
    Calculate maximum drawdown.

    Args:
        prices: Series of prices

    Returns:
        (max_drawdown, peak_idx, trough_idx)
    """
    if len(prices) == 0:
        return 0.0, 0, 0

    # Calculate running maximum
    cummax = prices.cum_max()

    # Drawdown at each point
    drawdown = (prices - cummax) / cummax

    # Find maximum drawdown
    max_dd = drawdown.min()
    max_dd = float(max_dd) if max_dd is not None else 0.0

    # Find indices
    trough_idx = drawdown.arg_min()
    peak_idx = prices[:trough_idx].arg_max() if trough_idx > 0 else 0

    return abs(max_dd), peak_idx, trough_idx
