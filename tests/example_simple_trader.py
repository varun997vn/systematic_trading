"""
Simple Trader Example - Quick Start
Minimal example showing how to use the systematic trading framework.

UPDATED: Now demonstrates the modular forecast configuration system
"""

from st.trader import Trader, TradingRulesConfig, TradingRuleConfig, RuleType
from utils.logger import setup_logger

logger = setup_logger(__name__)


def simple_example():
    """
    Simplest possible example - just the essentials.
    Uses default Carver's EWMAC suite.
    """
    print("\n" + "=" * 60)
    print("SIMPLE SYSTEMATIC TRADER - QUICK START")
    print("=" * 60)

    # Step 1: Define your portfolio
    tickers = ["SPY", "TLT", "GLD"]  # Stocks, Bonds, Gold
    capital = 100_000  # $100k starting capital

    # Step 2: Create the trader (uses Carver's standard EWMAC suite by default)
    trader = Trader(
        tickers=tickers,
        capital=capital,
    )

    print(f"\n✓ Trader initialized with {len(tickers)} instruments")
    print(f"  Portfolio: {', '.join(tickers)}")
    print(f"  Capital: ${capital:,.0f}")
    print(f"  Strategy: Carver's Standard EWMAC Suite (6 variations)")

    # Step 3: Generate trades
    print("\n⏳ Running trading pipeline...")
    trade_set = trader.generate_trades(
        start_date="2020-01-01",  # Historical data from 2020
    )

    # Step 4: Review the trades
    print(f"\n✓ Pipeline complete!")
    print(f"  Generated {trade_set.num_trades} trades")
    print(f"  Total notional: ${trade_set.total_notional:,.2f}")

    if trade_set.num_trades > 0:
        print(f"\n{'TRADES':-^60}")
        for trade in trade_set.trades:
            print(
                f"  {trade.action:4} {trade.ticker:5} | "
                f"{trade.contracts:6.2f} contracts @ ${trade.price:8.2f} | "
                f"Forecast: {trade.forecast:+6.2f}"
            )
    else:
        print("\n  No trades needed - portfolio at target positions")

    # Step 5: Get portfolio summary
    summary = trader.get_pipeline_summary()

    print(f"\n{'PORTFOLIO STATUS':-^60}")
    print(f"  Leverage: {summary['portfolio_leverage']:.2f}x")
    print(f"  Diversification Multiplier (IDM): {summary['idm']:.2f}")

    print(f"\n{'FORECASTS (Trend Signals)':-^60}")
    for ticker, forecast in summary['current_forecasts'].items():
        signal = "BULLISH" if forecast > 5 else "BEARISH" if forecast < -5 else "NEUTRAL"
        print(f"  {ticker:5} {forecast:+6.2f} [{signal}]")

    print(f"\n{'TRADING RULES USED':-^60}")
    for rule_name in summary['rules_used']:
        print(f"  • {rule_name}")

    print("\n" + "=" * 60)
    print("That's it! The system handled everything:")
    print("  ✓ Data loading & validation")
    print("  ✓ Volatility estimation")
    print("  ✓ Trend signal generation (6 EWMAC variations)")
    print("  ✓ Forecast combination")
    print("  ✓ Position sizing")
    print("  ✓ Risk management")
    print("=" * 60 + "\n")

    return trader, trade_set


def custom_strategy_example():
    """
    Example showing custom trading rule configuration.
    """
    print("\n" + "=" * 60)
    print("CUSTOM STRATEGY CONFIGURATION")
    print("=" * 60)

    # Step 1: Define your portfolio
    tickers = ["SPY", "TLT", "GLD"]
    capital = 100_000

    # Step 2: Create custom trading rules configuration
    # Mix of EWMAC and Mean Reversion
    custom_rules = TradingRulesConfig(
        rules=[
            # Primary trend following
            TradingRuleConfig(
                rule_type=RuleType.EWMAC,
                params={'fast_span': 16, 'slow_span': 64},
                weight=0.4,  # 40% weight
                use_volatility_standardization=True
            ),
            # Secondary trend following
            TradingRuleConfig(
                rule_type=RuleType.EWMAC,
                params={'fast_span': 32, 'slow_span': 128},
                weight=0.3,  # 30% weight
                use_volatility_standardization=True
            ),
            # Counter-trend mean reversion
            TradingRuleConfig(
                rule_type=RuleType.MEAN_REVERSION,
                params={'lookback': 30, 'entry_threshold': 2.0},
                weight=0.3,  # 30% weight
                use_volatility_standardization=True
            ),
        ],
        equal_weights=False  # Use the specified weights
    )

    print(f"\n✓ Custom strategy configured:")
    for rule in custom_rules.rules:
        weight_pct = rule.weight * 100 if rule.weight else 0
        print(f"  • {rule.rule_name}: {weight_pct:.0f}% weight")

    # Step 3: Create trader with custom configuration
    trader = Trader(
        tickers=tickers,
        capital=capital,
        trading_rules_config=custom_rules  # Pass custom config
    )

    print(f"\n✓ Trader initialized")
    print(f"  Portfolio: {', '.join(tickers)}")
    print(f"  Capital: ${capital:,.0f}")

    # Step 4: Generate trades
    print("\n⏳ Running trading pipeline...")
    trade_set = trader.generate_trades(start_date="2020-01-01")

    # Step 5: Review results
    print(f"\n✓ Pipeline complete!")
    print(f"  Generated {trade_set.num_trades} trades")
    print(f"  Total notional: ${trade_set.total_notional:,.2f}")

    summary = trader.get_pipeline_summary()

    print(f"\n{'TRADING RULES USED':-^60}")
    for rule_name in summary['rules_used']:
        print(f"  • {rule_name}")

    print(f"\n{'FORECASTS':-^60}")
    for ticker, forecast in summary['current_forecasts'].items():
        signal = "BULLISH" if forecast > 5 else "BEARISH" if forecast < -5 else "NEUTRAL"
        print(f"  {ticker:5} {forecast:+6.2f} [{signal}]")

    print("\n" + "=" * 60 + "\n")

    return trader, trade_set


def multi_strategy_example():
    """
    Example using the built-in multi-strategy suite.
    Includes EWMAC, Carry, Mean Reversion, and Turtle strategies.
    """
    print("\n" + "=" * 60)
    print("MULTI-STRATEGY PORTFOLIO")
    print("=" * 60)

    # Step 1: Use the preset multi-strategy configuration
    multi_strategy = TradingRulesConfig.multi_strategy_suite()

    print(f"\n✓ Multi-strategy suite loaded:")
    print(f"  Total rules: {len(multi_strategy.rules)}")

    weights = multi_strategy.get_weights()
    for rule in multi_strategy.rules:
        weight_pct = weights[rule.rule_name] * 100
        print(f"  • {rule.rule_name}: {weight_pct:.0f}% weight")

    # Step 2: Create trader
    tickers = ["SPY", "TLT", "GLD", "USO"]  # Diversified across asset classes
    capital = 250_000  # Larger capital for multi-strategy

    trader = Trader(
        tickers=tickers,
        capital=capital,
        trading_rules_config=multi_strategy
    )

    print(f"\n✓ Trader initialized")
    print(f"  Portfolio: {', '.join(tickers)}")
    print(f"  Capital: ${capital:,.0f}")

    # Step 3: Generate trades
    print("\n⏳ Running trading pipeline...")
    trade_set = trader.generate_trades(start_date="2020-01-01")

    # Step 4: Review results
    print(f"\n✓ Pipeline complete!")
    print(f"  Generated {trade_set.num_trades} trades")
    print(f"  Total notional: ${trade_set.total_notional:,.2f}")

    if trade_set.num_trades > 0:
        print(f"\n{'TRADES':-^60}")
        for trade in trade_set.trades:
            print(
                f"  {trade.action:4} {trade.ticker:5} | "
                f"{trade.contracts:6.2f} contracts @ ${trade.price:8.2f} | "
                f"Forecast: {trade.forecast:+6.2f}"
            )

    summary = trader.get_pipeline_summary()

    print(f"\n{'PORTFOLIO STATUS':-^60}")
    print(f"  Leverage: {summary['portfolio_leverage']:.2f}x")
    print(f"  Diversification Multiplier (IDM): {summary['idm']:.2f}")

    print(f"\n{'FORECASTS BY INSTRUMENT':-^60}")
    for ticker, forecast in summary['current_forecasts'].items():
        signal = "BULLISH" if forecast > 5 else "BEARISH" if forecast < -5 else "NEUTRAL"
        print(f"  {ticker:5} {forecast:+6.2f} [{signal}]")

    print("\n" + "=" * 60)
    print("Multi-strategy benefits:")
    print("  ✓ Diversified across signal types (trend, reversion, breakout)")
    print("  ✓ Reduced strategy risk through combination")
    print("  ✓ Higher Forecast Diversification Multiplier (FDM)")
    print("  ✓ More robust to different market regimes")
    print("=" * 60 + "\n")

    return trader, trade_set


def dynamic_strategy_switching():
    """
    Example showing how to dynamically switch strategies.
    """
    print("\n" + "=" * 60)
    print("DYNAMIC STRATEGY SWITCHING")
    print("=" * 60)

    tickers = ["SPY", "TLT"]
    capital = 100_000

    # Initialize with Carver's suite
    trader = Trader(tickers=tickers, capital=capital)

    print("\n1️⃣  Starting with Carver's EWMAC suite...")
    trade_set_1 = trader.generate_trades(start_date="2020-01-01")
    print(f"   Generated {trade_set_1.num_trades} trades")

    # Switch to multi-strategy
    print("\n2️⃣  Switching to multi-strategy suite...")
    multi_strategy = TradingRulesConfig.multi_strategy_suite()
    trade_set_2 = trader.generate_trades(
        start_date="2020-01-01",
        trading_rules_config=multi_strategy
    )
    print(f"   Generated {trade_set_2.num_trades} trades")

    # Switch to custom conservative strategy
    print("\n3️⃣  Switching to conservative custom strategy...")
    conservative = TradingRulesConfig(
        rules=[
            TradingRuleConfig(
                rule_type=RuleType.EWMAC,
                params={'fast_span': 32, 'slow_span': 128},
                # Slower, more stable
                weight=0.7
            ),
            TradingRuleConfig(
                rule_type=RuleType.MEAN_REVERSION,
                params={'lookback': 50, 'entry_threshold': 2.5},
                # Higher threshold
                weight=0.3
            ),
        ],
        equal_weights=False
    )
    trade_set_3 = trader.generate_trades(
        start_date="2020-01-01",
        trading_rules_config=conservative
    )
    print(f"   Generated {trade_set_3.num_trades} trades")

    # Permanently update trader's configuration
    print("\n4️⃣  Permanently updating trader configuration...")
    trader.set_trading_rules(conservative)
    trade_set_4 = trader.generate_trades(start_date="2020-01-01")
    print(f"   Generated {trade_set_4.num_trades} trades (using saved config)")

    print("\n" + "=" * 60)
    print("Strategy switching benefits:")
    print("  ✓ Test different strategies without recreating trader")
    print("  ✓ Adapt to market conditions")
    print("  ✓ Easy A/B testing")
    print("  ✓ Save and load configurations")
    print("=" * 60 + "\n")

    return trader, trade_set_4


if __name__ == "__main__":
    print("SYSTEMATIC TRADING FRAMEWORK - EXAMPLES")

    # Example 1: Simple default usage
    print("\n\n📊 Example 1: Simple Default (Carver's EWMAC)")
    print("─" * 60)
    trader1, trades1 = simple_example()

    # Example 2: Custom strategy
    print("\n\n📊 Example 2: Custom Strategy Mix")
    print("─" * 60)
    trader2, trades2 = custom_strategy_example()

    # Example 3: Multi-strategy suite
    print("\n\n📊 Example 3: Multi-Strategy Portfolio")
    print("─" * 60)
    trader3, trades3 = multi_strategy_example()

    # Example 4: Dynamic switching
    print("\n\n📊 Example 4: Dynamic Strategy Switching")
    print("─" * 60)
    trader4, trades4 = dynamic_strategy_switching()

    # Final summary
    print("\n" + "=" * 60)
    print("💡 NEXT STEPS")
    print("=" * 60)
    print("\nTo use in production:")
    print("  1. Choose your strategy configuration")
    print("  2. Connect to your data source (CSV, API, database)")
    print("  3. Connect to your broker's API")
    print("  4. Run generate_trades() on your schedule")
    print("  5. Execute trades and call update_positions()")
    print("  6. Monitor performance and adjust configuration")

    print("\nAvailable strategy presets:")
    print("  • TradingRulesConfig.carver_standard_suite()")
    print("  • TradingRulesConfig.multi_strategy_suite()")
    print("  • Custom: Build your own with TradingRuleConfig")

    print("\nAvailable rule types:")
    print("  • RuleType.EWMAC - Trend following")
    print("  • RuleType.CARRY - Carry/roll yield")
    print("  • RuleType.MEAN_REVERSION - Counter-trend")
    print("  • RuleType.TURTLE - Breakout strategy")

    print("\n" + "=" * 60)
    print("✨ Happy Trading! ✨")
    print("=" * 60 + "\n")
