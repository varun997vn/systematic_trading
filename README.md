# Systematic Trading System for US Markets

A Python-based systematic trading system for US equity markets, implementing principles from Robert Carver's "Systematic Trading: A Unique New Method for Designing Trading and Investing Systems".

## Overview

This project provides a complete framework for:
- Downloading and managing US stock data
- Implementing trend-following strategies (EWMAC, Moving Average Crossover)
- Backtesting with realistic cost modeling
- Position sizing using volatility targeting
- Performance analysis and reporting

## Key Features

### 1. **Robert Carver's Principles**
- **Volatility Targeting**: Positions scaled to achieve consistent risk exposure
- **Forecast Scaling**: Trading signals normalized to standard range (-20 to +20)
- **Cost Awareness**: Transaction costs and slippage built into backtests
- **Diversification**: Multi-timeframe and multi-asset approaches

### 2. **US Market Implementation**
- Yahoo Finance integration for US stocks
- Configurable for US market hours and trading costs
- Example stocks: GOOG, MSFT, TSLA

### 3. **Modular Architecture**
- Clean separation of concerns (data, strategy, risk, backtesting)
- Extensible base classes for custom strategies
- Comprehensive test suite

## Project Structure

```
systematic_trading/
├── config/                 # Configuration management
│   ├── __init__.py
│   └── settings.py         # Central config with environment variables
├── data/                   # Data management
│   ├── __init__.py
│   ├── data_manager.py     # Download and store market data
│   └── historical/         # Stored CSV files
├── strategy/               # Trading strategies
│   ├── __init__.py
│   ├── base_strategy.py    # Abstract base class
│   └── trend_following.py  # EWMAC, MA Crossover strategies
├── risk_management/        # Position sizing
│   ├── __init__.py
│   └── position_sizer.py   # Volatility-based position sizing
├── backtesting/            # Backtesting engine
│   ├── __init__.py
│   ├── backtest_engine.py  # Backtest execution
│   └── performance.py      # Performance analysis and plotting
├── utils/                  # Utilities
│   ├── __init__.py
│   ├── logger.py           # Logging configuration
│   └── calculations.py     # Financial calculations
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── test_calculations.py
│   ├── test_strategy.py
│   └── test_position_sizer.py
├── logs/                   # Application logs
├── main.py                 # Demo script
├── requirements.txt        # Python dependencies
├── .env.example            # Example configuration
├── .gitignore              # Git ignore rules
└── pytest.ini              # Pytest configuration
```

## Installation
## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup Steps

1. **Clone or navigate to the project directory**
   ```bash
   cd systematic_trading
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv

   # On Windows
   venv\Scripts\activate

   # On Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   uv pip install -e .
   ```

4. **Configure environment variables**
   ```bash
   # Copy the example config
   cp .env.example .env

   # Edit .env with your preferences (optional - defaults work fine)
   ```

## Quick Start

### Run the Demo

The demo script demonstrates all key features:

```bash
python main.py
```

This will:
1. Download historical data for GOOG, MSFT, and TSLA
2. Run backtests with EWMAC and MA Crossover strategies
3. Compare strategy performance
4. Generate performance charts (equity_curve.png, positions.png)
5. Display comprehensive performance metrics

### Expected Output

```
[STEP 1] Downloading historical data from Yahoo Finance...
 Successfully downloaded data for 3 stocks

[STEP 2] Running backtest on GOOG with EWMAC strategy...

[STEP 3] Analyzing performance...

============================================================
BACKTEST PERFORMANCE SUMMARY
============================================================

Period: 2018-01-01 to 2024-12-31
Initial Capital: $100,000.00
Final Equity: $XXX,XXX.XX

Total Return: XX.XX%
Annualized Return: XX.XX%
Annualized Volatility: XX.XX%
Sharpe Ratio: X.XX

Total Trades: XXX
Total Costs: $X,XXX.XX

Maximum Drawdown: -XX.XX%
============================================================
```

## Usage Guide

### 1. Download Stock Data

```python
from data.data_manager import DataManager

# Initialize data manager
dm = DataManager()

# Download single stock
data = dm.download_stock_data('GOOG', save=True)

# Download multiple stocks
stocks = ['GOOG', 'MSFT', 'TSLA', 'AAPL']
data_dict = dm.download_multiple_stocks(stocks, save=True)

# Load previously downloaded data
data = dm.load_data('GOOG')
```

### 2. Create and Test a Strategy

```python
from strategy.trend_following import EWMAC
from backtesting.backtest_engine import BacktestEngine
from risk_management.position_sizer import PositionSizer

# Create EWMAC strategy (Carver's preferred method)
strategy = EWMAC(fast_span=16, slow_span=64)

# Create position sizer with volatility targeting
position_sizer = PositionSizer(
    capital=100000,
    volatility_target=0.20  # 20% annual volatility target
)

# Create backtest engine
backtest = BacktestEngine(
    initial_capital=100000,
    transaction_cost=0.001,  # 0.1%
    slippage=0.0005  # 0.05%
)

# Run backtest
results = backtest.run(strategy, data, position_sizer)
```

### 3. Analyze Performance

```python
from backtesting.performance import PerformanceAnalyzer

# Create analyzer
analyzer = PerformanceAnalyzer(results)

# Print summary
analyzer.print_summary()

# Generate plots
analyzer.plot_equity_curve(show=True)
analyzer.plot_positions(show=True)

# Access raw metrics
print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
print(f"Total Return: {results['total_return']:.2%}")
```

### 4. Create Custom Strategies

```python
from strategy.base_strategy import BaseStrategy
import pandas as pd

class MyCustomStrategy(BaseStrategy):
    def __init__(self, parameter1, parameter2):
        super().__init__(name="MyCustomStrategy")
        self.parameter1 = parameter1
        self.parameter2 = parameter2

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        # Validate data
        if not self.validate_data(data):
            return pd.Series(index=data.index, dtype=float)

        # Your signal logic here
        signals = pd.Series(index=data.index, dtype=float)

        # ... calculate signals ...

        # Scale to Carver's forecast range
        scaled_signals = self.calculate_forecast_scalar(signals)

        return scaled_signals
```

## Running Tests

The project includes a comprehensive test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_strategy.py

# Run with verbose output
pytest -v
```

## Configuration

Edit `.env` to customize:

```bash
# Data Configuration
DATA_START_DATE=2018-01-01
DATA_END_DATE=2024-12-31

# Risk Management
INITIAL_CAPITAL=100000
MAX_POSITION_SIZE=0.10
VOLATILITY_TARGET=0.20
RISK_FREE_RATE=0.03

# Strategy Parameters
MA_FAST=16
MA_SLOW=64

# Trading Costs (adjust for US markets)
TRANSACTION_COST=0.001
SLIPPAGE=0.0005

# Stocks to trade
US_STOCKS=GOOG,MSFT,TSLA,AAPL,AMZN
```

## Key Concepts (Robert Carver's Approach)

### 1. Volatility Targeting
- Positions are sized to achieve consistent volatility exposure
- Higher volatility instruments get smaller positions
- Target: typically 15-25% annual volatility

### 2. Forecast Scaling
- Trading signals scaled to standard range (-20 to +20)
- Average absolute forecast = 10
- Allows combination of different trading rules

### 3. EWMAC (Exponentially Weighted Moving Average Crossover)
- Core trend-following rule
- Uses exponential moving averages (more responsive)
- Multiple timeframes for diversification (16/64, 32/128, 64/256)

### 4. Cost Awareness
- Transaction costs and slippage explicitly modeled
- Prevents over-trading
- Realistic performance expectations

### 5. Diversification
- Across instruments (multiple stocks)
- Across trading rules (different timeframes)
- Across strategies (trend, carry, mean-reversion)

## Extending the System

### Add More Strategies

Carver recommends combining:
- **Trend Following**: EWMAC (already implemented)
- **Carry**: Exploit risk premium (e.g., dividend yield)
- **Mean Reversion**: Short-term reversals

### Add More Assets

```python
# Add more US stocks to .env
US_STOCKS=GOOG,MSFT,TSLA,AAPL,AMZN,NVDA,META
```

### Implement Forecast Combination

Carver combines multiple forecasts with optimal weights:

```python
from strategy.trend_following import MultipleEWMAC

# Combine multiple EWMAC rules
strategy = MultipleEWMAC(
    rule_configs=[
        (16, 64),   # Fast
        (32, 128),  # Medium
        (64, 256),  # Slow
    ]
)
```

## Performance Tips

1. **Start Simple**: Begin with single-stock, single-strategy backtests
2. **Verify Costs**: Ensure transaction costs match your broker
3. **Use Volatility Targeting**: More robust than fixed position sizing
4. **Diversify**: Multiple assets and rules improve Sharpe ratio
5. **Monitor Turnover**: High turnover = high costs

## Common US Tech Stocks

| Ticker | Name | Sector |
|--------|------|--------|
| GOOG | Alphabet Inc. | Technology |
| MSFT | Microsoft Corporation | Technology |
| TSLA | Tesla Inc. | Automotive/Technology |
| AAPL | Apple Inc. | Technology |
| AMZN | Amazon.com Inc. | E-commerce/Technology |
| NVDA | NVIDIA Corporation | Technology |
| META | Meta Platforms Inc. | Technology |

## Troubleshooting

### Data Download Issues

If data download fails:
```python
# Check ticker format (use standard US ticker symbols)
ticker = 'GOOG'  # Correct
ticker = 'GOOGL' # Also valid (Class A shares)

# Check date ranges
DATA_START_DATE=2018-01-01  # Not too far back
```

### Import Errors

Ensure you're in the project root:
```bash
cd systematic_trading
python main.py
```

Or update PYTHONPATH:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

## Resources

### Robert Carver's Work
- **Book**: "Systematic Trading" (2015)
- **Blog**: [qoppac.blogspot.com](https://qoppac.blogspot.com)
- **GitHub**: [robcarver17/pysystemtrade](https://github.com/robcarver17/pysystemtrade)

### US Market Information
- **NYSE**: [www.nyse.com](https://www.nyse.com)
- **NASDAQ**: [www.nasdaq.com](https://www.nasdaq.com)
- **Yahoo Finance**: Use standard US ticker symbols

## License

This project is for educational purposes. Use at your own risk. Past performance does not guarantee future results.

## Contributing

To extend this system:
1. Follow the existing code structure
2. Add tests for new features
3. Update documentation
4. Ensure all tests pass (`pytest`)

## Next Steps

1. **Implement More Strategies**: Add carry and mean-reversion rules
2. **Optimize Parameters**: Use walk-forward analysis
3. **Portfolio Construction**: Implement instrument weighting (IDM)
4. **Risk Monitoring**: Add real-time risk dashboards
5. **Live Trading**: Add broker integration (paper trading first!)

---

**Disclaimer**: This is a research and educational tool. Not financial advice. Trading involves risk of loss.
