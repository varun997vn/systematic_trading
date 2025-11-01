"""
Data manager for downloading and managing market data.
Focuses on US equity markets via Yahoo Finance.
"""

import pandas as pd
import yfinance as yf
from pathlib import Path
from typing import List, Optional, Union
from datetime import datetime

from config.settings import Settings
from utils.logger import setup_logger


logger = setup_logger(__name__)


class DataManager:
    """
    Manages market data download and storage for US stocks.

    US stocks on Yahoo Finance use their standard ticker symbols (e.g., GOOG, MSFT, TSLA).
    """

    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize DataManager.

        Args:
            data_dir: Directory to store data (uses Settings.DATA_DIR if None)
        """
        self.data_dir = data_dir or Settings.DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def download_stock_data(
        self,
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        save: bool = True,
    ) -> pd.DataFrame:
        """
        Download historical data for a single stock from Yahoo Finance.

        Args:
            ticker: Stock ticker (e.g., 'GOOG', 'MSFT', 'TSLA')
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            save: If True, save data to CSV

        Returns:
            DataFrame with OHLCV data
        """
        start = start_date or Settings.DATA_START_DATE
        end = end_date or Settings.DATA_END_DATE

        logger.info(f"Downloading {ticker} from {start} to {end}")

        try:
            # Download data using yfinance
            stock = yf.Ticker(ticker)
            df = stock.history(start=start, end=end, auto_adjust=True)

            if df.empty:
                logger.warning(f"No data retrieved for {ticker}")
                return pd.DataFrame()

            # Clean up the data
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
            df.index.name = 'Date'

            logger.info(f"Downloaded {len(df)} rows for {ticker}")

            # Save to CSV if requested
            if save:
                self.save_data(ticker, df)

            return df

        except Exception as e:
            logger.error(f"Error downloading {ticker}: {e}")
            return pd.DataFrame()

    def download_multiple_stocks(
        self,
        tickers: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        save: bool = True,
    ) -> dict:
        """
        Download data for multiple stocks.

        Args:
            tickers: List of stock tickers
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            save: If True, save data to CSV

        Returns:
            Dictionary mapping ticker to DataFrame
        """
        data = {}

        for ticker in tickers:
            df = self.download_stock_data(ticker, start_date, end_date, save)
            if not df.empty:
                data[ticker] = df

        return data

    def save_data(self, ticker: str, df: pd.DataFrame) -> None:
        """
        Save stock data to CSV file.

        Args:
            ticker: Stock ticker
            df: DataFrame to save
        """
        filename = f"{ticker.replace('.', '_')}.csv"
        filepath = self.data_dir / filename

        df.to_csv(filepath)
        logger.info(f"Saved {ticker} data to {filepath}")

    def load_data(self, ticker: str) -> pd.DataFrame:
        """
        Load stock data from CSV file.

        Args:
            ticker: Stock ticker

        Returns:
            DataFrame with stock data
        """
        filename = f"{ticker.replace('.', '_')}.csv"
        filepath = self.data_dir / filename

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
        self,
        tickers: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Get close prices for multiple stocks as a DataFrame.

        This format is useful for portfolio analysis and Carver's multi-asset strategies.

        Args:
            tickers: List of stock tickers
            start_date: Start date filter
            end_date: End date filter

        Returns:
            DataFrame with tickers as columns and dates as index
        """
        close_prices = {}

        for ticker in tickers:
            df = self.load_data(ticker)
            if df.empty:
                logger.info(f"No local data for {ticker}, downloading...")
                df = self.download_stock_data(ticker, start_date, end_date)

            if not df.empty:
                # Filter by date if specified
                if start_date:
                    df = df[df.index >= start_date]
                if end_date:
                    df = df[df.index <= end_date]

                close_prices[ticker] = df['Close']

        if not close_prices:
            return pd.DataFrame()

        # Combine into single DataFrame
        price_df = pd.DataFrame(close_prices)

        # Forward fill missing values (common in multi-asset portfolios)
        price_df = price_df.fillna(method='ffill')

        return price_df

    def get_stock_info(self, ticker: str) -> dict:
        """
        Get stock information from Yahoo Finance.

        Args:
            ticker: Stock ticker

        Returns:
            Dictionary with stock information
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            return {
                'name': info.get('longName', ticker),
                'sector': info.get('sector', 'Unknown'),
                'currency': info.get('currency', 'USD'),
                'exchange': info.get('exchange', 'NASDAQ'),
            }
        except Exception as e:
            logger.error(f"Error getting info for {ticker}: {e}")
            return {}
