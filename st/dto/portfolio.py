"""
Portfolio layer for systematic trading using Carver's methodology.

This module coordinates multiple instruments at the portfolio level:
- Instrument bundling (InstrumentDTO)
- Instrument weighting (InstrumentWeightsDTO)
- Diversification multiplier calculation (InstrumentDiversificationMultiplierDTO)
- Portfolio aggregation (PortfolioDTO)
- Risk budget validation

Key concepts:
- IDM (Instrument Diversification Multiplier): Quantifies diversification benefit
- Instrument weights: Portfolio allocation across instruments (must sum to 1.0)
- Risk budgeting: Ensure portfolio risk matches target
"""
from copy import deepcopy
from typing import Any, Literal, Optional

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from utils.logger import setup_logger
from .data import PriceDataDTO, ReturnsDTO
from .forecast import CombinedForecastDTO
from .position import PortfolioRiskTargetDTO, InstrumentPositionDTO
from .volatility import VolatilityDTO, VolatilityStandardizationDTO

logger = setup_logger(__name__)


# ============================================================================
# Instrument Bundling
# ============================================================================

class InstrumentDTO(BaseModel):
    """
    Complete data bundle for a single instrument.

    Aggregates all instrument-level components:
    - Price data and returns
    - Volatility estimation
    - Strategy forecasts
    - Combined forecast

    This is the fundamental unit that gets fed into PortfolioDTO.

    Attributes:
        ticker: Instrument identifier (e.g., 'AAPL', 'ES', 'EURUSD')
        price_data: OHLCV price data
        returns: Calculated returns from price data
        volatility_standardization: Volatility model with returns
        combined_forecast: Weighted combination of strategy forecasts
        fx_rate: Conversion rate from instrument currency to account currency
    """
    ticker: str
    price_data: PriceDataDTO
    returns: ReturnsDTO = None
    volatility_standardization: VolatilityStandardizationDTO = None
    combined_forecast: CombinedForecastDTO = None
    fx_rate: float = Field(
        default=1.0,
        gt=0,
        description="FX rate: instrument_currency per account_currency"
    )

    class Config:
        arbitrary_types_allowed = True

    def model_post_init(self, __context: Any):
        self.price_data = deepcopy(self.price_data)
        self.returns = ReturnsDTO(price_data=self.price_data)
        self.volatility_standardization = VolatilityStandardizationDTO(
            price_data=self.price_data
        )
        logger.info(f"Creation completed: {self}")

    @property
    def volatility(self) -> VolatilityDTO:
        """Convenience property to access volatility model."""
        return self.volatility_standardization.volatility

    @property
    def strategies(self) -> dict:
        """Convenience property to access strategies from combined forecast."""
        if self.combined_forecast is None:
            return {}
        return self.combined_forecast.strategies

    def __str__(self):
        n_strategies = len(self.strategies) if self.combined_forecast else 0
        return (
            f"Instrument(ticker={self.ticker}, "
            f"strategies={n_strategies}, "
            f"fx_rate={self.fx_rate})"
        )

    __repr__ = __str__


# ============================================================================
# Instrument Weighting
# ============================================================================

class InstrumentWeightsDTO(BaseModel):
    """
    Portfolio allocation weights across instruments.

    Carver's approaches (Systematic Trading, Ch 12):
    1. Equal weights: 1/N for each instrument (simple, robust)
    2. Handcrafted: Expert-determined weights
    3. Optimized: Historical optimization (not recommended by Carver)

    Attributes:
        instruments: List of instrument tickers
        weights: Dict mapping ticker -> weight (must sum to 1.0)
        method: Weighting approach used

    Validation:
        - All weights must be positive
        - Weights must sum to 1.0 (within tolerance)
        - All instruments must have weights
    """
    instruments: list[str]
    weights: dict[str, float] = Field(default_factory=dict)
    method: Literal["equal", "handcrafted", "optimized"] = Field(
        default="equal",
        description="Method used to determine weights"
    )
    auto_equal_weight: bool = Field(
        default=True,
        description="Automatically assign equal weights if weights not provided"
    )

    class Config:
        arbitrary_types_allowed = True

    def model_post_init(self, __context: Any):
        # Auto-generate equal weights if not provided
        if self.auto_equal_weight and not self.weights:
            n_instruments = len(self.instruments)
            equal_weight = 1.0 / n_instruments
            self.weights = {ticker: equal_weight for ticker in self.instruments}
            logger.info(f"Auto-assigned equal weights: {equal_weight:.4f} each")

        # Validation
        self._validate_weights()

        logger.info(f"Creation completed: {self}")

    def _validate_weights(self):
        """Validate weight constraints."""
        # Check all instruments have weights
        if set(self.weights.keys()) != set(self.instruments):
            missing = set(self.instruments) - set(self.weights.keys())
            extra = set(self.weights.keys()) - set(self.instruments)
            raise ValueError(
                f"Weight/instrument mismatch. "
                f"Missing: {missing}, Extra: {extra}"
            )

        # Check all weights are positive
        negative_weights = {
            ticker: w for ticker, w in self.weights.items() if w <= 0
        }
        if negative_weights:
            raise ValueError(
                f"All weights must be positive, got: {negative_weights}"
            )

        # Check weights sum to 1.0 (with tolerance)
        total_weight = sum(self.weights.values())
        if not np.isclose(total_weight, 1.0, atol=1e-6):
            raise ValueError(
                f"Weights must sum to 1.0, got {total_weight:.6f}. "
                f"Weights: {self.weights}"
            )

    def get_weight(self, ticker: str) -> float:
        """Get weight for specific instrument."""
        if ticker not in self.weights:
            raise ValueError(f"No weight for ticker: {ticker}")
        return self.weights[ticker]

    def __str__(self):
        weight_str = ", ".join(
            f"{ticker}={w:.3f}" for ticker, w in self.weights.items()
        )
        return f"InstrumentWeights(method={self.method}, {weight_str})"

    __repr__ = __str__


# ============================================================================
# Instrument Diversification Multiplier (IDM)
# ============================================================================

class InstrumentDiversificationMultiplierDTO(BaseModel):
    """
    Calculate Instrument Diversification Multiplier (IDM) from correlations.

    Carver's formula (Systematic Trading, Ch 12):
        IDM = 1 / sqrt(sum of weighted correlation matrix)

    Where:
        - Correlations are between instrument **returns** (not forecasts)
        - Weights are instrument portfolio weights
        - IDM quantifies diversification benefit

    Typical ranges:
        - IDM = 1.0: No diversification (single instrument or perfect correlation)
        - IDM = 1.5: Moderate diversification
        - IDM = 2.5: High diversification (many uncorrelated instruments)

    Note: IDM is different from FDM (Forecast Diversification Multiplier)
        - FDM: Diversification of forecasts **within** an instrument
        - IDM: Diversification of instruments **across** portfolio

    Attributes:
        instrument_weights: Portfolio weights for instruments
        return_correlations: Correlation matrix of instrument returns
        idm: Calculated diversification multiplier
    """
    instrument_weights: InstrumentWeightsDTO
    return_correlations: pd.DataFrame
    idm: float = Field(default=1.0, description="Calculated IDM value")

    class Config:
        arbitrary_types_allowed = True

    def model_post_init(self, __context: Any):
        # Deep copy to avoid mutations
        self.return_correlations = deepcopy(self.return_correlations)

        # Validate inputs
        self._validate_inputs()

        # Calculate IDM
        self.idm = self._calculate_idm()

        logger.info(f"Creation completed: {self}")

    def _validate_inputs(self):
        """Validate correlation matrix and weights alignment."""
        # Check correlation matrix is square
        if self.return_correlations.shape[0] != self.return_correlations.shape[1]:
            raise ValueError(
                f"Correlation matrix must be square, got shape: "
                f"{self.return_correlations.shape}"
            )

        # Check instruments match
        corr_instruments = set(self.return_correlations.columns)
        weight_instruments = set(self.instrument_weights.instruments)

        if corr_instruments != weight_instruments:
            raise ValueError(
                f"Correlation matrix instruments {corr_instruments} "
                f"don't match weight instruments {weight_instruments}"
            )

        # Check for NaN values
        if self.return_correlations.isna().any().any():
            raise ValueError("Correlation matrix contains NaN values")

    def _calculate_idm(self) -> float:
        """
        Calculate IDM using Carver's formula.

        Formula:
            IDM = 1 / sqrt(w^T * Corr * w)

        Where:
            w = vector of instrument weights
            Corr = correlation matrix of instrument returns
        """
        # Extract weights in same order as correlation matrix
        weight_vector = np.array([
            self.instrument_weights.weights[ticker]
            for ticker in self.return_correlations.columns
        ])

        # Calculate weighted correlation: w^T * Corr * w
        corr_matrix = self.return_correlations.values
        weighted_corr = weight_vector @ corr_matrix @ weight_vector

        # IDM = 1 / sqrt(weighted_correlation)
        if weighted_corr <= 0:
            logger.warning(
                f"Weighted correlation is non-positive: {weighted_corr}. "
                "Setting IDM = 1.0"
            )
            return 1.0

        idm = 1.0 / np.sqrt(weighted_corr)

        # Sanity check: IDM should typically be between 1.0 and 2.5
        if idm < 0.9:
            logger.warning(
                f"IDM = {idm:.4f} is unusually low. "
                "Check your correlation matrix."
            )
        elif idm > 3.0:
            logger.warning(
                f"IDM = {idm:.4f} is unusually high. "
                "This suggests negative correlations or errors."
            )

        return idm

    def get_diversification_ratio(self) -> float:
        """
        Get diversification ratio: (actual IDM) / (max possible IDM).

        Max possible IDM occurs with zero correlations = sqrt(N).
        Ratio of 1.0 = perfect diversification, 0.0 = no diversification.

        Returns:
            Diversification ratio between 0 and 1
        """
        n_instruments = len(self.instrument_weights.instruments)
        max_idm = np.sqrt(n_instruments)

        if max_idm == 0:
            return 0.0

        return min(self.idm / max_idm, 1.0)

    def __str__(self):
        n_instruments = len(self.instrument_weights.instruments)
        div_ratio = self.get_diversification_ratio()
        return (
            f"IDM(value={self.idm:.4f}, "
            f"instruments={n_instruments}, "
            f"diversification={div_ratio:.2%})"
        )

    __repr__ = __str__


# ============================================================================
# Portfolio Aggregation
# ============================================================================

class PortfolioDTO(BaseModel):
    """
    Portfolio-level coordination of multiple instruments.

    This is the central coordinator that:
    1. Aggregates all instruments
    2. Calculates instrument return correlations
    3. Determines instrument weights
    4. Calculates IDM (Instrument Diversification Multiplier)
    5. Sizes positions for each instrument
    6. Validates risk budget

    Carver's framework (Systematic Trading, Ch 11-12):
    - Equal weights across instruments (default)
    - IDM accounts for diversification benefit
    - Portfolio risk target is met through proper position sizing

    Attributes:
        instruments: Dict mapping ticker -> InstrumentDTO
        portfolio_risk_target: Portfolio-level risk parameters
        weighting_method: How to allocate across instruments
        handcrafted_weights: Optional manual weight specification

    Computed attributes:
        instrument_correlations: Correlation matrix of returns
        instrument_weights: Allocation weights per instrument
        idm_calculator: IDM calculation details
        instrument_positions: Position sizing per instrument
    """
    # Inputs
    instruments: dict[str, InstrumentDTO]
    portfolio_risk_target: PortfolioRiskTargetDTO
    weighting_method: Literal["equal", "handcrafted"] = Field(
        default="equal",
        description="Method for determining instrument weights"
    )
    handcrafted_weights: Optional[dict[str, float]] = Field(
        default=None,
        description="Manual weight specification (if method='handcrafted')"
    )

    # Computed fields
    instrument_correlations: pd.DataFrame = None
    instrument_weights: InstrumentWeightsDTO = None
    idm_calculator: InstrumentDiversificationMultiplierDTO = None
    instrument_positions: dict[str, InstrumentPositionDTO] = None
    portfolio_metrics: dict = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True

    def model_post_init(self, __context: Any):
        # Validation
        if not self.instruments:
            raise ValueError("Portfolio must contain at least one instrument")

        # Deep copy to avoid mutations
        self.instruments = {
            ticker: deepcopy(inst)
            for ticker, inst in self.instruments.items()
        }

        # Step 1: Calculate instrument return correlations
        logger.info("Calculating instrument correlations...")
        self.instrument_correlations = self._calculate_correlations()

        # Step 2: Determine instrument weights
        logger.info("Determining instrument weights...")
        self.instrument_weights = self._determine_weights()

        # Step 3: Calculate IDM
        logger.info("Calculating IDM...")
        self.idm_calculator = InstrumentDiversificationMultiplierDTO(
            instrument_weights=self.instrument_weights,
            return_correlations=self.instrument_correlations
        )

        # Step 4: Calculate positions for each instrument
        logger.info("Calculating instrument positions...")
        self.instrument_positions = self._calculate_positions()

        # Step 5: Calculate portfolio metrics
        logger.info("Calculating portfolio metrics...")
        self.portfolio_metrics = self._calculate_portfolio_metrics()

        # Step 6: Validate risk budget
        logger.info("Validating risk budget...")
        self._validate_risk_budget()

        logger.info(f"Creation completed: {self}")

    def _calculate_correlations(self) -> pd.DataFrame:
        """
        Calculate pairwise correlations of instrument returns.

        Returns correlation matrix with tickers as both index and columns.
        """
        # Collect returns from each instrument
        returns_dict = {}
        for ticker, instrument in self.instruments.items():
            if instrument.returns is None or instrument.returns.returns is None:
                raise ValueError(
                    f"Instrument {ticker} missing returns. "
                    "Ensure ReturnsDTO is properly initialized."
                )
            returns_dict[ticker] = instrument.returns.returns

        # Create returns DataFrame (aligned by date)
        returns_df = pd.DataFrame(returns_dict)

        # Drop rows with any NaN (ensures proper correlation calculation)
        returns_df = returns_df.dropna()

        if len(returns_df) < 30:
            logger.warning(
                f"Only {len(returns_df)} aligned observations for correlation. "
                "Consider longer data history for reliable correlations."
            )

        # Calculate correlation matrix
        corr_matrix = returns_df.corr()

        logger.info(
            f"Calculated correlations from {len(returns_df)} observations"
        )

        return corr_matrix

    def _determine_weights(self) -> InstrumentWeightsDTO:
        """Determine portfolio weights based on weighting method."""
        tickers = list(self.instruments.keys())

        if self.weighting_method == "equal":
            # Equal weighting (Carver's default)
            weights = InstrumentWeightsDTO(
                instruments=tickers,
                method="equal",
                auto_equal_weight=True
            )
        elif self.weighting_method == "handcrafted":
            # Manual weights
            if self.handcrafted_weights is None:
                raise ValueError(
                    "Must provide handcrafted_weights when "
                    "weighting_method='handcrafted'"
                )
            weights = InstrumentWeightsDTO(
                instruments=tickers,
                weights=self.handcrafted_weights,
                method="handcrafted",
                auto_equal_weight=False
            )
        else:
            raise ValueError(
                f"Unknown weighting_method: {self.weighting_method}"
            )

        return weights

    def _calculate_positions(self) -> dict[str, InstrumentPositionDTO]:
        """
        Calculate position sizing for each instrument.

        Uses:
        - Combined forecast from instrument
        - Instrument volatility
        - Instrument price
        - Portfolio risk target
        - Instrument weight (from portfolio)
        - IDM (from portfolio)
        - FX rate

        Returns dict mapping ticker -> InstrumentPositionDTO.
        """
        positions = {}

        for ticker, instrument in self.instruments.items():
            # Validate instrument has combined forecast
            if instrument.combined_forecast is None:
                raise ValueError(
                    f"Instrument {ticker} missing combined_forecast. "
                    "Create CombinedForecastDTO before building portfolio."
                )

            # Get instrument weight from portfolio
            instrument_weight = self.instrument_weights.get_weight(ticker)

            # Create position DTO
            position = InstrumentPositionDTO(
                combined_forecast=instrument.combined_forecast.combined_forecast,
                instrument_volatility=instrument.volatility.annual_vol,
                price=instrument.price_data.data['Close'],
                portfolio_risk_target=self.portfolio_risk_target,
                instrument_weight=instrument_weight,
                idm=self.idm_calculator.idm,
                fx_rate=instrument.fx_rate
            )

            positions[ticker] = position

            logger.info(
                f"  {ticker}: weight={instrument_weight:.3f}, "
                f"mean_position={position.position.mean():.2f}"
            )

        return positions

    def _calculate_portfolio_metrics(self) -> dict:
        """
        Calculate portfolio-level metrics.

        Returns dict with:
        - expected_portfolio_vol: Theoretical portfolio volatility
        - position_counts: Number of positions per instrument
        - total_positions: Sum of absolute positions across instruments
        - capital_usage: Fraction of capital deployed
        """
        metrics = {}

        # Get latest volatilities and weights
        vols = []
        weights = []
        for ticker in self.instruments.keys():
            instrument = self.instruments[ticker]
            # Use latest annual volatility
            latest_vol = instrument.volatility.annual_vol.iloc[-1]
            vols.append(latest_vol)
            weights.append(self.instrument_weights.weights[ticker])

        vols = np.array(vols)
        weights = np.array(weights)

        # Calculate expected portfolio volatility
        # Portfolio var = w^T * (vol * vol^T * Corr) * w
        corr_matrix = self.instrument_correlations.values

        # Create covariance matrix from volatilities and correlations
        vol_outer = np.outer(vols, vols)
        cov_matrix = vol_outer * corr_matrix

        # Portfolio variance
        portfolio_var = weights @ cov_matrix @ weights
        portfolio_vol = np.sqrt(portfolio_var)

        metrics['expected_portfolio_vol'] = portfolio_vol
        metrics['target_portfolio_vol'] = (
            self.portfolio_risk_target.annual_volatility_target
        )
        metrics['vol_ratio'] = (
                portfolio_vol / self.portfolio_risk_target.annual_volatility_target
        )

        # Position counts
        position_counts = {
            ticker: (pos.position != 0).sum()
            for ticker, pos in self.instrument_positions.items()
        }
        metrics['position_counts'] = position_counts

        # Total positions (sum of absolute values across instruments)
        total_positions = sum(
            pos.position.abs().iloc[-1]
            for pos in self.instrument_positions.values()
        )
        metrics['total_positions'] = total_positions

        # Number of instruments
        metrics['n_instruments'] = len(self.instruments)

        # IDM value
        metrics['idm'] = self.idm_calculator.idm
        metrics['diversification_ratio'] = (
            self.idm_calculator.get_diversification_ratio()
        )

        return metrics

    def _validate_risk_budget(self):
        """
        Validate that portfolio risk is reasonable.

        This is a sanity check. Due to forecast scaling and IDM effects,
        realized portfolio volatility may differ from target by ±20%.

        Carver: "Don't worry if the actual portfolio vol doesn't exactly
        match your target. The system is approximate by design."
        """
        expected_vol = self.portfolio_metrics['expected_portfolio_vol']
        target_vol = self.portfolio_metrics['target_portfolio_vol']
        ratio = self.portfolio_metrics['vol_ratio']

        # Allow 50% tolerance (Carver is pragmatic about this)
        if ratio < 0.5 or ratio > 1.5:
            logger.warning(
                f"\n{'=' * 70}\n"
                f"RISK BUDGET MISMATCH\n"
                f"{'=' * 70}\n"
                f"Expected portfolio vol: {expected_vol:.2%}\n"
                f"Target portfolio vol:   {target_vol:.2%}\n"
                f"Ratio:                  {ratio:.2f}x\n"
                f"\n"
                f"This is outside the normal range (0.5x - 1.5x).\n"
                f"Possible causes:\n"
                f"  - IDM is very high/low (check correlations)\n"
                f"  - Forecast scaling issues\n"
                f"  - Volatility estimation problems\n"
                f"{'=' * 70}\n"
            )
        else:
            logger.info(
                f"Risk budget OK: expected={expected_vol:.2%} vs "
                f"target={target_vol:.2%} (ratio={ratio:.2f}x)"
            )

    def get_portfolio_summary(self) -> str:
        """
        Get a formatted summary of portfolio composition and metrics.

        Returns:
            Multi-line string with portfolio details
        """
        lines = [
            "\n" + "=" * 70,
            "PORTFOLIO SUMMARY",
            "=" * 70,
            f"\nInstruments: {len(self.instruments)}",
            f"Weighting: {self.weighting_method}",
            f"IDM: {self.idm_calculator.idm:.4f}",
            f"Diversification: {self.portfolio_metrics['diversification_ratio']:.1%}",
            f"\nRisk Budget:",
            f"  Target vol:   {self.portfolio_metrics['target_portfolio_vol']:.2%}",
            f"  Expected vol: {self.portfolio_metrics['expected_portfolio_vol']:.2%}",
            f"  Ratio:        {self.portfolio_metrics['vol_ratio']:.2f}x",
            f"\nInstrument Weights:",
        ]

        for ticker, weight in self.instrument_weights.weights.items():
            position = self.instrument_positions[ticker]
            mean_pos = position.position.abs().mean()
            lines.append(f"  {ticker:8s}: {weight:6.1%}  (avg |pos| = {mean_pos:6.2f})")

        lines.append("\nCorrelation Matrix:")
        corr_str = self.instrument_correlations.round(2).to_string()
        for line in corr_str.split('\n'):
            lines.append(f"  {line}")

        lines.append("=" * 70 + "\n")

        return "\n".join(lines)

    def get_position(self, ticker: str) -> InstrumentPositionDTO:
        """Get position for specific instrument."""
        if ticker not in self.instrument_positions:
            raise ValueError(f"No position for ticker: {ticker}")
        return self.instrument_positions[ticker]

    def get_current_positions(self) -> pd.DataFrame:
        """
        Get current (latest) positions for all instruments.

        Returns:
            DataFrame with columns: ticker, position, weight, idm
        """
        positions_data = []

        for ticker, position in self.instrument_positions.items():
            positions_data.append({
                'ticker': ticker,
                'position': position.position.iloc[-1],
                'weight': self.instrument_weights.weights[ticker],
                'idm': self.idm_calculator.idm
            })

        return pd.DataFrame(positions_data)

    def get_position_history(self) -> pd.DataFrame:
        """
        Get position history for all instruments.

        Returns:
            DataFrame with date index and ticker columns
        """
        position_dict = {
            ticker: pos.position
            for ticker, pos in self.instrument_positions.items()
        }

        return pd.DataFrame(position_dict)

    def __str__(self):
        n_instruments = len(self.instruments)
        idm = self.idm_calculator.idm if self.idm_calculator else None
        return (
            f"Portfolio("
            f"instruments={n_instruments}, "
            f"method={self.weighting_method}, "
            f"IDM={idm})"
        )

    __repr__ = __str__


# ============================================================================
# Portfolio Builder (Convenience Factory)
# ============================================================================

class PortfolioBuilder:
    """
    Convenience builder for constructing portfolios step-by-step.

    This is a helper class that makes it easier to build portfolios
    without manually creating all the DTOs.

    Usage:
        builder = PortfolioBuilder(portfolio_risk_target)
        builder.add_instrument(ticker, price_data, strategies)
        builder.add_instrument(ticker2, price_data2, strategies2)
        portfolio = builder.build()
    """

    def __init__(
            self,
            portfolio_risk_target: PortfolioRiskTargetDTO,
            weighting_method: Literal["equal", "handcrafted"] = "equal"
    ):
        """
        Initialize portfolio builder.

        Args:
            portfolio_risk_target: Portfolio risk parameters
            weighting_method: How to weight instruments
        """
        self.portfolio_risk_target = portfolio_risk_target
        self.weighting_method = weighting_method
        self.instruments = {}
        self.handcrafted_weights = {}

    def add_instrument(
            self,
            ticker: str,
            price_data: PriceDataDTO,
            strategies: dict,
            fx_rate: float = 1.0,
            weight: Optional[float] = None
    ):
        """
        Add an instrument to the portfolio.

        Args:
            ticker: Instrument identifier
            price_data: OHLCV price data
            strategies: Dict of strategy_name -> StrategyDTO
            fx_rate: FX conversion rate
            weight: Optional manual weight (if using handcrafted weights)
        """
        # Create combined forecast from strategies
        combined_forecast = CombinedForecastDTO(strategies=strategies)

        # Create instrument DTO
        instrument = InstrumentDTO(
            ticker=ticker,
            price_data=price_data,
            combined_forecast=combined_forecast,
            fx_rate=fx_rate
        )

        self.instruments[ticker] = instrument

        # Store handcrafted weight if provided
        if weight is not None:
            self.handcrafted_weights[ticker] = weight

        logger.info(f"Added instrument: {ticker}")

    def build(self) -> PortfolioDTO:
        """
        Build the portfolio from added instruments.

        Returns:
            Complete PortfolioDTO
        """
        if not self.instruments:
            raise ValueError("No instruments added. Use add_instrument() first.")

        # Determine handcrafted weights
        handcrafted_weights = None
        if self.weighting_method == "handcrafted":
            if not self.handcrafted_weights:
                raise ValueError(
                    "Using handcrafted weighting but no weights provided. "
                    "Pass weight parameter to add_instrument()."
                )
            handcrafted_weights = self.handcrafted_weights

        # Build portfolio
        portfolio = PortfolioDTO(
            instruments=self.instruments,
            portfolio_risk_target=self.portfolio_risk_target,
            weighting_method=self.weighting_method,
            handcrafted_weights=handcrafted_weights
        )

        logger.info(f"Built portfolio with {len(self.instruments)} instruments")

        return portfolio
