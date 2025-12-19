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
            self.ticker, start=self.start_date, end=self.end_date,
            auto_adjust=True, progress=False
        )

        if df.empty:
            raise ValueError(f"No data downloaded for {self.ticker}")

        # Handle multi-index columns from yfinance
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel('Ticker')

        df = df[["Open", "High", "Low", "Close", "Volume"]]
        df = df.reset_index()
        df.rename(columns={df.columns[0]: "Date"}, inplace=True)

        # Ensure no NaN in price data
        if df[['Open', 'High', 'Low', 'Close']].isna().any().any():
            logger.warning(f"{self.ticker}: Price data contains NaN values, forward-filling...")
            df[['Open', 'High', 'Low', 'Close']] = df[['Open', 'High', 'Low', 'Close']].fillna(method='ffill')

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

    IMPORTANT: First 'periods' observations will be NaN - this is correct!
    Downstream code should handle NaN appropriately (usually fillna(0) for forecasts).
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
        # Don't deep copy - let Pydantic handle it
        data = self.price_data.data

        if self.return_type == 'log':
            # Calculate log returns: ln(P_t / P_t-n)
            self.returns = pd.Series(
                np.log(data['Close'] / data['Close'].shift(self.periods)),
                index=data.index
            )
        elif self.return_type == 'percentage':
            # Calculate percentage returns: (P_t - P_t-n) / P_t-n
            self.returns = data['Close'].pct_change(periods=self.periods)
        else:
            raise ValueError(
                f"Invalid return_type: {self.return_type}. "
                "Must be 'log' or 'percentage'"
            )

        # DON'T fill NaN with 0 - let downstream handle it
        # The first 'periods' observations will be NaN, which is correct

        # Calculate cumulative returns (handle NaN properly)
        self.cumulative_returns = (1 + self.returns.fillna(0)).cumprod() - 1

        # Calculate skewness (excluding NaN)
        self.skew = self.returns.skew()

        logger.info(f"Creation completed: {self}")

    def __str__(self):
        non_nan_count = self.returns.notna().sum()
        return (
            f"Returns(ticker={self.price_data.ticker}, "
            f"return_type={self.return_type}, "
            f"shape={self.returns.shape}, "
            f"non_nan={non_nan_count}, "
            f"skew={self.skew:.4f})"
        )

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

        # Don't deep copy - unnecessary
        # self.price_datas = deepcopy(self.price_datas)

        # calculate returns
        returns_dict = {}

        for pdata in self.price_datas:
            df = pdata.data
            if df is None or df.empty:
                raise ValueError(
                    f"No data for ticker: {pdata.ticker}. "
                    "Provide data or remove it from the tickers list."
                )

            # Calculate returns based on return_type
            returns_dto = ReturnsDTO(price_data=pdata, return_type=self.return_type)
            returns_dict[pdata.ticker] = returns_dto.returns

        # Create returns DataFrame
        returns_df = pd.DataFrame(returns_dict)

        # Drop rows with ANY NaN to ensure clean correlation
        returns_df_clean = returns_df.dropna()

        if len(returns_df_clean) < 30:
            logger.warning(
                f"Only {len(returns_df_clean)} observations for correlation after "
                "dropping NaN. Consider longer data history."
            )

        # Calculate correlation matrix
        if len(returns_df_clean) > 1:
            self.correlation_matrix = returns_df_clean.corr()
        else:
            raise ValueError("Need at least 2 observations for correlation")

        # Set observation count
        self.observation_count = len(returns_df_clean)

        logger.info(f"Creation completed: {self}")

    def __str__(self):
        tickers = [i.ticker for i in self.price_datas]
        return (f"Correlation(tickers={tickers}, "
                f"total_observations={self.observation_count})")

    __repr__ = __str__
