"""
Trader Class - Systematic Trading Framework
Manages the full execution pipeline starting with data management.

Based on Robert Carver's "Systematic Trading"
REFACTORED: Modular forecast system with configurable trading rules
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd
import polars as pl
from pydantic import BaseModel, Field

from st.config.settings import Settings
from st.data import DataManager, PriceData
from st.forecast import ForecastConfig, ForecastManager, Forecast
from st.portfolio import PortfolioManager, PortfolioConfig, PortfolioWeights
from st.position import PositionManager, PositionConfig, PositionSet
from st.risk import RiskManager, RiskConfig
from st.volatility import VolatilityManager, VolatilityConfig, VolatilityResult
from utils.logger import setup_logger

logger = setup_logger(__name__)


# ---- Trading Rule Configuration ---- #


class RuleType(str, Enum):
    """Enumeration of available trading rule types."""
    EWMAC = "ewmac"
    CARRY = "carry"
    MEAN_REVERSION = "mean_reversion"
    TURTLE = "turtle"


class TradingRuleConfig(BaseModel):
    """Configuration for a single trading rule."""

    rule_type: RuleType
    params: Dict[str, Any] = Field(default_factory=dict)
    weight: Optional[float] = Field(
        default=None,
        description="Optional weight for this rule. If None, equal weighting is used."
    )
    use_volatility_standardization: bool = Field(
        default=True,
        description="Whether to apply volatility standardization"
    )

    @property
    def rule_name(self) -> str:
        """Generate a descriptive name for this rule."""
        if self.rule_type == RuleType.EWMAC:
            fast = self.params.get('fast_span', 16)
            slow = self.params.get('slow_span', 64)
            suffix = "_normalized" if self.use_volatility_standardization else ""
            return f"ewmac_{fast}_{slow}{suffix}"
        elif self.rule_type == RuleType.CARRY:
            span = self.params.get('smoothing_span', 30)
            suffix = "_normalized" if self.use_volatility_standardization else ""
            return f"carry_{span}{suffix}"
        elif self.rule_type == RuleType.MEAN_REVERSION:
            lookback = self.params.get('lookback', 30)
            suffix = "_normalized" if self.use_volatility_standardization else ""
            return f"mean_reversion_{lookback}{suffix}"
        elif self.rule_type == RuleType.TURTLE:
            entry = self.params.get('entry_window', 20)
            exit = self.params.get('exit_window', 10)
            suffix = "_normalized" if self.use_volatility_standardization else ""
            return f"turtle_{entry}_{exit}{suffix}"
        return str(self.rule_type)


class TradingRulesConfig(BaseModel):
    """Configuration for all trading rules in the system."""

    rules: List[TradingRuleConfig] = Field(
        default_factory=list,
        description="List of trading rules to apply"
    )
    equal_weights: bool = Field(
        default=True,
        description="Use equal weights if individual rule weights not specified"
    )

    def get_weights(self) -> Dict[str, float]:
        """
        Calculate weights for all rules.

        Returns:
            Dictionary mapping rule names to weights (summing to 1.0)
        """
        if self.equal_weights or all(
                rule.weight is None for rule in self.rules
        ):
            # Equal weighting
            n = len(self.rules)
            return {rule.rule_name: 1.0 / n for rule in self.rules}
        else:
            # Use specified weights and normalize
            weights = {
                rule.rule_name: (
                    rule.weight if rule.weight is not None else 1.0)
                for rule in self.rules
            }
            total = sum(weights.values())
            return {k: v / total for k, v in weights.items()}

    @classmethod
    def carver_standard_suite(cls) -> "TradingRulesConfig":
        """
        Create Carver's standard EWMAC suite.

        Returns:
            TradingRulesConfig with 6 EWMAC variations
        """
        ewmac_pairs = [(2, 8), (4, 16), (8, 32), (16, 64), (32, 128),
                       (64, 256)]
        rules = [
            TradingRuleConfig(
                rule_type=RuleType.EWMAC,
                params={'fast_span': fast, 'slow_span': slow},
                use_volatility_standardization=True
            )
            for fast, slow in ewmac_pairs
        ]
        return cls(rules=rules, equal_weights=True)

    @classmethod
    def multi_strategy_suite(cls) -> "TradingRulesConfig":
        """
        Create a diversified multi-strategy suite.

        Returns:
            TradingRulesConfig with EWMAC, Carry, Mean Reversion, and Turtle
        """
        rules = [
            # Primary EWMAC variations
            TradingRuleConfig(
                rule_type=RuleType.EWMAC,
                params={'fast_span': 16, 'slow_span': 64},
                weight=0.3
            ),
            TradingRuleConfig(
                rule_type=RuleType.EWMAC,
                params={'fast_span': 32, 'slow_span': 128},
                weight=0.2
            ),
            # Carry
            TradingRuleConfig(
                rule_type=RuleType.CARRY,
                params={'smoothing_span': 30},
                weight=0.2
            ),
            # Mean Reversion
            TradingRuleConfig(
                rule_type=RuleType.MEAN_REVERSION,
                params={'lookback': 30, 'entry_threshold': 2.0},
                weight=0.15
            ),
            # Turtle Breakout
            TradingRuleConfig(
                rule_type=RuleType.TURTLE,
                params={'entry_window': 20, 'exit_window': 10},
                weight=0.15
            ),
        ]
        return cls(rules=rules, equal_weights=False)


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
    prices: Dict[str, pd.Series]

    # Volatilities
    volatilities: Dict[str, VolatilityResult]

    # Forecasts
    raw_forecasts: Dict[
        str, Dict[str, Forecast]]  # ticker -> rule_name -> Forecast
    combined_forecasts: Dict[
        str, pd.Series]  # ticker -> combined forecast series
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
    rules_used: List[str]  # List of rule names used


class Trader:
    """
    Main trading orchestrator for systematic trading.

    Full Execution Pipeline (Carver):
    1. Data Ingestion & Validation
    2. Volatility Estimation (EWMA)
    3. Forecast Generation (Configurable Trading Rules)
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
            trading_rules_config: Optional[TradingRulesConfig] = None,
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
            trading_rules_config: Trading rules configuration
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

        # Trading rules configuration (defaults to Carver's standard suite)
        self.trading_rules_config = (trading_rules_config or
                                     TradingRulesConfig.multi_strategy_suite())

        # Pipeline state
        self.price_data: Dict[str, PriceData] = {}
        self.current_positions: Dict[str, float] = {t: 0.0 for t in tickers}
        self.pipeline_output: Optional[TradingPipeline] = None

    # ==========================================
    # FULL PIPELINE: generate_trades()
    # ==========================================

    def generate_trades(
            self,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            trading_rules_config: Optional[TradingRulesConfig] = None,
            portfolio_weights_method: str = "inverse_volatility",
            apply_buffering: bool = True,
    ) -> TradeSet:
        """
        Execute complete Carver systematic trading pipeline.

        Pipeline Steps:
        1. Load & validate data
        2. Calculate volatilities (EWMA)
        3. Generate forecasts (Configurable Rules)
        4. Combine forecasts (with FDM)
        5. Calculate portfolio weights (with IDM)
        6. Size positions (volatility targeting)
        7. Apply risk limits
        8. Generate trades

        Args:
            start_date: Data start date
            end_date: Data end date
            trading_rules_config: Override default trading rules configuration
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

        # Use provided rules config or default
        rules_config = trading_rules_config or self.trading_rules_config
        logger.info(f"\nUsing {len(rules_config.rules)} trading rules:")
        for rule in rules_config.rules:
            logger.info(
                f"  - {rule.rule_name} (weight: {rule.weight or 'equal'})"
            )

        # ---- STEP 1: Data Ingestion ---- #
        logger.info("\n[STEP 1] Loading Data...")
        self._load_all_data(start_date, end_date)

        # ---- STEP 2: Volatility Estimation ---- #
        logger.info("\n[STEP 2] Estimating Volatilities...")
        volatilities = self._estimate_volatilities()

        # ---- STEP 3: Forecast Generation ---- #
        logger.info("\n[STEP 3] Generating Forecasts...")
        raw_forecasts = self._generate_forecasts_modular(
            rules_config, volatilities
        )

        # ---- STEP 4: Forecast Combination ---- #
        logger.info("\n[STEP 4] Combining Forecasts...")
        combined_forecasts, current_forecasts = self._combine_forecasts_modular(
            raw_forecasts, rules_config
        )

        # ---- STEP 5: Portfolio Weights & Capital Allocation ---- #
        logger.info("\n[STEP 5] Calculating Portfolio Weights...")
        portfolio_weights, capital_allocation = self._calculate_portfolio_weights(
            volatilities, portfolio_weights_method
        )

        # ---- STEP 6: Position Sizing ---- #
        logger.info("\n[STEP 6] Sizing Positions...")
        position_set = self._size_positions(
            current_forecasts, capital_allocation, volatilities
        )

        # ---- STEP 7: Risk Management ---- #
        logger.info("\n[STEP 7] Applying Risk Limits...")
        position_set = self._apply_risk_limits(position_set)

        # ---- STEP 8: Trade Generation ---- #
        logger.info("\n[STEP 8] Generating Trades...")
        trade_set = self._generate_trade_orders(position_set, apply_buffering)

        # ---- Store Pipeline Output ---- #
        from datetime import datetime

        self.pipeline_output = TradingPipeline(
            tickers=self.tickers,
            prices={
                ticker: self.price_data[ticker].data["Close"]
                for ticker in self.tickers
            },
            volatilities=volatilities,
            raw_forecasts=raw_forecasts,
            combined_forecasts=combined_forecasts,
            current_forecasts=current_forecasts,
            portfolio_weights=portfolio_weights,
            capital_allocation=capital_allocation,
            position_set=position_set,
            trade_set=trade_set,
            timestamp=datetime.now().isoformat(),
            rules_used=[rule.rule_name for rule in rules_config.rules],
        )

        # ---- Summary ---- #
        logger.info("\n" + "=" * 60)
        logger.info("PIPELINE COMPLETE")
        logger.info(f"Generated {len(trade_set.trades)} trades")
        logger.info(f"Total notional: ${trade_set.total_notional:,.0f}")
        logger.info(
            f"Portfolio leverage: {position_set.portfolio_leverage:.2f}x"
        )
        logger.info("=" * 60)

        return trade_set

    # ==========================================
    # PIPELINE STEPS (REFACTORED)
    # ==========================================

    def _load_all_data(
            self, start_date: Optional[str] = None,
            end_date: Optional[str] = None
    ) -> None:
        """Step 1: Load and validate price data for all tickers."""
        for ticker in self.tickers:
            price_data = self.data_manager.get_data(
                ticker, start_date,
                end_date
            )
            self.price_data[ticker] = price_data
            logger.info(
                f"  Loaded {ticker}: {len(price_data.data)} rows, "
                f"last price: ${float(price_data.data['Close'].iloc[-1]):.2f}"
            )

        logger.info(f" Loaded data for {len(self.tickers)} instruments")

    def _estimate_volatilities(self) -> Dict[str, VolatilityResult]:
        """Step 2: Estimate volatility for each instrument using EWMA."""
        volatilities = {}

        for ticker in self.tickers:
            prices = self.price_data[ticker].data["Close"]
            vol_result = self.volatility_manager.estimate_from_prices(
                prices, ticker
            )
            volatilities[ticker] = vol_result

            logger.info(
                f"  {ticker}: annual_vol={vol_result.current_annual_vol:.2%}, "
                f"daily_vol={vol_result.current_daily_vol:.2%}"
            )

        logger.info(
            f" Calculated volatilities for {len(volatilities)} instruments"
        )
        return volatilities

    def _generate_forecasts_modular(
            self,
            rules_config: TradingRulesConfig,
            volatilities: Dict[str, VolatilityResult],
    ) -> Dict[str, Dict[str, Forecast]]:
        """
        Step 3: Generate forecasts using configured trading rules (MODULAR).

        Args:
            rules_config: Configuration of trading rules to apply
            volatilities: Dictionary of volatility results by ticker

        Returns:
            Nested dictionary: ticker -> rule_name -> Forecast
        """
        raw_forecasts = {}

        for ticker in self.tickers:
            prices = self.price_data[ticker].data["Close"]
            price_volatility = volatilities[ticker].daily_vol

            ticker_forecasts = {}

            for rule_config in rules_config.rules:
                forecast = self._generate_single_forecast(
                    ticker=ticker,
                    prices=prices,
                    price_volatility=price_volatility,
                    rule_config=rule_config,
                )
                ticker_forecasts[forecast.rule_name] = forecast

                logger.info(
                    f"  {ticker} - {forecast.rule_name}: "
                    f"current={forecast.current_forecast:.2f}"
                )

            raw_forecasts[ticker] = ticker_forecasts

        logger.info(
            f" Generated {sum(len(f) for f in raw_forecasts.values())} total forecasts "
            f"across {len(self.tickers)} instruments"
        )
        return raw_forecasts

    def _generate_single_forecast(
            self,
            ticker: str,
            prices: pd.Series,
            price_volatility: pd.Series,
            rule_config: TradingRuleConfig,
    ) -> Forecast:
        """
        Generate a single forecast based on rule configuration.

        Args:
            ticker: Instrument identifier
            prices: Price series
            price_volatility: Volatility series
            rule_config: Configuration for this specific rule

        Returns:
            Forecast object
        """
        if rule_config.rule_type == RuleType.EWMAC:
            return self.forecast_manager.generate_ewmac(
                prices=prices,
                price_volatility=price_volatility if rule_config.use_volatility_standardization else None,
                fast_span=rule_config.params.get('fast_span', 16),
                slow_span=rule_config.params.get('slow_span', 64),
                ticker=ticker,
                use_volatility_standardization=rule_config.use_volatility_standardization,
            )

        elif rule_config.rule_type == RuleType.CARRY:
            # Note: Carry requires additional data (forward prices or yields)
            # This is a placeholder - you'll need to provide this data
            logger.warning(
                f"Carry strategy for {ticker} requires forward/yield data - using placeholder"
            )
            # You would call: self.forecast_manager.generate_carry_from_prices(...)
            # For now, return a dummy forecast
            return self.forecast_manager.generate_ewmac(
                prices=prices,
                price_volatility=price_volatility if rule_config.use_volatility_standardization else None,
                ticker=ticker,
                use_volatility_standardization=rule_config.use_volatility_standardization,
            )

        elif rule_config.rule_type == RuleType.MEAN_REVERSION:
            return self.forecast_manager.generate_mean_reversion(
                prices=prices,
                price_volatility=price_volatility if rule_config.use_volatility_standardization else None,
                lookback=rule_config.params.get('lookback', 30),
                entry_threshold=rule_config.params.get('entry_threshold', 2.0),
                ticker=ticker,
                use_volatility_standardization=rule_config.use_volatility_standardization,
            )

        elif rule_config.rule_type == RuleType.TURTLE:
            return self.forecast_manager.generate_turtle(
                prices=prices,
                price_volatility=price_volatility if rule_config.use_volatility_standardization else None,
                entry_window=rule_config.params.get('entry_window', 20),
                exit_window=rule_config.params.get('exit_window', 10),
                ticker=ticker,
                use_volatility_standardization=rule_config.use_volatility_standardization,
            )

        else:
            raise ValueError(f"Unknown rule type: {rule_config.rule_type}")

    def _combine_forecasts_modular(
            self,
            raw_forecasts: Dict[str, Dict[str, Forecast]],
            rules_config: TradingRulesConfig,
    ) -> Tuple[Dict[str, pd.Series], Dict[str, float]]:
        """
        Step 4: Combine forecasts using configured weights (MODULAR).

        Args:
            raw_forecasts: Nested dict of forecasts
            rules_config: Configuration including weights

        Returns:
            Tuple of (combined forecast series dict, current forecast values dict)
        """
        forecast_weights = rules_config.get_weights()

        combined_forecasts = {}
        current_forecasts = {}

        for ticker in self.tickers:
            ticker_forecast_list = list(raw_forecasts[ticker].values())

            combined_series, fdm = self.forecast_manager.combine_forecasts(
                ticker_forecast_list, weights=forecast_weights
            )

            combined_forecasts[ticker] = combined_series
            current_forecasts[ticker] = float(combined_series.iloc[-1])

            logger.info(
                f"  {ticker}: combined_forecast={current_forecasts[ticker]:.2f}, "
                f"FDM={fdm:.2f}"
            )

        logger.info(f" Combined forecasts for {len(self.tickers)} instruments")
        return combined_forecasts, current_forecasts

    def _calculate_portfolio_weights(
            self,
            volatilities: Dict[str, VolatilityResult],
            method: str = "inverse_volatility",
    ) -> Tuple[PortfolioWeights, Dict[str, float]]:
        """Step 5: Calculate portfolio weights and allocate capital."""
        vols = {
            ticker: vol.current_annual_vol
            for ticker, vol in volatilities.items()
        }

        portfolio_weights = self.portfolio_manager.calculate_portfolio_weights(
            tickers=self.tickers,
            volatilities=vols, method=method
        )

        capital_allocation = self.portfolio_manager.allocate_capital(
            self.capital, portfolio_weights
        )

        logger.info(
            f"  Method: {method}, IDM: {portfolio_weights.diversification_multiplier:.2f}"
        )
        for ticker, capital in capital_allocation.items():
            logger.info(
                f"    {ticker}: weight={portfolio_weights.weights[ticker]:.2%}, "
                f"capital=${capital:,.0f}"
            )

        logger.info(
            f" Allocated capital across {len(capital_allocation)} instruments"
        )
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
            ticker: float(self.price_data[ticker].data["Close"].iloc[-1])
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
            f" Sized {len(position_set.positions)} positions, "
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
            f" Risk limits applied, portfolio leverage: "
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

        logger.info(f" Generated {len(trades)} trade orders")
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
                        self.current_positions.get(
                            trade.ticker, 0.0
                        ) + trade.contracts
                )
            else:  # SELL
                self.current_positions[trade.ticker] = (
                        self.current_positions.get(
                            trade.ticker, 0.0
                        ) - trade.contracts
                )

        logger.info(" Updated current positions")

    def set_trading_rules(self, rules_config: TradingRulesConfig) -> None:
        """
        Update the trading rules configuration.

        Args:
            rules_config: New trading rules configuration
        """
        self.trading_rules_config = rules_config
        logger.info(
            f"Updated trading rules: {len(rules_config.rules)} rules configured"
        )

    def get_pipeline_summary(self) -> Dict:
        """Get summary of last pipeline execution."""
        if self.pipeline_output is None:
            return {"status": "No pipeline executed yet"}

        po = self.pipeline_output

        return {
            "timestamp":          po.timestamp,
            "num_instruments":    len(po.tickers),
            "num_trades":         po.trade_set.num_trades,
            "total_notional":     po.trade_set.total_notional,
            "portfolio_leverage": po.position_set.portfolio_leverage,
            "idm":                po.portfolio_weights.diversification_multiplier,
            "current_forecasts":  po.current_forecasts,
            "capital_allocation": po.capital_allocation,
            "rules_used":         po.rules_used,
        }

    def get_risk_report(self) -> str:
        """Generate risk report for current portfolio."""
        if self.pipeline_output is None:
            return "No pipeline executed yet"

        # Calculate portfolio risk
        positions_dict = {
            ticker: float(pos.contracts) if pos.contracts is not None else 0.0
            for ticker, pos in
            self.pipeline_output.position_set.positions.items()
        }

        prices = {
            ticker: float(self.price_data[ticker].data["Close"][-1])
            for ticker in self.tickers
        }

        volatilities = {
            ticker: vol.current_annual_vol
            for ticker, vol in self.pipeline_output.volatilities.items()
        }

        # Get correlations (simplified - using returns)
        returns_data = {}
        for ticker in self.tickers:
            prices_series = self.price_data[ticker].data["Close"]
            returns = (prices_series / prices_series.shift(1)).log()
            returns_data[ticker] = returns

        returns_df = pl.DataFrame(returns_data)
        correlation_matrix = self.risk_manager.estimate_correlations(
            returns_df
        )

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
            f"rules={len(self.trading_rules_config.rules)}, "
            f"positions={len([p for p in self.current_positions.values() if p != 0])})"
        )
