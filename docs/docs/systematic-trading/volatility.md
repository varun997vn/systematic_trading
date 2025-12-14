---
id: volatility          # unique ID for this doc
title: Volatility       # this becomes the page title
sidebar_label: Volatility
---

# Volatility Module

## Overview

The Volatility module implements volatility estimation, forecasting, and targeting for systematic trading, based on Robert Carver's "Systematic Trading" methodology.

## Key Features

- **EWMA Volatility**: Exponentially weighted moving average (Carver's preferred method)
- **Standard Volatility**: Rolling standard deviation for comparison
- **Robust Volatility**: MAD-based estimation for outlier-resistant calculations
- **Volatility Targeting**: Risk normalization for position sizing
- **Forecasting**: Simple and EWMA-based volatility forecasts
- **Multi-Instrument**: Support for portfolio-level volatility calculations

---

## Core Components

### 1. VolatilityConfig

Configuration for volatility calculations:

```python
config = VolatilityConfig(
    span=36,                    # EWMA span (Carver recommends 32-36)
    min_periods=10,             # Minimum periods for calculation
    annualization_factor=256    # Trading days per year
)
```

### 2. EWMAVolatility

Exponentially weighted moving average volatility estimation:

```python
estimator = EWMAVolatility(config)

# From returns
vol_result = estimator.calculate(returns, ticker="AAPL")

# From prices
vol_result = estimator.calculate_from_prices(prices, ticker="AAPL")

print(f"Daily Vol: {vol_result.current_daily_vol:.4f}")
print(f"Annual Vol: {vol_result.current_annual_vol:.2%}")
```

### 3. StandardVolatility

Rolling standard deviation-based volatility:

```python
# Calculate rolling std
daily_vol = StandardVolatility.calculate(returns, window=36)

# Annualize
annual_vol = StandardVolatility.annualize(daily_vol, factor=256)
```

### 4. VolatilityTargeter

Volatility targeting for position sizing:

```python
targeter = VolatilityTargeter(target_vol=0.20)  # 20% target

# Calculate scalar
scalar = targeter.calculate_scalar(current_vol=0.15)
# Returns: 1.333 (to scale from 15% to 20%)

# Target position
targeted_position = targeter.target_position(
    base_position=100,
    current_vol=0.15
)
# Returns: 133.3
```

### 5. VolatilityForecaster

Forecast future volatility:

```python
forecaster = VolatilityForecaster()

# 1-day forecast
forecast = forecaster.simple_forecast(volatility, horizon=1)

# 5-day forecast (scaled by sqrt(5))
forecast_5d = forecaster.simple_forecast(volatility, horizon=5)

# EWMA forecast
ewma_forecast = forecaster.ewma_forecast(volatility, span=10)
```

### 6. VolatilityManager

Main interface coordinating all volatility operations:

```python
manager = VolatilityManager(
    config=VolatilityConfig(span=36),
    target_vol=0.20
)

# Estimate volatility
vol_result = manager.estimate_from_returns(returns, ticker="AAPL")

# Get position scalar
scalar = manager.get_position_scalar(vol_result)

# Forecast
forecast = manager.forecast(vol_result, horizon=1)

# Multi-instrument
results = manager.calculate_multi_instrument_vols(returns_df)
```

---

## Usage Examples

### Example 1: Basic Volatility Calculation

```python
import polars as pl
from volatility import EWMAVolatility, VolatilityConfig

# Your returns data
returns = pl.Series("returns", [0.01, -0.02, 0.015, -0.01, 0.008, ...])

# Calculate EWMA volatility
config = VolatilityConfig(span=36)
estimator = EWMAVolatility(config)
vol_result = estimator.calculate(returns, ticker="AAPL")

print(f"Current Annual Volatility: {vol_result.current_annual_vol:.2%}")
```

### Example 2: Volatility Targeting

```python
from volatility import VolatilityManager

# Initialize manager
manager = VolatilityManager(target_vol=0.20)

# Calculate volatility
vol_result = manager.estimate_from_prices(prices, ticker="TSLA")

# Get scaling factor
scalar = manager.get_position_scalar(vol_result)

# Scale your position
base_position = 100
targeted_position = base_position * scalar

print(f"TSLA Volatility: {vol_result.current_annual_vol:.2%}")
print(f"Position Scalar: {scalar:.4f}")
print(f"Targeted Position: {targeted_position:.2f}")
```

### Example 3: Multi-Instrument Portfolio

```python
import polars as pl
from volatility import VolatilityManager

# Returns DataFrame with multiple instruments
returns_df = pl.DataFrame({
    "AAPL": [0.01, -0.02, 0.015, ...],
    "GOOGL": [0.012, -0.015, 0.008, ...],
    "MSFT": [0.008, -0.01, 0.012, ...],
})

# Calculate volatilities
manager = VolatilityManager(target_vol=0.20)
vol_results = manager.calculate_multi_instrument_vols(returns_df)

# Display results
for ticker, vol_result in vol_results.items():
    print(f"{ticker}: {vol_result.current_annual_vol:.2%}")
```

### Example 4: Comparing EWMA Spans

```python
from volatility import EWMAVolatility, VolatilityConfig

returns = pl.Series([...])  # Your returns

# Test different spans
for span in [16, 32, 64, 128]:
    config = VolatilityConfig(span=span)
    estimator = EWMAVolatility(config)
    vol_result = estimator.calculate(returns)
    
    print(f"Span {span}: {vol_result.current_annual_vol:.2%}")
```

---

## Integration with Data Manager

```python
from data_manager import DataManager
from volatility import VolatilityManager

# Get data
data_mgr = DataManager()
price_data = data_mgr.get_data("AAPL", start_date="2020-01-01")

# Calculate volatility
vol_mgr = VolatilityManager()
vol_result = vol_mgr.estimate_from_prices(
    price_data.close,
    ticker="AAPL"
)

print(f"AAPL Volatility: {vol_result.current_annual_vol:.2%}")
```

---

## Carver's Volatility Principles

### 1. EWMA Over Simple Moving Average

Carver prefers EWMA because:
- More responsive to recent volatility changes
- Smoother estimates
- Better for systematic trading

**Recommended span**: 32-36 days

### 2. Volatility Targeting

Core principle: normalize risk across instruments

```
Position Size = (Target Vol / Current Vol) × Base Position
```

**Recommended target**: 20% annual volatility

### 3. Annualization

Convert daily volatility to annual:

```
Annual Vol = Daily Vol × √(256)
```

Carver uses **256 trading days/year**

### 4. Forecast Scaling

Volatility used to scale forecasts to consistent risk:

```
Scaled Forecast = Raw Forecast × (Target Vol / Current Vol)
```

---

## Performance Considerations

### Polars vs Pandas

This module uses **Polars** for performance:

```python
# Polars EWMA (fast)
vol = returns.ewm_mean(span=36)

# Pandas equivalent
vol = returns.ewm(span=36).mean()
```

Polars is 2-10x faster for large datasets.

### Caching Volatility

For production systems, cache volatility estimates:

```python
class VolatilityCache:
    def __init__(self):
        self._cache = {}
    
    def get(self, ticker: str, returns: pl.Series) -> VolatilityResult:
        key = (ticker, len(returns))
        if key not in self._cache:
            vol_mgr = VolatilityManager()
            self._cache[key] = vol_mgr.estimate_from_returns(returns, ticker)
        return self._cache[key]
```

---

## Testing

Run the test suite:

```bash
pytest test_volatility.py -v
```

Run example script:

```bash
python example_volatility.py
```

---

## API Reference

### VolatilityConfig

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| span | int | 36 | EWMA span (Carver: 32-36) |
| min_periods | int | 10 | Minimum periods required |
| annualization_factor | int | 256 | Trading days/year |

### VolatilityResult

| Property | Type | Description |
|----------|------|-------------|
| ticker | str | Instrument identifier |
| daily_vol | pl.Series | Daily volatility series |
| annual_vol | pl.Series | Annualized volatility series |
| current_daily_vol | float | Most recent daily vol |
| current_annual_vol | float | Most recent annual vol |

### EWMAVolatility

| Method | Parameters | Returns |
|--------|------------|---------|
| calculate | returns, ticker | VolatilityResult |
| calculate_from_prices | prices, ticker | VolatilityResult |

### VolatilityTargeter

| Method | Parameters | Returns |
|--------|------------|---------|
| calculate_scalar | current_vol | float |
| calculate_scalars | volatilities | pl.Series |
| target_position | base_position, current_vol | float |

### VolatilityManager

| Method | Parameters | Returns |
|--------|------------|---------|
| estimate_from_returns | returns, ticker | VolatilityResult |
| estimate_from_prices | prices, ticker | VolatilityResult |
| forecast | vol_result, horizon | pl.Series |
| get_position_scalar | vol_result | float |
| calculate_multi_instrument_vols | returns_df | dict |

---

## Common Issues

### Issue: NaN in volatility series

**Cause**: Insufficient data for EWMA calculation

**Solution**: Reduce `min_periods` or provide more data

```python
config = VolatilityConfig(span=36, min_periods=5)
```

### Issue: Extreme volatility values

**Cause**: Outliers in returns data

**Solution**: Use RobustVolatility (MAD-based)

```python
from volatility import RobustVolatility

vol = RobustVolatility.calculate(returns, window=36)
```

### Issue: Slow performance with large datasets

**Solution**: Use Polars throughout your pipeline

```python
# Convert pandas to polars
import pandas as pd
import polars as pl

df_pandas = pd.DataFrame(...)
df_polars = pl.from_pandas(df_pandas)
```

---

## References

- Carver, R. (2015). *Systematic Trading*. Harriman House.
- Chapter 4: Volatility
- Chapter 10: Risk Management

---

## License

Part of the Systematic Trading Framework. See main repository for license.