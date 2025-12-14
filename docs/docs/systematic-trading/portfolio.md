---
id: portfolio
title: Portfolio Module
sidebar_label: Portfolio
---

# Portfolio Management

**Module:** `st.portfolio`

The Portfolio module handles multi-instrument portfolio construction, weight optimization, diversification calculations,
and capital allocation based on Robert Carver's systematic trading framework.

---

## Overview

**Purpose:** Combine forecasts across instruments, optimize portfolio weights, calculate diversification multipliers,
and allocate capital.

**Key Concepts:**

- **Instrument Diversification Multiplier (IDM):** Accounts for diversification benefits across instruments
- **Weight Optimization:** Equal, inverse volatility, risk parity, or handcrafted weights
- **Correlation Estimation:** Standard, EWMA, and shrinkage methods
- **Capital Allocation:** Distributes capital with IDM adjustment

---

## Quick Start

```python
from st.portfolio import PortfolioManager

# Initialize portfolio manager
pm = PortfolioManager()

# Calculate equal weights for instruments
weights = pm.calculate_portfolio_weights(
    tickers=['SPY', 'TLT', 'GLD'],
    method='equal'
)

print(f"Weights: {weights.weights}")
print(f"IDM: {weights.diversification_multiplier:.4f}")

# Allocate capital
allocation = pm.allocate_capital(
    total_capital=100000,
    portfolio_weights=weights,
    apply_idm=True
)
```

---

## Core Components

### PortfolioConfig

Configuration for portfolio management.

**Parameters:**

- `use_instrument_weights` (bool): Use instrument-specific weights (default: True)
- `use_forecast_div_multiplier` (bool): Apply forecast diversification multiplier (default: True)
- `use_instrument_div_multiplier` (bool): Apply instrument diversification multiplier (default: True)
- `max_instruments` (int): Maximum number of instruments (default: 50)
- `min_instrument_weight` (float): Minimum weight per instrument (default: 0.01)

**Example:**

```python
from st.portfolio import PortfolioConfig

config = PortfolioConfig(
    use_instrument_div_multiplier=True,
    max_instruments=30,
    min_instrument_weight=0.02
)
```

---

### PortfolioWeights

Container for portfolio-level instrument weights.

**Attributes:**

- `weights` (Dict[str, float]): Instrument weights (sum to 1.0)
- `diversification_multiplier` (float): Instrument diversification multiplier
- `method` (str): Weight calculation method used

**Example:**

```python
weights = PortfolioWeights(
    weights={'SPY': 0.5, 'TLT': 0.3, 'GLD': 0.2},
    diversification_multiplier=1.15,
    method='equal'
)

print(f"Total weight: {sum(weights.weights.values()):.2f}")
```

---

## Weight Calculation Methods

### 1. Equal Weights

**Description:** Simple equal allocation across all instruments (Carver's default).

**When to use:** Starting point, high diversification, avoid optimization errors.

**Example:**

```python
weights = pm.calculate_portfolio_weights(
    tickers=['SPY', 'TLT', 'GLD', 'VTI'],
    method='equal'
)
# Result: Each instrument gets 0.25 (25%)
```

**Formula:** `w_i = 1/N` for N instruments

---

### 2. Inverse Volatility

**Description:** Weight inversely proportional to instrument volatility.

**When to use:** Risk balancing, lower-vol instruments get higher weights.

**Example:**

```python
volatilities = {'SPY': 0.16, 'TLT': 0.08, 'GLD': 0.15}

weights = pm.calculate_portfolio_weights(
    tickers=['SPY', 'TLT', 'GLD'],
    method='inverse_volatility',
    volatilities=volatilities
)
# TLT (lowest vol) gets highest weight
```

**Formula:** `w_i = (1/σ_i) / Σ(1/σ_j)`

---

### 3. Risk Parity

**Description:** Equal risk contribution from each instrument, accounting for correlations.

**When to use:** Advanced risk balancing with correlation awareness.

**Example:**

```python
import polars as pl

volatilities = {'SPY': 0.16, 'TLT': 0.08, 'GLD': 0.15}
correlation_matrix = pl.DataFrame({
    'SPY': [1.0, 0.2, 0.3],
    'TLT': [0.2, 1.0, 0.1],
    'GLD': [0.3, 0.1, 1.0]
})

weights = pm.calculate_portfolio_weights(
    tickers=['SPY', 'TLT', 'GLD'],
    method='risk_parity',
    volatilities=volatilities,
    correlation_matrix=correlation_matrix
)
```

**Formula:** `w_i ∝ 1 / (σ_i × √ρ̄_i)` where ρ̄_i is average correlation

---

### 4. Handcrafted Weights

**Description:** Use manually specified weights based on expertise or strategy.

**When to use:** Specific strategic views, regulatory constraints, custom allocations.

**Example:**

```python
my_weights = {
    'SPY': 0.50,  # 50% stocks
    'TLT': 0.30,  # 30% bonds
    'GLD': 0.20  # 20% gold
}

weights = pm.calculate_portfolio_weights(
    tickers=list(my_weights.keys()),
    method='handcrafted',
    handcrafted_weights=my_weights
)
```

---

## Instrument Diversification Multiplier (IDM)

The IDM scales portfolio capital to account for diversification benefits.

### Basic IDM Calculation

**Formula:** `IDM = 1 / √(Σ w_i²)`

**Example:**

```python
from st.portfolio import InstrumentDiversificationMultiplier

weights = {'SPY': 0.5, 'TLT': 0.5}
idm = InstrumentDiversificationMultiplier.calculate(weights)
print(f"IDM: {idm:.4f}")  # 1.4142 (sqrt(2))

# More instruments = higher IDM
weights_10 = {f'Asset{i}': 0.1 for i in range(10)}
idm_10 = InstrumentDiversificationMultiplier.calculate(weights_10)
print(f"IDM (10 assets): {idm_10:.4f}")  # 3.1623 (sqrt(10))
```

### Correlation-Adjusted IDM

**Formula:** `IDM = 1 / √(w^T × Corr × w)`

**Example:**

```python
import polars as pl

weights = {'SPY': 0.5, 'TLT': 0.5}
correlation_matrix = pl.DataFrame({
    'SPY': [1.0, -0.3],
    'TLT': [-0.3, 1.0]
})

idm = InstrumentDiversificationMultiplier.calculate_from_correlation(
    weights, correlation_matrix
)
print(f"Correlation-adjusted IDM: {idm:.4f}")
# Higher than basic IDM due to negative correlation
```

**Key Insight:** Negative correlations increase IDM (more diversification benefit).

---

## Correlation Estimation

### Standard Correlation

Calculate correlation from returns using standard method.

**Example:**

```python
import polars as pl

# DataFrame with returns for each instrument
returns_df = pl.DataFrame({
    'SPY': [0.01, -0.02, 0.015, ...],
    'TLT': [-0.005, 0.01, -0.008, ...],
    'GLD': [0.002, 0.003, -0.001, ...]
})

corr_matrix = pm.estimate_correlations(
    returns_df=returns_df,
    method='standard'
)
```

---

### EWMA Correlation

Exponentially weighted moving average correlation (gives more weight to recent data).

**Example:**

```python
corr_matrix = pm.estimate_correlations(
    returns_df=returns_df,
    method='ewma',
    span=60  # 60-day EWMA
)
```

---

### Correlation Shrinkage

Shrink correlation towards identity matrix to reduce estimation error.

**Example:**

```python
# Shrink 50% towards identity matrix
corr_matrix = pm.estimate_correlations(
    returns_df=returns_df,
    method='standard',
    shrinkage=0.5
)
# Result: Corr_shrunk = 0.5 × Corr + 0.5 × I
```

**Benefits:**

- Reduces overfitting
- More stable in small samples
- Carver recommends light shrinkage (0.2-0.5)

---

## Capital Allocation

Allocate capital across instruments with optional IDM application.

**Example:**

```python
from st.portfolio import CapitalAllocator

total_capital = 100000

weights = PortfolioWeights(
    weights={'SPY': 0.5, 'TLT': 0.3, 'GLD': 0.2},
    diversification_multiplier=1.41,
    method='equal'
)

# With IDM (recommended)
allocation = CapitalAllocator.allocate(
    total_capital=total_capital,
    portfolio_weights=weights,
    apply_idm=True
)
print(allocation)
# {'SPY': 70500, 'TLT': 42300, 'GLD': 28200}
# Total: $141,000 (100k × 1.41 IDM)

# Without IDM
allocation_no_idm = CapitalAllocator.allocate(
    total_capital=total_capital,
    portfolio_weights=weights,
    apply_idm=False
)
# Total: $100,000 (no scaling)
```

**Key Point:** IDM allows "leverage through diversification" - you can allocate more than 100% of capital when
diversified.

---

## Complete Workflow Example

```python
import polars as pl
from st.portfolio import PortfolioManager
from st.volatility import VolatilityManager

# 1. Initialize managers
pm = PortfolioManager()
vm = VolatilityManager()

# 2. Get returns data
returns_df = pl.DataFrame({
    'SPY': [...],  # Stock returns
    'TLT': [...],  # Bond returns
    'GLD': [...],  # Gold returns
    'VTI': [...]  # Total market returns
})

# 3. Calculate volatilities
volatilities = {}
for ticker in returns_df.columns:
    vol_result = vm.estimate_from_returns(returns_df[ticker], ticker)
    volatilities[ticker] = vol_result.current_annual_vol

# 4. Estimate correlations
corr_matrix = pm.estimate_correlations(
    returns_df=returns_df,
    method='standard',
    shrinkage=0.3
)

# 5. Calculate optimal weights
weights = pm.calculate_portfolio_weights(
    tickers=list(returns_df.columns),
    method='risk_parity',
    volatilities=volatilities,
    correlation_matrix=corr_matrix
)

print(f"Weights: {weights.weights}")
print(f"IDM: {weights.diversification_multiplier:.4f}")

# 6. Allocate capital
total_capital = 250000
allocation = pm.allocate_capital(
    total_capital=total_capital,
    portfolio_weights=weights,
    apply_idm=True
)

for ticker, capital in allocation.items():
    print(f"{ticker}: ${capital:,.0f} ({weights.weights[ticker]:.1%})")
```

---

## PortfolioManager API Reference

### `calculate_portfolio_weights()`

Calculate optimal portfolio weights.

**Parameters:**

- `tickers` (List[str]): Instrument tickers
- `method` (str): Weight method ('equal', 'inverse_volatility', 'risk_parity', 'handcrafted')
- `volatilities` (Optional[Dict[str, float]]): Instrument volatilities (required for inverse_vol/risk_parity)
- `correlation_matrix` (Optional[pl.DataFrame]): Correlation matrix (required for risk_parity)
- `handcrafted_weights` (Optional[Dict[str, float]]): Manual weights (required for handcrafted)

**Returns:** `PortfolioWeights` object

---

### `estimate_correlations()`

Estimate correlation matrix from returns.

**Parameters:**

- `returns_df` (pl.DataFrame): Returns data (instruments as columns)
- `method` (str): 'standard' or 'ewma'
- `span` (int): EWMA span (default: 60)
- `shrinkage` (float): Shrinkage factor 0-1 (default: 0.0)

**Returns:** `pl.DataFrame` correlation matrix

---

### `allocate_capital()`

Allocate capital across instruments.

**Parameters:**

- `total_capital` (float): Total portfolio capital
- `portfolio_weights` (PortfolioWeights): Portfolio weights object
- `apply_idm` (bool): Apply IDM scaling (default: True)

**Returns:** `Dict[str, float]` capital per instrument

---

## Best Practices

### 1. Weight Selection

```python
# Start simple
weights = pm.calculate_portfolio_weights(tickers, method='equal')

# Progress to risk-based if you have good volatility estimates
weights = pm.calculate_portfolio_weights(
    tickers,
    method='inverse_volatility',
    volatilities=vols
)
```

### 2. Correlation Estimation

```python
# Use shrinkage for small samples
corr = pm.estimate_correlations(
    returns_df,
    method='standard',
    shrinkage=0.3  # 30% shrinkage
)

# Use EWMA for time-varying correlations
corr = pm.estimate_correlations(
    returns_df,
    method='ewma',
    span=60
)
```

### 3. IDM Application

```python
# Always apply IDM for proper diversification accounting
allocation = pm.allocate_capital(
    total_capital,
    weights,
    apply_idm=True  # Recommended
)
```

### 4. Weight Validation

```python
from st.portfolio import validate_weights

# Check weights sum to 1.0
is_valid = validate_weights(weights.weights, tolerance=0.01)
if not is_valid:
    print("Warning: Weights validation failed")
```

---

## Common Patterns

### Rebalancing Portfolio Weights

```python
# Monthly rebalancing
for month in trading_months:
    # Get latest data
    returns_df = get_returns_for_period(month)

    # Recalculate volatilities and correlations
    volatilities = calculate_current_vols(returns_df)
    corr_matrix = pm.estimate_correlations(returns_df, shrinkage=0.3)

    # Update weights
    weights = pm.calculate_portfolio_weights(
        tickers,
        method='risk_parity',
        volatilities=volatilities,
        correlation_matrix=corr_matrix
    )

    # Reallocate capital
    allocation = pm.allocate_capital(total_capital, weights)
```

### Multi-Strategy Portfolio

```python
# Allocate capital across different strategies
strategy_weights = {
    'trend_following': 0.40,
    'carry': 0.30,
    'mean_reversion': 0.30
}

strategy_allocations = {}
for strategy, weight in strategy_weights.items():
    strategy_capital = total_capital * weight

    # Each strategy has its own instrument weights
    instr_weights = pm.calculate_portfolio_weights(
        tickers=strategy_instruments[strategy],
        method='equal'
    )

    strategy_allocations[strategy] = pm.allocate_capital(
        strategy_capital,
        instr_weights
    )
```

---

## Troubleshooting

### Issue: Weights don't sum to 1.0

**Solution:** Weights are automatically normalized in PortfolioWeights validator.

```python
# Even if input weights don't sum to 1
weights_dict = {'SPY': 50, 'TLT': 30, 'GLD': 20}
weights = pm.calculate_portfolio_weights(
    tickers=list(weights_dict.keys()),
    method='handcrafted',
    handcrafted_weights=weights_dict
)
# Automatically normalized: {SPY: 0.5, TLT: 0.3, GLD: 0.2}
```

### Issue: Correlation matrix singular/invalid

**Solution:** Use correlation shrinkage.

```python
corr = pm.estimate_correlations(
    returns_df,
    shrinkage=0.5  # Shrink towards identity
)
```

### Issue: IDM calculation fails

**Solution:** Check for zero or negative weights.

```python
# Filter out zero weights before IDM calculation
weights_filtered = {k: v for k, v in weights.items() if v > 0}
idm = InstrumentDiversificationMultiplier.calculate(weights_filtered)
```

---

## References

- **Robert Carver:** "Systematic Trading" - Chapters on portfolio construction
- **IDM Calculation:** Section on instrument diversification
- **Weight Optimization:** Carver prefers equal weights for simplicity
- **Correlation Estimation:** EWMA and shrinkage methods

---

## See Also

- [Position Module](./position.md) - Position sizing using portfolio weights
- [Volatility Module](./volatility.md) - Volatility estimation for weighting
- [Forecast Module](./forecast.md) - Forecast combination