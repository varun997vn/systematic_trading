from datetime import datetime
from pathlib import Path
from typing import Optional, Any

import numpy as np
import pandas as pd
import yfinance as yf
from pydantic import BaseModel

from st.config.settings import Settings


class PriceDataDTO(BaseModel):
    """
    Price data transfer object.

    Transfers OHLCV data between layers without validation logic.
    """
    ticker: str  # Stock symbol (e.g., 'AAPL', 'BTC-USD')
    data: pd.DataFrame = None  # OHLCV DataFrame with DatetimeIndex
    start_date: datetime = None  # First observation date
    end_date: datetime = None  # Last observation date
    interval: str = "1d"  # yfinance interval: '1m','5m','15m','30m','1h','1d','1wk','1mo'
    save_path: Path = None  # save path for data

    class Config:
        arbitrary_types_allowed = True

    def model_post_init(self, context: Any, /) -> None:
        # save path
        save_path = Path(Settings.DATA_DIR)
        save_path.mkdir(parents=True, exist_ok=True)
        save_path = save_path / f"{self.ticker.replace('.', '_')}.csv"
        self.save_path = save_path

        # data
        self.start_date = self.start_date or Settings.DATA_START_DATE
        self.end_date = self.end_date or Settings.DATA_END_DATE

        df = yf.download(
            self.ticker, start=self.start_date, end=self.end_date, auto_adjust=True, progress=False
        )

        df = df[["Open", "High", "Low", "Close", "Volume"]]
        df = df.reset_index()
        df.rename(columns={df.columns[0]: "Date"}, inplace=True)
        df.columns = df.columns.droplevel("Ticker")
        self.data = df

        # save the data
        df.to_csv(save_path, index=False)


class ReturnsDTO(BaseModel):
    """
    Returns data transfer object.

    Transfers calculated returns between layers.
    """
    ticker: str  # Stock symbol
    data: pd.DataFrame  # OHLCV data
    returns: pd.Series = None  # Calculated returns
    return_type: str = 'log'  # 'log' or 'percentage'
    periods: int = 1  # Period length (1 = daily)

    class Config:
        arbitrary_types_allowed = True

    def model_post_init(self, context: Any, /) -> None:

        if self.return_type == 'log':
            # Calculate log returns: ln(P_t / P_t-n)
            self.returns = pd.Series(np.log(self.data['Close'] / self.data['Close'].shift(self.periods)))
        elif self.return_type == 'percentage':
            # Calculate percentage returns: (P_t - P_t-n) / P_t-n
            self.returns = self.data['Close'].pct_change(periods=self.periods)
        else:
            raise ValueError(f"Invalid return_type: {self.return_type}. Must be 'log' or 'percentage'")

        # Remove NaN values created by the shift/pct_change operation
        # Keep the index aligned with the original data
        self.returns = self.returns.fillna(0) if len(self.returns) > 0 else self.returns


class CorrelationDTO(BaseModel):
    """
    Correlation analysis transfer object.

    Transfers correlation matrices between layers.
    """
    tickers: list[str]  # Analyzed tickers
    data: dict[str, pd.DataFrame]  # ticker -> OHLCV data
    correlation_matrix: pd.DataFrame = None  # Pairwise correlations
    return_type: str = 'log'  # 'log' or 'percentage'
    observation_count: int = None  # Number of observations used
    start_date: Optional[datetime] = None  # Analysis start date
    end_date: Optional[datetime] = None  # Analysis end date

    class Config:
        arbitrary_types_allowed = True

    def model_post_init(self, context: Any, /) -> None:
        """
        Calculates returns, correlation matrix, and metadata after object creation.
        """

        # calculate returns
        returns_dict = {}

        for ticker, df in self.data.items():
            if df is None or df.empty:
                raise ValueError(
                    f"No data for ticker: {ticker}. Consider providing data or removing it from the tickers list.")

            # Calculate returns based on return_type
            returns_dto = ReturnsDTO(ticker=ticker, data=df, return_type=self.return_type)
            returns_dict[ticker] = returns_dto.returns

        # Create returns DataFrame
        returns_df = pd.DataFrame(returns_dict)

        # Calculate correlation matrix
        if len(returns_df) > 1:
            self.correlation_matrix = returns_df.corr()

        # Set observation count
        self.observation_count = len(returns_df)

        # Set date range
        if self.start_date is None and not returns_df.empty:
            self.start_date = returns_df.index.min()

        if self.end_date is None and not returns_df.empty:
            self.end_date = returns_df.index.max()
