from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yfinance as yf
from pydantic import BaseModel

from st.config.settings import Settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


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
        if self.save_path is None:
            self.save_path = Path(Settings.DATA_DIR) / f"{self.ticker.replace('.', '_')}.csv"
        else:
            self.save_path = Path(self.save_path)
        self.save_path.parent.mkdir(parents=True, exist_ok=True)

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
        df.to_csv(self.save_path, index=False)
        logger.info(f"Creation completed: {self}")

    def __str__(self):
        return (f"PriceData(ticker={self.ticker}, "
                f"start_date={self.start_date}, "
                f"end_date={self.end_date}, "
                f"interval={self.interval}, "
                f"shape={self.data.shape})"
                )

    __repr__ = __str__


class ReturnsDTO(BaseModel):
    """
    Returns data transfer object.

    Transfers calculated returns between layers.
    """
    price_data: PriceDataDTO  # Price Data
    returns: pd.Series = None  # Calculated returns
    cumulative_returns: pd.Series = None  # Calculated cumulative returns
    return_type: str = 'log'  # 'log' or 'percentage'
    periods: int = 1  # Period length (1 = daily)
    skew: float = None  # Skewness of returns

    class Config:
        arbitrary_types_allowed = True

    def model_post_init(self, context: Any, /) -> None:
        self.price_data = deepcopy(self.price_data)
        data = self.price_data.data

        if self.return_type == 'log':
            # Calculate log returns: ln(P_t / P_t-n)
            self.returns = pd.Series(np.log(data['Close'] / data['Close'].shift(self.periods)))
        elif self.return_type == 'percentage':
            # Calculate percentage returns: (P_t - P_t-n) / P_t-n
            self.returns = data['Close'].pct_change(periods=self.periods)
        else:
            raise ValueError(f"Invalid return_type: {self.return_type}. Must be 'log' or 'percentage'")

        # cumulative returns
        self.cumulative_returns = (self.returns + 1).cumprod() - 1

        # Calculate skewness
        self.skew = self.returns.skew()

        logger.info(f"Creation completed: {self}")

    def __str__(self):
        return (f"Returns(ticker={self.price_data.ticker}, return_type={self.return_type}, "
                f"shape={self.returns.shape}, skew={self.skew:.4f})")

    __repr__ = __str__


class CorrelationDTO(BaseModel):
    """
    Correlation analysis transfer object.

    Transfers correlation matrices between layers.
    """
    price_datas: list[PriceDataDTO] = None  # list of PriceDataDTOs
    correlation_matrix: pd.DataFrame = None  # Pairwise correlations
    return_type: str = 'log'  # 'log' or 'percentage'
    observation_count: int = None  # Number of observations used

    class Config:
        arbitrary_types_allowed = True

    def model_post_init(self, context: Any, /) -> None:
        """
        Calculates returns, correlation matrix, and metadata after object creation.
        """

        self.price_datas = deepcopy(self.price_datas)

        # calculate returns
        returns_dict = {}

        for pdata in self.price_datas:
            df = pdata.data
            if df is None or df.empty:
                raise ValueError(
                    f"No data for ticker: {pdata.ticker}. Provide data or removing it from the tickers list.")

            # Calculate returns based on return_type
            returns_dto = ReturnsDTO(price_data=pdata, return_type=self.return_type)
            returns_dict[pdata.ticker] = returns_dto.returns

        # Create returns DataFrame
        returns_df = pd.DataFrame(returns_dict)

        # Calculate correlation matrix
        if len(returns_df) > 1:
            self.correlation_matrix = returns_df.corr()

        # Set observation count
        self.observation_count = len(returns_df)

        logger.info(f"Creation completed: {self}")

    def __str__(self):
        tickers = [i.ticker for i in self.price_datas]
        return (f"Correlation(tickers={tickers}, "
                f"total_observations={self.observation_count})")

    __repr__ = __str__
