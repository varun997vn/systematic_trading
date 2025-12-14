"""
Advanced Trader Example
Demonstrates customization and advanced features of the systematic trading framework.
"""

from typing import Dict, List

from st.config.settings import Settings
from st.data import DataManager
from st.forecast import ForecastConfig
from st.portfolio import PortfolioConfig
from st.position import PositionConfig
from st.risk import RiskConfig
from st.trader import Trader
from st.volatility import VolatilityConfig
from utils.logger import setup_logger

logger = setup_logger(__name__)


class AdvancedTrader:
    """
    Advanced systematic trader with custom configurations.

    This example demonstrates:
    - Custom volatility estimation
    - Custom forecast weighting
    - Advanced portfolio construction
    - Risk monitoring and constraints
    """

    def __init__(self):
        self.trader = None
        self.custom_configs = self._build_custom_configs()

    def _build_custom_configs(self) -> Dict:
        """
        Build custom configurations for advanced trading.

        Returns:
            Dictionary of configuration objects
        """
        # 1. Forecast Configuration
        # Adjust target forecast to be more conservative
        forecast_config = ForecastConfig(
            target_abs_forecast=8.0,  # Lower than Carver's default 10
            min_forecast=-20.0,
            max_forecast=20.0,
            cap_forecasts=True,
        )

        # 2. Volatility Configuration
        # Use faster-reacting volatility estimate
        volatility_config = VolatilityConfig(
            span=25,  # Faster than default 36
            min_periods=10,
            annualization_factor=252,  # Standard market convention
        )

        # 3. Position Configuration
        # More conservative position limits
        position_config = PositionConfig(
            instrument_weight=1.0,
            volatility_target=0.15,  # More conservative 15% target
            max_leverage=1.5,  # Lower max leverage
            max_position_size=0.10,  # Max 10% per instrument
            buffer_width=0.15,  # Wider buffer = less turnover
        )

        # 4. Portfolio Configuration
        # Custom IDM (Instrument Diversification Multiplier)
        portfolio_config = PortfolioConfig(
            default_idm=2.0,
            handcraft_idm=True,
        )

        # 5. Risk Configuration
        # Longer correlation window for stability
        risk_config = RiskConfig(
            correlation_estimation_window=120,
            min_correlation_periods=60,
        )

        return {
            'forecast': forecast_config,
            'volatility': volatility_config,
            'position': position_config,
            'portfolio': portfolio_config,
            'risk': risk_config,
        }

    def create_multi_asset_trader(
        self,
        capital: float = 500_000,
    ) -> Trader:
        """
        Create a sophisticated multi-asset class trader.

        Portfolio includes:
        - US Equities (Large, Mid, Small Cap)
        - International Equities (Developed, Emerging)
        - Fixed Income (Short, Medium, Long Duration)
        - Commodities (Gold, Oil, Agriculture)
        - Real Estate
        - Alternatives

        Args:
            capital: Trading capital

        Returns:
            Configured Trader instance
        """
        # Define multi-asset portfolio
        tickers = [
            # US Equities
            "SPY",   # S&P 500
            "IWM",   # Small Cap
            "QQQ",   # Tech/Growth

            # International
            "EFA",   # Developed Markets
            "EEM",   # Emerging Markets

            # Fixed Income
            "SHY",   # 1-3 Year Treasuries
            "IEF",   # 7-10 Year Treasuries
            "TLT",   # 20+ Year Treasuries

            # Commodities
            "GLD",   # Gold
            "USO",   # Oil
            "DBA",   # Agriculture

            # Real Estate
            "VNQ",   # REITs
        ]

        trader = Trader(
            tickers=tickers,
            capital=capital,
            forecast_config=self.custom_configs['forecast'],
            volatility_config=self.custom_configs['volatility'],
            position_config=self.custom_configs['position'],
            portfolio_config=self.custom_configs['portfolio'],
            risk_config=self.custom_configs['risk'],
        )

        self.trader = trader

        logger.info("=" * 70)
        logger.info("MULTI-ASSET TRADER CREATED")
        logger.info(f"Assets: {len(tickers)} instruments across 5 asset classes")
        logger.info(f"Capital: ${capital:,.0f}")
        logger.info("=" * 70)

        return trader

    def run_with_custom_ewmac_pairs(
        self,
        start_date: str = "2018-01-01",
    ):
        """
        Run trading pipeline with custom EWMAC pairs.

        Uses different trend-following timeframes than Carver's defaults.

        Args:
            start_date: Historical data start date

        Returns:
            TradeSet
        """
        if self.trader is None:
            raise ValueError("Trader not initialized. Call create_multi_asset_trader() first.")

        # Custom EWMAC pairs emphasizing medium-term trends
        custom_ewmac_pairs = [
            (4, 16),    # Short-term
            (8, 32),    # Medium-term (emphasized)
            (16, 64),   # Medium-long term (emphasized)
            (32, 128),  # Long-term
        ]

        # Custom forecast weights - emphasize medium-term trends
        custom_weights = {
            'ewmac_4_16': 0.15,
            'ewmac_8_32': 0.35,   # Highest weight
            'ewmac_16_64': 0.35,  # Highest weight
            'ewmac_32_128': 0.15,
        }

        logger.info("\nRunning pipeline with custom EWMAC configuration...")
        logger.info(f"EWMAC pairs: {custom_ewmac_pairs}")
        logger.info(f"Custom weights: {custom_weights}")

        trade_set = self.trader.generate_trades(
            start_date=start_date,
            ewmac_pairs=custom_ewmac_pairs,
            forecast_weights=custom_weights,
            portfolio_weights_method="inverse_volatility",  # Weight by inverse volatility
            apply_buffering=True,
        )

        return trade_set

    def run_sector_rotation(
        self,
        capital: float = 250_000,
    ):
        """
        Create a sector rotation strategy.

        Trades sector ETFs with higher turnover to capture sector trends.

        Args:
            capital: Trading capital

        Returns:
            TradeSet
        """
        # Sector ETFs
        sector_tickers = [
            "XLK",  # Technology
            "XLF",  # Financials
            "XLV",  # Healthcare
            "XLE",  # Energy
            "XLI",  # Industrials
            "XLY",  # Consumer Discretionary
            "XLP",  # Consumer Staples
            "XLU",  # Utilities
            "XLB",  # Materials
        ]

        # Create specialized config for sector rotation
        sector_config = self.custom_configs.copy()

        # Faster-reacting volatility for sectors
        sector_config['volatility'] = VolatilityConfig(
            span=20,  # Very fast
            min_periods=10,
        )

        # Tighter buffer for more active rotation
        sector_config['position'] = PositionConfig(
            volatility_target=0.18,
            max_leverage=1.8,
            max_position_size=0.12,
            buffer_width=0.08,  # Tighter buffer = more active
        )

        trader = Trader(
            tickers=sector_tickers,
            capital=capital,
            forecast_config=sector_config['forecast'],
            volatility_config=sector_config['volatility'],
            position_config=sector_config['position'],
            portfolio_config=sector_config['portfolio'],
            risk_config=sector_config['risk'],
        )

        logger.info("=" * 70)
        logger.info("SECTOR ROTATION STRATEGY")
        logger.info(f"Sectors: {len(sector_tickers)}")
        logger.info("=" * 70)

        # Shorter-term EWMAC pairs for sector rotation
        fast_ewmac_pairs = [
            (2, 8),
            (4, 16),
            (8, 32),
        ]

        trade_set = trader.generate_trades(
            start_date="2020-01-01",
            ewmac_pairs=fast_ewmac_pairs,
            portfolio_weights_method="risk_parity",
            apply_buffering=True,
        )

        return trader, trade_set

    def monitor_risk_continuously(self):
        """
        Demonstrate continuous risk monitoring.

        In a live system, this would run regularly to check risk limits.
        """
        if self.trader is None:
            logger.warning("No trader initialized")
            return

        print("\n" + "=" * 70)
        print("CONTINUOUS RISK MONITORING")
        print("=" * 70)

        # Get current risk metrics
        summary = self.trader.get_pipeline_summary()

        # Check leverage
        current_leverage = summary.get('portfolio_leverage', 0)
        max_leverage = self.custom_configs['position'].max_leverage

        print(f"\nLeverage Check:")
        print(f"  Current: {current_leverage:.2f}x")
        print(f"  Maximum: {max_leverage:.2f}x")
        print(f"  Status: {'✓ OK' if current_leverage <= max_leverage else '⚠ WARNING'}")

        # Check concentration
        capital_alloc = summary.get('capital_allocation', {})
        max_allocation = max(capital_alloc.values()) if capital_alloc else 0
        max_pct = (max_allocation / self.trader.capital) * 100

        print(f"\nConcentration Check:")
        print(f"  Largest position: {max_pct:.1f}%")
        print(f"  Maximum allowed: {self.custom_configs['position'].max_position_size * 100:.1f}%")
        print(f"  Status: {'✓ OK' if max_pct <= self.custom_configs['position'].max_position_size * 100 else '⚠ WARNING'}")

        # Get full risk report
        print(f"\n{'DETAILED RISK REPORT':-^70}")
        risk_report = self.trader.get_risk_report()
        print(risk_report)

        print("=" * 70)


def main():
    """
    Main function demonstrating advanced features.
    """
    print("\n" + "=" * 80)
    print("ADVANCED SYSTEMATIC TRADER - CUSTOM CONFIGURATIONS")
    print("=" * 80)

    advanced = AdvancedTrader()

    # Example 1: Multi-Asset Portfolio with Custom EWMAC
    print("\n[EXAMPLE 1] Multi-Asset Portfolio with Custom Trend Following")
    print("-" * 80)

    trader = advanced.create_multi_asset_trader(capital=500_000)
    trade_set = advanced.run_with_custom_ewmac_pairs(start_date="2018-01-01")

    print(f"\n✓ Generated {trade_set.num_trades} trades")
    print(f"  Total notional: ${trade_set.total_notional:,.2f}")

    if trade_set.num_trades > 0:
        print(f"\n{'TOP TRADES BY NOTIONAL':-^80}")
        sorted_trades = sorted(trade_set.trades, key=lambda t: t.notional, reverse=True)
        for trade in sorted_trades[:5]:  # Top 5
            print(
                f"  {trade.action:4} {trade.ticker:5} | "
                f"{trade.contracts:7.2f} @ ${trade.price:8.2f} | "
                f"${trade.notional:>12,.0f} | Forecast: {trade.forecast:+6.2f}"
            )

    # Monitor risk
    advanced.monitor_risk_continuously()

    # Example 2: Sector Rotation Strategy
    print("\n\n[EXAMPLE 2] Active Sector Rotation Strategy")
    print("-" * 80)

    sector_trader, sector_trades = advanced.run_sector_rotation(capital=250_000)

    print(f"\n✓ Generated {sector_trades.num_trades} sector rotation trades")
    print(f"  Total notional: ${sector_trades.total_notional:,.2f}")

    sector_summary = sector_trader.get_pipeline_summary()
    print(f"\n{'SECTOR ALLOCATION':-^80}")
    for ticker, capital in sector_summary['capital_allocation'].items():
        forecast = sector_summary['current_forecasts'].get(ticker, 0)
        signal = "LONG" if forecast > 0 else "SHORT" if forecast < 0 else "FLAT"
        print(f"  {ticker:5} ${capital:>12,.0f} | Forecast: {forecast:+6.2f} [{signal}]")

    print("\n" + "=" * 80)
    print("ADVANCED EXAMPLES COMPLETE")
    print("=" * 80)
    print("\nKey Advanced Features Demonstrated:")
    print("  ✓ Custom volatility estimation parameters")
    print("  ✓ Custom EWMAC pairs and forecast weights")
    print("  ✓ Multiple portfolio weighting methods")
    print("  ✓ Risk monitoring and constraint checking")
    print("  ✓ Different strategies for different markets")
    print("  ✓ Position buffering to control turnover")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()