# Setup Guide - Systematic Trading System

## Quick Start (5 Minutes)

Follow these steps to get the system running:

### Step 1: Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### Step 2: Configure Environment (Optional)

```bash
# Copy example config (optional - system works with defaults)
cp .env.example .env

# Edit .env if you want to customize settings
# nano .env  # or use your preferred editor
```

### Step 3: Run the Demo

```bash
# Run the demonstration script
python main.py
```

This will:
- Download historical data for DBS.SI, O39.SI, and ES3.SI
- Run multiple backtests with different strategies
- Generate performance charts
- Display comprehensive performance metrics

Expected runtime: 2-5 minutes (depending on internet speed for data download)

### Step 4: Run Tests (Optional)

```bash
# Verify everything is working correctly
pytest

# For detailed test output:
pytest -v
```

## What You Should See

### Successful Output Example:

```
============================================================
SYSTEMATIC TRADING SYSTEM - SGX DEMO
Based on Robert Carver's 'Systematic Trading'
============================================================

Testing with SGX stocks: ['DBS.SI', 'O39.SI', 'ES3.SI']

[STEP 1] Downloading historical data from Yahoo Finance...
Downloading DBS.SI from 2018-01-01 to 2024-12-31
Downloaded 1234 rows for DBS.SI
✓ Successfully downloaded data for 3 stocks

[STEP 2] Running backtest on DBS.SI with EWMAC strategy...

[STEP 3] Analyzing performance...

============================================================
BACKTEST PERFORMANCE SUMMARY
============================================================

Period: 2018-01-01 to 2024-12-31
Initial Capital: $100,000.00
Final Equity: $XXX,XXX.XX

Total Return: XX.XX%
Annualized Return: XX.XX%
Sharpe Ratio: X.XX
...
```

## Project Files Created

After running the demo, you'll see these new files:

```
systematic_trading/
├── data/historical/          # Downloaded stock data
│   ├── DBS_SI.csv
│   ├── O39_SI.csv
│   └── ES3_SI.csv
├── logs/                     # Log files
│   └── systematic_trading.log
├── equity_curve.png         # Performance chart
└── positions.png            # Position sizing chart
```

## Verification Checklist

- [ ] Python 3.8+ installed (`python --version`)
- [ ] Virtual environment created and activated
- [ ] All dependencies installed (`pip list`)
- [ ] Demo runs without errors (`python main.py`)
- [ ] Tests pass (`pytest`)
- [ ] Charts generated (equity_curve.png, positions.png)
- [ ] Data downloaded to data/historical/

## Common Issues and Solutions

### Issue 1: "ModuleNotFoundError"

**Solution**: Make sure you're in the project directory and virtual environment is activated

```bash
cd systematic_trading
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Issue 2: "No data retrieved for ticker"

**Possible causes**:
- No internet connection
- Yahoo Finance API temporary issue
- Invalid ticker format

**Solution**:
- Check internet connection
- Verify tickers have .SI suffix (e.g., DBS.SI not DBS)
- Try again later if Yahoo Finance is down

### Issue 3: "Import Error" when running main.py

**Solution**: Run from the project root directory

```bash
# Ensure you're in the right directory
cd /path/to/systematic_trading
python main.py
```

### Issue 4: Matplotlib/Plotting Errors

**Solution**: If running on a headless server or WSL without display:

```python
# The demo automatically saves plots to files
# Charts are saved as equity_curve.png and positions.png
# You don't need a display to run the demo
```

## Next Steps After Setup

### 1. Experiment with Parameters

Edit `.env` to try different settings:

```bash
# Try different volatility targets
VOLATILITY_TARGET=0.15  # More conservative (15%)
VOLATILITY_TARGET=0.25  # More aggressive (25%)

# Try different moving average periods
MA_FAST=32
MA_SLOW=128
```

### 2. Add More Stocks

```bash
# Edit .env
SGX_STOCKS=DBS.SI,O39.SI,ES3.SI,D05.SI,C6L.SI,U11.SI,Z74.SI
```

### 3. Create Custom Strategies

See `strategy/trend_following.py` for examples, then create your own:

```python
from strategy.base_strategy import BaseStrategy

class MyStrategy(BaseStrategy):
    def generate_signals(self, data):
        # Your strategy logic here
        pass
```

### 4. Analyze Individual Stocks

```python
from data.data_manager import DataManager
from strategy.trend_following import EWMAC
from backtesting.backtest_engine import BacktestEngine

# Download data
dm = DataManager()
data = dm.download_stock_data('D05.SI')

# Run backtest
strategy = EWMAC(16, 64)
engine = BacktestEngine()
results = engine.run(strategy, data)

# Analyze
from backtesting.performance import PerformanceAnalyzer
PerformanceAnalyzer(results).print_summary()
```

## Performance Optimization

### For Faster Downloads

```python
# Download data once, then load from disk
dm = DataManager()
dm.download_multiple_stocks(['DBS.SI', 'O39.SI'], save=True)

# Later, just load from disk (much faster)
data = dm.load_data('DBS.SI')
```

### For Multiple Backtests

```python
# Reuse position sizer and backtest engine
sizer = PositionSizer(capital=100000)
engine = BacktestEngine(initial_capital=100000)

# Run multiple strategies
for strategy in strategies:
    results = engine.run(strategy, data, sizer)
```

## Understanding the Output

### Key Metrics Explained

- **Total Return**: Cumulative return over the entire period
- **Annualized Return**: Return expressed as annual rate
- **Annualized Volatility**: Standard deviation of returns (annualized)
- **Sharpe Ratio**: Risk-adjusted return (higher is better, >1 is good, >2 is excellent)
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Total Trades**: Number of position changes
- **Total Costs**: Transaction costs and slippage

### Interpreting Results

**Good signs**:
- Positive Sharpe ratio (>1 is good)
- Smooth equity curve
- Reasonable number of trades (not too many = high costs)
- Drawdowns recover

**Warning signs**:
- Negative Sharpe ratio
- Very high number of trades (over-trading)
- Drawdowns that don't recover
- Equity curve that's very erratic

## Resources

### Documentation
- [README.md](README.md) - Full documentation
- Robert Carver's blog: https://qoppac.blogspot.com

### Code Examples
- [main.py](main.py) - Complete working example
- [tests/](tests/) - Unit tests with usage examples

### Getting Help
- Check logs in `logs/systematic_trading.log`
- Run tests: `pytest -v`
- Review error messages carefully

## Development Workflow

### Making Changes

1. Make your changes to the code
2. Run tests: `pytest`
3. Test manually: `python main.py`
4. Check logs if something fails

### Adding New Features

1. Create new module in appropriate directory
2. Add tests in `tests/`
3. Update documentation
4. Run full test suite

### Best Practices

- Always test on historical data first
- Start with small position sizes
- Understand transaction costs for your broker
- Diversify across multiple stocks
- Monitor performance regularly

---

**You're all set!** Run `python main.py` to start trading system development.
