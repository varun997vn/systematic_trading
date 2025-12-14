"""
Example: Calculate correlation between tickers
Demonstrates the get_ticker_correlation() method
"""

from st.data import DataManager

# Initialize DataManager
dm = DataManager()

# Define tickers to analyze
tickers = ["AAPL", "MSFT", "GOOGL", "SPY", "TLT", "GLD"]

# Calculate correlation matrix
print("=" * 60)
print("CORRELATION MATRIX - Tech Stocks + Diversifiers")
print("=" * 60)

corr_matrix = dm.get_ticker_correlation(
    tickers=tickers,
    start_date="2020-01-01",
    end_date="2024-12-01",
    return_type="log",  # Use log returns (Carver's preference)
    min_periods=100,
)

print("\nCorrelation Matrix:")
print(corr_matrix.round(3))

# Analyze specific pairs
print("\n" + "=" * 60)
print("KEY CORRELATION INSIGHTS")
print("=" * 60)

if not corr_matrix.empty:
    # Tech stocks correlations
    if "AAPL" in corr_matrix.index and "MSFT" in corr_matrix.columns:
        print(f"\nAPPL vs MSFT: {corr_matrix.loc['AAPL', 'MSFT']:.3f}")

    if "AAPL" in corr_matrix.index and "GOOGL" in corr_matrix.columns:
        print(f"APPL vs GOOGL: {corr_matrix.loc['AAPL', 'GOOGL']:.3f}")

    # Diversification benefits
    if "SPY" in corr_matrix.index and "TLT" in corr_matrix.columns:
        print(f"\nSPY vs TLT (stocks vs bonds): {corr_matrix.loc['SPY', 'TLT']:.3f}")

    if "SPY" in corr_matrix.index and "GLD" in corr_matrix.columns:
        print(f"SPY vs GLD (stocks vs gold): {corr_matrix.loc['SPY', 'GLD']:.3f}")

    # Average correlation per ticker
    print("\n" + "=" * 60)
    print("AVERAGE CORRELATION (excl. self)")
    print("=" * 60)
    for ticker in corr_matrix.index:
        # Exclude diagonal (self-correlation = 1.0)
        avg_corr = corr_matrix.loc[ticker].drop(ticker).mean()
        print(f"{ticker:6s}: {avg_corr:.3f}")

# Example: Portfolio diversification analysis
print("\n" + "=" * 60)
print("PORTFOLIO DIVERSIFICATION ANALYSIS")
print("=" * 60)

# Compare different portfolio compositions
portfolios = {
    "Tech Only": ["AAPL", "MSFT", "GOOGL"],
    "Diversified": ["SPY", "TLT", "GLD"],
    "Mixed": ["AAPL", "SPY", "TLT"],
}

for name, portfolio_tickers in portfolios.items():
    corr = dm.get_ticker_correlation(
        tickers=portfolio_tickers,
        start_date="2020-01-01",
        return_type="log",
    )

    if not corr.empty:
        # Calculate average pairwise correlation
        n = len(corr)
        total_corr = corr.sum().sum() - n  # Exclude diagonal
        avg_corr = total_corr / (n * (n - 1))

        print(f"\n{name}:")
        print(f"  Tickers: {', '.join(portfolio_tickers)}")
        print(f"  Avg Correlation: {avg_corr:.3f}")
        print(f"  Diversification Benefit: {'High' if avg_corr < 0.5 else 'Medium' if avg_corr < 0.7 else 'Low'}")

print("\n" + "=" * 60)
print("CARVER'S DIVERSIFICATION INSIGHTS")
print("=" * 60)
print("""
Lower correlation = Better diversification
- < 0.3: Excellent diversification
- 0.3-0.5: Good diversification  
- 0.5-0.7: Moderate diversification
- > 0.7: Limited diversification

Use correlation for:
1. Instrument Diversification Multiplier (IDM) calculation
2. Portfolio weight optimization
3. Risk budgeting
4. Hedging strategy development
""")