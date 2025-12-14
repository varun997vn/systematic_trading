---
id: position
title: Position Sizing Module
sidebar_label: Position Sizing
---

# Position Sizing & Management

**Module:** `st.position`

The Position module implements Robert Carver's position sizing methodology, converting forecasts and risk targets into actual tradeable positions with leverage control and risk management.

---

## Overview

**Purpose:** Calculate optimal position sizes based on forecasts, volatility targeting, capital allocation, and risk constraints.

**Key Concepts:**
- **Volatility Targeting:** Size positions for consistent risk across instruments
- **Carver's Formula:** Core position sizing equation
- **Position Buffering:** Reduce turnover by only trading when positions move outside buffer zone
- **Leverage Control:** Enforce maximum leverage limits
- **Risk Calculation:** Monitor portfolio and instrument-level risk

---

## Quick Start

```python
from st.position import PositionManager

# Initialize position manager
pm = PositionManager()

# Calculate position for a single instrument
position = pm.calculate_position(
    ticker='SPY',
    forecast=10.0,           # Scaled forecast (-20 to +20)
    capital=100000,          # Allocated capital
    instrument_volatility=0.16,  # 16% annual vol
    price=450.0,             # Current price
    instrument_weight=0.33   # 33% portfolio weight
)

print(f"Contracts: {position.contracts:.2f}")
print(f"Notional: ${position.notional_position:,.0f}")
print(f"Leverage: {position.leverage:.2f}x")
```

---

## Core Components

### PositionConfig

Configuration for position sizing and risk management.

**Parameters:**
- `volatility_target` (float): Annual volatility target (default: 0.20 = 20%)
- `use_buffering` (bool): Apply position buffering (default: True)
- `buffer_width` (float): Buffer width as fraction (default: 0.10 = 10%)
- `max_leverage` (float): Maximum leverage allowed (default: from Settings)
- `max_forecast` (float): Maximum forecast value (default: 20.0)

**Example:**
```python
from st.position import PositionConfig

config = PositionConfig(
    volatility_target=0.15,  # 15% target vol
    use_buffering=True,
    buffer_width=0.12,       # 12% buffer
    max_leverage=3.0
)

pm = PositionManager(config)
```

---

### Position

Container for position information and calculations.

**Attributes:**
- `ticker` (str): Instrument identifier
- `forecast` (float): Combined scaled forecast (-20 to +20)
- `volatility` (float): Annual instrument volatility
- `price` (float): Current instrument price
- `capital` (float): Allocated capital
- `contract_size` (float): Contract multiplier (default: 1.0)
- `fx_rate` (float): FX rate to base currency (default: 1.0)
- `notional_position` (float): Notional exposure in $ terms
- `contracts` (float): Number of contracts to trade
- `leverage` (float): Position leverage
- `risk_contribution` (float): Risk in $ terms

**Example:**
```python
position = Position(
    ticker='SPY',
    forecast=10.0,
    volatility=0.16,
    price=450.0,
    capital=100000
)
```

---

### PositionSet

Container for multiple instrument positions.

**Attributes:**
- `positions` (Dict[str, Position]): Dictionary of positions by ticker
- `total_capital` (float): Total portfolio capital
- `timestamp` (Optional[str]): Timestamp of position set

**Properties:**
- `total_notional`: Sum of absolute notional positions
- `portfolio_leverage`: Total notional / total capital
- `tickers`: List of tickers in set

**Example:**
```python
position_set = PositionSet(
    positions={
        'SPY': position_spy,
        'TLT': position_tlt,
        'GLD': position_gld
    },
    total_capital=300000
)

print(f"Portfolio leverage: {position_set.portfolio_leverage:.2f}x")
print(f"Total notional: ${position_set.total_notional:,.0f}")
```

---

## Carver's Position Sizing Formula

### The Core Equation

**Formula:**
```
Notional Position = (Capital × Vol_Target × Weight × Forecast) / (10 × Instrument_Vol)
```

**Where:**
- `Capital`: Allocated capital for instrument
- `Vol_Target`: Target annual volatility (e.g., 0.20 for 20%)
- `Weight`: Instrument weight in portfolio (e.g., 0.33 for 33%)
- `Forecast`: Scaled forecast (-20 to +20)
- `Instrument_Vol`: Annual instrument volatility

**The "10" Factor:** Dividing by 10 means a forecast of 10 equals 1× target risk position.

---

### Step-by-Step Calculation

```python
# Given parameters
capital = 100000
volatility_target = 0.20
instrument_weight = 0.33
forecast = 10.0
instrument_volatility = 0.16
price = 450.0

# Step 1: Calculate notional position
numerator = capital * volatility_target * instrument_weight * forecast
# = 100000 × 0.20 × 0.33 × 10 = 66,000

denominator = 10.0 * instrument_volatility
# = 10 × 0.16 = 1.6

notional_position = numerator / denominator
# = 66,000 / 1.6 = 41,250

# Step 2: Convert to contracts
contracts = notional_position / price
# = 41,250 / 450 = 91.67 contracts

# Step 3: Calculate leverage
leverage = notional_position / capital
# = 41,250 / 100,000 = 0.41x
```

---

### Formula Intuition

**Forecast Impact:**
- Forecast = 0 → No position (neutral)
- Forecast = +10 → 1× target risk long position
- Forecast = +20 → 2× target risk long position
- Forecast = -10 → 1× target risk short position

**Volatility Impact:**
- High vol instruments → Smaller positions (risk normalization)
- Low vol instruments → Larger positions (risk normalization)

**Example:**
```python
# High volatility asset (30% annual vol)
position_high_vol = pm.calculate_position(
    ticker='BTC',
    forecast=10.0,
    capital=100000,
    instrument_volatility=0.30,
    price=50000
)
# Result: Smaller position due to high vol

# Low volatility asset (8% annual vol)
position_low_vol = pm.calculate_position(
    ticker='TLT',
    forecast=10.0,
    capital=100000,
    instrument_volatility=0.08,
    price=95
)
# Result: Larger position due to low vol
```

---

## Position Sizing Examples

### Basic Position Calculation

```python
from st.position import PositionManager

pm = PositionManager()

# Calculate position for SPY ETF
position = pm.calculate_position(
    ticker='SPY',
    forecast=10.0,              # Bullish signal
    capital=100000,
    instrument_volatility=0.16,
    price=450.0
)

print(f"Ticker: {position.ticker}")
print(f"Forecast: {position.forecast}")
print(f"Contracts: {position.contracts:.2f}")
print(f"Notional: ${position.notional_position:,.0f}")
print(f"Leverage: {position.leverage:.2f}x")
print(f"Risk: ${position.risk_contribution:,.0f}")
```

---

### Multiple Instruments Portfolio

```python
# Forecasts for each instrument
forecasts = {
    'SPY': 10.0,   # Bullish
    'TLT': -5.0,   # Bearish
    'GLD': 15.0    # Very bullish
}

# Capital allocation from portfolio module
capital_allocation = {
    'SPY': 50000,
    'TLT': 30000,
    'GLD': 20000
}

# Volatilities
volatilities = {
    'SPY': 0.16,
    'TLT': 0.08,
    'GLD': 0.15
}

# Current prices
prices = {
    'SPY': 450.0,
    'TLT': 95.0,
    'GLD': 180.0
}

# Calculate all positions
position_set = pm.calculate_portfolio_positions(
    forecasts=forecasts,
    capital_allocation=capital_allocation,
    volatilities=volatilities,
    prices=prices
)

# Review positions
for ticker, position in position_set.positions.items():
    print(f"{ticker}: {position.contracts:.2f} contracts, "
          f"${position.notional_position:,.0f} notional")

print(f"\nPortfolio leverage: {position_set.portfolio_leverage:.2f}x")
```

---

### Futures Contracts

```python
# ES (E-mini S&P 500 futures)
position_es = pm.calculate_position(
    ticker='ES',
    forecast=12.0,
    capital=100000,
    instrument_volatility=0.16,
    price=4500.0,
    contract_size=50.0,  # $50 per point
    instrument_weight=0.50
)

print(f"ES Contracts: {position_es.contracts:.2f}")
# Note: May need to round to integer contracts for futures
```

---

### Foreign Exchange

```python
# EUR/USD position with FX rate
position_eur = pm.calculate_position(
    ticker='EURUSD',
    forecast=8.0,
    capital=100000,
    instrument_volatility=0.10,
    price=1.08,
    fx_rate=1.08,  # EUR to USD conversion
    instrument_weight=0.25
)
```

---

## Position Buffering

Buffering reduces trading costs by only rebalancing when positions move outside a buffer zone.

### How Buffering Works

**Buffer Zone:** ±10% around current position (default)

**Rebalance Rules:**
- Current = 100, Buffer = ±10 → Zone is [90, 110]
- Target = 95 → Don't rebalance (within buffer)
- Target = 115 → Rebalance (outside buffer)

**Example:**
```python
# Current positions (from yesterday)
current_positions = {
    'SPY': 100.0,  # Currently hold 100 shares
    'TLT': 200.0,
    'GLD': 50.0
}

# New target positions (calculated today)
target_position_set = pm.calculate_portfolio_positions(
    forecasts=new_forecasts,
    capital_allocation=allocation,
    volatilities=vols,
    prices=prices
)

# Apply buffering
buffered_positions = pm.apply_buffering(
    current_positions=current_positions,
    target_position_set=target_position_set
)

# Only positions outside buffer will be rebalanced
```

---

### Buffering Benefits

**Reduces:**
- Trading costs (commissions, spreads)
- Market impact
- Turnover

**Example Turnover Reduction:**
```python
from st.position import PositionBuffer

buffer = PositionBuffer(buffer_width=0.10)

# Without buffering: trade every small change
# With buffering: only trade significant changes

# Check if rebalance needed
current = 100.0
target = 105.0  # 5% change

should_trade = buffer.should_rebalance(current, target)
print(f"Rebalance needed: {should_trade}")  # False (within 10% buffer)

target = 115.0  # 15% change
should_trade = buffer.should_rebalance(current, target)
print(f"Rebalance needed: {should_trade}")  # True (outside buffer)
```

---

## Leverage Control

### Maximum Leverage Limit

Enforce maximum leverage per position and portfolio.

**Example:**
```python
# Set max leverage to 3x
config = PositionConfig(max_leverage=3.0)
pm = PositionManager(config)

# Calculate position with high forecast
position = pm.calculate_position(
    ticker='QQQ',
    forecast=20.0,  # Maximum forecast
    capital=100000,
    instrument_volatility=0.20,
    price=350.0
)

# Leverage will be capped at 3.0x if it exceeds
if position.leverage > 3.0:
    print("Leverage capped at 3.0x")
```

---

### Portfolio Leverage

Monitor total portfolio leverage across all positions.

**Example:**
```python
position_set = pm.calculate_portfolio_positions(
    forecasts=forecasts,
    capital_allocation=allocation,
    volatilities=vols,
    prices=prices
)

portfolio_leverage = position_set.portfolio_leverage

if portfolio_leverage > 2.0:
    print(f"Warning: High portfolio leverage ({portfolio_leverage:.2f}x)")
    
# Calculate total exposure
total_notional = position_set.total_notional
print(f"Total notional exposure: ${total_notional:,.0f}")
print(f"Total capital: ${position_set.total_capital:,.0f}")
```

---

## Risk Calculation

### Position Risk

Risk contribution of individual position = |Notional| × Volatility

**Example:**
```python
from st.position import RiskCalculator

position = pm.calculate_position(
    ticker='SPY',
    forecast=10.0,
    capital=100000,
    instrument_volatility=0.16,
    price=450.0
)

position_risk = RiskCalculator.position_risk(position)
print(f"Position risk: ${position_risk:,.0f}")

# Risk as % of capital
risk_pct = position_risk / position.capital
print(f"Risk: {risk_pct:.2%} of capital")
```

---

### Portfolio Risk

Calculate total portfolio risk with correlation adjustment.

**Example:**
```python
import polars as pl

# Correlation matrix
correlation_matrix = pl.DataFrame({
    'SPY': [1.0, 0.2, 0.3],
    'TLT': [0.2, 1.0, 0.1],
    'GLD': [0.3, 0.1, 1.0]
})

# Calculate portfolio risk metrics
risk_metrics = pm.calculate_portfolio_risk(
    position_set=position_set,
    correlation_matrix=correlation_matrix
)

print(f"Total portfolio risk: ${risk_metrics['total_risk']:,.0f}")
print(f"Portfolio volatility: {risk_metrics['portfolio_volatility']:.2%}")
print(f"Portfolio leverage: {risk_metrics['portfolio_leverage']:.2f}x")
print(f"Number of positions: {risk_metrics['num_positions']}")
```

---

### Maximum Position Risk

Calculate theoretical maximum risk from a single position.

**Example:**
```python
max_risk = RiskCalculator.max_position_risk(
    capital=100000,
    volatility_target=0.20,
    max_forecast=20.0
)

print(f"Max position risk: ${max_risk:,.0f}")
# = $40,000 (20% of capital at max forecast of 20)
```

---

## Complete Workflow Example

```python
from st.position import PositionManager
from st.portfolio import PortfolioManager
from st.forecast import ForecastManager
from st.volatility import VolatilityManager

# 1. Initialize managers
pos_mgr = PositionManager()
port_mgr = PortfolioManager()
forecast_mgr = ForecastManager()
vol_mgr = VolatilityManager()

# 2. Generate forecasts (from forecast module)
forecasts = {
    'SPY': 10.0,
    'TLT': -5.0,
    'GLD': 12.0
}

# 3. Calculate portfolio weights
portfolio_weights = port_mgr.calculate_portfolio_weights(
    tickers=['SPY', 'TLT', 'GLD'],
    method='equal'
)

# 4. Allocate capital
total_capital = 300000
capital_allocation = port_mgr.allocate_capital(
    total_capital=total_capital,
    portfolio_weights=portfolio_weights,
    apply_idm=True
)

# 5. Get current volatilities and prices
volatilities = {
    'SPY': 0.16,
    'TLT': 0.08,
    'GLD': 0.15
}

prices = {
    'SPY': 450.0,
    'TLT': 95.0,
    'GLD': 180.0
}

# 6. Calculate positions
position_set = pos_mgr.calculate_portfolio_positions(
    forecasts=forecasts,
    capital_allocation=capital_allocation,
    volatilities=volatilities,
    prices=prices
)

# 7. Apply buffering (if we have previous positions)
previous_positions = {
    'SPY': 98.0,
    'TLT': 420.0,
    'GLD': 135.0
}

final_positions = pos_mgr.apply_buffering(
    current_positions=previous_positions,
    target_position_set=position_set
)

# 8. Review and execute
print("\n=== POSITION SUMMARY ===")
for ticker, position in final_positions.positions.items():
    print(f"\n{ticker}:")
    print(f"  Forecast: {position.forecast:+.1f}")
    print(f"  Contracts: {position.contracts:.2f}")
    print(f"  Notional: ${position.notional_position:,.0f}")
    print(f"  Leverage: {position.leverage:.2f}x")
    print(f"  Risk: ${position.risk_contribution:,.0f}")

print(f"\n=== PORTFOLIO ===")
print(f"Total capital: ${final_positions.total_capital:,.0f}")
print(f"Total notional: ${final_positions.total_notional:,.0f}")
print(f"Portfolio leverage: {final_positions.portfolio_leverage:.2f}x")
```

---

## PositionManager API Reference

### `calculate_position()`

Calculate position for a single instrument.

**Parameters:**
- `ticker` (str): Instrument ticker
- `forecast` (float): Scaled forecast (-20 to +20)
- `capital` (float): Allocated capital
- `instrument_volatility` (float): Annual volatility
- `price` (float): Current price
- `instrument_weight` (float): Portfolio weight (default: 1.0)
- `contract_size` (float): Contract multiplier (default: 1.0)
- `fx_rate` (float): FX rate to base currency (default: 1.0)

**Returns:** `Position` object

---

### `calculate_portfolio_positions()`

Calculate positions for entire portfolio.

**Parameters:**
- `forecasts` (Dict[str, float]): Instrument forecasts
- `capital_allocation` (Dict[str, float]): Capital per instrument
- `volatilities` (Dict[str, float]): Instrument volatilities
- `prices` (Dict[str, float]): Current prices
- `contract_sizes` (Optional[Dict[str, float]]): Contract sizes
- `fx_rates` (Optional[Dict[str, float]]): FX rates

**Returns:** `PositionSet` object

---

### `apply_buffering()`

Apply position buffering to reduce turnover.

**Parameters:**
- `current_positions` (Dict[str, float]): Current position sizes
- `target_position_set` (PositionSet): Target positions

**Returns:** `PositionSet` with buffering applied

---

### `calculate_portfolio_risk()`

Calculate portfolio risk metrics.

**Parameters:**
- `position_set` (PositionSet): Set of positions
- `correlation_matrix` (Optional[pl.DataFrame]): Correlation matrix

**Returns:** Dict with risk metrics:
  - `total_risk`: Total portfolio risk ($)
  - `portfolio_volatility`: Portfolio volatility (%)
  - `portfolio_leverage`: Portfolio leverage
  - `total_notional`: Total notional exposure
  - `num_positions`: Number of positions

---

## Utility Functions

### `calculate_required_capital()`

Calculate capital needed for a given position.

**Example:**
```python
from st.position import calculate_required_capital

required = calculate_required_capital(
    forecast=10.0,
    target_volatility=0.20,
    instrument_volatility=0.16,
    price=450.0,
    contracts=100.0
)

print(f"Required capital: ${required:,.0f}")
```

---

### `round_contracts()`

Round contracts to tradeable lot sizes.

**Example:**
```python
from st.position import round_contracts

# Round to nearest whole contract
rounded = round_contracts(91.67, lot_size=1.0, method='round')
print(f"Rounded: {rounded}")  # 92.0

# Floor to lot size of 10
floored = round_contracts(91.67, lot_size=10.0, method='floor')
print(f"Floored: {floored}")  # 90.0
```

---

### `validate_position()`

Validate position is within acceptable bounds.

**Example:**
```python
from st.position import validate_position

is_valid = validate_position(position, max_leverage=3.0)

if not is_valid:
    print("Position validation failed!")
```

---

## Best Practices

### 1. Always Use Volatility Targeting

```python
# Good: Consistent risk across instruments
config = PositionConfig(volatility_target=0.20)
pm = PositionManager(config)

# Bad: Arbitrary position sizes without vol adjustment
```

### 2. Enable Position Buffering

```python
# Reduces trading costs
config = PositionConfig(
    use_buffering=True,
    buffer_width=0.10
)
```

### 3. Monitor Leverage

```python
# Check portfolio leverage regularly
if position_set.portfolio_leverage > 2.0:
    logger.warning("High portfolio leverage!")
```

### 4. Round Contracts Appropriately

```python
# For stocks: round to whole shares
contracts = round_contracts(position.contracts, lot_size=1.0)

# For futures: always round to whole contracts
contracts = round_contracts(position.contracts, lot_size=1.0, method='floor')
```

---

## Common Patterns

### Daily Rebalancing

```python
# Daily position calculation
def daily_rebalance(date):
    # Get latest forecasts, vols, prices
    forecasts = get_current_forecasts(date)
    vols = get_current_volatilities(date)
    prices = get_current_prices(date)
    
    # Calculate new positions
    position_set = pm.calculate_portfolio_positions(
        forecasts=forecasts,
        capital_allocation=allocation,
        volatilities=vols,
        prices=prices
    )
    
    # Apply buffering
    final_positions = pm.apply_buffering(
        current_positions=get_current_holdings(),
        target_position_set=position_set
    )
    
    return final_positions
```

### Risk Monitoring

```python
# Check risk limits
def check_risk_limits(position_set):
    risk_metrics = pm.calculate_portfolio_risk(position_set)
    
    # Portfolio volatility limit
    if risk_metrics['portfolio_volatility'] > 0.25:
        alert("Portfolio volatility exceeds 25%")
    
    # Leverage limit
    if risk_metrics['portfolio_leverage'] > 3.0:
        alert("Portfolio leverage exceeds 3x")
    
    # Individual position check
    for ticker, position in position_set.positions.items():
        if position.leverage > 2.0:
            alert(f"{ticker} leverage exceeds 2x")
```

---

## Troubleshooting

### Issue: Position leverage too high

**Solution:** Reduce volatility target or max forecast.

```python
config = PositionConfig(
    volatility_target=0.15,  # Lower target
    max_forecast=15.0        # Cap forecast
)
```

### Issue: Excessive trading from small forecast changes

**Solution:** Increase buffer width.

```python
config = PositionConfig(
    use_buffering=True,
    buffer_width=0.15  # Wider buffer = less trading
)
```

### Issue: Zero or negative contracts

**Solution:** Check for valid forecast and volatility.

```python
if position.contracts <= 0:
    print(f"Invalid position: forecast={position.forecast}, "
          f"vol={position.volatility}")
```

---

## References

- **Robert Carver:** "Systematic Trading" - Position sizing chapters
- **Formula Derivation:** Appendix on position calculation
- **Buffering:** Section on reducing costs
- **Leverage:** Risk management chapters

---

## See Also

- [Portfolio Module](./portfolio) - Calculate capital allocation
- [Forecast Module](./forecast) - Generate scaled forecasts
- [Volatility Module](./volatility) - Estimate instrument volatilities
- [Risk Management](./risk.md) - Advanced risk monitoring