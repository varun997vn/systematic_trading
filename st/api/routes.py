"""
FastAPI Trading System Backend - Updated for Current Project Structure
Complete API for trading system UI with database integration
"""

from datetime import datetime
from typing import List, Dict, Optional, Any

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

# Import trading system modules
from st.data import DataManager, DownloadRequest
from st.database import crud
# Import database modules
from st.database import get_db, init_db
from st.strategy import (
    RSIMomentumStrategy,
    MovingAverageCrossoverStrategy,
    BollingerBandStrategy,
    MACDStrategy,
    VolumeWeightedStrategy
)
from st.trader import Trader

# Initialize database
init_db()

app = FastAPI(
    title="Trading System API",
    description="FastAPI backend for algorithmic trading system with database integration",
    version="2.0.0"
)

# CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# Pydantic Models for Request/Response
# ==========================================

class TickerRequest(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")


class DownloadTickersRequest(BaseModel):
    tickers: List[str] = Field(..., description="List of tickers to download")
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class StrategyCreateRequest(BaseModel):
    name: str = Field(..., description="Strategy name")
    strategy_type: str = Field(..., description="Strategy type (rsi_momentum, ma_crossover, etc.)")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    status: str = Field(default="inactive", description="Strategy status (active/inactive)")


class StrategyUpdateRequest(BaseModel):
    status: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class SignalRequest(BaseModel):
    ticker: str
    strategies: List[str] = Field(default=["rsi_momentum", "ma_crossover", "macd"])
    mode: str = Field(default="aggregate", description="Signal aggregation mode")
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class TradeCreateRequest(BaseModel):
    strategy_id: int
    symbol: str
    side: str = Field(..., description="buy or sell")
    quantity: float = Field(..., gt=0)
    signal_price: Optional[float] = None
    signal_indicators: Optional[Dict[str, Any]] = None
    order_type: str = Field(default="market")
    notes: Optional[str] = None


class TradeCloseRequest(BaseModel):
    trade_id: int
    exit_price: float


class BrokerConfigRequest(BaseModel):
    broker_name: str
    api_key: str
    api_secret: str
    is_paper: bool = True


class PositionUpdateRequest(BaseModel):
    symbol: str
    quantity_change: float
    price: float = Field(..., gt=0)


# ==========================================
# Global State
# ==========================================

class AppState:
    def __init__(self):
        self.data_manager = DataManager()
        self.trader = Trader(data_manager=self.data_manager)
        self.strategy_map = {
            "rsi_momentum": RSIMomentumStrategy,
            "ma_crossover": MovingAverageCrossoverStrategy,
            "bollinger": BollingerBandStrategy,
            "macd": MACDStrategy,
            "volume_weighted": VolumeWeightedStrategy
        }

    def get_strategy_instance(self, strategy_type: str, parameters: Dict = None):
        """Create strategy instance from type string"""
        if strategy_type not in self.strategy_map:
            raise ValueError(f"Unknown strategy type: {strategy_type}")

        strategy_class = self.strategy_map[strategy_type]
        if parameters:
            return strategy_class(**parameters)
        return strategy_class()


state = AppState()


# ==========================================
# Health & Info Endpoints
# ==========================================

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Trading System API",
        "version": "2.0.0",
        "docs": "/docs",
        "status": "operational",
        "features": [
            "Data Management",
            "Strategy Management",
            "Trade Execution",
            "Portfolio Tracking",
            "Signal Generation",
            "Database Integration"
        ]
    }


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Test database connection
        config = crud.get_config(db)
        db_healthy = config is not None
    except:
        db_healthy = False

    return {
        "status": "healthy" if db_healthy else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "data_manager": state.data_manager is not None,
            "trader": state.trader is not None,
            "database": db_healthy
        }
    }


# ==========================================
# Config & Broker Endpoints
# ==========================================

@app.get("/api/config")
async def get_config(db: Session = Depends(get_db)):
    """Get current configuration"""
    config = crud.get_config(db)
    return {
        "broker_name": config.broker_name,
        "is_paper": config.is_paper,
        "initial_capital": config.initial_capital,
        "cash_balance": config.cash_balance
    }


@app.post("/api/config/broker")
async def update_broker_config(request: BrokerConfigRequest, db: Session = Depends(get_db)):
    """Update broker configuration"""
    try:
        config = crud.update_broker_config(
            db,
            broker_name=request.broker_name,
            api_key=request.api_key,
            api_secret=request.api_secret,
            is_paper=request.is_paper
        )
        return {
            "message": "Broker configuration updated",
            "broker_name": config.broker_name,
            "is_paper": config.is_paper
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/config/cash")
async def update_cash_balance(cash_balance: float, db: Session = Depends(get_db)):
    """Update cash balance"""
    try:
        config = crud.update_cash_balance(db, cash_balance)
        return {
            "message": "Cash balance updated",
            "cash_balance": config.cash_balance
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# Data Management Endpoints
# ==========================================

@app.get("/api/data/tickers")
async def get_available_tickers():
    """Get list of all available tickers in local storage"""
    try:
        tickers = state.data_manager.list_available_tickers()
        return {
            "tickers": tickers,
            "count": len(tickers)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/data/download")
async def download_ticker_data(request: TickerRequest, background_tasks: BackgroundTasks):
    """Download data for a single ticker"""
    try:
        # Download in background
        background_tasks.add_task(
            state.data_manager.download_stock_data,
            DownloadRequest(
                ticker=request.ticker,
                start_date=request.start_date,
                end_date=request.end_date
            )
        )

        return {
            "message": f"Download started for {request.ticker}",
            "ticker": request.ticker,
            "status": "processing"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/data/download-multiple")
async def download_multiple_tickers(request: DownloadTickersRequest):
    """Download data for multiple tickers"""
    try:
        download_requests = [
            DownloadRequest(
                ticker=ticker,
                start_date=request.start_date,
                end_date=request.end_date
            )
            for ticker in request.tickers
        ]

        results = state.data_manager.download_multiple_stocks(download_requests, parallel=True)

        return {
            "message": f"Downloaded {len(results)} tickers",
            "tickers": list(results.keys()),
            "successful": [t for t, df in results.items() if not df.empty],
            "failed": [t for t, df in results.items() if df.empty]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/data/ticker/{ticker}")
async def get_ticker_data(
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
):
    """Get OHLCV data for a ticker"""
    try:
        df = state.data_manager.get_ohlcv(ticker, start_date, end_date)

        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {ticker}")

        # Convert to dict for JSON response
        return {
            "ticker": ticker,
            "data": df.to_dict(orient="records"),
            "rows": len(df)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/data/ticker/{ticker}/info")
async def get_ticker_info(ticker: str):
    """Get information about a specific ticker"""
    try:
        # Check if data exists locally
        exists = state.data_manager.data_exists(ticker)

        if not exists:
            return {
                "ticker": ticker,
                "exists": False
            }

        date_range = state.data_manager.get_data_date_range(ticker)
        is_stale = state.data_manager.is_data_stale(ticker)

        # Try to get stock info from Yahoo
        stock_info = state.data_manager.get_stock_info(ticker)

        return {
            "ticker": ticker,
            "exists": True,
            "date_range": date_range,
            "is_stale": is_stale,
            "info": stock_info.dict() if stock_info else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/data/ticker/{ticker}")
async def delete_ticker_data(ticker: str):
    """Delete stored data for a ticker"""
    try:
        success = state.data_manager.delete_data(ticker)

        if not success:
            raise HTTPException(status_code=404, detail=f"No data found for {ticker}")

        return {
            "message": f"Data deleted for {ticker}",
            "ticker": ticker
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/data/storage-info")
async def get_storage_info():
    """Get information about data storage"""
    try:
        info = state.data_manager.get_storage_info()
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# Strategy Endpoints
# ==========================================

@app.post("/api/strategies")
async def create_strategy(request: StrategyCreateRequest, db: Session = Depends(get_db)):
    """Create a new trading strategy"""
    try:
        strategy = crud.create_strategy(
            db,
            name=request.name,
            strategy_type=request.strategy_type,
            parameters=request.parameters,
            status=request.status
        )

        return {
            "message": f"Strategy '{request.name}' created",
            "strategy_id": strategy.id,
            "name": strategy.name,
            "strategy_type": strategy.strategy_type,
            "status": strategy.status
        }

    except IntegrityError as e:
        db.rollback()
        # Handle name uniqueness
        if "UNIQUE constraint failed: strategies.name" in str(e.orig):
            raise HTTPException(
                status_code=409,
                detail=f"A strategy with name '{request.name}' already exists."
            )
        # Generic integrity error
        raise HTTPException(
            status_code=400,
            detail="Database integrity error occurred."
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while creating the strategy."
        )


@app.get("/api/strategies")
async def get_all_strategies(active_only: bool = False, db: Session = Depends(get_db)):
    """Get all strategies"""
    try:
        strategies = crud.get_all_strategies(db, active_only=active_only)

        return {
            "strategies": [
                {
                    "id": s.id,
                    "name": s.name,
                    "strategy_type": s.strategy_type,
                    "status": s.status.value,
                    "parameters": s.parameters,
                    "total_trades": s.total_trades,
                    "winning_trades": s.winning_trades,
                    "total_pnl": s.total_pnl,
                    "win_rate": (s.winning_trades / s.total_trades * 100) if s.total_trades > 0 else 0
                }
                for s in strategies
            ],
            "count": len(strategies)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/strategies/{strategy_id}")
async def get_strategy(strategy_id: int, db: Session = Depends(get_db)):
    """Get a specific strategy"""
    try:
        strategy = crud.get_strategy(db, strategy_id)

        if not strategy:
            raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")

        return {
            "id": strategy.id,
            "name": strategy.name,
            "strategy_type": strategy.strategy_type,
            "status": strategy.status.value,
            "parameters": strategy.parameters,
            "total_trades": strategy.total_trades,
            "winning_trades": strategy.winning_trades,
            "total_pnl": strategy.total_pnl,
            "created_at": strategy.created_at
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/strategies/{strategy_id}")
async def update_strategy(
        strategy_id: int,
        request: StrategyUpdateRequest,
        db: Session = Depends(get_db)
):
    """Update strategy status or parameters"""
    try:
        if request.status:
            strategy = crud.update_strategy_status(db, strategy_id, request.status)
            if not strategy:
                raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")

        return {
            "message": f"Strategy {strategy_id} updated",
            "strategy_id": strategy_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/strategies/{strategy_id}")
async def delete_strategy(strategy_id: int, db: Session = Depends(get_db)):
    """Delete a strategy"""
    try:
        strategy = crud.get_strategy(db, strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")

        db.delete(strategy)
        db.commit()

        return {
            "message": f"Strategy {strategy_id} deleted",
            "strategy_id": strategy_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/strategies/types/available")
async def get_available_strategy_types():
    """Get list of available strategy types"""
    return {
        "strategy_types": list(state.strategy_map.keys()),
        "descriptions": {
            "rsi_momentum": "RSI-based momentum strategy with oversold/overbought detection",
            "ma_crossover": "Dual moving average crossover strategy",
            "bollinger": "Bollinger Band mean reversion strategy",
            "macd": "MACD convergence/divergence strategy",
            "volume_weighted": "Volume-weighted price momentum strategy"
        }
    }


# ==========================================
# Trade Endpoints
# ==========================================

@app.post("/api/trades")
async def create_trade(request: TradeCreateRequest, db: Session = Depends(get_db)):
    """Create a new trade"""
    try:
        # Validate strategy exists
        strategy = crud.get_strategy(db, request.strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail=f"Strategy {request.strategy_id} not found")

        trade = crud.create_trade(
            db,
            strategy_id=request.strategy_id,
            symbol=request.symbol,
            side=request.side,
            quantity=request.quantity,
            signal_price=request.signal_price,
            signal_indicators=request.signal_indicators,
            order_type=request.order_type,
            notes=request.notes
        )

        return {
            "message": "Trade created",
            "trade_id": trade.id,
            "symbol": trade.symbol,
            "side": trade.side.value,
            "quantity": trade.quantity,
            "status": trade.status.value
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.patch("/api/trades/{trade_id}/entry")
async def update_trade_entry(
        trade_id: int,
        entry_price: float,
        broker_order_id: Optional[str] = None,
        db: Session = Depends(get_db)
):
    """Update trade with entry execution details"""
    try:
        trade = crud.update_trade_entry(
            db,
            trade_id=trade_id,
            entry_price=entry_price,
            broker_order_id=broker_order_id
        )

        if not trade:
            raise HTTPException(status_code=404, detail=f"Trade {trade_id} not found")

        return {
            "message": "Trade entry updated",
            "trade_id": trade.id,
            "entry_price": trade.entry_price,
            "status": trade.status.value
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.patch("/api/trades/{trade_id}/close")
async def close_trade(trade_id: int, request: TradeCloseRequest, db: Session = Depends(get_db)):
    """Close a trade"""
    try:
        trade = crud.close_trade(db, trade_id, request.exit_price)

        if not trade:
            raise HTTPException(status_code=404, detail=f"Trade {trade_id} not found")

        return {
            "message": "Trade closed",
            "trade_id": trade.id,
            "exit_price": trade.exit_price,
            "realized_pnl": trade.realized_pnl,
            "is_open": trade.is_open
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/trades/open")
async def get_open_trades(strategy_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Get all open trades"""
    try:
        trades = crud.get_open_trades(db, strategy_id)

        return {
            "trades": [
                {
                    "id": t.id,
                    "strategy_id": t.strategy_id,
                    "symbol": t.symbol,
                    "side": t.side.value,
                    "quantity": t.quantity,
                    "entry_price": t.entry_price,
                    "entry_time": t.entry_time,
                    "signal_price": t.signal_price
                }
                for t in trades
            ],
            "count": len(trades)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/trades/history")
async def get_trade_history(
        strategy_id: Optional[int] = None,
        symbol: Optional[str] = None,
        limit: int = Query(default=100, le=1000),
        db: Session = Depends(get_db)
):
    """Get trade history"""
    try:
        trades = crud.get_trade_history(db, strategy_id, symbol, limit)

        return {
            "trades": [
                {
                    "id": t.id,
                    "strategy_id": t.strategy_id,
                    "symbol": t.symbol,
                    "side": t.side.value,
                    "quantity": t.quantity,
                    "entry_price": t.entry_price,
                    "exit_price": t.exit_price,
                    "realized_pnl": t.realized_pnl,
                    "is_open": t.is_open,
                    "created_at": t.created_at
                }
                for t in trades
            ],
            "count": len(trades)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# Position Endpoints
# ==========================================

@app.get("/api/positions")
async def get_all_positions(db: Session = Depends(get_db)):
    """Get all current positions"""
    try:
        positions = crud.get_all_positions(db)

        return {
            "positions": [
                {
                    "symbol": p.symbol,
                    "quantity": p.quantity,
                    "average_price": p.average_price,
                    "current_price": p.current_price,
                    "unrealized_pnl": p.unrealized_pnl,
                    "market_value": p.quantity * p.current_price if p.current_price else 0,
                    "updated_at": p.updated_at
                }
                for p in positions
            ],
            "count": len(positions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/positions/{symbol}")
async def get_position(symbol: str, db: Session = Depends(get_db)):
    """Get position for a specific symbol"""
    try:
        position = crud.get_position(db, symbol)

        if not position or position.quantity == 0:
            raise HTTPException(status_code=404, detail=f"No position found for {symbol}")

        return {
            "symbol": position.symbol,
            "quantity": position.quantity,
            "average_price": position.average_price,
            "current_price": position.current_price,
            "unrealized_pnl": position.unrealized_pnl,
            "market_value": position.quantity * position.current_price if position.current_price else 0
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/positions/{symbol}")
async def update_position(symbol: str, request: PositionUpdateRequest, db: Session = Depends(get_db)):
    """Update position after a trade"""
    try:
        position = crud.update_position(
            db,
            symbol=request.symbol,
            quantity_change=request.quantity_change,
            price=request.price
        )

        return {
            "message": f"Position updated for {symbol}",
            "symbol": position.symbol,
            "quantity": position.quantity,
            "average_price": position.average_price,
            "unrealized_pnl": position.unrealized_pnl
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.patch("/api/positions/{symbol}/price")
async def update_position_price(symbol: str, current_price: float, db: Session = Depends(get_db)):
    """Update current price for a position"""
    try:
        position = crud.update_position_price(db, symbol, current_price)

        if not position:
            raise HTTPException(status_code=404, detail=f"Position {symbol} not found")

        return {
            "message": f"Price updated for {symbol}",
            "symbol": position.symbol,
            "current_price": position.current_price,
            "unrealized_pnl": position.unrealized_pnl
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==========================================
# Portfolio Summary Endpoint
# ==========================================

@app.get("/api/portfolio/summary")
async def get_portfolio_summary(db: Session = Depends(get_db)):
    """Get comprehensive portfolio summary"""
    try:
        summary = crud.get_portfolio_summary(db)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# Trading Signal Endpoints
# ==========================================

@app.post("/api/signals/generate")
async def generate_signals(request: SignalRequest):
    """Generate trading signals for a ticker"""
    try:
        # Load data
        state.trader.load_data(
            ticker=request.ticker,
            start_date=request.start_date,
            end_date=request.end_date
        )

        # Clear existing strategies and add requested ones
        state.trader.strategies = []

        for strategy_type in request.strategies:
            try:
                strategy = state.get_strategy_instance(strategy_type)
                state.trader.add_strategy(strategy)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

        # Generate signals
        signals_df = state.trader.generate_signals(mode=request.mode)

        # Get summary
        buy_signals = len(signals_df.filter(signals_df["final_signal"] > 0))
        sell_signals = len(signals_df.filter(signals_df["final_signal"] < 0))
        neutral_signals = len(signals_df.filter(signals_df["final_signal"] == 0))

        # Get latest signal
        latest = state.trader.get_latest_signal()

        return {
            "ticker": request.ticker,
            "mode": request.mode,
            "signals_generated": len(signals_df),
            "buy_signals": buy_signals,
            "sell_signals": sell_signals,
            "neutral_signals": neutral_signals,
            "latest_signal": latest
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/signals/latest/{ticker}")
async def get_latest_signal(ticker: str):
    """Get the most recent trading signal"""
    try:
        if state.trader.current_ticker != ticker:
            raise HTTPException(
                status_code=400,
                detail=f"Signals not generated for {ticker}. Call /api/signals/generate first."
            )

        latest = state.trader.get_latest_signal()
        return latest
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/signals/history/{ticker}")
async def get_signal_history(
        ticker: str,
        limit: int = Query(default=100, le=1000)
):
    """Get signal history for a ticker"""
    try:
        if state.trader.current_ticker != ticker:
            raise HTTPException(
                status_code=400,
                detail=f"Signals not generated for {ticker}. Call /api/signals/generate first."
            )

        signals_df = state.trader.get_signal_history(last_n=limit)

        # Convert to list of dicts
        signals_list = [
            {
                "date": row["date"],
                "close": row["close"],
                "signal": row["final_signal"],
                "label": row["signal_label"]
            }
            for row in signals_df.iter_rows(named=True)
        ]

        return {
            "ticker": ticker,
            "signals": signals_list,
            "count": len(signals_list)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/signals/buy-sell/{ticker}")
async def get_buy_sell_points(
        ticker: str,
        min_strength: int = Query(default=10, ge=5, le=20)
):
    """Get distinct buy and sell points"""
    try:
        if state.trader.current_ticker != ticker:
            raise HTTPException(
                status_code=400,
                detail=f"Signals not generated for {ticker}. Call /api/signals/generate first."
            )

        points = state.trader.get_buy_sell_points(min_signal_strength=min_strength)

        # Convert to list of dicts
        buy_points = [
            {
                "date": row["date"],
                "signal": row["final_signal"],
                "price": row["close"]
            }
            for row in points["buy"].iter_rows(named=True)
        ]

        sell_points = [
            {
                "date": row["date"],
                "signal": row["final_signal"],
                "price": row["close"]
            }
            for row in points["sell"].iter_rows(named=True)
        ]

        return {
            "ticker": ticker,
            "min_strength": min_strength,
            "buy_points": buy_points,
            "sell_points": sell_points
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# Market Data Endpoints (Database)
# ==========================================

@app.post("/api/market-data")
async def save_market_data(
        symbol: str,
        timestamp: datetime,
        open: float,
        high: float,
        low: float,
        close: float,
        volume: float,
        timeframe: str = "1d",
        db: Session = Depends(get_db)
):
    """Save market data to database"""
    try:
        data = crud.save_market_data(
            db, symbol, timestamp, open, high, low, close, volume, timeframe
        )
        return {
            "message": "Market data saved",
            "symbol": symbol,
            "timestamp": timestamp
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/market-data/{symbol}")
async def get_market_data(
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        timeframe: str = "1d",
        limit: int = Query(default=100, le=1000),
        db: Session = Depends(get_db)
):
    """Get market data from database"""
    try:
        data = crud.get_market_data(
            db, symbol, start_date, end_date, timeframe, limit
        )

        return {
            "symbol": symbol,
            "data": [
                {
                    "timestamp": d.timestamp,
                    "open": d.open,
                    "high": d.high,
                    "low": d.low,
                    "close": d.close,
                    "volume": d.volume
                }
                for d in data
            ],
            "count": len(data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/market-data/{symbol}/latest")
async def get_latest_price(symbol: str, db: Session = Depends(get_db)):
    """Get the latest price for a symbol"""
    try:
        price = crud.get_latest_price(db, symbol)

        if price is None:
            raise HTTPException(status_code=404, detail=f"No market data found for {symbol}")

        return {
            "symbol": symbol,
            "price": price
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# Utility Endpoints
# ==========================================

@app.get("/api/market/status")
async def get_market_status():
    """Get current market status"""
    now = datetime.now()
    is_market_hours = 9 <= now.hour < 16 and now.weekday() < 5

    return {
        "is_open": is_market_hours,
        "current_time": now.isoformat(),
        "is_trading_day": now.weekday() < 5
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
