"""
Main demonstration script for systematic trading system.

This script demonstrates:
1. Downloading SGX stock data
2. Implementing a trend-following strategy
3. Running a backtest with proper position sizing
4. Analyzing performance

Based on Robert Carver's "Systematic Trading" principles.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from data.data_manager import DataManager
from strategy.trend_following import EWMAC, MovingAverageCrossover
from risk_management.position_sizer import PositionSizer
from backtesting.backtest_engine import BacktestEngine
from backtesting.performance import PerformanceAnalyzer
from config.settings import Settings
from utils.logger import setup_logger


# Set up logging
logger = setup_logger(__name__, log_file='systematic_trading.log')


def main():
    """
    Main demonstration function.
    """
    logger.info("=" * 60)
    logger.info("SYSTEMATIC TRADING SYSTEM - SGX DEMO")
    logger.info("Based on Robert Carver's 'Systematic Trading'")
    logger.info("=" * 60)

    # Validate settings
    Settings.validate()

    # Define SGX stocks to test
    sgx_stocks = ['DBS.SI', 'O39.SI', 'ES3.SI']
    logger.info(f"\nTesting with SGX stocks: {sgx_stocks}")

    # =========================================================================
    # STEP 1: Download Data
    # =========================================================================
    print("\n[STEP 1] Downloading historical data from Yahoo Finance...")
    logger.info("Downloading historical data...")

    data_manager = DataManager()

    # Download data for all stocks
    stock_data = data_manager.download_multiple_stocks(
        tickers=sgx_stocks,
        start_date=Settings.DATA_START_DATE,
        end_date=Settings.DATA_END_DATE,
        save=True
    )

    if not stock_data:
        logger.error("Failed to download any data. Exiting.")
        return

    print(f"✓ Successfully downloaded data for {len(stock_data)} stocks")

    # Display sample data
    for ticker, df in stock_data.items():
        print(f"\n{ticker}: {len(df)} rows from {df.index[0]} to {df.index[-1]}")
        print(df.head())

    # =========================================================================
    # STEP 2: Run Single-Stock Backtest
    # =========================================================================
    print("\n[STEP 2] Running backtest on DBS.SI with EWMAC strategy...")
    logger.info("Running single-stock backtest...")

    # Select DBS for detailed analysis
    ticker = 'DBS.SI'
    data = stock_data[ticker]

    # Create EWMAC strategy (Carver's preferred method)
    strategy = EWMAC(fast_span=16, slow_span=64, name="EWMAC_16_64")

    # Create position sizer with volatility targeting
    position_sizer = PositionSizer(
        capital=Settings.INITIAL_CAPITAL,
        volatility_target=Settings.VOLATILITY_TARGET
    )

    # Create backtest engine
    backtest_engine = BacktestEngine(
        initial_capital=Settings.INITIAL_CAPITAL,
        transaction_cost=Settings.TRANSACTION_COST,
        slippage=Settings.SLIPPAGE
    )

    # Run backtest
    results = backtest_engine.run(
        strategy=strategy,
        data=data,
        position_sizer=position_sizer
    )

    # =========================================================================
    # STEP 3: Analyze Performance
    # =========================================================================
    print("\n[STEP 3] Analyzing performance...")
    logger.info("Analyzing performance...")

    analyzer = PerformanceAnalyzer(results)
    analyzer.print_summary()

    # Generate plots
    print("\nGenerating performance charts...")
    analyzer.plot_equity_curve(show=False, save_path=Path('equity_curve.png'))
    analyzer.plot_positions(show=False, save_path=Path('positions.png'))
    print("✓ Charts saved: equity_curve.png, positions.png")

    # =========================================================================
    # STEP 4: Compare Strategies
    # =========================================================================
    print("\n[STEP 4] Comparing different strategies on DBS.SI...")
    logger.info("Comparing strategies...")

    strategies_to_test = [
        EWMAC(fast_span=16, slow_span=64, name="EWMAC_16_64"),
        EWMAC(fast_span=32, slow_span=128, name="EWMAC_32_128"),
        MovingAverageCrossover(fast_period=16, slow_period=64, name="MA_16_64"),
    ]

    comparison_results = []

    for strat in strategies_to_test:
        result = backtest_engine.run(strat, data, position_sizer)
        comparison_results.append({
            'strategy': strat.name,
            'total_return': result['total_return'],
            'annualized_return': result['annualized_return'],
            'sharpe_ratio': result['sharpe_ratio'],
            'max_trades': result['total_trades'],
        })

    # Print comparison table
    print("\nStrategy Comparison:")
    print("-" * 80)
    print(f"{'Strategy':<20} {'Total Return':>15} {'Annual Return':>15} {'Sharpe':>10} {'Trades':>10}")
    print("-" * 80)

    for res in comparison_results:
        print(
            f"{res['strategy']:<20} "
            f"{res['total_return']:>14.2%} "
            f"{res['annualized_return']:>14.2%} "
            f"{res['sharpe_ratio']:>10.2f} "
            f"{res['max_trades']:>10.0f}"
        )

    print("-" * 80)

    # =========================================================================
    # STEP 5: Multi-Asset Portfolio Backtest
    # =========================================================================
    print("\n[STEP 5] Running multi-asset portfolio backtest...")
    logger.info("Running multi-asset backtest...")

    # Use EWMAC strategy for all assets
    portfolio_strategy = EWMAC(fast_span=16, slow_span=64, name="EWMAC_Portfolio")

    portfolio_results = backtest_engine.run_multiple_assets(
        strategy=portfolio_strategy,
        data_dict=stock_data,
        position_sizer=position_sizer
    )

    print("\nPortfolio Performance:")
    print("-" * 60)
    print(f"Total Return: {portfolio_results['total_return']:.2%}")
    print(f"Annualized Return: {portfolio_results['annualized_return']:.2%}")
    print(f"Annualized Volatility: {portfolio_results['annualized_volatility']:.2%}")
    print(f"Sharpe Ratio: {portfolio_results['sharpe_ratio']:.2f}")
    print("-" * 60)

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "=" * 60)
    print("DEMO COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("\nKey takeaways from Carver's approach:")
    print("1. ✓ Volatility targeting for consistent risk exposure")
    print("2. ✓ Transaction costs and slippage accounted for")
    print("3. ✓ Multiple timeframes for diversification")
    print("4. ✓ Portfolio approach across multiple assets")
    print("\nNext steps:")
    print("- Experiment with different EWMAC combinations")
    print("- Add more SGX stocks to the portfolio")
    print("- Implement forecast combination rules")
    print("- Add carry and mean reversion strategies")
    print("=" * 60 + "\n")

    logger.info("Demo completed successfully")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
        logger.info("Demo interrupted by user")
    except Exception as e:
        logger.error(f"Error in demo: {e}", exc_info=True)
        print(f"\nError: {e}")
        raise
