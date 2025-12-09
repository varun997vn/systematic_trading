"""
SQLAlchemy Models for Trading Application - Single User Version
"""
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean,
    ForeignKey, Text, Enum, JSON, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from database import Base


# Enums for standardized values
class OrderType(str, enum.Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderSide(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class StrategyStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


# ==================== Configuration ====================

class Config(Base):
    """Single configuration table for app settings and broker credentials"""
    __tablename__ = "config"

    id = Column(Integer, primary_key=True)

    # Broker credentials
    broker_name = Column(String(100))  # alpaca, binance, etc.
    api_key = Column(String(255))
    api_secret = Column(String(255))
    is_paper = Column(Boolean, default=True)

    # Portfolio settings
    initial_capital = Column(Float, default=10000.0)
    cash_balance = Column(Float, default=10000.0)

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ==================== Trading Strategies ====================

class Strategy(Base):
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    strategy_type = Column(String(100), nullable=False)  # mean_reversion, momentum, etc.
    status = Column(Enum(StrategyStatus), default=StrategyStatus.INACTIVE)

    # Strategy parameters and risk management stored as JSON
    parameters = Column(JSON, default={})

    # Performance metrics
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    total_pnl = Column(Float, default=0.0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    trades = relationship("Trade", back_populates="strategy", cascade="all, delete-orphan")


# ==================== Market Data ====================

class MarketData(Base):
    __tablename__ = "market_data"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)

    # OHLCV data
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)

    timeframe = Column(String(10), default="1d")  # 1m, 5m, 1h, 1d

    __table_args__ = (
        Index('idx_symbol_timestamp', 'symbol', 'timestamp'),
    )


# ==================== Trades ====================

class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    symbol = Column(String(20), nullable=False, index=True)

    # Order details
    side = Column(Enum(OrderSide), nullable=False)
    order_type = Column(Enum(OrderType), default=OrderType.MARKET)
    quantity = Column(Float, nullable=False)

    # Signal data
    signal_price = Column(Float)
    signal_indicators = Column(JSON)  # Technical indicators at signal time

    # Entry
    entry_price = Column(Float)
    entry_time = Column(DateTime(timezone=True), index=True)

    # Exit (nullable if still open)
    exit_price = Column(Float)
    exit_time = Column(DateTime(timezone=True))

    # Status and P&L
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, index=True)
    is_open = Column(Boolean, default=True, index=True)
    realized_pnl = Column(Float)

    # Broker reference
    broker_order_id = Column(String(255))

    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    strategy = relationship("Strategy", back_populates="trades")


# ==================== Portfolio Positions ====================

class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, unique=True, index=True)

    # Position details
    quantity = Column(Float, default=0.0)
    average_price = Column(Float)
    current_price = Column(Float)

    # P&L
    unrealized_pnl = Column(Float, default=0.0)
    total_pnl = Column(Float, default=0.0)

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())