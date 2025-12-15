"""
Data Management Module for Systematic Trading Framework
Based on Robert Carver's "Systematic Trading"

Core responsibilities:
- PriceData structure (OHLCV)
- DataLoader (load market data)
- DataValidator (check completeness)
- ReturnCalculator (compute returns)
"""

from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd
import yfinance as yf
from pydantic import BaseModel, Field

from st.config.settings import Settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


# ---- Core Data Structures ---- #


class PriceData(BaseModel):
    """OHLCV data structure for systematic trading."""

    model_config = {"arbitrary_types_allowed": True}

    ticker: str
    data: pd.DataFrame = Field(
        ..., description="OHLCV DataFrame with DatetimeIndex"
    )

    def __init__(self, ticker: str, data: pd.DataFrame):
        super().__init__(ticker=ticker, data=data)
        self._validate_structure()

    def _validate_structure(self):
        """Ensure data has required OHLCV columns."""
        required = ["Open", "High", "Low", "Close", "Volume"]
        missing = [col for col in required if col not in self.data.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

    @property
    def close(self) -> pd.Series:
        """Return close prices."""
        return self.data["Close"]

    @property
    def volume(self) -> pd.Series:
        """Return volume."""
        return self.data["Volume"]


# ---- Data Loader ---- #


class DataLoader:
    """Load market data from files or Yahoo Finance."""

    def __init__(self, data_dir: str = Settings.DATA_DIR):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def load_csv(self, ticker: str) -> Optional[PriceData]:
        """Load price data from CSV file."""
        filepath = self._get_filepath(ticker)

        if not filepath.exists():
            logger.warning(f"Data file not found for {ticker}: {filepath}")
            return None

        try:
            df = pd.read_csv(
                filepath,
                index_col="Date",
                parse_dates=["Date"]
            )

            logger.info(f"Loaded {len(df)} rows for {ticker}")
            return PriceData(ticker=ticker, data=df)
        except Exception as e:
            logger.error(f"Error loading {ticker}: {e}")
            return None

    def download(
            self,
            ticker: str,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            save: bool = True,
    ) -> Optional[PriceData]:
        """Download historical data from Yahoo Finance."""
        start = start_date or Settings.DATA_START_DATE
        end = end_date or Settings.DATA_END_DATE

        logger.info(f"Downloading {ticker} from {start} to {end}")

        try:
            df = yf.download(
                ticker, start=start, end=end, auto_adjust=True, progress=False
            )

            if df.empty:
                logger.warning(f"No data retrieved for {ticker}")
                return None

            df = df[["Open", "High", "Low", "Close", "Volume"]]
            df.index.name = "Date"
            # df.index = df.index.tz_localize(None)

            if save:
                self._save_csv(ticker, df)

            logger.info(f"Downloaded {len(df)} rows for {ticker}")
            return self.load_csv(ticker)

        except Exception as e:
            logger.error(f"Error downloading {ticker}: {e}")
            return None

    def download_batch(
            self,
            tickers: List[str],
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            save: bool = True,
    ) -> dict[str, PriceData]:
        """Download multiple tickers in batch."""
        start = start_date or Settings.DATA_START_DATE
        end = end_date or Settings.DATA_END_DATE

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
                    df = data[ticker] if len(tickers) > 1 else data

                    if not df.empty:
                        df = df[["Open", "High", "Low", "Close", "Volume"]]
                        # df.index = df.index.tz_localize(None)

                        if save:
                            self._save_csv(ticker, df)

                        result[ticker] = self.load_csv(ticker)
                        logger.info(f"Downloaded {len(df)} rows for {ticker}")

                except Exception as e:
                    logger.error(f"Error processing {ticker}: {e}")

            return result

        except Exception as e:
            logger.error(f"Batch download failed: {e}")
            return {}

    def _save_csv(self, ticker: str, df: pd.DataFrame) -> None:
        """Save data to CSV."""
        filepath = self._get_filepath(ticker)

        # Move index into a column
        df = df.reset_index()

        # Ensure the column is named 'Date'
        df.rename(columns={df.columns[0]: "Date"}, inplace=True)
        df.columns = df.columns.droplevel("Ticker")

        df.to_csv(filepath, index=False)
        logger.info(f"Saved {ticker} to {filepath}")

    def _get_filepath(self, ticker: str) -> Path:
        """Get filepath for ticker."""
        filename = f"{ticker.replace('.', '_')}.csv"
        return self.data_dir / filename


# ---- Data Validator ---- #


class DataValidator:
    """Check data completeness and quality."""

    @staticmethod
    def check(price_data: PriceData, min_rows: int = 100) -> bool:
        """
        Validate price data completeness.

        Args:
            price_data: PriceData object to validate
            min_rows: Minimum required rows

        Returns:
            True if data passes validation
        """
        df = price_data.data

        # Check minimum rows
        if len(df) < min_rows:
            logger.warning(
                f"{price_data.ticker}: Insufficient data ({len(df)} < {min_rows})"
            )
            return False

        # Check for missing values
        missing = df.isnull().sum()
        if missing.any():
            logger.warning(
                f"{price_data.ticker}: Missing values found\n{missing}"
            )
            return False

        # Check for zero/negative prices
        price_cols = ["Open", "High", "Low", "Close"]
        if (df[price_cols] <= 0).any().any():
            logger.warning(
                f"{price_data.ticker}: Zero or negative prices found"
            )
            return False

        # Check high >= low
        bad_high_low = df["High"] < df["Low"]
        if bad_high_low.any().item():
            logger.warning(f"{price_data.ticker}: High < Low detected")
            return False

        logger.info(f"{price_data.ticker}: Validation passed")
        return True

    @staticmethod
    def get_missing_dates(price_data: PriceData) -> List[str]:
        """Identify missing trading days (simple business day check)."""
        df = price_data.data
        date_range = pd.bdate_range(start=df.index[0], end=df.index[-1])
        missing = date_range.difference(df.index)
        return [str(d.date()) for d in missing]


# ---- Return Calculator ---- #


class ReturnCalculator:
    """Compute returns for systematic trading."""

    @staticmethod
    def log_returns(price_data: PriceData) -> pd.Series:
        """
        Calculate log returns from close prices.

        Returns: Series of log returns
        """
        close = price_data.close
        returns = np.log(close / close.shift(1))
        returns.name = f"{price_data.ticker}_log_returns"
        return returns

    @staticmethod
    def percentage_returns(price_data: PriceData) -> pd.Series:
        """
        Calculate percentage returns from close prices.

        Returns: Series of percentage returns
        """
        close = price_data.close
        returns = close.pct_change()
        returns.name = f"{price_data.ticker}_pct_returns"
        return returns

    @staticmethod
    def multi_period_returns(
            price_data: PriceData, periods: int, return_type: str = "log"
    ) -> pd.Series:
        """
        Calculate multi-period returns.

        Args:
            price_data: Price data
            periods: Number of periods
            return_type: 'log' or 'percentage'

        Returns: Series of multi-period returns
        """
        close = price_data.close

        if return_type == "log":
            returns = np.log(close / close.shift(periods))
        else:
            returns = close.pct_change(periods)

        returns.name = f"{price_data.ticker}_{periods}p_{return_type}_returns"
        return returns


# ---- Data Manager (Main Interface) ---- #


class DataManager:
    """
    Main interface for data management in systematic trading.
    Coordinates DataLoader, DataValidator, and ReturnCalculator.
    """

    def __init__(self, data_dir: str = Settings.DATA_DIR):
        self.loader = DataLoader(data_dir)
        self.validator = DataValidator()

    def get_data(
            self,
            ticker: str,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            validate: bool = True,
    ) -> Optional[PriceData]:
        """
        Get price data, downloading if necessary.

        Args:
            ticker: Stock ticker
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            validate: Run validation checks

        Returns: PriceData object or None
        """
        # Try loading from file
        price_data = self.loader.load_csv(ticker)

        # Download if not available
        if price_data is None:
            logger.info(f"No local data for {ticker}, downloading...")
            price_data = self.loader.download(ticker, start_date, end_date)

        if price_data is None:
            return None

        # Apply date filtering
        if start_date or end_date:
            df = price_data.data
            if start_date:
                df = df[df.index >= start_date]
            if end_date:
                df = df[df.index <= end_date]
            price_data = PriceData(ticker=ticker, data=df)

        # Validate if requested
        if validate and not self.validator.check(price_data):
            logger.warning(f"Validation failed for {ticker}")
            return None

        return price_data

    def get_returns(
            self,
            ticker: str,
            return_type: str = "log",
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
    ) -> Optional[pd.Series]:
        """
        Get returns for a ticker.

        Args:
            ticker: Stock ticker
            return_type: 'log' or 'percentage'
            start_date: Start date
            end_date: End date

        Returns: Series of returns or None
        """
        price_data = self.get_data(ticker, start_date, end_date)
        if price_data is None:
            return None

        if return_type == "log":
            return ReturnCalculator.log_returns(price_data)
        else:
            return ReturnCalculator.percentage_returns(price_data)

    def get_close_prices(
            self,
            tickers: List[str],
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Get close prices for multiple tickers as DataFrame.

        Args:
            tickers: List of tickers
            start_date: Start date
            end_date: End date

        Returns: DataFrame with close prices
        """
        close_prices = {}

        for ticker in tickers:
            price_data = self.get_data(
                ticker, start_date, end_date, validate=False
            )
            if price_data is not None:
                close_prices[ticker] = price_data.close

        if not close_prices:
            return pd.DataFrame()

        df = pd.DataFrame(close_prices)
        df = df.ffill()  # Forward fill missing values
        return df

    def get_ticker_correlation(
            self,
            tickers: List[str],
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            return_type: str = "log",
            min_periods: int = 100,
    ) -> pd.DataFrame:
        """
        Calculate correlation matrix between tickers based on returns.

        Args:
            tickers: List of tickers
            start_date: Start date
            end_date: End date
            return_type: 'log' or 'percentage'
            min_periods: Minimum observations required for correlation

        Returns:
            DataFrame correlation matrix (tickers as both index and columns)
        """
        if len(tickers) < 2:
            logger.warning("Need at least 2 tickers for correlation")
            return pd.DataFrame()

        # Get returns for all tickers
        returns_dict = {}
        for ticker in tickers:
            returns = self.get_returns(
                ticker, return_type, start_date, end_date
            )
            if returns is not None:
                if len(returns) >= min_periods:
                    returns_dict[ticker] = returns
                else:
                    logger.warning(
                        f"Insufficient data for {ticker} "
                        f"({len(returns)} < {min_periods})"
                    )
            else:
                logger.warning(f"No data available for {ticker}")

        if len(returns_dict) < 2:
            logger.error(
                "Insufficient tickers with valid data for correlation"
            )
            return pd.DataFrame()

        # Debug: Check what we have
        for ticker, returns in returns_dict.items():
            logger.info(
                f"Debug - {ticker}: type={type(returns)}, len={len(returns) if hasattr(returns, '__len__') else 'N/A'}"
            )

        # Create returns DataFrame
        returns_df = pd.DataFrame(returns_dict)

        # Calculate correlation matrix
        corr_matrix = returns_df.corr(min_periods=min_periods)

        logger.info(
            f"Calculated correlation matrix for {len(returns_dict)} tickers "
            f"({len(returns_df)} observations)"
        )

        return corr_matrix
