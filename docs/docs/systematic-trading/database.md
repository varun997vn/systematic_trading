---
id: database          # unique ID for this doc
title: Database      # this becomes the page title
sidebar_label: Database
---
# Trading Database Setup

Clean SQLAlchemy database for systematic trading - **5 tables, zero bloat**.

## Tables

| Table | Purpose |
|-------|---------|
| `config` | Broker credentials & cash balance |
| `strategies` | Your trading strategies |
| `trades` | Complete trade records (signal → execution → P&L) |
| `market_data` | Price data (OHLCV) |
| `positions` | Current holdings |

## Setup

```bash
pip install -r requirements.txt
python init_db.py create
```

## Core Usage

```python
from st.database import SessionLocal
from st.database.crud import *

db = SessionLocal()

# Set broker credentials
update_broker_config(db, "alpaca", "key", "secret", is_paper=True)

# Create strategy
strategy = create_strategy(
    db, 
    name="Mean Reversion",
    strategy_type="mean_reversion",
    parameters={"stop_loss_pct": 2.0, "take_profit_pct": 5.0}
)

# Create trade with signal
trade = create_trade(
    db,
    strategy_id=strategy.id,
    symbol="AAPL",
    side="buy",
    quantity=100,
    signal_price=150.50,
    signal_indicators={"rsi": 35}
)

# Mark filled
update_trade_entry(db, trade.id, entry_price=150.52)

# Close trade
close_trade(db, trade.id, exit_price=155.00)
# P&L auto-calculated: $448

# Update position
update_position(db, symbol="AAPL", quantity_change=100, price=150.52)

# Get portfolio summary
summary = get_portfolio_summary(db)
# Returns: cash, position_value, total_pnl, return_pct, etc.
```

## Key CRUD Functions

**Config**
- `get_config(db)` - Get settings
- `update_broker_config(db, broker, key, secret)` - Set broker
- `update_cash_balance(db, amount)` - Update cash

**Strategies**
- `create_strategy(db, name, type, parameters)` - New strategy
- `get_all_strategies(db, active_only=False)` - List strategies
- `update_strategy_status(db, id, status)` - Activate/deactivate

**Trades**
- `create_trade(db, strategy_id, symbol, side, quantity, ...)` - New trade
- `update_trade_entry(db, trade_id, entry_price)` - Mark filled
- `close_trade(db, trade_id, exit_price)` - Close & calculate P&L
- `get_open_trades(db)` - Open positions
- `get_trade_history(db, limit=100)` - Past trades

**Positions**
- `update_position(db, symbol, quantity_change, price)` - Update holding
- `get_all_positions(db)` - Current positions
- `get_portfolio_summary(db)` - Complete overview

**Market Data**
- `save_market_data(db, symbol, timestamp, open, high, low, close, volume)` - Store data
- `get_market_data(db, symbol, timeframe="1d", limit=100)` - Retrieve data
- `get_latest_price(db, symbol)` - Latest close price

## FastAPI Integration

```python
from fastapi import FastAPI, Depends
from st.database import get_db, get_portfolio_summary, create_trade

app = FastAPI()

@app.get("/portfolio")
def portfolio(db = Depends(get_db)):
    return get_portfolio_summary(db)

@app.post("/trades")
def new_trade(strategy_id: int, symbol: str, side: str, quantity: float, db = Depends(get_db)):
    return create_trade(db, strategy_id, symbol, side, quantity)
```

## Models Overview

**Config** - Single row with broker settings, API keys, cash balance

**Strategy** - Name, type, status, parameters (JSON), performance metrics

**Trade** - Complete lifecycle: signal data → order details → entry/exit → P&L

**MarketData** - Symbol, timestamp, OHLCV, timeframe

**Position** - Symbol, quantity, average_price, current_price, unrealized_pnl

## Commands

```bash
python init_db.py create   # Create tables
python init_db.py reset    # Reset database
python init_db.py drop     # Drop all tables
```

## Production Notes

**Switch to PostgreSQL:**
```bash
export DATABASE_URL="postgresql://user:pass@localhost/trading"
```

**Encrypt API keys before storing** (use `cryptography` library)

**Backup regularly:**
```bash
sqlite3 trading_app.db ".backup backup.db"
```

That's it. Simple, focused, everything you need.