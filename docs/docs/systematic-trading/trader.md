---
id: trader
title: Trader
sidebar_label: Trader
---

# Trader Module - generate_trades() Method

## Overview

The `Trader.generate_trades()` method implements Robert Carver's complete systematic trading pipeline in a single, comprehensive function. It handles the full execution flow from data loading to trade generation, with volatility standardization applied throughout (as per Carver's principles).

## Full Pipeline (8 Steps)

The `generate_trades()` method executes Carver's systematic trading framework in the following sequence:

```
1. Data Ingestion & Validation
   ↓
2. Volatility Estimation (EWMA)
   ↓
3. Forecast Generation (Trading Rules)
   ↓
4. Forecast Combination (FDM - Forecast Diversification Multiplier)
   ↓
5. Portfolio Weights (IDM - Instrument Diversification Multiplier)
   ↓
6. Position Sizing (Volatility Targeting)
   ↓
7. Risk Management (Leverage Limits)
   ↓
8. Trade Generation (with optional buffering)
```

## Key Features

### ✓ Volatility Standardization Throughout
- All forecasts are scaled by volatility
- Position sizing uses volatility targeting
- Risk management incorporates volatility metrics
- Follows Carver's principle: "Volatility is the common currency of risk"

### ✓ Complete Pipeline Integration
- Seamlessly connects all modules (data, volatility, forecast, position, portfolio, risk)
- Maintains state for incremental trading
- Stores full pipeline output for analysis

### ✓ Flexible Configuration
- Customizable EWMAC pairs (defaults to Carver's standard 6-pair suite)
- Multiple portfolio weighting methods (equal, inverse volatility, risk parity)
- Optional position buffering to reduce turnover
- Configurable risk limits and volatility targets

## Basic Usage

```python
from st.trader import Trader

# Initialize trader
trader = Trader(
    tickers=["AAPL", "MSFT", "GOOGL"],
    capital=100_000,
)

# Generate trades (uses all Carver defaults)
trade_set = trader.generate_trades(
    start_date="2020-01-01",
    end_date="2024-12-01",
)

# View trades
for trade in trade_set.trades:
    print(f"{trade.action} {trade.ticker}: {trade.contracts:.2f} @ ${trade.price:.2f}")

# Get pipeline summary
summary = trader.get_pipeline_summary()
print(summary)
```

## Method Signature

```python
def generate_trades(
    self,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    ewmac_pairs: Optional[List[Tuple[int, int]]] = None,
    forecast_weights: Optional[Dict[str, float]] = None,
    portfolio_weights_method: str = "equal",
    apply_buffering: bool = True,
) -> TradeSet:
```

### Parameters

- **start_date** (str, optional): Data start date (YYYY-MM-DD)
- **end_date** (str, optional): Data end date (YYYY-MM-DD)
- **ewmac_pairs** (List[Tuple], optional): List of (fast, slow) EWMAC pairs
  - Default: `[(2,8), (4,16), (8,32), (16,64), (32,128), (64,256)]` (Carver's standard)
- **forecast_weights** (Dict, optional): Custom forecast weights (equal if None)
- **portfolio_weights_method** (str): Portfolio weighting method
  - Options: `"equal"`, `"inverse_volatility"`, `"risk_parity"`
  - Default: `"equal"`
- **apply_buffering** (bool): Apply position buffering to reduce turnover
  - Default: `True`

### Returns

**TradeSet**: Collection of trade orders with:
- `trades`: List of Trade objects
- `num_trades`: Number of trades generated
- `total_notional`: Total notional value
- `timestamp`: Generation timestamp

## Advanced Usage

### Custom Configuration

```python
from st.trader import Trader
from st.forecast import ForecastConfig
from st.volatility import VolatilityConfig
from st.position import PositionConfig

# Custom configurations
forecast_config = ForecastConfig(
    target_abs_forecast=10.0,
    cap_forecasts=True,
)

volatility_config = VolatilityConfig(
    span=36,  # EWMA span
    annualization_factor=256,
)

position_config = PositionConfig(
    volatility_target=0.20,  # 20% annual vol
    max_leverage=2.0,
    use_buffering=True,
)

# Initialize with custom configs
trader = Trader(
    tickers=["SPY", "QQQ", "TLT"],
    capital=250_000,
    forecast_config=forecast_config,
    volatility_config=volatility_config,
    position_config=position_config,
)

# Generate trades with custom EWMAC rules
trade_set = trader.generate_trades(
    start_date="2020-01-01",
    ewmac_pairs=[(8, 32), (16, 64), (32, 128)],
    portfolio_weights_method="risk_parity",
)
```

### Different Portfolio Weighting Methods

```python
# Equal weighting (default)
trade_set = trader.generate_trades(
    portfolio_weights_method="equal"
)

# Inverse volatility weighting
trade_set = trader.generate_trades(
    portfolio_weights_method="inverse_volatility"
)

# Risk parity weighting
trade_set = trader.generate_trades(
    portfolio_weights_method="risk_parity"
)
```

### Incremental Trading

```python
# Initial trades
trade_set_1 = trader.generate_trades(
    start_date="2023-01-01",
    end_date="2023-06-30",
)

# Update positions
trader.update_positions(trade_set_1)

# Generate rebalancing trades
trade_set_2 = trader.generate_trades(
    start_date="2023-01-01",
    end_date="2023-12-31",
)

# Buffering will reduce turnover automatically
trader.update_positions(trade_set_2)
```

## Pipeline Output

The `generate_trades()` method stores comprehensive pipeline output:

```python
trader.pipeline_output.tickers              # List of tickers
trader.pipeline_output.prices               # Price series
trader.pipeline_output.volatilities         # Volatility results
trader.pipeline_output.raw_forecasts        # Individual EWMAC forecasts
trader.pipeline_output.combined_forecasts   # Combined forecast series
trader.pipeline_output.current_forecasts    # Latest forecast values
trader.pipeline_output.portfolio_weights    # Portfolio weights with IDM
trader.pipeline_output.capital_allocation   # Capital per instrument
trader.pipeline_output.position_set         # Target positions
trader.pipeline_output.trade_set            # Generated trades
```

### Get Summary

```python
summary = trader.get_pipeline_summary()
# Returns:
# {
#     'timestamp': '2024-12-14T...',
#     'num_instruments': 3,
#     'num_trades': 3,
#     'total_notional': 150000.0,
#     'portfolio_leverage': 1.5,
#     'idm': 1.732,
#     'current_forecasts': {'AAPL': 12.5, 'MSFT': -8.2, ...},
#     'capital_allocation': {'AAPL': 50000, 'MSFT': 50000, ...}
# }
```

### Get Risk Report

```python
risk_report = trader.get_risk_report()
print(risk_report)
# Displays:
# - Portfolio volatility
# - Leverage
# - Risk per instrument
# - Diversification multiplier
# - Risk limit checks
```

## Trade Structure

Each `Trade` object contains:

```python
trade.ticker         # Instrument ticker
trade.action         # "BUY" or "SELL"
trade.contracts      # Number of contracts
trade.price          # Current price
trade.notional       # Notional value
trade.forecast       # Combined forecast
trade.volatility     # Instrument volatility
trade.timestamp      # Trade timestamp
```

## Volatility Standardization Details

Carver's framework uses volatility as the "common currency" of risk. The pipeline applies volatility standardization at multiple stages:

### 1. Forecast Generation
- EWMAC forecasts can be normalized by price volatility
- Ensures comparable signals across instruments

### 2. Forecast Scaling
- All forecasts scaled to -20 to +20 range
- Target average absolute forecast of 10

### 3. Position Sizing (Core Formula)
```
Position = (Capital × Vol_Target × IDM × Weight × Forecast) / (10 × Instrument_Vol)
```

Where:
- `Capital`: Allocated capital for instrument
- `Vol_Target`: Annual volatility target (default 20%)
- `IDM`: Instrument Diversification Multiplier
- `Weight`: Instrument portfolio weight
- `Forecast`: Combined scaled forecast (-20 to +20)
- `Instrument_Vol`: Annual instrument volatility

### 4. Risk Management
- Portfolio leverage capped at maximum
- Positions scaled proportionally if limits exceeded
- Volatility-adjusted risk metrics

## Configuration Defaults

### From Settings (settings.py)
```python
VOLATILITY_TARGET = 0.20        # 20% annual
MAX_LEVERAGE = 2.0              # 2x maximum
INITIAL_CAPITAL = 100,000       # $100k
BUSINESS_DAYS_PER_YEAR = 256    # Carver's convention
```

### EWMAC Pairs (Carver's Standard)
```python
DEFAULT_EWMAC_PAIRS = [
    (2, 8),      # Very fast
    (4, 16),     # Fast
    (8, 32),     # Medium-fast
    (16, 64),    # Medium
    (32, 128),   # Medium-slow
    (64, 256),   # Slow
]
```

## Error Handling

The pipeline will raise errors if:
- Data fails to load for any ticker
- Validation fails (insufficient data, missing values, etc.)
- Invalid configurations provided
- Required data missing at any pipeline step

## Performance Considerations

### Data Loading
- Caches loaded data in `trader.price_data`
- Reuses data for multiple `generate_trades()` calls
- Validates data only once per ticker

### Buffering
- Reduces turnover by avoiding small position changes
- Default buffer width: 10% of position size
- Can be disabled with `apply_buffering=False`

### Computational Efficiency
- Uses Polars for fast data operations
- Vectorized calculations throughout
- Minimal Python loops

## Changes from Original trader.py

### New Features
1. **generate_trades()** method - Complete pipeline execution
2. **Trade and TradeSet** classes - Structured trade representation
3. **TradingPipeline** class - Comprehensive output storage
4. **update_positions()** - Position tracking
5. **get_pipeline_summary()** - Quick summary access
6. **get_risk_report()** - Risk reporting

### New Dependencies
Added imports for:
- ForecastManager
- VolatilityManager
- PositionManager
- PortfolioManager
- RiskManager

### Updated settings.py
Added `MAX_LEVERAGE = 2.0` configuration

## Examples

See `example_generate_trades.py` for comprehensive examples:
- Basic usage
- Advanced configuration
- Portfolio optimization
- Incremental trading
- Custom EWMAC rules

## References

- **Book**: "Systematic Trading" by Robert Carver
- **Key Concepts**:
  - Volatility targeting (Chapter 6)
  - Forecast combination (Chapter 8)
  - Position sizing (Chapter 9)
  - Portfolio optimization (Chapter 10)

## Future Enhancements

Potential additions:
- [ ] Carry and mean reversion strategies
- [ ] Custom trading rules
- [ ] Backtesting integration
- [ ] Performance attribution
- [ ] Transaction cost modeling
- [ ] Execution algorithms