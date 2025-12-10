# Quick Start Guide - Trading Signal System

## What You Have

A complete trading system with **5 professional strategies** that analyze stock data and generate signals from **-20 (
Very Strong Sell)** to **+20 (Very Strong Buy)**.

## Files

- `trader.py` - Main Trader class
- `strategy_base.py` - Base class for strategies
- `strategies.py` - 5 trading strategies
- `example_usage.py` - Usage examples
- `requirements.txt` - Dependencies
- `README.md` - Full documentation

## Your 5 Strategies

1. **RSI Momentum** - Relative Strength Index + momentum
2. **Moving Average Crossover** - Fast/slow MA crossover
3. **Bollinger Bands** - Mean reversion
4. **MACD** - Trend following
5. **Volume Weighted** - Price momentum with volume

## 30-Second Start

```python
from st.trader import Trader
from st.strategy import *

# Initialize with all strategies
trader = Trader(strategies=[
    RSIMomentumStrategy(),
    MovingAverageCrossoverStrategy(),
    BollingerBandStrategy(),
    MACDStrategy(),
    VolumeWeightedStrategy()
])

# Load your CSV (date, open, high, low, close, volume)
trader.load_data("your_data.csv")

# Generate signals
signals = trader.generate_signals(mode="aggregate")

# Get latest signal
latest = trader.get_latest_signal()
print(f"{latest['label']}: {latest['signal']}")

# Save results
trader.save_signals("signals.csv")
```

## CSV Format Required

```csv
date,open,high,low,close,volume
2024-01-01,150.00,152.50,149.50,151.00,1000000
2024-01-02,151.00,153.00,150.50,152.50,1100000
```

## Signal Scale

```
+20  ████████ VERY STRONG BUY
+15  ██████   STRONG BUY
+10  ████     GOOD BUY
+5   ██       WEAK BUY
 0   ─        NEUTRAL
-5   ██       WEAK SELL
-10  ████     GOOD SELL
-15  ██████   STRONG SELL
-20  ████████ VERY STRONG SELL
```

## Integration with Your Database

```python
from st.database import SessionLocal
from st.database.crud import create_trade

db = SessionLocal()
latest = trader.get_latest_signal()

if latest['signal'] >= 10:  # Good buy or better
    trade = create_trade(
        db,
        strategy_id=1,
        symbol="AAPL",
        side="buy",
        quantity=100,
        signal_price=latest['close'],
        signal_indicators=latest['individual_signals']
    )
```

## Aggregation Modes

- **`aggregate`** - Average all strategies (balanced)
- **`max`** - Take strongest signal (aggressive)
- **`consensus`** - Majority voting (conservative)

```python
signals = trader.generate_signals(mode="aggregate")  # Default
signals = trader.generate_signals(mode="max")  # Aggressive
signals = trader.generate_signals(mode="consensus")  # Conservative
```

## Get Strong Signals Only

```python
# Get only strong buy/sell points
points = trader.get_buy_sell_points(min_signal_strength=10)

print(f"Strong buys: {len(points['buy'])}")
print(f"Strong sells: {len(points['sell'])}")
```

---