# Quick Reference - Systematic Trading System

## Installation & Setup

```bash
# Setup (one-time)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run demo
python main.py

# Run tests
pytest
```

## Common Code Snippets

### Download Data

```python
from data.data_manager import DataManager

dm = DataManager()

# Single stock
data = dm.download_stock_data('DBS.SI', save=True)

# Multiple stocks
stocks = dm.download_multiple_stocks(['DBS.SI', 'O39.SI', 'ES3.SI'])

# Load cached data
data = dm.load_data('DBS.SI')
```

### Run a Backtest

```python
from strategy.trend_following import EWMAC
from backtesting.backtest_engine import BacktestEngine
from backtesting.performance import PerformanceAnalyzer

# Create strategy
strategy = EWMAC(fast_span=16, slow_span=64)

# Run backtest
engine = BacktestEngine()
results = engine.run(strategy, data)

# Analyze
analyzer = PerformanceAnalyzer(results)
analyzer.print_summary()
analyzer.plot_equity_curve()
```

### Compare Strategies

```python
strategies = [
    EWMAC(16, 64, name="EWMAC_Fast"),
    EWMAC(32, 128, name="EWMAC_Medium"),
    EWMAC(64, 256, name="EWMAC_Slow"),
]

for strategy in strategies:
    results = engine.run(strategy, data)
    print(f"{strategy.name}: Sharpe = {results['sharpe_ratio']:.2f}")
```

### Custom Strategy

```python
from strategy.base_strategy import BaseStrategy
import pandas as pd

class MyStrategy(BaseStrategy):
    def __init__(self, param1, param2):
        super().__init__(name="MyStrategy")
        self.param1 = param1
        self.param2 = param2

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        if not self.validate_data(data):
            return pd.Series(index=data.index, dtype=float)

        # Your logic here
        signals = pd.Series(0.0, index=data.index)

        # Generate signals...
        # signals[condition] = 1.0  # Long
        # signals[condition] = -1.0  # Short

        return self.calculate_forecast_scalar(signals)
```

### Position Sizing

```python
from risk_management.position_sizer import PositionSizer

# Volatility-based (Carver's method)
sizer = PositionSizer(
    capital=100000,
    volatility_target=0.20,  # 20% annual volatility
    max_position_size=0.10   # 10% max per position
)

# Calculate position
shares = sizer.calculate_instrument_weight(
    price=100.0,
    volatility=0.25,
    forecast=10.0
)

# Fixed fractional (simpler method)
shares = sizer.calculate_fixed_fractional(price=100.0, fraction=0.02)
```

### Performance Analysis

```python
from backtesting.performance import PerformanceAnalyzer

analyzer = PerformanceAnalyzer(results)

# Print metrics
analyzer.print_summary()

# Plot charts
analyzer.plot_equity_curve(save_path='equity.png')
analyzer.plot_positions(save_path='positions.png')

# Access specific metrics
sharpe = results['sharpe_ratio']
total_return = results['total_return']
max_dd = results['max_drawdown']
```

## Configuration (.env)

```bash
# Data
DATA_START_DATE=2018-01-01
DATA_END_DATE=2024-12-31

# Capital & Risk
INITIAL_CAPITAL=100000
MAX_POSITION_SIZE=0.10
VOLATILITY_TARGET=0.20

# Strategy
MA_FAST=16
MA_SLOW=64

# Costs
TRANSACTION_COST=0.001  # 0.1%
SLIPPAGE=0.0005         # 0.05%

# Stocks
SGX_STOCKS=DBS.SI,O39.SI,ES3.SI
```

## Key Formulas (Carver's Method)

### Position Size
```
position = (target_vol / instrument_vol) × (forecast / 10) × capital / price
```

### Forecast Scaling
```
scaled_forecast = raw_forecast × (10 / avg_abs_forecast)
capped at ±20
```

### Sharpe Ratio
```
sharpe = (mean_return - risk_free_rate) / std_return × √252
```

### Volatility (Annualized)
```
annual_vol = daily_vol × √252
```

## Common SGX Tickers

| Ticker | Name | Sector |
|--------|------|--------|
| DBS.SI | DBS Bank | Financial |
| O39.SI | OCBC Bank | Financial |
| D05.SI | DBS Group | Financial |
| U11.SI | UOB | Financial |
| C6L.SI | SIA | Aviation |
| ES3.SI | STI ETF | Index |
| Z74.SI | Singtel | Telecom |

## Directory Structure

```
systematic_trading/
├── config/           # Settings
├── data/            # Data management
│   └── historical/  # Downloaded CSV files
├── strategy/        # Trading strategies
├── risk_management/ # Position sizing
├── backtesting/     # Backtest engine
├── utils/           # Helper functions
├── tests/           # Unit tests
├── logs/            # Log files
└── main.py          # Demo script
```

## Testing

```bash
# All tests
pytest

# Specific test file
pytest tests/test_strategy.py

# With coverage
pytest --cov=. --cov-report=html

# Verbose
pytest -v
```

## Logging

```python
from utils.logger import setup_logger

logger = setup_logger(__name__, log_file='my_log.log')
logger.info("Message")
logger.error("Error message")
```

## Carver's Key Principles

1. **Volatility Targeting**: Scale positions inversely to volatility
2. **Forecast Scaling**: Normalize signals to -20 to +20 range
3. **Diversification**: Multiple rules, timeframes, and instruments
4. **Cost Awareness**: Model transaction costs realistically
5. **Trend Following**: Core strategy using EWMAC

## Typical Workflows

### Research New Strategy
1. Implement strategy class in `strategy/`
2. Add tests in `tests/`
3. Run backtest with `BacktestEngine`
4. Analyze with `PerformanceAnalyzer`
5. Compare to existing strategies

### Optimize Parameters
1. Define parameter ranges
2. Loop through combinations
3. Run backtests for each
4. Compare Sharpe ratios
5. Use walk-forward analysis (avoid overfitting)

### Portfolio Construction
1. Download data for multiple stocks
2. Run individual backtests
3. Use `run_multiple_assets()`
4. Analyze portfolio Sharpe ratio
5. Adjust position sizes if needed

## Performance Benchmarks

**Good Systematic Strategy** (Carver's standards):
- Sharpe Ratio: > 0.5 (good), > 1.0 (excellent)
- Win Rate: Not important (trend following has ~40% win rate)
- Max Drawdown: < 30% acceptable
- Turnover: Moderate (too high = excessive costs)

## Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| No module named 'X' | `pip install -r requirements.txt` |
| No data downloaded | Check internet, verify .SI suffix |
| Import errors | Run from project root directory |
| Matplotlib errors | Plots saved to files (no display needed) |
| Test failures | Check logs in `logs/` directory |

## Resources

- **Documentation**: [README.md](README.md)
- **Setup Guide**: [SETUP.md](SETUP.md)
- **Carver's Blog**: https://qoppac.blogspot.com
- **Book**: "Systematic Trading" by Robert Carver

---

**Ready to start?** Run: `python main.py`
