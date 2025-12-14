"""
Simple Trader Example - Quick Start
Minimal example showing how to use the systematic trading framework.
"""

from st.trader import Trader
from utils.logger import setup_logger

logger = setup_logger(__name__)


def simple_example():
    """
    Simplest possible example - just the essentials.
    """
    print("\n" + "=" * 60)
    print("SIMPLE SYSTEMATIC TRADER - QUICK START")
    print("=" * 60)

    # Step 1: Define your portfolio
    tickers = ["SPY", "TLT", "GLD"]  # Stocks, Bonds, Gold
    capital = 100_000  # $100k starting capital

    # Step 2: Create the trader
    trader = Trader(
        tickers=tickers,
        capital=capital,
    )

    print(f"\n✓ Trader initialized with {len(tickers)} instruments")
    print(f"  Portfolio: {', '.join(tickers)}")
    print(f"  Capital: ${capital:,.0f}")

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

    print("\n" + "=" * 60)
    print("That's it! The system handled everything:")
    print("  ✓ Data loading & validation")
    print("  ✓ Volatility estimation")
    print("  ✓ Trend signal generation")
    print("  ✓ Position sizing")
    print("  ✓ Risk management")
    print("=" * 60 + "\n")

    return trader, trade_set


if __name__ == "__main__":
    trader, trades = simple_example()

    # Optionally execute the trades (simulated)
    if trades.num_trades > 0:
        print("💡 To execute these trades in a live system:")
        print("   1. Connect to your broker's API")
        print("   2. Send the trade orders")
        print("   3. Call trader.update_positions(trades)")
        print("   4. Run generate_trades() again daily/weekly")
