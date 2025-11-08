# Systematic Trading System - Notebooks

This directory contains Jupyter notebooks demonstrating the complete systematic trading workflow.

## 📚 Notebook Overview

### 🎯 Main Workflow
- **[00_complete_trading_workflow.ipynb](00_complete_trading_workflow.ipynb)** - **START HERE**
  - Complete end-to-end demonstration of the entire trading system
  - Covers all 8 components: strategy development, data management, backtesting, risk management, execution, monitoring, compliance, and continuous improvement
  - Best for understanding the complete system

### 📈 Strategy-Specific Notebooks
- **01_trend_following_strategies.ipynb** - EWMAC and moving average crossover strategies
- **02_mean_reversion_strategies.ipynb** - Bollinger Bands, RSI, and Z-Score strategies
- **03_momentum_strategies.ipynb** - Rate of Change, MACD, and Dual Momentum
- **04_breakout_strategies.ipynb** - Donchian, Volatility, and Range breakouts
- **05_carry_strategies.ipynb** - Dividend yield and value-based strategies

### 🔬 Advanced Topics
- **06_portfolio_optimization.ipynb** - Risk parity, minimum variance, and maximum Sharpe
- **07_risk_management.ipynb** - Drawdown analysis, position sizing, and risk controls
- **08_execution_simulation.ipynb** - Realistic trading costs, slippage, and market impact
- **09_strategy_optimization.ipynb** - Parameter optimization and walk-forward analysis

## 🚀 Getting Started

### Prerequisites
```bash
# Install dependencies
uv pip install -e ../.

# Activate virtual environment (if using)
source ../venv/bin/activate  # Linux/Mac
# or
../venv/Scripts/activate  # Windows
```

### Running Notebooks

1. **Start Jupyter**:
   ```bash
   cd notebooks
   jupyter notebook
   ```

2. **Open any notebook** and run cells sequentially

3. **Start with** `00_complete_trading_workflow.ipynb` for the full overview

## 📊 What You'll Learn

### 1. Strategy Development
- Implement trend-following, mean-reversion, momentum, and breakout strategies
- Generate continuous trading signals (Carver's approach)
- Combine multiple strategies for diversification

### 2. Data Management
- Download historical stock data from Yahoo Finance
- Handle data cleaning and validation
- Store and retrieve historical data

### 3. Backtesting
- Test strategies on historical data
- Account for transaction costs and slippage
- Calculate realistic performance metrics

### 4. Risk Management
- Implement volatility targeting (Carver's method)
- Portfolio optimization techniques
- Drawdown monitoring and controls
- Position sizing algorithms

### 5. Execution
- Simulate realistic trade execution
- Model commissions, slippage, and market impact
- Order management and fill simulation

### 6. Performance Monitoring
- Calculate comprehensive performance metrics
- Visualize equity curves and returns
- Rolling performance analysis
- Risk-adjusted return metrics

### 7. Compliance
- Monitor risk limits
- Automatic position scaling
- Trading alerts and notifications

### 8. Continuous Improvement
- Parameter optimization
- Walk-forward analysis
- Strategy performance tracking

## 📁 Output Files

Notebooks save results to `../data/`:
- `strategy_comparison.csv` - Performance comparison of all strategies
- `portfolio_asset_performance.csv` - Multi-asset portfolio results
- `execution_equity_curve.csv` - Equity curve from execution simulation
- Generated charts and visualizations

## 🎓 Learning Path

**Beginner**: Start with these in order
1. `00_complete_trading_workflow.ipynb` - Overview
2. `01_trend_following_strategies.ipynb` - Simplest strategies
3. `06_portfolio_optimization.ipynb` - Portfolio concepts

**Intermediate**: Deep dive into strategies
1. `02_mean_reversion_strategies.ipynb`
2. `03_momentum_strategies.ipynb`
3. `04_breakout_strategies.ipynb`
4. `07_risk_management.ipynb`

**Advanced**: Optimization and execution
1. `08_execution_simulation.ipynb`
2. `09_strategy_optimization.ipynb`
3. Combine everything in custom workflows

## 💡 Tips

- **Run cells sequentially** - Each cell builds on previous ones
- **Modify parameters** - Experiment with strategy parameters
- **Try different stocks** - Change the ticker list
- **Compare strategies** - Run multiple strategies on the same data
- **Save your work** - Notebooks auto-save, but export important results

## 🔧 Troubleshooting

### Data Download Issues
```python
# If Yahoo Finance fails, try:
import yfinance as yf
yf.pdr_override()

# Or use alternative tickers
tickers = ['AAPL', 'MSFT', 'GOOGL']  # More reliable
```

### Import Errors
```bash
# Ensure you're in the right directory
cd /path/to/systematic_trading
uv pip install -e .
```

### Memory Issues
```python
# For large datasets, limit date range
start_date = '2022-01-01'  # Shorter period
end_date = '2024-12-31'
```

## 📖 References

Based on **Robert Carver's "Systematic Trading"** principles:
- Trend following as core strategy
- Volatility targeting for consistent risk
- Multiple timeframes for diversification
- Cost-aware trading
- Systematic approach removes emotion

## 🤝 Contributing

To add new notebooks:
1. Follow the naming convention: `NN_descriptive_name.ipynb`
2. Include markdown cells with clear explanations
3. Add to this README with description
4. Test all cells run without errors

## 📧 Support

For issues or questions:
1. Check the main [README.md](../README.md)
2. Review [DEVELOPERS_GUIDE.md](../DEVELOPERS_GUIDE.md)
3. See [ARCHITECTURE.md](../ARCHITECTURE.md) for system design

---

**Happy Trading! 📈**

Remember: Past performance does not guarantee future results. This system is for educational and research purposes.
