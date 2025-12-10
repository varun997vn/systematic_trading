"""
Enhanced data manager for downloading and managing market data via Yahoo Finance.
Includes improvements for better integration with the Trader class.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import yfinance as yf
from pydantic import BaseModel, Field, field_validator

from st.config.settings import Settings
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
        return v.upper()


# ---- Data Manager ---- #


class DataManager(BaseModel):
    """
    Manages market data download and storage for US stocks using Yahoo Finance.
    Enhanced with better error handling, batch operations, and data validation.
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
            df = yf.download(
                req.ticker, start=start, end=end, auto_adjust=True, progress=False
            )

            if df.empty:
                logger.warning(f"No data retrieved for {req.ticker}")
                return pd.DataFrame()

            df = df[["Open", "High", "Low", "Close", "Volume"]]
            df.index.name = "Date"
            df.index = df.index.tz_localize(None)  # removing timezone

            if req.save:
                self.save_data(req.ticker, df)

            logger.info(f"Downloaded {len(df)} rows for {req.ticker}")
            return df
        except Exception as e:
            logger.error(f"Error downloading {req.ticker}: {e}", exc_info=True)
            return pd.DataFrame()

    def download_multiple_stocks(
        self, req: List[DownloadRequest], parallel: bool = True
    ) -> Dict[str, pd.DataFrame]:
        """
        Download data for multiple stocks.

        Args:
            req: List of download requests
            parallel: If True, use yfinance's batch download (faster but less control)
        """
        if parallel and len(req) > 1:
            return self._download_batch([r.ticker for r in req], req[0])

        data = {}
        for d_req in req:
            df = self.download_stock_data(d_req)
            data[d_req.ticker] = df
        return data

    def _download_batch(
        self, tickers: List[str], template_req: DownloadRequest
    ) -> Dict[str, pd.DataFrame]:
        """Batch download using yfinance for better performance."""
        start = template_req.start_date or Settings.DATA_START_DATE
        end = template_req.end_date or Settings.DATA_END_DATE

        logger.info(f"Batch downloading {len(tickers)} tickers")

        try:
            data = yf.download(
                tickers,
                start=start,
                end=end,
                auto_adjust=True,
                progress=False,
                group_by="ticker",
            )

            result = {}
            for ticker in tickers:
                try:
                    if len(tickers) == 1:
                        df = data
                    else:
                        df = data[ticker]

                    if not df.empty:
                        df = df[["Open", "High", "Low", "Close", "Volume"]]
                        df.index = df.index.tz_localize(None)

                        if template_req.save:
                            self.save_data(ticker, df)

                        result[ticker] = df
                        logger.info(f"Downloaded {len(df)} rows for {ticker}")
                except Exception as e:
                    logger.error(f"Error processing {ticker} from batch: {e}")
                    result[ticker] = pd.DataFrame()

            return result

        except Exception as e:
            logger.error(f"Batch download failed: {e}", exc_info=True)
            raise e

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
            df = pd.read_csv(filepath, index_col="Date", parse_dates=True)
            logger.info(f"Loaded {len(df)} rows for {ticker} from {filepath}")
            return df
        except Exception as e:
            logger.error(f"Error loading {ticker}: {e}")
            return pd.DataFrame()

    def get_close_prices(
        self,
        tickers: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Get close prices for multiple stocks as a DataFrame."""
        close_prices = {}

        for ticker in tickers:
            df = self.load_data(ticker)
            if df.empty:
                logger.info(f"No local data for {ticker}, downloading...")
                df = self.download_stock_data(
                    DownloadRequest(
                        ticker=ticker, start_date=start_date, end_date=end_date
                    )
                )

            if not df.empty:
                if start_date:
                    df = df[df.index >= start_date]
                if end_date:
                    df = df[df.index <= end_date]
                close_prices[ticker] = df["Close"]

        if not close_prices:
            return pd.DataFrame()

        price_df = pd.DataFrame(close_prices)
        price_df = price_df.ffill()  # forward fill missing values
        return price_df

    def get_stock_info(self, ticker: str) -> Optional[StockInfo]:
        """Get stock information from Yahoo Finance."""
        try:
            stock = yf.Ticker(ticker)
            info = stock.get_info()
            return StockInfo(
                name=info.get("longName", ticker),
                sector=info.get("sector", "Unknown"),
                currency=info.get("currency", "USD"),
                exchange=info.get("exchange", "NASDAQ"),
            )
        except Exception as e:
            logger.error(f"Error getting info for {ticker}: {e}")
            return None

    # ---------------------------
    # Enhanced methods
    # ---------------------------

    def data_exists(self, ticker: str) -> bool:
        """Check if data file exists for a ticker."""
        filename = f"{ticker.replace('.', '_')}.csv"
        filepath = Path(self.data_dir) / filename
        return filepath.exists()

    def get_data_date_range(self, ticker: str) -> Optional[Tuple[str, str]]:
        """Get the date range of stored data for a ticker."""
        df = self.load_data(ticker)
        if df.empty:
            return None
        return str(df.index[0].date()), str(df.index[-1].date())

    def is_data_stale(self, ticker: str, max_days_old: int = 1) -> bool:
        """Check if data is stale (older than max_days_old)."""
        date_range = self.get_data_date_range(ticker)
        if not date_range:
            return True

        _, end_date = date_range
        last_date = datetime.strptime(end_date, "%Y-%m-%d")
        days_old = (datetime.now() - last_date).days

        return days_old > max_days_old

    def update_stale_data(
        self, tickers: List[str], max_days_old: int = 1
    ) -> Dict[str, pd.DataFrame]:
        """Update data for tickers that are stale."""
        updated = {}

        for ticker in tickers:
            if self.is_data_stale(ticker, max_days_old):
                logger.info(f"Updating stale data for {ticker}")
                df = self.download_stock_data(DownloadRequest(ticker=ticker, save=True))
                if not df.empty:
                    updated[ticker] = df

        logger.info(f"Updated {len(updated)} stale tickers")
        return updated

    def get_ohlcv(
        self,
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Get OHLCV data for a ticker with optional date filtering."""
        df = self.load_data(ticker)

        if df.empty:
            return pd.DataFrame()

        if start_date:
            df = df[df.index >= start_date]
        if end_date:
            df = df[df.index <= end_date]

        return df

    def delete_data(self, ticker: str) -> bool:
        """Delete stored data for a ticker."""
        filename = f"{ticker.replace('.', '_')}.csv"
        filepath = Path(self.data_dir) / filename

        if filepath.exists():
            filepath.unlink()
            logger.info(f"Deleted data for {ticker}")
            return True

        return False

    def list_available_tickers(self) -> List[str]:
        """List all tickers with stored data."""
        data_path = Path(self.data_dir)
        csv_files = data_path.glob("*.csv")

        tickers = []
        for file in csv_files:
            ticker = file.stem.replace("_", ".")
            tickers.append(ticker)

        return sorted(tickers)

    def get_storage_info(self) -> Dict[str, any]:
        """Get information about data storage."""
        data_path = Path(self.data_dir)
        csv_files = list(data_path.glob("*.csv"))

        total_size = sum(f.stat().st_size for f in csv_files)

        return {
            "data_dir": str(data_path),
            "num_files": len(csv_files),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "tickers": self.list_available_tickers(),
        }
