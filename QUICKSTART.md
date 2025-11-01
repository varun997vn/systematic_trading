# Quick Start Guide - Systematic Trading System

## 🚀 Get Started in 5 Minutes

### Step 1: Verify Installation

```bash
cd /home/varuvenk/systematic_trading
./venv/bin/python test_new_features.py
```

You should see:
```
✅ ALL TESTS PASSED!
📊 System Summary:
  - 18 trading strategies available
  - 5 portfolio optimization methods
  - Complete execution simulation
  ...
```

### Step 2: Launch Jupyter Notebook

```bash
./venv/bin/jupyter notebook notebooks/
```

This will open your browser with the notebooks directory.

### Step 3: Open the Main Workflow Notebook

Click on `00_complete_trading_workflow.ipynb`

### Step 4: Run All Cells

In Jupyter, select:
- **Cell → Run All**

Or press **Shift+Enter** on each cell sequentially.

### Step 5: Explore Results

The notebook will:
1. Download stock data for AAPL, MSFT, GOOGL, TSLA, NVDA, META
2. Test 8 different trading strategies
3. Compare their performance
4. Optimize a portfolio
5. Simulate realistic execution
6. Generate performance reports and visualizations

## 📊 Expected Output

You'll see:
- ✅ Strategy performance comparison table
- 📈 Equity curve charts
- 📉 Drawdown analysis
- 💰 Trading cost breakdown
- 🎯 Portfolio optimization results
- 📊 Performance metrics dashboard

## 🎯 Quick Command Reference

### Run the Main Demo
```bash
./venv/bin/python main.py
```

### Test New Features
```bash
./venv/bin/python test_new_features.py
```

### Start Jupyter
```bash
./venv/bin/jupyter notebook notebooks/
```

### Run Specific Strategy
```python
from data.data_manager import DataManager
from strategy import EWMAC
from backtesting.backtest_engine import BacktestEngine
from risk_management.position_sizer import PositionSizer

# Get data
dm = DataManager()
data = dm.download_stock('AAPL', start_date='2020-01-01')

# Create strategy
strategy = EWMAC(fast_span=16, slow_span=64)

# Backtest
engine = BacktestEngine(initial_capital=100000)
sizer = PositionSizer(capital=100000)
results = engine.run(strategy, data, sizer)

print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
print(f"Total Return: {results['total_return']:.2%}")
```

## 📚 Available Strategies

### Trend Following (3)
- `EWMAC` - Exponentially Weighted Moving Average Crossover
- `MovingAverageCrossover` - Simple MA crossover
- `MultipleEWMAC` - Combined EWMAC rules

### Mean Reversion (3)
- `BollingerBands` - Bollinger Bands strategy
- `RSIMeanReversion` - RSI-based mean reversion
- `ZScoreMeanReversion` - Z-score based strategy

### Momentum (4)
- `RateOfChange` - Price momentum
- `RelativeStrength` - Comparative momentum
- `DualMomentum` - Multi-timeframe momentum
- `MACD` - Moving Average Convergence Divergence

### Breakout (4)
- `DonchianBreakout` - Channel breakout
- `VolatilityBreakout` - Vol-adjusted breakout
- `SupportResistanceBreakout` - S/R levels
- `RangeBreakout` - Trading range breakout

### Carry/Value (4)
- `DividendYieldCarry` - Dividend-based
- `ValueStrategy` - Value-based signals
- `YieldCurveCarry` - Curve slope signals
- `SeasonalityCarry` - Seasonal patterns

## 🔧 Common Tasks

### Add a New Stock
```python
tickers = ['AAPL', 'MSFT', 'YOUR_STOCK']
stock_data = data_manager.download_multiple_stocks(
    tickers=tickers,
    start_date='2020-01-01'
)
```

### Test Multiple Strategies
```python
from strategy import EWMAC, BollingerBands, MACD

strategies = {
    'EWMAC': EWMAC(16, 64),
    'Bollinger': BollingerBands(20, 2.0),
    'MACD': MACD(12, 26, 9)
}

results = {}
for name, strategy in strategies.items():
    results[name] = engine.run(strategy, data, sizer)
```

### Optimize Portfolio
```python
from risk_management.portfolio_optimizer import PortfolioOptimizer

optimizer = PortfolioOptimizer()
weights = optimizer.optimize_portfolio(
    returns_df,
    method='risk_parity'  # or 'min_variance', 'max_sharpe'
)
print(weights)
```

### Simulate Execution
```python
from execution.mock_broker import MockBroker
from execution.execution_engine import ExecutionEngine

broker = MockBroker(initial_capital=100000)
exec_engine = ExecutionEngine(broker, sizer)

results = exec_engine.run_backtest(strategy, data_dict)
print(f"Total costs: ${results['trade_statistics']['total_costs']:.2f}")
```

## 📖 Next Steps

1. **Read the Documentation**
   - [README.md](README.md) - Project overview
   - [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - What was built
   - [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
   - [DEVELOPERS_GUIDE.md](DEVELOPERS_GUIDE.md) - Development guide

2. **Explore Notebooks**
   - Start with [00_complete_trading_workflow.ipynb](notebooks/00_complete_trading_workflow.ipynb)
   - See [notebooks/README.md](notebooks/README.md) for all notebooks

3. **Experiment**
   - Try different strategies
   - Test on different stocks
   - Adjust parameters
   - Combine strategies

4. **Build Your Own**
   - Create custom strategies
   - Add new indicators
   - Implement your ideas

## 💡 Pro Tips

- **Start Simple**: Begin with trend following (EWMAC) before complex strategies
- **Understand Costs**: Transaction costs matter! Always include realistic costs
- **Diversify**: Use multiple strategies and instruments
- **Monitor Risk**: Check drawdowns and use stop-loss rules
- **Paper Trade First**: Test everything before risking real capital
- **Keep Learning**: Read Carver's "Systematic Trading" book

## ⚠️ Important Reminders

1. **This is for Education**: Not financial advice
2. **Past Performance**: Doesn't guarantee future results
3. **Risk Warning**: Trading involves substantial risk
4. **Test Thoroughly**: Paper trade before going live
5. **Understand Limits**: Backtesting has limitations

## 🤝 Need Help?

- Check [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) for feature list
- Review [notebooks/README.md](notebooks/README.md) for learning path
- Run `./venv/bin/python test_new_features.py` to verify setup
- Examine example code in notebooks

## 🎉 You're Ready!

Run this to get started:
```bash
./venv/bin/jupyter notebook notebooks/00_complete_trading_workflow.ipynb
```

**Happy Systematic Trading! 📈**
