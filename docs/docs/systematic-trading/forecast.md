---
id: forecast
title: Forecasting Module
sidebar_label: Forecast
---

# Forecasting Module

**Generate trading signals using systematic rules**

The forecasting module implements Robert Carver's standardized approach to generating and combining trading signals. All forecasts are scaled to a range of -20 to +20, with a target average absolute forecast of 10.

---

## Core Concepts

### Forecast Standardization

Carver's framework requires all trading rules to produce forecasts in a standardized range:

- **Range:** -20 to +20
- **Target Average:** 10 (average absolute forecast)
- **Interpretation:**
  - Positive values = Long signal
  - Negative values = Short signal
  - Magnitude = Signal strength

### Trading Rules

Three primary strategies are implemented:

1. **EWMAC** - Trend following (primary strategy)
2. **Carry** - Yield differential (futures/FX)
3. **Mean Reversion** - Counter-trend

---

## Quick Start

```python
from st.forecast import ForecastManager
from st.data import DataManager
import polars as pl

# Get price data
dm = DataManager()
price_data = dm.get_data("AAPL", start_date="2020-01-01")
prices = pl.Series(price_data.close)

# Initialize forecast manager
fm = ForecastManager()

# Generate EWMAC forecast
forecast = fm.generate_ewmac(
    prices=prices,
    fast_span=16,
    slow_span=64,
    ticker="AAPL"
)

print(f"Current forecast: {forecast.current_forecast}")
# Output: Current forecast: 8.45
```

---

## EWMAC (Exponentially Weighted Moving Average Crossover)

### Overview

EWMAC is Carver's primary trend-following strategy. It calculates the difference between two exponential moving averages and scales the result to the standardized forecast range.

### Single EWMAC Forecast

```python
# Generate single EWMAC
forecast = fm.generate_ewmac(
    prices=prices,
    fast_span=16,    # Fast EMA span
    slow_span=64,    # Slow EMA span
    ticker="AAPL"
)

# Access components
raw = forecast.raw_forecast      # Unscaled values
scaled = forecast.scaled_forecast # Scaled to -20/+20
current = forecast.current_forecast # Most recent value
```

### Standard EWMAC Suite

Carver recommends using multiple EWMAC variations for diversification:

```python
# Generate all 6 standard EWMAC combinations
forecasts = fm.generate_standard_suite(prices, ticker="AAPL")

# Returns dictionary with these rules:
# - ewmac_2_8
# - ewmac_4_16
# - ewmac_8_32
# - ewmac_16_64
# - ewmac_32_128
# - ewmac_64_256

for name, forecast in forecasts.items():
    print(f"{name}: {forecast.current_forecast:.2f}")
```

### Risk-Adjusted EWMAC

For better signal quality, normalize by price volatility:

```python
from st.volatility import VolatilityManager

# Calculate price volatility
vm = VolatilityManager()
vol_result = vm.estimate_from_prices(prices, ticker="AAPL")
price_vol = vol_result.daily_vol * prices  # Price volatility

# Generate normalized EWMAC
forecast = fm.generate_ewmac_normalized(
    prices=prices,
    price_volatility=price_vol,
    fast_span=16,
    slow_span=64,
    ticker="AAPL"
)
```

### EWMAC Parameters

| Parameter | Carver's Standard Values | Description |
|-----------|-------------------------|-------------|
| fast_span | 2, 4, 8, 16, 32, 64 | Fast EMA period |
| slow_span | 8, 16, 32, 64, 128, 256 | Slow EMA period |
| Ratio | 4:1 (slow:fast) | Typical ratio between spans |

---

## Carry Strategy

### Overview

Carry strategies exploit yield differentials between spot and forward prices. Particularly effective for futures, FX, and fixed income.

### Basic Carry

```python
# Calculate carry from spot and forward prices
forecast = fm.generate_carry(
    spot_prices=spot_series,
    forward_prices=forward_series,
    smoothing_span=30,
    ticker="CL"  # Crude oil futures
)
```

### Yield-Based Carry

```python
from st.forecast import Carry

carry = Carry(smoothing_span=30)

# Calculate from yield differential
raw = carry.calculate_from_yields(
    current_yield=current_yields,
    expected_yield=expected_yields,
    ticker="ZN"  # 10-year Treasury
)
```

### Carry Formula

```
Raw Carry = (Forward Price - Spot Price) / Spot Price
Smoothed = EWMA(Raw Carry, span=30)
```

---

## Mean Reversion

### Overview

Mean reversion strategies bet against extreme price movements, assuming prices will revert to their average.

### Basic Mean Reversion

```python
forecast = fm.generate_mean_reversion(
    prices=prices,
    lookback=30,           # Rolling window
    entry_threshold=2.0,   # Std devs for entry
    ticker="SPY"
)
```

### How It Works

```python
# Calculate z-score
z_score = (price - rolling_mean) / rolling_std

# Mean reversion signal (inverted)
signal = -z_score

# When price is 2 std devs above mean → signal = -2 (short)
# When price is 2 std devs below mean → signal = +2 (long)
```

### Parameters

- **lookback:** Window for mean/std calculation (typically 20-60 days)
- **entry_threshold:** Standard deviations for signal strength (1.5-2.5)

---

## Forecast Scaling

### Why Scale Forecasts?

Carver's framework requires all trading rules to produce comparable forecasts. Scaling ensures:

1. **Consistency** across different strategies
2. **Predictable risk** from each forecast
3. **Easy combination** of multiple rules

### Automatic Scaling

```python
from st.forecast import ForecastScaler

scaler = ForecastScaler()

# Calculate scaling factor
scalar = scaler.calculate_scalar(raw_forecast)
# Returns: target_abs_forecast / avg_abs(raw_forecast)

# Apply scaling
scaled = scaler.scale(raw_forecast)
# Scaled to average absolute value of 10
# Capped at -20 to +20
```

### Custom Configuration

```python
from st.forecast import ForecastConfig

config = ForecastConfig(
    target_abs_forecast=10.0,  # Target average
    min_forecast=-20.0,        # Floor
    max_forecast=20.0,         # Ceiling
    cap_forecasts=True         # Apply caps
)

fm = ForecastManager(config=config)
```

---

## Combining Forecasts

### Equal Weighting

```python
# Generate multiple forecasts
ewmac_16_64 = fm.generate_ewmac(prices, 16, 64, "AAPL")
ewmac_32_128 = fm.generate_ewmac(prices, 32, 128, "AAPL")
mean_rev = fm.generate_mean_reversion(prices, 30, 2.0, "AAPL")

forecasts = [ewmac_16_64, ewmac_32_128, mean_rev]

# Combine with equal weights
combined, fdm = fm.combine_forecasts(forecasts)

print(f"Combined forecast: {combined[-1]:.2f}")
print(f"Diversification multiplier: {fdm:.2f}")
```

### Custom Weighting

```python
# Define custom weights (must sum to 1.0)
weights = {
    "ewmac_16_64": 0.5,      # 50% trend following
    "ewmac_32_128": 0.3,     # 30% longer trend
    "mean_reversion_30": 0.2 # 20% mean reversion
}

combined, fdm = fm.combine_forecasts(forecasts, weights=weights)
```

### Diversification Multiplier (FDM)

The FDM accounts for diversification benefits when combining forecasts:

```
FDM = 1 / sqrt(sum of squared weights)
```

**Examples:**
- 1 forecast → FDM = 1.0
- 2 equal forecasts → FDM = 1.41
- 4 equal forecasts → FDM = 2.0

Applied in position sizing to scale positions up when using multiple forecasts.

---

## Complete Workflow Example

### Multi-Strategy System

```python
from st.data import DataManager
from st.forecast import ForecastManager
from st.volatility import VolatilityManager
import polars as pl

# 1. Load data
dm = DataManager()
price_data = dm.get_data("SPY", start_date="2020-01-01")
prices = pl.Series(price_data.close)

# 2. Calculate volatility (for normalized EWMAC)
vm = VolatilityManager()
vol_result = vm.estimate_from_prices(prices, "SPY")
price_vol = vol_result.daily_vol * prices

# 3. Initialize forecast manager
fm = ForecastManager()

# 4. Generate multiple forecasts
forecasts = []

# Trend following (3 EWMAC variations)
forecasts.append(fm.generate_ewmac(prices, 8, 32, "SPY"))
forecasts.append(fm.generate_ewmac_normalized(
    prices, price_vol, 16, 64, "SPY"
))
forecasts.append(fm.generate_ewmac(prices, 32, 128, "SPY"))

# Mean reversion
forecasts.append(fm.generate_mean_reversion(prices, 30, 2.0, "SPY"))

# 5. Combine with custom weights
weights = {
    "ewmac_8_32": 0.3,
    "ewmac_16_64_normalized": 0.4,
    "ewmac_32_128": 0.2,
    "mean_reversion_30": 0.1
}

combined_forecast, fdm = fm.combine_forecasts(forecasts, weights)

# 6. Use combined forecast for position sizing
current_signal = combined_forecast[-1]
print(f"Combined forecast: {current_signal:.2f}")
print(f"Diversification multiplier: {fdm:.2f}")
```

---

## Advanced Topics

### Forecast Correlation Analysis

```python
from st.forecast import calculate_forecast_diversity

# Generate multiple forecasts
forecasts_dict = fm.generate_standard_suite(prices, "AAPL")

# Extract scaled forecasts
forecast_series = {
    name: f.scaled_forecast 
    for name, f in forecasts_dict.items()
}

# Calculate correlation matrix
corr_matrix = calculate_forecast_diversity(forecast_series)
print(corr_matrix)

# Lower correlation = better diversification
```

### Forecast Validation

```python
from st.forecast import validate_forecast, ForecastConfig

config = ForecastConfig()

# Validate forecast is within bounds
is_valid = validate_forecast(forecast.scaled_forecast, config)

if not is_valid:
    print("Warning: Forecast outside expected range")
```

### Custom Trading Rules

```python
from st.forecast import EWMAC, ForecastScaler

# Create custom EWMAC instance
custom_ewmac = EWMAC(fast_span=10, slow_span=50)

# Calculate raw forecast
raw = custom_ewmac.calculate(prices, ticker="AAPL")

# Scale manually
scaler = ForecastScaler()
scaled = scaler.scale(raw)
```

---

## API Reference

### ForecastManager

Main interface for forecast generation.

#### Methods

**`__init__(config: Optional[ForecastConfig] = None)`**
- Initialize forecast manager with optional configuration

**`generate_ewmac(prices, fast_span, slow_span, ticker) -> Forecast`**
- Generate EWMAC trend-following forecast
- **Args:**
  - `prices` (pl.Series): Price series
  - `fast_span` (int): Fast EMA span
  - `slow_span` (int): Slow EMA span
  - `ticker` (str): Instrument identifier
- **Returns:** Forecast object

**`generate_ewmac_normalized(prices, price_volatility, fast_span, slow_span, ticker) -> Forecast`**
- Generate volatility-normalized EWMAC forecast
- **Args:** Same as `generate_ewmac` plus `price_volatility`
- **Returns:** Forecast object

**`generate_carry(spot_prices, forward_prices, smoothing_span, ticker) -> Forecast`**
- Generate carry-based forecast
- **Args:**
  - `spot_prices` (pl.Series): Spot price series
  - `forward_prices` (pl.Series): Forward price series
  - `smoothing_span` (int): EWMA smoothing period
  - `ticker` (str): Instrument identifier
- **Returns:** Forecast object

**`generate_mean_reversion(prices, lookback, entry_threshold, ticker) -> Forecast`**
- Generate mean reversion forecast
- **Args:**
  - `prices` (pl.Series): Price series
  - `lookback` (int): Rolling window size
  - `entry_threshold` (float): Std dev threshold
  - `ticker` (str): Instrument identifier
- **Returns:** Forecast object

**`combine_forecasts(forecasts, weights=None) -> Tuple[pl.Series, float]`**
- Combine multiple forecasts
- **Args:**
  - `forecasts` (List[Forecast]): List of Forecast objects
  - `weights` (Dict[str, float], optional): Custom weights
- **Returns:** (combined_forecast, diversification_multiplier)

**`generate_standard_suite(prices, ticker) -> Dict[str, Forecast]`**
- Generate Carver's 6 standard EWMAC variations
- **Args:**
  - `prices` (pl.Series): Price series
  - `ticker` (str): Instrument identifier
- **Returns:** Dictionary of Forecast objects

---

### Forecast

Container for forecast results.

#### Attributes

- `rule_name` (str): Name of trading rule
- `ticker` (str): Instrument identifier
- `raw_forecast` (pl.Series): Unscaled forecast values
- `scaled_forecast` (pl.Series): Scaled forecast (-20 to +20)
- `params` (dict): Rule parameters

#### Properties

- `current_forecast` (float): Most recent forecast value

---

### ForecastConfig

Configuration for forecast generation.

#### Attributes

- `target_abs_forecast` (float): Target average absolute forecast (default: 10.0)
- `min_forecast` (float): Minimum forecast value (default: -20.0)
- `max_forecast` (float): Maximum forecast value (default: 20.0)
- `cap_forecasts` (bool): Apply min/max capping (default: True)

---

## Best Practices

### 1. Use Multiple Forecasts

Combine different trading rules for diversification:

```python
# ✅ Good: Multiple strategies
forecasts = [
    fm.generate_ewmac(prices, 16, 64, ticker),
    fm.generate_ewmac(prices, 32, 128, ticker),
    fm.generate_mean_reversion(prices, 30, 2.0, ticker)
]

# ❌ Avoid: Single strategy
forecast = fm.generate_ewmac(prices, 16, 64, ticker)
```

### 2. Normalize by Volatility

Use normalized EWMAC for better risk-adjusted signals:

```python
# ✅ Good: Risk-adjusted
forecast = fm.generate_ewmac_normalized(
    prices, price_vol, 16, 64, ticker
)

# ⚠️ Acceptable: Standard EWMAC
forecast = fm.generate_ewmac(prices, 16, 64, ticker)
```

### 3. Monitor Forecast Correlations

Check correlations between forecasts to ensure diversification:

```python
# Calculate correlations
corr_matrix = calculate_forecast_diversity(forecast_series)

# Ideal: Correlations < 0.5
# Warning: Correlations > 0.8 (low diversification)
```

### 4. Validate Forecasts

Always validate forecasts are within expected range:

```python
is_valid = validate_forecast(
    forecast.scaled_forecast, 
    config
)
```

---

## Troubleshooting

### Forecasts Not Scaling Properly

**Problem:** Scaled forecasts far from target average of 10

**Solution:**
```python
# Check raw forecast statistics
print(f"Avg abs raw: {forecast.raw_forecast.abs().mean():.4f}")
print(f"Avg abs scaled: {forecast.scaled_forecast.abs().mean():.4f}")

# Manually inspect scaler
scaler = ForecastScaler()
scalar = scaler.calculate_scalar(raw_forecast)
print(f"Scaling factor: {scalar:.4f}")
```

### High Forecast Correlation

**Problem:** All forecasts moving together

**Solution:**
```python
# Use different timeframes
forecasts = [
    fm.generate_ewmac(prices, 8, 32, ticker),   # Short-term
    fm.generate_ewmac(prices, 32, 128, ticker), # Medium-term
    fm.generate_ewmac(prices, 64, 256, ticker)  # Long-term
]

# Add counter-trend strategy
forecasts.append(
    fm.generate_mean_reversion(prices, 30, 2.0, ticker)
)
```

### Extreme Forecast Values

**Problem:** Forecasts hitting caps (-20/+20) frequently

**Solution:**
```python
# Check if capping is too aggressive
config = ForecastConfig(
    cap_forecasts=False  # Disable caps temporarily
)

# Or adjust target
config = ForecastConfig(
    target_abs_forecast=8.0  # Lower target
)
```

---

## Next Steps

- **[Portfolio Module](portfolio)** - Combine forecasts across instruments
- **[Position Sizing](position)** - Convert forecasts to positions
- **[Risk Management](risk)** - Apply portfolio risk controls