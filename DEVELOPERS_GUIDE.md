# Developer's Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Environment Setup](#development-environment-setup)
3. [Code Organization](#code-organization)
4. [Development Workflow](#development-workflow)
5. [Testing Guidelines](#testing-guidelines)
6. [Adding New Features](#adding-new-features)
7. [Best Practices](#best-practices)
8. [Common Patterns](#common-patterns)
9. [Debugging](#debugging)
10. [Performance Optimization](#performance-optimization)
11. [Contributing Guidelines](#contributing-guidelines)

---

## Getting Started

### Prerequisites

```bash
# Required
- Python 3.8+
- pip
- git (optional)

# Recommended
- Virtual environment (venv or conda)
- IDE with Python support (VS Code, PyCharm)
- Basic understanding of pandas and numpy
```

### Initial Setup

```bash
# Clone/navigate to project
cd systematic_trading

# Create virtual environment
python -m venv venv

# Activate (choose your platform)
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install black flake8 mypy ipython jupyter

# Verify installation
pytest
python main.py
```

---

## Development Environment Setup

### Recommended IDE Configuration

#### VS Code Settings (`.vscode/settings.json`)

```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "editor.formatOnSave": true,
  "editor.rulers": [88],
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true
  }
}
```

#### PyCharm Configuration

1. Enable pytest: Settings → Tools → Python Integrated Tools → Testing → pytest
2. Set line length: Settings → Editor → Code Style → Python → Hard wrap at 88
3. Enable type checking: Settings → Editor → Inspections → Python → Type checker

### Environment Variables

Create `.env` from `.env.example`:

```bash
cp .env.example .env
# Edit .env with your settings
```

### Git Configuration (Optional)

```bash
git init
git add .
git commit -m "Initial commit"
```

---

## Code Organization

### Module Structure

```
systematic_trading/
├── config/              # Configuration (read-only for most modules)
├── data/               # Data layer (external dependencies)
├── strategy/           # Business logic (core domain)
├── risk_management/    # Business logic (position sizing)
├── backtesting/        # Application layer (orchestration)
├── utils/              # Infrastructure (cross-cutting concerns)
└── tests/              # Test suite (mirrors main structure)
```

### Import Conventions

```python
# Standard library imports first
import os
from pathlib import Path
from typing import List, Dict, Optional

# Third-party imports second
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Local imports last
from config.settings import Settings
from utils.logger import setup_logger
from strategy.base_strategy import BaseStrategy
```

### Naming Conventions

```python
# Classes: PascalCase
class TrendFollowingStrategy:
    pass

# Functions/Methods: snake_case
def calculate_moving_average():
    pass

# Constants: UPPER_SNAKE_CASE
MAX_POSITION_SIZE = 0.10

# Private methods/attributes: _leading_underscore
def _internal_helper():
    pass

# Module-level "private": _leading_underscore
_cache = {}
```

---

## Development Workflow

### Feature Development Cycle

```bash
# 1. Create feature branch (if using git)
git checkout -b feature/my-new-feature

# 2. Write failing tests first (TDD)
# Edit tests/test_my_feature.py
pytest tests/test_my_feature.py  # Should fail

# 3. Implement feature
# Edit appropriate module files

# 4. Run tests until they pass
pytest tests/test_my_feature.py

# 5. Run full test suite
pytest

# 6. Format code
black .

# 7. Check linting
flake8 .

# 8. Commit changes
git add .
git commit -m "Add: my new feature"
```

### Daily Development Tasks

```bash
# Morning: Update dependencies
pip install -r requirements.txt --upgrade

# During development: Run specific tests
pytest tests/test_strategy.py -v

# Before commit: Full verification
pytest && black . && flake8 .

# End of day: Clean up
find . -type d -name __pycache__ -exec rm -rf {} +
```

---

## Testing Guidelines

### Test Structure

Follow AAA pattern (Arrange, Act, Assert):

```python
def test_calculate_position_size():
    # Arrange
    sizer = PositionSizer(capital=100000, volatility_target=0.20)
    price = 100.0
    volatility = 0.25
    forecast = 10.0

    # Act
    position = sizer.calculate_instrument_weight(price, volatility, forecast)

    # Assert
    assert position > 0
    assert position < (100000 / price)  # Can't exceed all capital
```

### Test Coverage Goals

- **Unit tests**: 80%+ coverage for core logic
- **Integration tests**: Key workflows (data → strategy → backtest)
- **Edge cases**: Empty data, invalid inputs, boundary conditions

### Writing Good Tests

```python
# Good: Descriptive name, clear assertion
def test_ewmac_generates_signals_within_valid_range():
    strategy = EWMAC(16, 64)
    data = create_sample_data()
    signals = strategy.generate_signals(data)

    assert signals.max() <= 20
    assert signals.min() >= -20

# Bad: Vague name, unclear purpose
def test_strategy():
    s = EWMAC(16, 64)
    d = get_data()
    result = s.generate_signals(d)
    assert result is not None
```

### Test Fixtures

```python
import pytest
import pandas as pd
import numpy as np

@pytest.fixture
def sample_price_data():
    """Create realistic price data for testing."""
    dates = pd.date_range('2020-01-01', periods=252, freq='D')
    prices = 100 * (1 + np.random.randn(252).cumsum() * 0.01)

    return pd.DataFrame({
        'Open': prices * 0.99,
        'High': prices * 1.01,
        'Low': prices * 0.98,
        'Close': prices,
        'Volume': np.random.randint(1000000, 5000000, 252)
    }, index=dates)

def test_strategy_with_realistic_data(sample_price_data):
    strategy = EWMAC(16, 64)
    signals = strategy.generate_signals(sample_price_data)
    assert len(signals) == len(sample_price_data)
```

### Running Tests

```bash
# All tests
pytest

# Specific file
pytest tests/test_strategy.py

# Specific test
pytest tests/test_strategy.py::test_ewmac_signals

# With coverage
pytest --cov=. --cov-report=html

# Verbose output
pytest -v

# Stop on first failure
pytest -x

# Run only failed tests from last run
pytest --lf
```

---

## Adding New Features

### Adding a New Strategy

**Step 1: Create strategy class**

```python
# strategy/my_strategy.py
from strategy.base_strategy import BaseStrategy
import pandas as pd
import numpy as np

class BollingerBandStrategy(BaseStrategy):
    """
    Bollinger Band mean reversion strategy.

    Carver's principles:
    - Returns continuous forecasts (-20 to +20)
    - Normalized by volatility
    - Can be combined with other strategies
    """

    def __init__(self, window: int = 20, num_std: float = 2.0, name: str = "BollingerBand"):
        super().__init__(name)
        self.window = window
        self.num_std = num_std

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate mean reversion signals based on Bollinger Bands.

        Args:
            data: DataFrame with 'Close' prices

        Returns:
            Series of forecasts (-20 to +20)
        """
        if not self.validate_data(data):
            return pd.Series(index=data.index, dtype=float)

        prices = data['Close']

        # Calculate Bollinger Bands
        sma = prices.rolling(window=self.window).mean()
        std = prices.rolling(window=self.window).std()

        upper_band = sma + (std * self.num_std)
        lower_band = sma - (std * self.num_std)

        # Generate raw signals (mean reversion)
        # Negative when price is high (sell)
        # Positive when price is low (buy)
        raw_signals = pd.Series(index=data.index, dtype=float)
        raw_signals = (sma - prices) / std  # Normalized by volatility

        # Scale to Carver's forecast range
        scaled_signals = self.calculate_forecast_scalar(raw_signals)

        return scaled_signals
```

**Step 2: Add tests**

```python
# tests/test_my_strategy.py
import pytest
import pandas as pd
import numpy as np
from strategy.my_strategy import BollingerBandStrategy

class TestBollingerBandStrategy:
    @pytest.fixture
    def sample_data(self):
        dates = pd.date_range('2020-01-01', periods=100, freq='D')
        prices = 100 + np.random.randn(100).cumsum()
        return pd.DataFrame({'Close': prices}, index=dates)

    def test_initialization(self):
        strategy = BollingerBandStrategy(window=20, num_std=2.0)
        assert strategy.window == 20
        assert strategy.num_std == 2.0

    def test_generates_valid_signals(self, sample_data):
        strategy = BollingerBandStrategy()
        signals = strategy.generate_signals(sample_data)

        assert len(signals) == len(sample_data)
        assert signals.max() <= 20
        assert signals.min() >= -20

    def test_handles_empty_data(self):
        strategy = BollingerBandStrategy()
        empty_data = pd.DataFrame()
        signals = strategy.generate_signals(empty_data)

        assert len(signals) == 0
```

**Step 3: Register strategy**

```python
# strategy/__init__.py
from .base_strategy import BaseStrategy
from .trend_following import MovingAverageCrossover, EWMAC
from .my_strategy import BollingerBandStrategy

__all__ = [
    'BaseStrategy',
    'MovingAverageCrossover',
    'EWMAC',
    'BollingerBandStrategy',
]
```

**Step 4: Use in backtest**

```python
# Example usage
from strategy.my_strategy import BollingerBandStrategy
from backtesting.backtest_engine import BacktestEngine

strategy = BollingerBandStrategy(window=20, num_std=2.0)
engine = BacktestEngine()
results = engine.run(strategy, data)
```

### Adding a New Data Source

```python
# data/alternative_source.py
from data.data_manager import DataManager
import pandas as pd

class AlphaVantageDataManager(DataManager):
    """Data manager for Alpha Vantage API."""

    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key

    def download_stock_data(self, ticker: str, **kwargs) -> pd.DataFrame:
        """Download from Alpha Vantage instead of Yahoo Finance."""
        # Implementation here
        pass
```

### Adding Custom Performance Metrics

```python
# utils/calculations.py

def calculate_sortino_ratio(
    returns: pd.Series,
    target_return: float = 0.0,
    annualize: bool = True
) -> float:
    """
    Calculate Sortino ratio (downside deviation version of Sharpe).

    Args:
        returns: Returns series
        target_return: Minimum acceptable return
        annualize: If True, annualize the ratio

    Returns:
        Sortino ratio
    """
    from config.settings import Settings

    excess_returns = returns - target_return
    downside_returns = excess_returns[excess_returns < 0]

    if len(downside_returns) == 0:
        return float('inf')

    downside_std = downside_returns.std()

    if downside_std == 0:
        return 0.0

    sortino = excess_returns.mean() / downside_std

    if annualize:
        sortino = sortino * np.sqrt(Settings.BUSINESS_DAYS_PER_YEAR)

    return sortino

# Then use in PerformanceAnalyzer
# backtesting/performance.py
from utils.calculations import calculate_sortino_ratio

class PerformanceAnalyzer:
    def calculate_sortino(self) -> float:
        """Calculate Sortino ratio for the backtest."""
        return calculate_sortino_ratio(self.results['returns'])
```

---

## Best Practices

### 1. Logging

```python
# Good: Use logger, not print
from utils.logger import setup_logger

logger = setup_logger(__name__)

def my_function():
    logger.info("Starting process")
    try:
        # Do work
        logger.debug("Intermediate result: {result}")
    except Exception as e:
        logger.error(f"Error occurred: {e}", exc_info=True)

# Bad: Using print statements
def my_function():
    print("Starting process")  # Don't do this
```

### 2. Error Handling

```python
# Good: Specific exception handling
def load_data(ticker: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(f"data/{ticker}.csv")
        return df
    except FileNotFoundError:
        logger.warning(f"File not found for {ticker}, downloading...")
        return download_data(ticker)
    except pd.errors.EmptyDataError:
        logger.error(f"Empty data file for {ticker}")
        return pd.DataFrame()

# Bad: Catching all exceptions
def load_data(ticker):
    try:
        return pd.read_csv(f"data/{ticker}.csv")
    except:  # Too broad
        return None  # Unclear what happened
```

### 3. Type Hints

```python
# Good: Clear type hints
def calculate_position(
    price: float,
    volatility: float,
    forecast: float
) -> float:
    """Calculate position size."""
    return price * volatility * forecast

# Better: Use typing module for complex types
from typing import List, Dict, Optional

def get_portfolio_data(
    tickers: List[str],
    start_date: Optional[str] = None
) -> Dict[str, pd.DataFrame]:
    """Download data for multiple tickers."""
    pass
```

### 4. Documentation

```python
# Good: Comprehensive docstring
def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.03,
    annualize: bool = True
) -> float:
    """
    Calculate Sharpe ratio for a returns series.

    The Sharpe ratio measures risk-adjusted returns. Higher is better.
    Carver considers > 0.5 acceptable, > 1.0 excellent.

    Args:
        returns: Series of periodic returns
        risk_free_rate: Annual risk-free rate (default: 3%)
        annualize: If True, annualize the result (default: True)

    Returns:
        Sharpe ratio (annualized if annualize=True)

    Examples:
        >>> returns = pd.Series([0.01, -0.02, 0.03, 0.01])
        >>> sharpe = calculate_sharpe_ratio(returns)
        >>> print(f"Sharpe: {sharpe:.2f}")

    References:
        - Carver, R. "Systematic Trading" (2015), Chapter 3
    """
    pass
```

### 5. Configuration Management

```python
# Good: Use Settings class
from config.settings import Settings

def my_function():
    capital = Settings.INITIAL_CAPITAL
    vol_target = Settings.VOLATILITY_TARGET

# Bad: Hardcoded values
def my_function():
    capital = 100000  # What if this changes?
    vol_target = 0.20  # Hard to modify
```

### 6. Data Validation

```python
# Good: Validate inputs
def calculate_position(price: float, volatility: float) -> float:
    if price <= 0:
        raise ValueError(f"Price must be positive, got {price}")
    if volatility < 0:
        raise ValueError(f"Volatility cannot be negative, got {volatility}")

    # Calculate position
    return price / volatility

# Also good: Return safe default
def calculate_position(price: float, volatility: float) -> float:
    if price <= 0 or volatility <= 0:
        logger.warning(f"Invalid inputs: price={price}, vol={volatility}")
        return 0.0

    return price / volatility
```

---

## Common Patterns

### 1. Strategy Pattern

```python
# Define interface
class BaseStrategy(ABC):
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        pass

# Implement variations
class TrendStrategy(BaseStrategy):
    def generate_signals(self, data):
        # Trend logic
        pass

class MeanReversionStrategy(BaseStrategy):
    def generate_signals(self, data):
        # Mean reversion logic
        pass

# Use interchangeably
def backtest_strategy(strategy: BaseStrategy, data: pd.DataFrame):
    signals = strategy.generate_signals(data)
    # Rest of backtest logic
```

### 2. Factory Pattern

```python
class StrategyFactory:
    """Create strategies by name."""

    @staticmethod
    def create(strategy_type: str, **kwargs):
        strategies = {
            'ewmac': EWMAC,
            'ma_crossover': MovingAverageCrossover,
            'bollinger': BollingerBandStrategy,
        }

        strategy_class = strategies.get(strategy_type.lower())
        if not strategy_class:
            raise ValueError(f"Unknown strategy: {strategy_type}")

        return strategy_class(**kwargs)

# Usage
strategy = StrategyFactory.create('ewmac', fast_span=16, slow_span=64)
```

### 3. Builder Pattern

```python
class BacktestBuilder:
    """Build complex backtest configurations."""

    def __init__(self):
        self.strategy = None
        self.data = None
        self.position_sizer = None
        self.costs = {}

    def with_strategy(self, strategy):
        self.strategy = strategy
        return self

    def with_data(self, data):
        self.data = data
        return self

    def with_position_sizer(self, sizer):
        self.position_sizer = sizer
        return self

    def with_costs(self, transaction_cost, slippage):
        self.costs = {
            'transaction_cost': transaction_cost,
            'slippage': slippage
        }
        return self

    def build(self):
        engine = BacktestEngine(**self.costs)
        return engine.run(self.strategy, self.data, self.position_sizer)

# Usage
results = (BacktestBuilder()
    .with_strategy(EWMAC(16, 64))
    .with_data(price_data)
    .with_position_sizer(PositionSizer(100000))
    .with_costs(0.001, 0.0005)
    .build())
```

### 4. Decorator Pattern

```python
from functools import wraps
import time

def timing_decorator(func):
    """Measure function execution time."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        logger.info(f"{func.__name__} took {elapsed:.2f}s")
        return result
    return wrapper

@timing_decorator
def run_backtest(strategy, data):
    # Backtest logic
    pass
```

---

## Debugging

### Using Python Debugger (pdb)

```python
# Insert breakpoint
import pdb; pdb.set_trace()

# Or use built-in (Python 3.7+)
breakpoint()

# Common pdb commands:
# n - next line
# s - step into function
# c - continue
# p variable - print variable
# l - list source code
# q - quit debugger
```

### Logging for Debugging

```python
# Add debug logging
logger.setLevel('DEBUG')

def calculate_position(price, volatility, forecast):
    logger.debug(f"Inputs: price={price}, vol={volatility}, forecast={forecast}")

    position = (volatility * forecast) / price

    logger.debug(f"Calculated position: {position}")

    return position
```

### Common Issues and Solutions

**Issue: Import errors**
```bash
# Solution: Ensure you're in project root
cd systematic_trading
python main.py

# Or add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Issue: Tests fail with "No module named 'config'"**
```bash
# Solution: Install package in editable mode
pip install -e .

# Or run pytest from project root
pytest
```

**Issue: Data not downloading**
```python
# Add debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check internet connectivity
# Verify ticker format (must have .SI suffix)
# Check Yahoo Finance status
```

---

## Performance Optimization

### 1. Use Vectorized Operations

```python
# Slow: Loop through DataFrame
for i in range(len(df)):
    df.loc[i, 'result'] = df.loc[i, 'a'] * df.loc[i, 'b']

# Fast: Vectorized operation
df['result'] = df['a'] * df['b']
```

### 2. Cache Expensive Calculations

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def calculate_expensive_metric(ticker: str, period: int):
    # Expensive calculation
    return result
```

### 3. Use Appropriate Data Structures

```python
# Slow: List membership testing
tickers = ['GOOG', 'MSFT', 'TSLA']  # List
if 'GOOG' in tickers:  # O(n)
    pass

# Fast: Set membership testing
tickers = {'GOOG', 'MSFT', 'TSLA'}  # Set
if 'GOOG' in tickers:  # O(1)
    pass
```

### 4. Profile Your Code

```python
# Using cProfile
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Code to profile
run_backtest(strategy, data)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)  # Top 10 functions
```

---

## Contributing Guidelines

### Code Review Checklist

- [ ] Tests added and passing
- [ ] Documentation updated
- [ ] Code formatted (black)
- [ ] No linting errors (flake8)
- [ ] Type hints added
- [ ] Logging instead of print statements
- [ ] Error handling implemented
- [ ] Performance considered

### Commit Message Format

```
Type: Brief description (50 chars max)

Detailed explanation of what and why (wrap at 72 chars).

Examples:
- Add: Bollinger Band mean reversion strategy
- Fix: Position sizing calculation for negative forecasts
- Update: Documentation for EWMAC strategy
- Refactor: Extract signal scaling to base class
- Test: Add edge cases for empty data handling
```

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing
- [ ] Unit tests added
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes
```

---

## Quick Reference

### Common Commands

```bash
# Run tests
pytest
pytest -v
pytest --cov=.

# Format code
black .
black --check .

# Lint code
flake8 .

# Type checking
mypy .

# Run demo
python main.py

# Interactive shell
ipython
python -i main.py
```

### Key Files to Know

- `main.py` - Entry point, examples
- `config/settings.py` - All configuration
- `strategy/base_strategy.py` - Strategy interface
- `backtesting/backtest_engine.py` - Core backtest logic
- `tests/` - Test examples

### Resources

- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **User Guide**: [README.md](README.md)
- **Setup**: [SETUP.md](SETUP.md)
- **Quick Ref**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

---

**Happy coding!** Remember: test first, commit often, document everything.
