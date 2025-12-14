---
id: risk
title: Risk Management
sidebar_label: Risk Management
---

# Risk Management Module

**Based on Robert Carver's "Systematic Trading"**

The risk management module provides comprehensive tools for measuring, monitoring, and controlling portfolio risk in systematic trading strategies.

---

## Overview

Risk management is critical in systematic trading. This module implements Carver's risk framework:

- **Position-level risk** - Individual instrument exposure
- **Portfolio-level risk** - Aggregate risk accounting for correlations
- **Diversification benefits** - Instrument Diversification Multiplier (IDM)
- **Capital allocation** - Multiple allocation strategies
- **Risk limits** - Automatic constraint enforcement
- **Real-time monitoring** - Continuous risk tracking

---

## Quick Start

```python
from st.risk import RiskManager
from st.data import DataManager
from st.volatility import VolatilityManager

# Initialize managers
risk_mgr = RiskManager()
data_mgr = DataManager()
vol_mgr = VolatilityManager()

# Get returns for correlation estimation
tickers = ['AAPL', 'MSFT', 'GOOGL']
returns_df = data_mgr.get_returns_df(tickers, start_date='2023-01-01')

# Estimate correlations
correlation_matrix = risk_mgr.estimate_correlations(returns_df)

# Calculate portfolio risk
positions = {'AAPL': 100, 'MSFT': 150, 'GOOGL': 75}
prices = {'AAPL': 180.0, 'MSFT': 380.0, 'GOOGL': 140.0}
volatilities = {'AAPL': 0.25, 'MSFT': 0.22, 'GOOGL': 0.28}

portfolio_risk = risk_mgr.calculate_portfolio_risk(
    positions=positions,
    prices=prices,
    volatilities=volatilities,
    correlation_matrix=correlation_matrix,
    capital=100000
)

# Generate risk report
print(risk_mgr.get_risk_report(portfolio_risk))

# Check limits
all_ok, checks = risk_mgr.check_limits(portfolio_risk)
```

---

## Core Components

### 1. RiskManager

Main interface for all risk management operations.

```python
from st.risk import RiskManager, RiskConfig

# Default configuration
risk_mgr = RiskManager()

# Custom configuration
config = RiskConfig(
    max_instrument_risk=0.15,      # 15% max per instrument
    max_portfolio_risk=0.20,        # 20% max portfolio risk
    max_forecast=20.0,              # Forecast cap at ±20
    max_leverage=2.0,               # 2x max leverage
    correlation_lookback=120,       # 120 days for correlation
    min_correlation_samples=30      # Min 30 samples
)
risk_mgr = RiskManager(config=config)
```

**Key Methods:**

| Method | Description |
|--------|-------------|
| `estimate_correlations()` | Calculate correlation matrix |
| `calculate_portfolio_risk()` | Compute portfolio risk metrics |
| `allocate_capital()` | Distribute capital across instruments |
| `check_limits()` | Verify all risk constraints |
| `get_risk_report()` | Generate formatted risk report |

---

### 2. CorrelationEstimator

Estimates correlations between instrument returns.

```python
from st.risk import CorrelationEstimator

estimator = CorrelationEstimator(
    lookback=120,      # Days of history
    min_samples=30     # Minimum required samples
)

# Standard correlation
corr_matrix = estimator.estimate(returns_df)

# EWMA correlation (Carver's preferred method)
ewma_corr = estimator.ewma_correlation(returns_df, span=60)
```

**Methods:**

- `estimate()` - Standard Pearson correlation
- `ewma_correlation()` - Exponentially weighted correlation
- Returns polars DataFrame with correlation matrix

**Example Output:**

```
        AAPL    MSFT    GOOGL
AAPL    1.000   0.652   0.548
MSFT    0.652   1.000   0.701
GOOGL   0.548   0.701   1.000
```

---

### 3. DiversificationMultiplier

Calculates the Instrument Diversification Multiplier (IDM).

The IDM quantifies the benefit of holding multiple instruments:
- **IDM = 1** → No diversification (single instrument)
- **IDM = 2** → Portfolio volatility is half of average instrument volatility
- **Higher IDM** → Greater diversification benefit

```python
from st.risk import DiversificationMultiplier
import polars as pl

# Equal weights
weights = pl.Series([0.33, 0.33, 0.34])
idm = DiversificationMultiplier.calculate(weights, correlation_matrix)

# Approximate IDM for equal weights
idm_approx = DiversificationMultiplier.calculate_equal_weights(
    n_instruments=3,
    avg_correlation=0.60
)
```

**Carver's Formula:**

```
IDM = 1 / sqrt(w^T * C * w)

where:
  w = instrument weights
  C = correlation matrix
```

---

### 4. RiskCalculator

Computes position and portfolio risk metrics.

```python
from st.risk import RiskCalculator

calculator = RiskCalculator()

# Single position risk
position_risk = calculator.position_risk(
    position_size=100,       # 100 shares
    instrument_price=180.0,  # $180/share
    volatility=0.25,         # 25% annual vol
    capital=100000           # $100k capital
)
# Returns: 0.045 (4.5% of capital at risk)

# Full portfolio risk
portfolio_risk = calculator.portfolio_risk(
    positions={'AAPL': 100, 'MSFT': 150},
    prices={'AAPL': 180.0, 'MSFT': 380.0},
    volatilities={'AAPL': 0.25, 'MSFT': 0.22},
    correlation_matrix=corr_matrix,
    capital=100000
)
```

**PortfolioRisk Attributes:**

| Attribute | Description |
|-----------|-------------|
| `total_capital` | Total available capital |
| `gross_exposure` | Sum of absolute position values |
| `net_exposure` | Net long/short exposure |
| `portfolio_volatility` | Expected portfolio volatility |
| `portfolio_risk` | Portfolio risk as % of capital |
| `diversification_multiplier` | IDM value |
| `leverage` | Gross exposure / capital |
| `num_instruments` | Number of positions |
| `instrument_risks` | Dict of per-instrument risks |

---

### 5. PositionLimits

Enforces risk constraints and position limits.

```python
from st.risk import PositionLimits

limits = PositionLimits()

# Check forecast limit
is_valid, capped = limits.check_forecast_limit(25.0)
# Returns: (False, 20.0) - forecast exceeds ±20 limit

# Check instrument risk
ok = limits.check_instrument_risk(0.15, ticker='AAPL')
# Returns: True if risk <= max_instrument_risk

# Scale position to meet risk target
scaled_pos = limits.scale_for_risk_limit(
    current_risk=0.25,    # Current 25% risk
    target_risk=0.20,     # Target 20% risk
    position_size=100     # Current position
)
# Returns: 80 (scaled down to meet target)
```

**Available Checks:**

- `check_forecast_limit()` - Cap forecasts at ±20
- `check_instrument_risk()` - Verify per-instrument risk
- `check_portfolio_risk()` - Verify total portfolio risk
- `check_leverage()` - Ensure leverage within bounds

---

### 6. CapitalAllocator

Distributes capital across instruments using different strategies.

```python
from st.risk import CapitalAllocator

allocator = CapitalAllocator()

# Equal weight allocation
equal_alloc = allocator.equal_weight(
    tickers=['AAPL', 'MSFT', 'GOOGL'],
    total_capital=100000
)
# Returns: {'AAPL': 33333.33, 'MSFT': 33333.33, 'GOOGL': 33333.34}

# Risk parity (inverse volatility weighting)
risk_parity = allocator.risk_parity(
    tickers=['AAPL', 'MSFT', 'GOOGL'],
    volatilities={'AAPL': 0.25, 'MSFT': 0.20, 'GOOGL': 0.30},
    total_capital=100000
)
# Lower vol instruments get more capital

# Custom weights
custom = allocator.custom_weights(
    weights={'AAPL': 0.5, 'MSFT': 0.3, 'GOOGL': 0.2},
    total_capital=100000
)
# Returns: {'AAPL': 50000, 'MSFT': 30000, 'GOOGL': 20000}
```

**Allocation Methods:**

| Method | Description | Use Case |
|--------|-------------|----------|
| `equal_weight()` | 1/N allocation | Simple diversification |
| `risk_parity()` | Inverse volatility | Equal risk contribution |
| `custom_weights()` | User-defined | Strategic allocation |

---

### 7. RiskMonitor

Real-time risk monitoring and reporting.

```python
from st.risk import RiskMonitor

monitor = RiskMonitor()

# Check all limits
checks = monitor.check_all_limits(portfolio_risk)
# Returns: {'portfolio_risk': True, 'leverage': True, ...}

# Generate formatted report
report = monitor.generate_report(portfolio_risk)
print(report)
```

**Sample Report:**

```
============================================================
PORTFOLIO RISK REPORT
============================================================
Capital: $100,000.00
Gross Exposure: $75,000.00
Net Exposure: $75,000.00
Leverage: 0.75x
Portfolio Risk: 12.50%
Portfolio Volatility: 18.75%
Diversification Multiplier: 1.450
Number of Instruments: 3
Concentration Ratio: 0.577

Instrument Risk Breakdown:
------------------------------------------------------------
✓ AAPL      :  4.50%
✓ MSFT      :  5.70%
✓ GOOGL     :  2.95%

Risk Limits:
------------------------------------------------------------
Max Instrument Risk: 20.00%
Max Portfolio Risk: 25.00%
Max Leverage: 2.00x
============================================================
```

---

## Configuration

### RiskConfig

All risk parameters are configurable via `RiskConfig`:

```python
from st.risk import RiskConfig

config = RiskConfig(
    max_instrument_risk=0.20,       # 20% max per instrument
    max_portfolio_risk=0.25,        # 25% max portfolio risk
    max_forecast=20.0,              # Standard Carver limit
    max_leverage=2.0,               # 2x max leverage
    correlation_lookback=120,       # 120 trading days
    min_correlation_samples=30      # Minimum for valid correlation
)
```

**Parameter Reference:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_instrument_risk` | 0.20 | Max risk per instrument (20%) |
| `max_portfolio_risk` | 0.25 | Max total portfolio risk (25%) |
| `max_forecast` | 20.0 | Forecast scalar cap (Carver standard) |
| `max_leverage` | 2.0 | Maximum portfolio leverage |
| `correlation_lookback` | 120 | Days for correlation estimation |
| `min_correlation_samples` | 30 | Minimum samples for valid correlation |

---

## Advanced Usage

### Multi-Instrument Portfolio Risk

```python
import polars as pl
from st.risk import RiskManager
from st.data import DataManager
from st.volatility import VolatilityManager

# Initialize
risk_mgr = RiskManager()
data_mgr = DataManager()
vol_mgr = VolatilityManager()

# Define portfolio
tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']
capital = 500000

# Get data
returns_df = data_mgr.get_returns_df(tickers, start_date='2023-01-01')

# Calculate volatilities
volatilities = {}
for ticker in tickers:
    vol_result = vol_mgr.estimate_from_returns(
        returns_df[ticker], ticker
    )
    volatilities[ticker] = vol_result.current_annual_vol

# Estimate correlations
correlation_matrix = risk_mgr.estimate_correlations(
    returns_df, method='ewma'
)

# Allocate capital (risk parity)
allocations = risk_mgr.allocate_capital(
    tickers=tickers,
    total_capital=capital,
    method='risk_parity',
    volatilities=volatilities
)

# Define positions (example)
positions = {
    'AAPL': 500,
    'MSFT': 300,
    'GOOGL': 200,
    'AMZN': 400,
    'META': 350
}

# Get current prices (example)
prices = {
    'AAPL': 180.0,
    'MSFT': 380.0,
    'GOOGL': 140.0,
    'AMZN': 150.0,
    'META': 320.0
}

# Calculate portfolio risk
portfolio_risk = risk_mgr.calculate_portfolio_risk(
    positions=positions,
    prices=prices,
    volatilities=volatilities,
    correlation_matrix=correlation_matrix,
    capital=capital
)

# Check all limits
all_ok, detailed_checks = risk_mgr.check_limits(portfolio_risk)

if not all_ok:
    print("⚠️  Risk limits breached!")
    for check_name, passed in detailed_checks.items():
        if not passed:
            print(f"  ✗ {check_name}")
else:
    print("✓ All risk limits satisfied")

# Display report
print(risk_mgr.get_risk_report(portfolio_risk))
```

---

### Dynamic Position Sizing with Risk Constraints

```python
from st.risk import RiskManager, PositionLimits

risk_mgr = RiskManager()
limits = PositionLimits()

# Target position from forecast
base_position = 150

# Current instrument volatility
instrument_vol = 0.28

# Calculate initial position risk
initial_risk = risk_mgr.calculator.position_risk(
    position_size=base_position,
    instrument_price=200.0,
    volatility=instrument_vol,
    capital=100000
)

# Check if within limits
max_risk = 0.15  # 15% max per instrument

if initial_risk > max_risk:
    # Scale down to meet risk target
    adjusted_position = limits.scale_for_risk_limit(
        current_risk=initial_risk,
        target_risk=max_risk,
        position_size=base_position
    )
    print(f"Position scaled: {base_position} → {adjusted_position:.0f}")
else:
    adjusted_position = base_position
    print(f"Position within limits: {base_position}")
```

---

### Correlation Analysis

```python
from st.risk import CorrelationEstimator
import polars as pl

estimator = CorrelationEstimator(lookback=120)

# Calculate correlation
corr_matrix = estimator.estimate(returns_df)

# Analyze correlation structure
tickers = corr_matrix.columns

print("Correlation Matrix:")
print(corr_matrix)

# Find highly correlated pairs
for i, ticker1 in enumerate(tickers):
    for j, ticker2 in enumerate(tickers):
        if i < j:  # Upper triangle only
            corr = corr_matrix[ticker1][j]
            if abs(corr) > 0.7:
                print(f"High correlation: {ticker1}-{ticker2}: {corr:.3f}")

# Average correlation
avg_corr = estimator._avg_correlation(corr_matrix.to_numpy())
print(f"\nAverage correlation: {avg_corr:.3f}")

# Expected diversification benefit
n = len(tickers)
from st.risk import DiversificationMultiplier
idm = DiversificationMultiplier.calculate_equal_weights(n, avg_corr)
print(f"Expected IDM (equal weights): {idm:.3f}")
```

---

### Custom Risk Metrics

```python
from st.risk import calculate_var, calculate_cvar, calculate_sharpe_ratio
from st.risk import calculate_max_drawdown

# Calculate VaR and CVaR
returns = returns_df['AAPL']

var_95 = calculate_var(returns, confidence_level=0.95)
cvar_95 = calculate_cvar(returns, confidence_level=0.95)

print(f"95% VaR: {var_95:.2%}")
print(f"95% CVaR: {cvar_95:.2%}")

# Sharpe ratio
sharpe = calculate_sharpe_ratio(returns, risk_free_rate=0.03)
print(f"Sharpe Ratio: {sharpe:.2f}")

# Maximum drawdown
prices = data_mgr.get_data('AAPL').close
max_dd, peak_idx, trough_idx = calculate_max_drawdown(
    pl.Series(prices.values)
)
print(f"Max Drawdown: {max_dd:.2%}")
print(f"Peak: {prices.index[peak_idx]}, Trough: {prices.index[trough_idx]}")
```

---

## Integration with Other Modules

### Complete Trading System

```python
from st.data import DataManager
from st.volatility import VolatilityManager
from st.forecast import ForecastCombiner
from st.position import PositionSizer
from st.risk import RiskManager

# Initialize all managers
data_mgr = DataManager()
vol_mgr = VolatilityManager()
risk_mgr = RiskManager()

# 1. Get data
ticker = 'AAPL'
price_data = data_mgr.get_data(ticker)

# 2. Calculate volatility
vol_result = vol_mgr.estimate_from_prices(
    pl.Series(price_data.close.values), ticker
)

# 3. Generate forecast (example)
forecast = 10.0  # From your trading rules

# 4. Size position
position_sizer = PositionSizer()
position = position_sizer.calculate(
    forecast=forecast,
    volatility=vol_result.current_annual_vol,
    capital=100000,
    instrument_price=price_data.close.iloc[-1]
)

# 5. Check risk limits
position_risk = risk_mgr.calculator.position_risk(
    position_size=position,
    instrument_price=price_data.close.iloc[-1],
    volatility=vol_result.current_annual_vol,
    capital=100000
)

if not risk_mgr.limits.check_instrument_risk(position_risk, ticker):
    print(f"⚠️  Position risk too high: {position_risk:.2%}")
    # Scale down position
    position = risk_mgr.limits.scale_for_risk_limit(
        current_risk=position_risk,
        target_risk=0.15,
        position_size=position
    )

print(f"Final position: {position:.0f} shares")
```

---

## Best Practices

### 1. Regular Correlation Updates

```python
# Update correlations periodically
def update_correlations(returns_df, method='ewma'):
    """Update correlation matrix weekly."""
    risk_mgr = RiskManager()
    corr_matrix = risk_mgr.estimate_correlations(
        returns_df, method=method
    )
    return corr_matrix

# Use EWMA for more responsive correlation estimates
corr = update_correlations(returns_df, method='ewma')
```

### 2. Pre-Trade Risk Checks

```python
def pre_trade_risk_check(proposed_position, ticker, portfolio_state):
    """Verify risk limits before executing trade."""
    risk_mgr = RiskManager()
    
    # Calculate new portfolio risk with proposed position
    new_positions = portfolio_state.positions.copy()
    new_positions[ticker] = proposed_position
    
    new_portfolio_risk = risk_mgr.calculate_portfolio_risk(
        positions=new_positions,
        prices=portfolio_state.prices,
        volatilities=portfolio_state.volatilities,
        correlation_matrix=portfolio_state.correlations,
        capital=portfolio_state.capital
    )
    
    # Check all limits
    all_ok, checks = risk_mgr.check_limits(new_portfolio_risk)
    
    return all_ok, new_portfolio_risk
```

### 3. Risk Decomposition

```python
def analyze_risk_contributors(portfolio_risk):
    """Identify main risk contributors."""
    # Sort by risk contribution
    sorted_risks = sorted(
        portfolio_risk.instrument_risks.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    print("Top Risk Contributors:")
    for ticker, risk in sorted_risks[:5]:
        pct = risk / portfolio_risk.portfolio_risk * 100
        print(f"  {ticker}: {risk:.2%} ({pct:.1f}% of total)")
    
    # Check concentration
    print(f"\nConcentration Ratio: {portfolio_risk.concentration_ratio:.3f}")
    print(f"Diversification Multiplier: {portfolio_risk.diversification_multiplier:.3f}")
```

### 4. Stress Testing

```python
def stress_test_portfolio(portfolio_risk, shock_magnitude=0.10):
    """Simulate portfolio under stress scenarios."""
    print(f"Stress Test: {shock_magnitude:.0%} shock")
    
    # Scenario 1: All instruments down
    stressed_risk = portfolio_risk.portfolio_risk * (1 + shock_magnitude)
    print(f"  All down: {stressed_risk:.2%}")
    
    # Scenario 2: Correlation spike
    # Assume correlations increase to 0.9
    # Portfolio risk increases when correlations rise
    high_corr_risk = portfolio_risk.portfolio_risk * 1.5
    print(f"  High correlation: {high_corr_risk:.2%}")
    
    # Scenario 3: Volatility spike
    vol_spike_risk = portfolio_risk.portfolio_risk * 1.3
    print(f"  Volatility spike: {vol_spike_risk:.2%}")
```

---

## Common Patterns

### Pattern 1: Risk Budget Management

```python
# Allocate risk budget across instruments
total_risk_budget = 0.20  # 20% of capital

# Equal risk allocation
n_instruments = 5
risk_per_instrument = total_risk_budget / n_instruments

print(f"Risk budget per instrument: {risk_per_instrument:.2%}")

# Adjust positions to meet risk budget
for ticker in portfolio:
    current_risk = calculate_position_risk(ticker)
    if current_risk > risk_per_instrument:
        scale_down_position(ticker, target_risk=risk_per_instrument)
```

### Pattern 2: Dynamic Leverage Control

```python
# Adjust leverage based on market conditions
def adjust_leverage(portfolio_risk, market_volatility):
    """Reduce leverage in high volatility environments."""
    base_max_leverage = 2.0
    
    if market_volatility > 0.30:  # High vol
        max_leverage = base_max_leverage * 0.7
    elif market_volatility > 0.20:  # Medium vol
        max_leverage = base_max_leverage * 0.85
    else:  # Low vol
        max_leverage = base_max_leverage
    
    if portfolio_risk.leverage > max_leverage:
        scale_factor = max_leverage / portfolio_risk.leverage
        return scale_factor
    
    return 1.0
```

### Pattern 3: Rebalancing Triggers

```python
# Define rebalancing rules based on risk
def check_rebalance_needed(portfolio_risk, config):
    """Determine if rebalancing is needed."""
    rebalance = False
    reasons = []
    
    # Check portfolio risk drift
    if portfolio_risk.portfolio_risk > config.max_portfolio_risk * 0.9:
        rebalance = True
        reasons.append("Approaching max portfolio risk")
    
    # Check concentration
    if portfolio_risk.concentration_ratio > 0.7:
        rebalance = True
        reasons.append("High concentration")
    
    # Check leverage
    if portfolio_risk.leverage > config.max_leverage * 0.85:
        rebalance = True
        reasons.append("High leverage")
    
    return rebalance, reasons
```

---

## Troubleshooting

### Issue: Correlation Matrix Not Positive Definite

```python
# Add small regularization to diagonal
def regularize_correlation(corr_matrix, epsilon=1e-6):
    """Ensure correlation matrix is positive definite."""
    import numpy as np
    corr_np = corr_matrix.to_numpy()
    corr_np += np.eye(len(corr_np)) * epsilon
    return pl.DataFrame(corr_np, schema=corr_matrix.columns)
```

### Issue: Insufficient Data for Correlation

```python
# Handle missing data gracefully
estimator = CorrelationEstimator(
    lookback=120,
    min_samples=20  # Reduce minimum if data is limited
)

# Fallback to identity matrix if needed
try:
    corr = estimator.estimate(returns_df)
except Exception:
    # Use uncorrelated assumption
    n = len(returns_df.columns)
    corr = pl.DataFrame(np.eye(n), schema=returns_df.columns)
```

### Issue: Extreme Risk Values

```python
# Validate and cap risk metrics
def validate_risk(risk_value, max_risk=1.0):
    """Ensure risk values are reasonable."""
    if risk_value < 0:
        return 0.0
    if risk_value > max_risk:
        logger.warning(f"Risk {risk_value:.2%} exceeds max {max_risk:.2%}")
        return max_risk
    return risk_value
```

---

## API Reference

### Classes

- **RiskManager** - Main risk management interface
- **RiskConfig** - Risk parameter configuration
- **CorrelationEstimator** - Correlation matrix estimation
- **DiversificationMultiplier** - IDM calculation
- **RiskCalculator** - Risk metric computation
- **PositionLimits** - Risk constraint enforcement
- **CapitalAllocator** - Capital distribution strategies
- **RiskMonitor** - Real-time monitoring and reporting
- **PortfolioRisk** - Portfolio risk metrics container
- **PositionRisk** - Individual position risk metrics

### Functions

- `calculate_var()` - Value at Risk
- `calculate_cvar()` - Conditional Value at Risk
- `calculate_sharpe_ratio()` - Sharpe ratio
- `calculate_max_drawdown()` - Maximum drawdown

---

## Related Modules

- **[Data Manager](./data-manager)** - Price data and returns
- **[Volatility](./volatility)** - Volatility estimation
- **[Forecasting](./forecast)** - Trading signals
- **[Position Sizing](./position)** - Position calculations
- **[Portfolio](./portfolio)** - Multi-instrument management

---

## References

- Carver, Robert. *Systematic Trading: A Unique New Method for Designing Trading and Investing Systems*. Harriman House, 2015.
- Chapter 9: Risk Management
- Chapter 10: Portfolio Optimization
- Chapter 11: Costs and Execution