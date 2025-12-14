"""
Trader Class - Systematic Trading Framework
Manages the full execution pipeline starting with data management.

Based on Robert Carver's "Systematic Trading"
"""

from typing import List, Optional

import pandas as pd
import polars as pl

from st.data import DataManager, PriceData
from st.strategy import Strategy


class Trader:
    """
    Main trading orchestrator for systematic trading.

    Execution Pipeline:
    1. Data Ingestion & Validation
    2. Volatility Estimation (future)
    3. Forecast Generation (future)
    4. Forecast Combination (future)
    5. Position Sizing (future)
    6. Risk Management & Execution (future)
    """

    def __init__(
            self,
            strategies: List[Strategy] = None,
            data_manager: DataManager = None
    ):
        """
        Initialize Trader.

        Args:
            strategies: List of Strategy objects
            data_manager: DataManager instance (creates new if not provided)
        """
        self.strategies = strategies or []
        self.data_manager = data_manager or DataManager()

        # Data storage
        self.price_data: Optional[PriceData] = None
        self.data: Optional[pl.DataFrame] = None  # Polars DataFrame for strategies
        self.current_ticker: Optional[str] = None

        # Pipeline outputs (to be implemented)
        self.signals: Optional[pl.DataFrame] = None

    # ==========================================
    # STEP 1: DATA INGESTION & VALIDATION
    # ==========================================

    def load_data(
            self,
            ticker: str,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            validate: bool = True,
    ) -> pl.DataFrame:
        """
        Load and validate OHLCV data for a ticker.

        This is Step 1 of the systematic trading pipeline.
        Outputs: OHLCV Data, Log Returns, Percentage Returns

        Args:
            ticker: Stock ticker (e.g., 'AAPL', 'GOOGL')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            validate: Run data validation checks

        Returns:
            Polars DataFrame with OHLCV data
        """
        self.current_ticker = ticker

        # Get price data using DataManager
        print(f"Loading data for {ticker}...")
        self.price_data = self.data_manager.get_data(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            validate=validate
        )

        if self.price_data is None:
            raise ValueError(f"Failed to load data for {ticker}")

        # Convert to Polars for strategy processing
        pandas_df = self.price_data.data.reset_index()
        self.data = pl.from_pandas(pandas_df)

        # Standardize column names (lowercase)
        self.data = self.data.rename({col: col.lower() for col in self.data.columns})

        # Ensure proper date format
        if "date" in self.data.columns:
            try:
                self.data = self.data.with_columns([
                    pl.col("date").cast(pl.Date).alias("date")
                ])
            except:
                pass  # Already in correct format

        # Sort by date
        self.data = self.data.sort("date")

        print(f"✓ Loaded {len(self.data)} rows for {ticker}")
        print(f"  Date range: {self.data['date'][0]} to {self.data['date'][-1]}")
        print(f"  Columns: {self.data.columns}")

        return self.data

    def get_returns(
            self,
            return_type: str = "log"
    ) -> pd.Series:
        """
        Get returns for the loaded data.

        Args:
            return_type: 'log' or 'percentage'

        Returns:
            Series of returns
        """
        if self.price_data is None:
            raise ValueError("No data loaded. Call load_data() first.")

        returns = self.data_manager.get_returns(
            ticker=self.current_ticker,
            return_type=return_type
        )

        if returns is None:
            raise ValueError(f"Failed to calculate returns for {self.current_ticker}")

        return returns

    def get_close_prices(
            self,
            tickers: List[str],
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Get close prices for multiple tickers.

        Useful for portfolio construction and correlation analysis.

        Args:
            tickers: List of ticker symbols
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with close prices for all tickers
        """
        return self.data_manager.get_close_prices(
            tickers=tickers,
            start_date=start_date,
            end_date=end_date
        )

    # ==========================================
    # STRATEGY MANAGEMENT
    # ==========================================

    def add_strategy(self, strategy: Strategy):
        """Add a trading strategy."""
        self.strategies.append(strategy)
        print(f"✓ Added strategy: {strategy.name}")

    def prepare_data(self) -> pl.DataFrame:
        """
        Prepare data by adding all indicators from strategies.

        This connects to Step 3 (Forecast Generation) of the pipeline.

        Returns:
            DataFrame with all indicators added
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")

        df = self.data.clone()

        print("\nPreparing data with indicators...")
        for strategy in self.strategies:
            print(f"  - Adding indicators for: {strategy.name}")
            df = strategy.add_indicators(df)

        print(f"✓ Data preparation complete")
        print(f"  Total columns: {len(df.columns)}")

        self.data = df
        return df

    # ==========================================
    # FUTURE PIPELINE STEPS (Placeholders)
    # ==========================================

    # Step 2: Volatility Estimation
    # - Calculate EWMA volatility
    # - Estimate annual volatility
    # - Generate volatility forecasts

    # Step 3: Forecast Generation
    # - Apply trading rules (EWMAC, carry, mean reversion)
    # - Scale forecasts to -20 to +20 range

    # Step 4: Forecast Combination
    # - Combine multiple forecasts
    # - Calculate diversification multiplier

    # Step 5: Position Sizing
    # - Convert forecasts to positions
    # - Apply volatility targeting
    # - Calculate capital allocation

    # Step 6: Risk Management & Execution
    # - Apply risk limits
    # - Calculate portfolio metrics
    # - Generate trade orders

    # ==========================================
    # UTILITIES
    # ==========================================

    def get_data_summary(self) -> dict:
        """Get summary of loaded data."""
        if self.data is None:
            return {"status": "No data loaded"}

        return {
            "ticker": self.current_ticker,
            "rows": len(self.data),
            "start_date": str(self.data['date'][0]),
            "end_date": str(self.data['date'][-1]),
            "columns": self.data.columns,
        }

    def __repr__(self):
        ticker_info = f", ticker={self.current_ticker}" if self.current_ticker else ""
        strategies_info = f"strategies={len(self.strategies)}"
        data_info = f"data_loaded={self.data is not None}"
        return f"Trader({strategies_info}, {data_info}{ticker_info})"
