"""
CRUD Operations - Single User System
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional, Dict, Any
from datetime import datetime

from .models import Config, Strategy, Trade, MarketData, Position


# ==================== Config CRUD ====================

def get_config(db: Session) -> Config:
    """Get configuration (creates if doesn't exist)"""
    config = db.query(Config).first()
    if not config:
        config = Config(
            initial_capital=10000.0,
            cash_balance=10000.0
        )
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


def update_broker_config(
        db: Session,
        broker_name: str,
        api_key: str,
        api_secret: str,
        is_paper: bool = True
) -> Config:
    """Update broker credentials"""
    config = get_config(db)
    config.broker_name = broker_name
    config.api_key = api_key
    config.api_secret = api_secret
    config.is_paper = is_paper
    db.commit()
    db.refresh(config)
    return config


def update_cash_balance(db: Session, cash_balance: float) -> Config:
    """Update cash balance"""
    config = get_config(db)
    config.cash_balance = cash_balance
    db.commit()
    db.refresh(config)
    return config


# ==================== Strategy CRUD ====================

def create_strategy(
        db: Session,
        name: str,
        strategy_type: str,
        parameters: Dict[str, Any] = None,
        status: str = "inactive"
) -> Strategy:
    """Create a new trading strategy"""
    db_strategy = Strategy(
        name=name,
        strategy_type=strategy_type,
        parameters=parameters or {},
        status=status
    )
    db.add(db_strategy)
    db.commit()
    db.refresh(db_strategy)
    return db_strategy


def get_strategy(db: Session, strategy_id: int) -> Optional[Strategy]:
    """Get strategy by ID"""
    return db.query(Strategy).filter(Strategy.id == strategy_id).first()


def get_strategy_by_name(db: Session, name: str) -> Optional[Strategy]:
    """Get strategy by name"""
    return db.query(Strategy).filter(Strategy.name == name).first()


def get_all_strategies(db: Session, active_only: bool = False) -> List[Strategy]:
    """Get all strategies"""
    query = db.query(Strategy)
    if active_only:
        query = query.filter(Strategy.status == "active")
    return query.all()


def update_strategy_status(db: Session, strategy_id: int, status: str) -> Optional[Strategy]:
    """Update strategy status"""
    strategy = get_strategy(db, strategy_id)
    if strategy:
        strategy.status = status
        db.commit()
        db.refresh(strategy)
    return strategy


def update_strategy_performance(
        db: Session,
        strategy_id: int,
        total_trades: int = None,
        winning_trades: int = None,
        total_pnl: float = None
) -> Optional[Strategy]:
    """Update strategy performance metrics"""
    strategy = get_strategy(db, strategy_id)
    if strategy:
        if total_trades is not None:
            strategy.total_trades = total_trades
        if winning_trades is not None:
            strategy.winning_trades = winning_trades
        if total_pnl is not None:
            strategy.total_pnl = total_pnl
        db.commit()
        db.refresh(strategy)
    return strategy


# ==================== Trade CRUD ====================

def create_trade(
        db: Session,
        strategy_id: int,
        symbol: str,
        side: str,
        quantity: float,
        signal_price: float = None,
        signal_indicators: Dict = None,
        order_type: str = "market",
        notes: str = None
) -> Trade:
    """Create a new trade"""
    db_trade = Trade(
        strategy_id=strategy_id,
        symbol=symbol,
        side=side,
        quantity=quantity,
        signal_price=signal_price,
        signal_indicators=signal_indicators,
        order_type=order_type,
        notes=notes
    )
    db.add(db_trade)
    db.commit()
    db.refresh(db_trade)
    return db_trade


def update_trade_entry(
        db: Session,
        trade_id: int,
        entry_price: float,
        entry_time: datetime = None,
        broker_order_id: str = None
) -> Optional[Trade]:
    """Update trade with entry execution details"""
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if trade:
        trade.entry_price = entry_price
        trade.entry_time = entry_time or datetime.utcnow()
        trade.status = "filled"
        if broker_order_id:
            trade.broker_order_id = broker_order_id
        db.commit()
        db.refresh(trade)
    return trade


def close_trade(
        db: Session,
        trade_id: int,
        exit_price: float,
        exit_time: datetime = None
) -> Optional[Trade]:
    """Close a trade and calculate P&L"""
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if trade and trade.is_open:
        trade.exit_price = exit_price
        trade.exit_time = exit_time or datetime.utcnow()
        trade.is_open = False

        # Calculate realized P&L
        if trade.entry_price:
            if trade.side == "buy":
                trade.realized_pnl = (exit_price - trade.entry_price) * trade.quantity
            else:  # sell
                trade.realized_pnl = (trade.entry_price - exit_price) * trade.quantity

        db.commit()
        db.refresh(trade)
    return trade


def get_open_trades(db: Session, strategy_id: int = None) -> List[Trade]:
    """Get all open trades"""
    query = db.query(Trade).filter(Trade.is_open == True)
    if strategy_id:
        query = query.filter(Trade.strategy_id == strategy_id)
    return query.all()


def get_trade_history(
        db: Session,
        strategy_id: int = None,
        symbol: str = None,
        limit: int = 100
) -> List[Trade]:
    """Get trade history"""
    query = db.query(Trade)
    if strategy_id:
        query = query.filter(Trade.strategy_id == strategy_id)
    if symbol:
        query = query.filter(Trade.symbol == symbol)
    return query.order_by(desc(Trade.created_at)).limit(limit).all()


# ==================== Position CRUD ====================

def get_position(db: Session, symbol: str) -> Optional[Position]:
    """Get position for a symbol"""
    return db.query(Position).filter(Position.symbol == symbol).first()


def update_position(
        db: Session,
        symbol: str,
        quantity_change: float,
        price: float
) -> Position:
    """Update position after a trade"""
    position = get_position(db, symbol)

    if not position:
        position = Position(symbol=symbol, quantity=0.0)
        db.add(position)

    # Update quantity and average price
    if quantity_change != 0:
        old_value = position.quantity * (position.average_price or 0)
        new_value = abs(quantity_change) * price

        position.quantity += quantity_change

        if position.quantity != 0:
            position.average_price = (old_value + new_value) / abs(position.quantity)
        else:
            position.average_price = 0

    position.current_price = price

    # Calculate unrealized P&L
    if position.quantity != 0 and position.average_price:
        position.unrealized_pnl = (position.current_price - position.average_price) * position.quantity
    else:
        position.unrealized_pnl = 0

    db.commit()
    db.refresh(position)
    return position


def get_all_positions(db: Session) -> List[Position]:
    """Get all positions"""
    return db.query(Position).filter(Position.quantity != 0).all()


def update_position_price(db: Session, symbol: str, current_price: float) -> Optional[Position]:
    """Update current price and recalculate P&L"""
    position = get_position(db, symbol)
    if position:
        position.current_price = current_price
        if position.quantity != 0 and position.average_price:
            position.unrealized_pnl = (current_price - position.average_price) * position.quantity
        db.commit()
        db.refresh(position)
    return position


# ==================== Market Data CRUD ====================

def save_market_data(
        db: Session,
        symbol: str,
        timestamp: datetime,
        open: float,
        high: float,
        low: float,
        close: float,
        volume: float,
        timeframe: str = "1d"
) -> MarketData:
    """Save market data"""
    db_data = MarketData(
        symbol=symbol,
        timestamp=timestamp,
        open=open,
        high=high,
        low=low,
        close=close,
        volume=volume,
        timeframe=timeframe
    )
    db.add(db_data)
    db.commit()
    db.refresh(db_data)
    return db_data


def get_market_data(
        db: Session,
        symbol: str,
        start_date: datetime = None,
        end_date: datetime = None,
        timeframe: str = "1d",
        limit: int = 100
) -> List[MarketData]:
    """Get market data for a symbol"""
    query = db.query(MarketData).filter(MarketData.symbol == symbol)

    if timeframe:
        query = query.filter(MarketData.timeframe == timeframe)
    if start_date:
        query = query.filter(MarketData.timestamp >= start_date)
    if end_date:
        query = query.filter(MarketData.timestamp <= end_date)

    return query.order_by(desc(MarketData.timestamp)).limit(limit).all()


def get_latest_price(db: Session, symbol: str, timeframe: str = "1d") -> Optional[float]:
    """Get the latest price for a symbol"""
    data = db.query(MarketData).filter(
        MarketData.symbol == symbol,
        MarketData.timeframe == timeframe
    ).order_by(desc(MarketData.timestamp)).first()

    return data.close if data else None


# ==================== Portfolio Summary ====================

def get_portfolio_summary(db: Session) -> Dict[str, Any]:
    """Get complete portfolio summary"""
    config = get_config(db)
    positions = get_all_positions(db)

    total_position_value = sum(
        p.quantity * p.current_price for p in positions if p.current_price
    )
    total_unrealized_pnl = sum(p.unrealized_pnl or 0 for p in positions)

    # Get all closed trades for realized P&L
    closed_trades = db.query(Trade).filter(Trade.is_open == False).all()
    total_realized_pnl = sum(t.realized_pnl or 0 for t in closed_trades)

    total_value = config.cash_balance + total_position_value
    total_pnl = total_realized_pnl + total_unrealized_pnl

    return {
        "cash_balance": config.cash_balance,
        "position_value": total_position_value,
        "total_value": total_value,
        "initial_capital": config.initial_capital,
        "total_pnl": total_pnl,
        "realized_pnl": total_realized_pnl,
        "unrealized_pnl": total_unrealized_pnl,
        "return_pct": (total_pnl / config.initial_capital * 100) if config.initial_capital else 0,
        "positions": len(positions)
    }
