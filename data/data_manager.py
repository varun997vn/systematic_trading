"""
Data manager for downloading and managing market data via Yahoo Finance.
"""

import re
from pathlib import Path
from typing import List, Optional, Dict

import pandas as pd
import yfinance as yf
from pydantic import BaseModel, Field, field_validator

from config.settings import Settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


# ---- Pydantic Models ---- #

class StockInfo(BaseModel):
    """Metadata for a stock."""
    name: str
    sector: str
    currency: str
    exchange: str


class DownloadRequest(BaseModel):
    """Request parameters for downloading stock data."""
    ticker: str = Field(..., description="Stock ticker (e.g., GOOG, TSLA, AAPL)")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    save: bool = Field(True, description="Save data to CSV")

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v):
        if not re.match(r"^[A-Za-z0-9.\-]+$", v):
            raise ValueError("Invalid ticker format")
        return v


# ---- Data Manager ---- #

class DataManager(BaseModel):
    """
    Manages market data download and storage for US stocks using Yahoo Finance.
    """

    data_dir: str = Field(default_factory=lambda: str(Settings.DATA_DIR))

    def __init__(self, **data):
        super().__init__(**data)
        Path(self.data_dir).mkdir(parents=True, exist_ok=True)

    # ---------------------------
    # Core download/load methods
    # ---------------------------

    def download_stock_data(self, req: DownloadRequest) -> pd.DataFrame:
        """Download historical data for a single stock from Yahoo Finance."""
        start = req.start_date or Settings.DATA_START_DATE
        end = req.end_date or Settings.DATA_END_DATE

        logger.info(f"Downloading {req.ticker} from {start} to {end}")

        try:
            df = yf.download(req.ticker, start=start, end=end, auto_adjust=True, progress=False)

            if df.empty:
                logger.warning(f"No data retrieved for {req.ticker}")
                return pd.DataFrame()

            df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
            df.index.name = 'Date'
            df.index = df.index.tz_localize(None)  # maintaining timezone

            if req.save:
                self.save_data(req.ticker, df)

            logger.info(f"Downloaded {len(df)} rows for {req.ticker}")
            return df
        except Exception as e:
            logger.error(f"Error downloading {req.ticker}: {e}", exc_info=True)
            return pd.DataFrame()

    def download_multiple_stocks(self, req: List[DownloadRequest]) -> Dict[str, pd.DataFrame]:
        """Download data for multiple stocks."""
        data = {}
        for d_req in req:
            df = self.download_stock_data(d_req)
            data[d_req.ticker] = df
        return data

    def save_data(self, ticker: str, df: pd.DataFrame) -> None:
        """Save stock data to CSV."""
        filename = f"{ticker.replace('.', '_')}.csv"
        filepath = Path(self.data_dir) / filename

        # flatten multi-level columns if present: (0: ohlcv, 1: ticker-name)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0].strip() for col in df.columns.values]

        df.to_csv(filepath)
        logger.info(f"Saved {ticker} data to {filepath}")

    def load_data(self, ticker: str) -> pd.DataFrame:
        """Load stock data from CSV."""
        filename = f"{ticker.replace('.', '_')}.csv"
        filepath = Path(self.data_dir) / filename

        if not filepath.exists():
            logger.warning(f"Data file not found for {ticker}: {filepath}")
            return pd.DataFrame()

        try:
            df = pd.read_csv(filepath, index_col='Date', parse_dates=True)
            logger.info(f"Loaded {len(df)} rows for {ticker} from {filepath}")
            return df
        except Exception as e:
            logger.error(f"Error loading {ticker}: {e}")
            return pd.DataFrame()

    def get_close_prices(
            self, tickers: List[str], start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """Get close prices for multiple stocks as a DataFrame."""
        close_prices = {}

        for ticker in tickers:
            df = self.load_data(ticker)
            if df.empty:
                logger.info(f"No local data for {ticker}, downloading...")
                df = self.download_stock_data(
                    DownloadRequest(ticker=ticker, start_date=start_date, end_date=end_date)
                )

            if not df.empty:
                if start_date:
                    df = df[df.index >= start_date]
                if end_date:
                    df = df[df.index <= end_date]
                close_prices[ticker] = df['Close']

        if not close_prices:
            return pd.DataFrame()

        price_df = pd.DataFrame(close_prices)
        price_df = price_df.ffill()
        return price_df

    def get_stock_info(self, ticker: str) -> Optional[StockInfo]:
        """Get stock information from Yahoo Finance."""
        try:
            stock = yf.Ticker(ticker)
            info = stock.get_info()
            return StockInfo(
                name=info.get('longName', ticker),
                sector=info.get('sector', 'Unknown'),
                currency=info.get('currency', 'USD'),
                exchange=info.get('exchange', 'NASDAQ'),
            )
        except Exception as e:
            logger.error(f"Error getting info for {ticker}: {e}")
            return None
