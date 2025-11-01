# Architecture Documentation

## System Overview

The Systematic Trading System is built on a **modular, layered architecture** following the principles of separation of concerns, single responsibility, and extensibility.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE LAYER                         │
│                          (main.py, scripts)                          │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                               │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────────────┐    │
│  │  Backtesting │  │  Performance  │  │  Strategy Execution  │    │
│  │    Engine    │  │   Analyzer    │  │     Orchestrator     │    │
│  └──────────────┘  └───────────────┘  └──────────────────────┘    │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        DOMAIN LAYER                                  │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────────────┐    │
│  │   Strategy   │  │     Risk      │  │   Data Management    │    │
│  │   Module     │  │  Management   │  │      Module          │    │
│  └──────────────┘  └───────────────┘  └──────────────────────┘    │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    INFRASTRUCTURE LAYER                              │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────────────┐    │
│  │    Config    │  │    Logging    │  │   Calculations       │    │
│  │   Settings   │  │    Utils      │  │      Utils           │    │
│  └──────────────┘  └───────────────┘  └──────────────────────┘    │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       DATA LAYER                                     │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────────────┐    │
│  │  Yahoo       │  │  CSV Storage  │  │   Cache/Logs         │    │
│  │  Finance API │  │  (Historical) │  │                      │    │
│  └──────────────┘  └───────────────┘  └──────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Architecture

### 1. Data Management Module (`data/`)

**Responsibility**: Handle all data acquisition, storage, and retrieval

```
┌─────────────────────────────────────────┐
│         DataManager                      │
├─────────────────────────────────────────┤
│ + download_stock_data()                 │
│ + download_multiple_stocks()            │
│ + save_data()                           │
│ + load_data()                           │
│ + get_close_prices()                    │
│ + get_stock_info()                      │
└───────────┬─────────────────────────────┘
            │
            ├─► Yahoo Finance API (yfinance)
            ├─► CSV Storage (data/historical/)
            └─► Pandas DataFrames
```

**Key Design Patterns**:
- **Repository Pattern**: Abstracts data storage/retrieval
- **Caching Strategy**: Local CSV files prevent redundant downloads
- **Error Handling**: Graceful fallback for failed downloads

**Data Flow**:
```
User Request → DataManager → Yahoo Finance → Raw Data
                    ↓
              Validation & Cleaning
                    ↓
              CSV Storage ← DataFrame
                    ↓
              Return to Caller
```

### 2. Strategy Module (`strategy/`)

**Responsibility**: Generate trading signals from market data

```
┌──────────────────────────────────────────────────────────┐
│              BaseStrategy (Abstract)                      │
├──────────────────────────────────────────────────────────┤
│ + generate_signals() [abstract]                          │
│ + validate_data()                                        │
│ + calculate_forecast_scalar()                            │
└───────────┬──────────────────────────────────────────────┘
            │
            ├─► MovingAverageCrossover
            │   ├─ Simple MA logic
            │   └─ Binary signals (-1, 0, 1)
            │
            ├─► EWMAC (Exponential Weighted MA)
            │   ├─ Exponential MAs
            │   ├─ Volatility normalization
            │   └─ Carver's forecast scaling
            │
            └─► MultipleEWMAC
                ├─ Combines multiple EWMAC rules
                └─ Equal-weighted averaging
```

**Key Design Patterns**:
- **Strategy Pattern**: Interchangeable trading algorithms
- **Template Method**: Base class defines structure
- **Factory Method**: Easy creation of strategy variations

**Signal Generation Pipeline**:
```
Price Data → Strategy.generate_signals()
                ↓
          Calculate Indicators
                ↓
          Generate Raw Signals
                ↓
          Normalize/Scale (Carver's method)
                ↓
          Return Forecast Series (-20 to +20)
```

### 3. Risk Management Module (`risk_management/`)

**Responsibility**: Determine position sizes based on risk parameters

```
┌──────────────────────────────────────────────────────────┐
│              PositionSizer                                │
├──────────────────────────────────────────────────────────┤
│ - capital: float                                         │
│ - volatility_target: float                               │
│ - max_position_size: float                               │
├──────────────────────────────────────────────────────────┤
│ + calculate_instrument_weight()                          │
│ + calculate_position_from_signal()                       │
│ + calculate_fixed_fractional()                           │
│ + calculate_portfolio_leverage()                         │
│ + adjust_for_costs()                                     │
└──────────────────────────────────────────────────────────┘
```

**Position Sizing Flow (Carver's Method)**:
```
Input: Price, Volatility, Forecast
    ↓
Calculate Volatility Scalar = target_vol / instrument_vol
    ↓
Apply Forecast Scalar = forecast / 10
    ↓
Calculate Notional Position = scalar × forecast_scalar × capital
    ↓
Convert to Shares = notional / price
    ↓
Apply Position Limits (max_position_size)
    ↓
Return: Number of Shares
```

**Key Principles**:
- **Inverse Volatility Weighting**: Higher vol → smaller position
- **Forecast Scaling**: Stronger signals → larger positions
- **Capital Constraints**: Never exceed max position size
- **Cost Awareness**: Avoid trades with excessive costs

### 4. Backtesting Module (`backtesting/`)

**Responsibility**: Simulate strategy performance on historical data

```
┌──────────────────────────────────────────────────────────┐
│           BacktestEngine                                  │
├──────────────────────────────────────────────────────────┤
│ + run(strategy, data, position_sizer)                    │
│ + run_multiple_assets(strategy, data_dict)               │
│ - _calculate_performance()                               │
└───────────┬──────────────────────────────────────────────┘
            │
            ▼
┌──────────────────────────────────────────────────────────┐
│         PerformanceAnalyzer                               │
├──────────────────────────────────────────────────────────┤
│ + print_summary()                                        │
│ + plot_equity_curve()                                    │
│ + plot_positions()                                       │
│ + generate_report()                                      │
└──────────────────────────────────────────────────────────┘
```

**Backtest Execution Flow**:
```
Input: Strategy + Historical Data + Position Sizer
    ↓
1. Generate Trading Signals
    ↓
2. Calculate Position Sizes (with vol targeting)
    ↓
3. Calculate Position Changes (trades)
    ↓
4. Apply Transaction Costs & Slippage
    ↓
5. Calculate Returns (positions × price changes)
    ↓
6. Build Equity Curve
    ↓
7. Calculate Performance Metrics
    ↓
Output: Results Dictionary
```

**Performance Metrics Calculated**:
- Total & Annualized Returns
- Sharpe Ratio
- Maximum Drawdown
- Total Trades & Costs
- Annualized Volatility

### 5. Configuration Module (`config/`)

**Responsibility**: Centralized configuration management

```
┌──────────────────────────────────────────────────────────┐
│              Settings (Singleton Pattern)                 │
├──────────────────────────────────────────────────────────┤
│ Configuration Categories:                                │
│ ├─ Data: dates, sources                                  │
│ ├─ Risk: capital, volatility target, limits              │
│ ├─ Strategy: MA periods, EWMAC spans                     │
│ ├─ Costs: transaction costs, slippage                    │
│ └─ Logging: levels, file paths                           │
├──────────────────────────────────────────────────────────┤
│ + get_data_path()                                        │
│ + get_log_path()                                         │
│ + validate()                                             │
└──────────────────────────────────────────────────────────┘
```

**Configuration Hierarchy**:
```
1. .env file (highest priority)
2. Environment variables
3. Default values in Settings class
```

### 6. Utils Module (`utils/`)

**Responsibility**: Shared utilities and helper functions

```
┌──────────────────────────┐    ┌────────────────────────┐
│      Logger              │    │   Calculations         │
├──────────────────────────┤    ├────────────────────────┤
│ + setup_logger()         │    │ + calculate_returns()  │
│ + get_logger()           │    │ + calculate_volatility()│
│ File + Console output    │    │ + calculate_sharpe()   │
│ Configurable levels      │    │ + calculate_max_dd()   │
└──────────────────────────┘    │ + exponential_weights()│
                                └────────────────────────┘
```

## Data Flow Architecture

### Complete Trading System Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. DATA ACQUISITION                                              │
│    User → DataManager → Yahoo Finance → CSV → DataFrame         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. SIGNAL GENERATION                                             │
│    DataFrame → Strategy.generate_signals() → Signal Series      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. POSITION SIZING                                               │
│    Signals + Volatility → PositionSizer → Position Sizes        │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. BACKTEST SIMULATION                                           │
│    Positions + Prices → BacktestEngine → Performance Results    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. PERFORMANCE ANALYSIS                                          │
│    Results → PerformanceAnalyzer → Metrics + Charts             │
└─────────────────────────────────────────────────────────────────┘
```

### Multi-Asset Portfolio Flow

```
Multiple Tickers
    ↓
┌───────────────────────────────────────┐
│ For Each Asset:                        │
│   ├─ Download Data                     │
│   ├─ Generate Signals                  │
│   ├─ Size Positions                    │
│   └─ Calculate Returns                 │
└───────────────┬───────────────────────┘
                ↓
        Combine Results
                ↓
    Portfolio Equity Curve
                ↓
    Portfolio Metrics
```

## Design Patterns Used

### 1. **Strategy Pattern** (Strategy Module)
- Allows interchangeable trading algorithms
- Common interface: `generate_signals()`
- Easy to add new strategies

### 2. **Template Method** (BaseStrategy)
- Defines algorithm structure
- Subclasses implement specific steps
- Ensures consistent signal generation

### 3. **Repository Pattern** (DataManager)
- Abstracts data storage/retrieval
- Decouples business logic from data access
- Enables easy switching of data sources

### 4. **Facade Pattern** (BacktestEngine)
- Simplifies complex backtesting process
- Single interface for multiple operations
- Hides complexity from user

### 5. **Singleton Pattern** (Settings)
- Single configuration instance
- Global access to settings
- Prevents configuration conflicts

### 6. **Factory Method** (Strategy Creation)
- Creates strategy instances
- Parameterized construction
- Enables strategy variations

## Class Diagram

```
┌──────────────────┐
│   BaseStrategy   │◄──────────────────┐
└────────┬─────────┘                   │
         │ inherits                    │
         ├──────────────┬──────────────┤
         ▼              ▼              ▼
┌──────────────┐  ┌─────────┐  ┌────────────────┐
│MovingAverage │  │  EWMAC  │  │ MultipleEWMAC  │
│  Crossover   │  │         │  │                │
└──────────────┘  └─────────┘  └────────────────┘

┌──────────────────┐        ┌──────────────────┐
│  DataManager     │◄───────│  Settings        │
└────────┬─────────┘  uses  └──────────────────┘
         │
         │ provides data
         ▼
┌──────────────────┐        ┌──────────────────┐
│ BacktestEngine   │◄───────│ PositionSizer    │
└────────┬─────────┘  uses  └──────────────────┘
         │
         │ generates
         ▼
┌──────────────────┐
│ PerformanceAnalyzer│
└──────────────────┘
```

## Module Dependencies

```
main.py
  ├─► data.DataManager
  ├─► strategy.EWMAC
  ├─► strategy.MovingAverageCrossover
  ├─► risk_management.PositionSizer
  ├─► backtesting.BacktestEngine
  ├─► backtesting.PerformanceAnalyzer
  ├─► config.Settings
  └─► utils.logger

backtesting.BacktestEngine
  ├─► strategy.BaseStrategy (interface)
  ├─► risk_management.PositionSizer
  ├─► config.Settings
  └─► utils.logger

strategy.* (all strategies)
  ├─► config.Settings
  └─► utils.logger

data.DataManager
  ├─► config.Settings
  └─► utils.logger

utils.calculations
  ├─► config.Settings
  └─► (no external dependencies)
```

## File System Architecture

```
systematic_trading/
│
├── config/                    # Configuration Layer
│   ├── __init__.py           # Exports Settings
│   └── settings.py           # Centralized config (env vars)
│
├── data/                      # Data Access Layer
│   ├── __init__.py           # Exports DataManager
│   ├── data_manager.py       # Data acquisition/storage
│   └── historical/           # CSV storage (gitignored)
│       ├── DBS_SI.csv
│       ├── O39_SI.csv
│       └── ES3_SI.csv
│
├── strategy/                  # Domain Layer - Strategies
│   ├── __init__.py           # Exports all strategies
│   ├── base_strategy.py      # Abstract base class
│   └── trend_following.py    # Trend strategies (EWMAC, MA)
│
├── risk_management/           # Domain Layer - Risk
│   ├── __init__.py           # Exports PositionSizer
│   └── position_sizer.py     # Carver's position sizing
│
├── backtesting/               # Application Layer
│   ├── __init__.py           # Exports Engine & Analyzer
│   ├── backtest_engine.py    # Backtest execution
│   └── performance.py        # Performance analysis
│
├── utils/                     # Infrastructure Layer
│   ├── __init__.py           # Exports utilities
│   ├── logger.py             # Logging setup
│   └── calculations.py       # Financial calculations
│
├── tests/                     # Test Layer
│   ├── __init__.py
│   ├── test_calculations.py
│   ├── test_strategy.py
│   └── test_position_sizer.py
│
├── logs/                      # Runtime artifacts (gitignored)
│   └── systematic_trading.log
│
├── main.py                    # Entry point / Demo
├── requirements.txt           # Dependencies
├── pytest.ini                # Test configuration
├── .env.example              # Config template
└── .gitignore                # Git ignore rules
```

## Extension Points

### Adding a New Strategy

```python
# 1. Create new strategy class
class MyStrategy(BaseStrategy):
    def generate_signals(self, data):
        # Implement your logic
        signals = ...
        return self.calculate_forecast_scalar(signals)

# 2. Register in strategy/__init__.py
from .my_strategy import MyStrategy
__all__ = ['BaseStrategy', 'EWMAC', 'MovingAverageCrossover', 'MyStrategy']

# 3. Use in backtest
strategy = MyStrategy(param1, param2)
results = engine.run(strategy, data)
```

### Adding a New Data Source

```python
# 1. Extend DataManager or create new manager
class AlternativeDataManager(DataManager):
    def download_from_alternative_source(self, ticker):
        # Custom implementation
        pass

# 2. Use same interface
manager = AlternativeDataManager()
data = manager.download_stock_data('DBS.SI')
```

### Adding Custom Performance Metrics

```python
# 1. Add to utils/calculations.py
def calculate_sortino_ratio(returns, target_return=0):
    # Implementation
    pass

# 2. Use in PerformanceAnalyzer
class PerformanceAnalyzer:
    def calculate_sortino(self):
        return calculate_sortino_ratio(self.results['returns'])
```

## Scalability Considerations

### Current Design
- **Single-threaded**: Sequential processing
- **In-memory**: All data loaded into RAM
- **Local storage**: CSV files on disk

### Future Scalability Options

1. **Parallel Processing**
   - Use `multiprocessing` for multiple stocks
   - Async data downloads with `asyncio`

2. **Database Integration**
   - Replace CSV with PostgreSQL/TimescaleDB
   - Better query performance for large datasets

3. **Distributed Computing**
   - Use Dask for large-scale backtests
   - Distribute across multiple nodes

4. **Caching Layer**
   - Redis for frequently accessed data
   - Memcached for computed indicators

## Security Considerations

1. **API Keys**: Store in `.env`, never commit
2. **Data Validation**: Validate all external data
3. **Input Sanitization**: Validate user inputs
4. **Error Handling**: Don't expose system details
5. **Logging**: Avoid logging sensitive data

## Performance Optimization Tips

1. **Data Caching**: Cache downloaded data to CSV
2. **Vectorization**: Use pandas/numpy operations
3. **Lazy Loading**: Load data only when needed
4. **Batch Processing**: Process multiple stocks together
5. **Pre-computation**: Calculate indicators once

---

This architecture supports Robert Carver's systematic trading principles while maintaining flexibility for extensions and modifications.
