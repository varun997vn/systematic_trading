"""
Complete example of Carver-style systematic trading system using uncorrelated ETFs.

This script demonstrates:
1. Data acquisition for multiple uncorrelated asset classes
2. Strategy creation (EWMAC, Carry, Mean Reversion, Turtle)
3. Forecast combination with correlation analysis
4. Portfolio construction with IDM calculation
5. Position sizing and buffering
6. Performance reporting

ETFs selected for low correlation:
- SPY: US Large Cap Equities
- TLT: US Long-Term Treasuries (negative correlation to stocks)
- GLD: Gold (diversifier, inflation hedge)
- DBC: Commodities (different cycle than equities)
- VNQ: Real Estate (different fundamentals)
"""

import warnings
from datetime import datetime
from pathlib import Path

import pandas as pd

# Assuming the modules are in a package called 'st' (systematic trading)
# Adjust imports based on your actual package structure
from st.dto.data import PriceDataDTO, CorrelationDTO
from st.dto.forecast import CombinedForecastDTO
from st.dto.portfolio import (
    PortfolioDTO,
    InstrumentDTO
)
from st.dto.position import (
    PortfolioRiskTargetDTO,
    PositionPipelineDTO
)
from st.dto.strategy import (
    EWMACStrategyDTO,
    CarryStrategyDTO,
    MeanReversionStrategyDTO,
    TurtleStrategyDTO,
    ForecastConfig
)

warnings.filterwarnings('ignore')

# ============================================================================
# Configuration
# ============================================================================

# Data parameters
START_DATE = datetime(2018, 1, 1)
END_DATE = datetime(2024, 12, 1)

# Portfolio parameters
INITIAL_CAPITAL = 100_000  # $100k
TARGET_VOLATILITY = 0.20  # 20% annual volatility target
BUFFER_FRACTION = 0.10  # 10% position change threshold

# ETF tickers - selected for low correlation
TICKERS = {
    'SPY': 'US Equities',
    'TLT': 'Long-Term Treasuries',
    'GLD': 'Gold',
    'DBC': 'Commodities',
    'VNQ': 'Real Estate'
}

print("=" * 80)
print("CARVER SYSTEMATIC TRADING - MULTI-ASSET PORTFOLIO")
print("=" * 80)
print(f"\nPortfolio Configuration:")
print(f"  Capital:          ${INITIAL_CAPITAL:,.0f}")
print(f"  Target Vol:       {TARGET_VOLATILITY:.1%}")
print(f"  Date Range:       {START_DATE.date()} to {END_DATE.date()}")
print(f"  Instruments:      {len(TICKERS)}")
for ticker, name in TICKERS.items():
    print(f"    {ticker:6s} - {name}")
print()

# ============================================================================
# Step 1: Data Acquisition
# ============================================================================

print("Step 1: Acquiring price data...")
print("-" * 80)

price_data_dict = {}
for ticker in TICKERS.keys():
    try:
        price_data = PriceDataDTO(
            ticker=ticker,
            start_date=START_DATE,
            end_date=END_DATE
        )
        price_data_dict[ticker] = price_data
        print(f"✓ {ticker}: {len(price_data.data)} observations")
    except Exception as e:
        print(f"✗ {ticker}: Failed - {e}")

if len(price_data_dict) < 2:
    raise ValueError("Need at least 2 instruments for portfolio construction")

print(f"\nSuccessfully loaded {len(price_data_dict)} instruments\n")

# ============================================================================
# Step 2: Analyze Instrument Correlations
# ============================================================================

print("Step 2: Analyzing instrument return correlations...")
print("-" * 80)

correlation_dto = CorrelationDTO(
    price_datas=list(price_data_dict.values()),
    return_type='log'
)

print("\nReturn Correlation Matrix:")
print(correlation_dto.correlation_matrix.round(3).to_string())

# Check for diversification
print("\nCorrelation Analysis:")
for i, ticker_a in enumerate(correlation_dto.correlation_matrix.columns):
    for ticker_b in correlation_dto.correlation_matrix.columns[i + 1:]:
        corr = correlation_dto.correlation_matrix.loc[ticker_a, ticker_b]

        if abs(corr) < 0.3:
            status = "✓ Excellent diversification"
        elif abs(corr) < 0.5:
            status = "✓ Good diversification"
        elif abs(corr) < 0.7:
            status = "⚠ Moderate correlation"
        else:
            status = "✗ High correlation"

        print(f"  {ticker_a} <-> {ticker_b}: {corr:6.3f}  {status}")

print()

# ============================================================================
# Step 3: Create Strategies for Each Instrument
# ============================================================================

print("Step 3: Creating trading strategies for each instrument...")
print("-" * 80)

# Shared forecast configuration
forecast_config = ForecastConfig(
    target_abs_forecast=10.0,
    min_forecast=-20.0,
    max_forecast=20.0,
    cap_forecasts=True,
    use_volatility_standardization=True
)

# Store strategies per instrument
instrument_strategies = {}

for ticker, price_data in price_data_dict.items():
    print(f"\n{ticker} ({TICKERS[ticker]}):")

    strategies = {}

    # EWMAC 16/64 (fast trend following)
    try:
        ewmac_fast = EWMACStrategyDTO(
            price_data=price_data,
            fast_span=16,
            slow_span=64,
            volatility_model='ewma',
            forecast_config=forecast_config
        )
        strategies['EWMAC_16_64'] = ewmac_fast
        print(f"  ✓ EWMAC 16/64")
    except Exception as e:
        print(f"  ✗ EWMAC 16/64: {e}")

    # EWMAC 32/128 (slower trend following)
    try:
        ewmac_slow = EWMACStrategyDTO(
            price_data=price_data,
            fast_span=32,
            slow_span=128,
            volatility_model='ewma',
            forecast_config=forecast_config
        )
        strategies['EWMAC_32_128'] = ewmac_slow
        print(f"  ✓ EWMAC 32/128")
    except Exception as e:
        print(f"  ✗ EWMAC 32/128: {e}")

    # Carry strategy (for non-equity assets)
    if ticker != 'SPY':  # Carry works better for bonds, commodities, etc.
        try:
            carry = CarryStrategyDTO(
                price_data=price_data,
                smoothing_span=30,
                volatility_model='ewma',
                forecast_config=forecast_config
            )
            strategies['Carry_30'] = carry
            print(f"  ✓ Carry 30")
        except Exception as e:
            print(f"  ✗ Carry 30: {e}")

    # Mean reversion (cautious - can conflict with trend following)
    try:
        mean_rev = MeanReversionStrategyDTO(
            price_data=price_data,
            lookback=20,
            entry_threshold=2.0,
            volatility_model='ewma',
            forecast_config=forecast_config
        )
        strategies['MeanRev_20'] = mean_rev
        print(f"  ✓ Mean Reversion 20")
    except Exception as e:
        print(f"  ✗ Mean Reversion 20: {e}")

    # Turtle breakout
    try:
        turtle = TurtleStrategyDTO(
            price_data=price_data,
            entry_window=20,
            exit_window=10,
            volatility_model='ewma',
            forecast_config=forecast_config
        )
        strategies['Turtle_20_10'] = turtle
        print(f"  ✓ Turtle 20/10")
    except Exception as e:
        print(f"  ✗ Turtle 20/10: {e}")

    instrument_strategies[ticker] = strategies

print()

# ============================================================================
# Step 4: Combine Forecasts Within Each Instrument
# ============================================================================

print("Step 4: Combining forecasts within each instrument...")
print("-" * 80)

combined_forecasts = {}

for ticker, strategies in instrument_strategies.items():
    print(f"\n{ticker}:")

    if not strategies:
        print(f"  ✗ No valid strategies - skipping")
        continue

    # Combine forecasts with auto-filtering of highly correlated strategies
    try:
        combined = CombinedForecastDTO(
            strategies=strategies,
            forecast_config=forecast_config,
            auto_filter_correlated=True  # Remove redundant strategies
        )

        combined_forecasts[ticker] = combined

        # Print results
        print(f"  Strategies used: {list(combined.strategies.keys())}")
        print(f"  FDM: {combined.fdm_calculator.fdm:.4f}")

        # Show if any were filtered
        original_count = len(strategies)
        final_count = len(combined.strategies)
        if final_count < original_count:
            removed = set(strategies.keys()) - set(combined.strategies.keys())
            print(f"  ⚠ Auto-removed {original_count - final_count} correlated: {removed}")

        # Show forecast correlation matrix
        if len(combined.strategies) > 1:
            print(f"  Forecast correlations:")
            print(combined.forecast_correlation.round(3).to_string().replace('\n', '\n    '))

    except Exception as e:
        print(f"  ✗ Failed to combine forecasts: {e}")

print()

# ============================================================================
# Step 5: Build Multi-Instrument Portfolio
# ============================================================================

print("Step 5: Building multi-instrument portfolio...")
print("-" * 80)

# Create portfolio risk target
portfolio_risk = PortfolioRiskTargetDTO(
    annual_volatility_target=TARGET_VOLATILITY,
    notional_trading_capital=INITIAL_CAPITAL
)

# Create instruments
instruments = {}
for ticker in combined_forecasts.keys():
    instrument = InstrumentDTO(
        ticker=ticker,
        price_data=price_data_dict[ticker],
        combined_forecast=combined_forecasts[ticker],
        fx_rate=1.0  # All USD-denominated
    )
    instruments[ticker] = instrument
    print(f"  ✓ Created instrument: {ticker}")

# Build portfolio with equal weighting
print("\nBuilding portfolio with equal weights...")
portfolio = PortfolioDTO(
    instruments=instruments,
    portfolio_risk_target=portfolio_risk,
    weighting_method='equal'
)

# Print portfolio summary
print(portfolio.get_portfolio_summary())

# ============================================================================
# Step 6: Calculate Positions with Buffering
# ============================================================================

print("Step 6: Calculating positions with buffering...")
print("-" * 80)

position_histories = {}
final_positions = {}

for ticker, instrument in portfolio.instruments.items():
    print(f"\n{ticker}:")

    # Get the basic position from portfolio (no buffering yet)
    portfolio_position = portfolio.get_position(ticker)

    # Apply buffering and rounding pipeline
    position_pipeline = PositionPipelineDTO(
        combined_forecast=instrument.combined_forecast.combined_forecast,
        instrument_volatility=instrument.volatility.annual_vol,
        price=instrument.price_data.data['Close'],
        portfolio_risk_target=portfolio_risk,
        instrument_weight=portfolio.instrument_weights.weights[ticker],
        idm=portfolio.idm_calculator.idm,
        fx_rate=instrument.fx_rate,
        current_position=None,  # Starting fresh (no existing positions)
        buffer_fraction=BUFFER_FRACTION,
        min_position_size=1.0
    )

    position_histories[ticker] = position_pipeline.final_position
    final_positions[ticker] = position_pipeline.final_position.iloc[-1]

    # Statistics
    mean_pos = position_pipeline.final_position.abs().mean()
    max_pos = position_pipeline.final_position.abs().max()
    current_pos = position_pipeline.final_position.iloc[-1]

    print(f"  Mean |position|:    {mean_pos:6.2f}")
    print(f"  Max |position|:     {max_pos:6.2f}")
    print(f"  Current position:   {current_pos:6.2f}")
    print(f"  Instrument weight:  {portfolio.instrument_weights.weights[ticker]:.1%}")

print()

# ============================================================================
# Step 7: Portfolio Metrics and Summary
# ============================================================================

print("Step 7: Portfolio metrics and summary")
print("-" * 80)

# Current positions DataFrame
current_positions_df = portfolio.get_current_positions()
print("\nCurrent Portfolio Positions:")
print(current_positions_df.round(2).to_string())

# Position history
position_history_df = portfolio.get_position_history()
print(f"\nPosition History:")
print(f"  Shape: {position_history_df.shape}")
print(f"  Date range: {position_history_df.index[0]} to {position_history_df.index[-1]}")

# Calculate portfolio statistics
print("\nPortfolio Statistics:")
print(f"  Number of instruments:        {len(instruments)}")
print(f"  IDM:                          {portfolio.idm_calculator.idm:.4f}")
print(f"  Diversification ratio:        {portfolio.idm_calculator.get_diversification_ratio():.1%}")
print(f"  Expected portfolio vol:       {portfolio.portfolio_metrics['expected_portfolio_vol']:.2%}")
print(f"  Target portfolio vol:         {portfolio.portfolio_metrics['target_portfolio_vol']:.2%}")
print(f"  Vol ratio (expected/target):  {portfolio.portfolio_metrics['vol_ratio']:.2f}x")

# Per-instrument metrics
print("\nPer-Instrument Metrics:")
print(f"{'Ticker':<8} {'Weight':<8} {'Strategies':<4} {'FDM':<6} {'Mean|Pos|':<10} {'Current Pos':<12}")
print("-" * 70)
for ticker in instruments.keys():
    weight = portfolio.instrument_weights.weights[ticker]
    n_strat = len(combined_forecasts[ticker].strategies)
    fdm = combined_forecasts[ticker].fdm_calculator.fdm
    mean_pos = position_histories[ticker].abs().mean()
    current = final_positions[ticker]

    print(f"{ticker:<8} {weight:<8.1%} {n_strat:<4} {fdm:<6.3f} {mean_pos:<10.2f} {current:<12.2f}")

# ============================================================================
# Step 8: Save Results
# ============================================================================

print("\n" + "=" * 80)
print("Step 8: Saving results...")
print("-" * 80)

output_dir = Path("./output")
output_dir.mkdir(exist_ok=True)

# Save position history
position_history_df.to_csv(output_dir / "position_history.csv")
print(f"✓ Saved position history to {output_dir / 'position_history.csv'}")

# Save current positions
current_positions_df.to_csv(output_dir / "current_positions.csv")
print(f"✓ Saved current positions to {output_dir / 'current_positions.csv'}")

# Save instrument correlations
correlation_dto.correlation_matrix.to_csv(output_dir / "instrument_correlations.csv")
print(f"✓ Saved correlations to {output_dir / 'instrument_correlations.csv'}")

# Save forecast details per instrument
for ticker, combined in combined_forecasts.items():
    forecast_df = pd.DataFrame({
        'combined_forecast': combined.combined_forecast,
        'combined_forecast_raw': combined.combined_forecast_raw,
    })

    # Add individual strategy forecasts
    for strat_name, strategy in combined.strategies.items():
        forecast_df[f'{strat_name}_scaled'] = strategy.forecasts_scaled

    forecast_df.to_csv(output_dir / f"forecasts_{ticker}.csv")
    print(f"✓ Saved {ticker} forecasts to {output_dir / f'forecasts_{ticker}.csv'}")

# Create summary report
with open(output_dir / "portfolio_summary.txt", 'w') as f:
    f.write(portfolio.get_portfolio_summary())
    f.write("\n\n")
    f.write("FORECAST CORRELATION ANALYSIS\n")
    f.write("=" * 80 + "\n\n")

    for ticker, combined in combined_forecasts.items():
        f.write(f"\n{ticker}:\n")
        f.write(combined.correlation_analysis.get_recommendation_summary())
        f.write("\n")

print(f"✓ Saved summary report to {output_dir / 'portfolio_summary.txt'}")

# ============================================================================
# Step 9: Simple Backtest Metrics
# ============================================================================

print("\n" + "=" * 80)
print("Step 9: Calculating simple backtest metrics...")
print("-" * 80)

# Calculate P&L per instrument (simplified - actual implementation would be more complex)
print("\nNote: This is a simplified P&L calculation for demonstration.")
print("Real implementation should account for:")
print("  - Exact entry/exit prices")
print("  - Transaction costs (spreads, commissions)")
print("  - Slippage")
print("  - Dividends/interest")
print()

for ticker in instruments.keys():
    instrument = instruments[ticker]
    positions = position_histories[ticker]
    prices = instrument.price_data.data['Close']
    returns = instrument.returns.returns

    # Align positions and returns
    positions_aligned, returns_aligned = positions.align(returns, join='inner')

    # Calculate daily P&L (position[t-1] * return[t])
    daily_pnl = positions_aligned.shift(1) * returns_aligned * prices.loc[returns_aligned.index]

    # Statistics
    total_pnl = daily_pnl.sum()
    sharpe = daily_pnl.mean() / daily_pnl.std() * (252 ** 0.5) if daily_pnl.std() > 0 else 0

    print(f"{ticker}:")
    print(f"  Total P&L (simplified):  ${total_pnl:,.2f}")
    print(f"  Sharpe Ratio:            {sharpe:.2f}")
    print(f"  Daily Vol:               ${daily_pnl.std():,.2f}")

# ============================================================================
# Final Summary
# ============================================================================

print("\n" + "=" * 80)
print("EXECUTION COMPLETE")
print("=" * 80)
print("\nSystem successfully built a Carver-style systematic portfolio with:")
print(f"  ✓ {len(instruments)} uncorrelated instruments")
print(f"  ✓ {sum(len(c.strategies) for c in combined_forecasts.values())} total strategy forecasts")
print(f"  ✓ Diversification benefit captured (IDM = {portfolio.idm_calculator.idm:.4f})")
print(f"  ✓ Risk budget validated (vol ratio = {portfolio.portfolio_metrics['vol_ratio']:.2f}x)")
print(f"\nAll results saved to: {output_dir.absolute()}")
print("\nNext steps:")
print("  1. Review forecast correlations in portfolio_summary.txt")
print("  2. Implement proper backtesting with transaction costs")
print("  3. Add live execution capabilities")
print("  4. Monitor and rebalance positions")
print("=" * 80)
