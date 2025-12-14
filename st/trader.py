"""
Trader Class - Systematic Trading Framework
Manages the full execution pipeline starting with data management.

Based on Robert Carver's "Systematic Trading"
"""

from typing import Dict, List, Optional, Tuple

import polars as pl
from pydantic import BaseModel, Field

from st.config.settings import Settings
from st.data import DataManager
from st.forecast import ForecastConfig, ForecastManager, Forecast
from st.portfolio import PortfolioManager, PortfolioConfig, PortfolioWeights
from st.position import PositionManager, PositionConfig, PositionSet
from st.risk import RiskManager, RiskConfig
from st.volatility import VolatilityManager, VolatilityConfig, VolatilityResult
from utils.logger import setup_logger

logger = setup_logger(__name__)


# ---- Trade Structures ---- #


class Trade(BaseModel):
    """Represents a single trade order."""

    ticker: str
    action: str = Field(..., description="BUY or SELL")
    contracts: float = Field(..., description="Number of contracts to trade")
    price: float = Field(..., description="Current price")
    notional: float = Field(..., description="Notional value of trade")
    forecast: float = Field(..., description="Combined forecast")
    volatility: float = Field(..., description="Instrument volatility")
    timestamp: Optional[str] = Field(default=None)

    @property
    def trade_value(self) -> float:
        """Calculate trade value."""
        return abs(self.contracts * self.price)


class TradeSet(BaseModel):
    """Collection of trades for portfolio."""

    trades: List[Trade] = Field(default_factory=list)
    total_capital: float
    timestamp: Optional[str] = Field(default=None)

    @property
    def num_trades(self) -> int:
        """Number of trades."""
        return len(self.trades)

    @property
    def total_notional(self) -> float:
        """Total notional value of all trades."""
        return sum(t.notional for t in self.trades)

    def get_trades_by_action(self, action: str) -> List[Trade]:
        """Filter trades by action (BUY/SELL)."""
        return [t for t in self.trades if t.action == action]


class TradingPipeline(BaseModel):
    """Container for all pipeline outputs."""

    model_config = {"arbitrary_types_allowed": True}

    # Data
    tickers: List[str]
    prices: Dict[str, pl.Series]

    # Volatilities
    volatilities: Dict[str, VolatilityResult]

    # Forecasts
    raw_forecasts: Dict[str, Dict[str, Forecast]]  # ticker -> rule_name -> Forecast
    combined_forecasts: Dict[str, pl.Series]  # ticker -> combined forecast series
    current_forecasts: Dict[str, float]  # ticker -> current forecast value

    # Portfolio
    portfolio_weights: PortfolioWeights
    capital_allocation: Dict[str, float]

    # Positions
    position_set: PositionSet

    # Trades
    trade_set: TradeSet

    # Metadata
    timestamp: str


class Trader:
    """
    Main trading orchestrator for systematic trading.

    Full Execution Pipeline (Carver):
    1. Data Ingestion & Validation
    2. Volatility Estimation (EWMA)
    3. Forecast Generation (Trading Rules)
    4. Forecast Combination (FDM)
    5. Portfolio Weights (IDM)
    6. Position Sizing (Volatility Targeting)
    7. Risk Management & Trade Generation
    """

    def __init__(
            self,
            tickers: List[str],
            capital: float = Settings.INITIAL_CAPITAL,
            data_manager: Optional[DataManager] = None,
            forecast_config: Optional[ForecastConfig] = None,
            volatility_config: Optional[VolatilityConfig] = None,
            position_config: Optional[PositionConfig] = None,
            portfolio_config: Optional[PortfolioConfig] = None,
            risk_config: Optional[RiskConfig] = None,
    ):
        """
        Initialize Trader.

        Args:
            tickers: List of instrument tickers
            capital: Total portfolio capital
            data_manager: DataManager instance
            forecast_config: Forecast configuration
            volatility_config: Volatility configuration
            position_config: Position configuration
            portfolio_config: Portfolio configuration
            risk_config: Risk configuration
        """
        # Core parameters
        self.tickers = tickers
        self.capital = capital

        # Managers
        self.data_manager = data_manager or DataManager()
        self.forecast_manager = ForecastManager(forecast_config)
        self.volatility_manager = VolatilityManager(volatility_config)
        self.position_manager = PositionManager(position_config)
        self.portfolio_manager = PortfolioManager(portfolio_config)
        self.risk_manager = RiskManager(risk_config)

        # Pipeline state
        self.price_data: Dict[str, pl.DataFrame] = {}
        self.current_positions: Dict[str, float] = {t: 0.0 for t in tickers}
        self.pipeline_output: Optional[TradingPipeline] = None

    # ==========================================
    # FULL PIPELINE: generate_trades()
    # ==========================================

    def generate_trades(
            self,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            ewmac_pairs: Optional[List[Tuple[int, int]]] = None,
            forecast_weights: Optional[Dict[str, float]] = None,
            portfolio_weights_method: str = "inverse_volatility",
            apply_buffering: bool = True,
    ) -> TradeSet:
        """
        Execute complete Carver systematic trading pipeline.

        Pipeline Steps:
        1. Load & validate data
        2. Calculate volatilities (EWMA)
        3. Generate forecasts (EWMAC rules)
        4. Combine forecasts (with FDM)
        5. Calculate portfolio weights (with IDM)
        6. Size positions (volatility targeting)
        7. Apply risk limits
        8. Generate trades

        Args:
            start_date: Data start date
            end_date: Data end date
            ewmac_pairs: List of (fast, slow) EWMAC pairs, defaults to Carver's standard
            forecast_weights: Custom forecast weights (equal if None)
            portfolio_weights_method: 'equal', 'inverse_volatility', 'risk_parity'
            apply_buffering: Apply position buffering to reduce turnover

        Returns:
            TradeSet with all trades
        """
        logger.info("=" * 60)
        logger.info("STARTING SYSTEMATIC TRADING PIPELINE")
        logger.info(f"Tickers: {self.tickers}")
        logger.info(f"Capital: ${self.capital:,.0f}")
        logger.info("=" * 60)

        # Default EWMAC pairs (Carver's standard suite)
        if ewmac_pairs is None:
            ewmac_pairs = [(2, 8), (4, 16), (8, 32), (16, 64), (32, 128), (64, 256)]

        # ---- STEP 1: Data Ingestion ---- #
        logger.info("\n[STEP 1] Loading Data...")
        self._load_all_data(start_date, end_date)

        # ---- STEP 2: Volatility Estimation ---- #
        logger.info("\n[STEP 2] Estimating Volatilities...")
        volatilities = self._estimate_volatilities()

        # ---- STEP 3: Forecast Generation ---- #
        logger.info("\n[STEP 3] Generating Forecasts...")
        raw_forecasts = self._generate_forecasts(ewmac_pairs)

        # ---- STEP 4: Forecast Combination ---- #
        logger.info("\n[STEP 4] Combining Forecasts...")
        combined_forecasts, current_forecasts = self._combine_forecasts(
            raw_forecasts, forecast_weights
        )

        # ---- STEP 5: Portfolio Weights & Capital Allocation ---- #
        logger.info("\n[STEP 5] Calculating Portfolio Weights...")
        portfolio_weights, capital_allocation = self._calculate_portfolio_weights(
            volatilities, portfolio_weights_method
        )

        # ---- STEP 6: Position Sizing ---- #
        logger.info("\n[STEP 6] Sizing Positions...")
        position_set = self._size_positions(
            current_forecasts,
            capital_allocation,
            volatilities,
        )

        # ---- STEP 7: Risk Management ---- #
        logger.info("\n[STEP 7] Applying Risk Limits...")
        position_set = self._apply_risk_limits(position_set)

        # ---- STEP 8: Trade Generation ---- #
        logger.info("\n[STEP 8] Generating Trades...")
        trade_set = self._generate_trade_orders(position_set, apply_buffering)

        # Store pipeline output
        from datetime import datetime
        self.pipeline_output = TradingPipeline(
            tickers=self.tickers,
            prices={t: self.price_data[t]["close"] for t in self.tickers},
            volatilities=volatilities,
            raw_forecasts=raw_forecasts,
            combined_forecasts=combined_forecasts,
            current_forecasts=current_forecasts,
            portfolio_weights=portfolio_weights,
            capital_allocation=capital_allocation,
            position_set=position_set,
            trade_set=trade_set,
            timestamp=datetime.now().isoformat(),
        )

        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("PIPELINE COMPLETE")
        logger.info(f"Generated {trade_set.num_trades} trades")
        logger.info(f"Total notional: ${trade_set.total_notional:,.0f}")
        logger.info(f"Portfolio leverage: {position_set.portfolio_leverage:.2f}x")
        logger.info("=" * 60)

        return trade_set

    # ==========================================
    # PIPELINE STEP IMPLEMENTATIONS
    # ==========================================

    def _load_all_data(
            self,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
    ) -> None:
        """Step 1: Load and validate price data for all tickers."""
        for ticker in self.tickers:
            logger.info(f"  Loading {ticker}...")

            price_data = self.data_manager.get_data(
                ticker=ticker,
                start_date=start_date,
                end_date=end_date,
                validate=True,
            )

            if price_data is None:
                raise ValueError(f"Failed to load data for {ticker}")

            # Convert to Polars
            df = pl.from_pandas(price_data.data.reset_index())
            df = df.rename({col: col.lower() for col in df.columns})

            # Ensure date format
            if "date" in df.columns:
                try:
                    df = df.with_columns([pl.col("date").cast(pl.Date)])
                except:
                    pass

            self.price_data[ticker] = df.sort("date")

        logger.info(f"✓ Loaded data for {len(self.tickers)} instruments")

    def _estimate_volatilities(self) -> Dict[str, VolatilityResult]:
        """Step 2: Estimate EWMA volatilities for all instruments."""
        volatilities = {}

        for ticker in self.tickers:
            prices = self.price_data[ticker]["close"]
            vol_result = self.volatility_manager.estimate_from_prices(prices, ticker)
            volatilities[ticker] = vol_result

            logger.info(
                f"  {ticker}: Current vol = {vol_result.current_annual_vol:.2%}"
            )

        logger.info(f"✓ Calculated volatilities for {len(volatilities)} instruments")
        return volatilities

    def _generate_forecasts(
            self,
            ewmac_pairs: List[Tuple[int, int]],
    ) -> Dict[str, Dict[str, Forecast]]:
        """Step 3: Generate EWMAC forecasts for all instruments."""
        raw_forecasts = {}

        for ticker in self.tickers:
            prices = self.price_data[ticker]["close"]
            ticker_forecasts = {}

            logger.info(f"  Generating forecasts for {ticker}...")

            for fast, slow in ewmac_pairs:
                forecast = self.forecast_manager.generate_ewmac(
                    prices, fast, slow, ticker
                )
                ticker_forecasts[forecast.rule_name] = forecast

            raw_forecasts[ticker] = ticker_forecasts
            logger.info(f"    Generated {len(ticker_forecasts)} EWMAC rules")

        total_forecasts = sum(len(f) for f in raw_forecasts.values())
        logger.info(f"✓ Generated {total_forecasts} total forecasts")
        return raw_forecasts

    def _combine_forecasts(
            self,
            raw_forecasts: Dict[str, Dict[str, Forecast]],
            weights: Optional[Dict[str, float]] = None,
    ) -> Tuple[Dict[str, pl.Series], Dict[str, float]]:
        """Step 4: Combine forecasts for each instrument."""
        combined_forecasts = {}
        current_forecasts = {}

        for ticker in self.tickers:
            forecasts = list(raw_forecasts[ticker].values())

            # Combine with FDM
            combined, fdm = self.forecast_manager.combine_forecasts(
                forecasts, weights
            )

            combined_forecasts[ticker] = combined
            current_forecasts[ticker] = float(combined[-1])

            logger.info(
                f"  {ticker}: Combined forecast = {current_forecasts[ticker]:.2f}, "
                f"FDM = {fdm:.3f}"
            )

        logger.info(f"✓ Combined forecasts for {len(combined_forecasts)} instruments")
        return combined_forecasts, current_forecasts

    def _calculate_portfolio_weights(
            self,
            volatilities: Dict[str, VolatilityResult],
            method: str = "equal",
    ) -> Tuple[PortfolioWeights, Dict[str, float]]:
        """Step 5: Calculate portfolio weights and allocate capital."""
        # Extract current volatilities
        current_vols = {
            ticker: vol.current_annual_vol
            for ticker, vol in volatilities.items()
        }

        # Calculate weights
        portfolio_weights = self.portfolio_manager.calculate_portfolio_weights(
            tickers=self.tickers,
            method=method,
            volatilities=current_vols,
        )

        # Allocate capital (with IDM)
        capital_allocation = self.portfolio_manager.allocate_capital(
            total_capital=self.capital,
            portfolio_weights=portfolio_weights,
            apply_idm=True,
        )

        logger.info(f"  Portfolio method: {method}")
        logger.info(f"  IDM: {portfolio_weights.diversification_multiplier:.3f}")
        for ticker, capital in capital_allocation.items():
            logger.info(
                f"    {ticker}: weight={portfolio_weights.weights[ticker]:.2%}, "
                f"capital=${capital:,.0f}"
            )

        logger.info(f"✓ Allocated capital across {len(capital_allocation)} instruments")
        return portfolio_weights, capital_allocation

    def _size_positions(
            self,
            forecasts: Dict[str, float],
            capital_allocation: Dict[str, float],
            volatilities: Dict[str, VolatilityResult],
    ) -> PositionSet:
        """Step 6: Size positions using Carver's formula with volatility targeting."""
        # Get current prices
        prices = {
            ticker: float(self.price_data[ticker]["close"][-1])
            for ticker in self.tickers
        }

        # Get current volatilities
        vols = {
            ticker: vol.current_annual_vol
            for ticker, vol in volatilities.items()
        }

        # Calculate positions
        position_set = self.position_manager.calculate_portfolio_positions(
            forecasts=forecasts,
            capital_allocation=capital_allocation,
            volatilities=vols,
            prices=prices,
        )

        for ticker, position in position_set.positions.items():
            logger.info(
                f"  {ticker}: forecast={position.forecast:.2f}, "
                f"contracts={position.contracts:.2f}, "
                f"notional=${position.notional_position:,.0f}, "
                f"leverage={position.leverage:.2f}x"
            )

        logger.info(
            f"✓ Sized {len(position_set.positions)} positions, "
            f"total notional: ${position_set.total_notional:,.0f}"
        )
        return position_set

    def _apply_risk_limits(self, position_set: PositionSet) -> PositionSet:
        """Step 7: Apply risk limits to positions."""
        # Check portfolio leverage
        if position_set.portfolio_leverage > self.position_manager.config.max_leverage:
            logger.warning(
                f"Portfolio leverage {position_set.portfolio_leverage:.2f}x exceeds "
                f"limit {self.position_manager.config.max_leverage:.2f}x, scaling down"
            )

            # Scale down all positions proportionally
            scale_factor = self.position_manager.config.max_leverage / position_set.portfolio_leverage

            for position in position_set.positions.values():
                if position.contracts is not None:
                    position.contracts *= scale_factor
                if position.notional_position is not None:
                    position.notional_position *= scale_factor
                if position.leverage is not None:
                    position.leverage *= scale_factor

        logger.info(
            f"✓ Risk limits applied, portfolio leverage: "
            f"{position_set.portfolio_leverage:.2f}x"
        )
        return position_set

    def _generate_trade_orders(
            self,
            position_set: PositionSet,
            apply_buffering: bool = True,
    ) -> TradeSet:
        """Step 8: Generate trade orders from target positions."""
        from datetime import datetime

        trades = []

        # Apply buffering if requested
        if apply_buffering:
            position_set = self.position_manager.apply_buffering(
                self.current_positions, position_set
            )

        # Generate trades
        for ticker, position in position_set.positions.items():
            current = self.current_positions.get(ticker, 0.0)
            target = position.contracts if position.contracts is not None else 0.0

            delta = target - current

            # Only trade if there's a meaningful change
            if abs(delta) < 0.01:  # Minimum trade size
                continue

            action = "BUY" if delta > 0 else "SELL"

            trade = Trade(
                ticker=ticker,
                action=action,
                contracts=abs(delta),
                price=position.price,
                notional=abs(delta * position.price),
                forecast=position.forecast,
                volatility=position.volatility,
                timestamp=datetime.now().isoformat(),
            )

            trades.append(trade)
            logger.info(
                f"  {action} {ticker}: {abs(delta):.2f} contracts @ ${position.price:.2f} "
                f"(notional: ${trade.notional:,.0f})"
            )

        trade_set = TradeSet(
            trades=trades,
            total_capital=self.capital,
            timestamp=datetime.now().isoformat(),
        )

        logger.info(f"✓ Generated {len(trades)} trade orders")
        return trade_set

    # ==========================================
    # CONVENIENCE METHODS
    # ==========================================

    def update_positions(self, trade_set: TradeSet) -> None:
        """
        Update current positions after executing trades.

        Args:
            trade_set: TradeSet with executed trades
        """
        for trade in trade_set.trades:
            if trade.action == "BUY":
                self.current_positions[trade.ticker] = (
                        self.current_positions.get(trade.ticker, 0.0) + trade.contracts
                )
            else:  # SELL
                self.current_positions[trade.ticker] = (
                        self.current_positions.get(trade.ticker, 0.0) - trade.contracts
                )

        logger.info("✓ Updated current positions")

    def get_pipeline_summary(self) -> Dict:
        """Get summary of last pipeline execution."""
        if self.pipeline_output is None:
            return {"status": "No pipeline executed yet"}

        po = self.pipeline_output

        return {
            "timestamp": po.timestamp,
            "num_instruments": len(po.tickers),
            "num_trades": po.trade_set.num_trades,
            "total_notional": po.trade_set.total_notional,
            "portfolio_leverage": po.position_set.portfolio_leverage,
            "idm": po.portfolio_weights.diversification_multiplier,
            "current_forecasts": po.current_forecasts,
            "capital_allocation": po.capital_allocation,
        }

    def get_risk_report(self) -> str:
        """Generate risk report for current portfolio."""
        if self.pipeline_output is None:
            return "No pipeline executed yet"

        # Calculate portfolio risk
        positions_dict = {
            ticker: float(pos.contracts) if pos.contracts is not None else 0.0
            for ticker, pos in self.pipeline_output.position_set.positions.items()
        }

        prices = {
            ticker: float(self.price_data[ticker]["close"][-1])
            for ticker in self.tickers
        }

        volatilities = {
            ticker: vol.current_annual_vol
            for ticker, vol in self.pipeline_output.volatilities.items()
        }

        # Get correlations (simplified - using returns)
        returns_data = {}
        for ticker in self.tickers:
            prices_series = self.price_data[ticker]["close"]
            returns = (prices_series / prices_series.shift(1)).log()
            returns_data[ticker] = returns

        returns_df = pl.DataFrame(returns_data)
        correlation_matrix = self.risk_manager.estimate_correlations(returns_df)

        portfolio_risk = self.risk_manager.calculate_portfolio_risk(
            positions=positions_dict,
            prices=prices,
            volatilities=volatilities,
            correlation_matrix=correlation_matrix,
            capital=self.capital,
        )

        return self.risk_manager.get_risk_report(portfolio_risk)

    def __repr__(self):
        return (
            f"Trader(tickers={len(self.tickers)}, "
            f"capital=${self.capital:,.0f}, "
            f"positions={len([p for p in self.current_positions.values() if p != 0])})"
        )
