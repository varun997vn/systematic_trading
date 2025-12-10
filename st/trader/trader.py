"""
Trader class for managing the complete trading workflow with enhanced data management.
Reorganized with proper class hierarchy for Portfolio and Universe.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
from pydantic import BaseModel, Field

from st.config.settings import Settings
from st.data import (
    DataCache,
    DataManager,
    DownloadRequest,
    Portfolio,
    StockInfo,
    Universe,
)
from utils.logger import setup_logger

logger = setup_logger(__name__)


# ==========================================
# Main Trader Class
# ==========================================


class Trader(BaseModel):
    """
    Main trader class orchestrating the complete trading workflow.
    Manages data, universe, portfolio, and trading operations.
    """

    # Core components
    data_manager: DataManager = Field(default_factory=DataManager)
    universe: Universe = Field(default_factory=Universe)
    portfolio: Portfolio = Field(default_factory=Portfolio)

    # Data management
    data_cache: DataCache = Field(default_factory=DataCache)
    stock_info_cache: Dict[str, StockInfo] = Field(default_factory=dict)

    # Configuration
    start_date: Optional[str] = Field(None, description="Default start date for data")
    end_date: Optional[str] = Field(None, description="Default end date for data")
    auto_download: bool = Field(True, description="Auto-download missing data")

    model_config = {"arbitrary_types_allowed": True}

    # ==========================================
    # Initialization & Setup
    # ==========================================

    def __init__(self, **data):
        """Initialize trader with optional universe and portfolio."""
        super().__init__(**data)
        if not self.start_date:
            self.start_date = Settings.DATA_START_DATE
        if not self.end_date:
            self.end_date = Settings.DATA_END_DATE
        logger.info("Trader initialized")

    @classmethod
    def with_universe(cls, tickers: List[str], **kwargs) -> "Trader":
        """Create trader with a predefined universe."""
        universe = Universe(tickers=tickers)
        return cls(universe=universe, **kwargs)

    @classmethod
    def with_portfolio(
        cls, positions: Dict[str, Tuple[float, float]], cash: float = 100000.0, **kwargs
    ) -> "Trader":
        """
        Create trader with existing portfolio.

        Args:
            positions: Dict of {ticker: (quantity, avg_price)}
            cash: Available cash
        """
        portfolio = Portfolio(cash=cash, initial_cash=cash)
        for ticker, (quantity, price) in positions.items():
            portfolio.add_position(ticker, quantity, price, update_cash=False)

        return cls(portfolio=portfolio, **kwargs)

    # ==========================================
    # Universe Management (delegates to Universe)
    # ==========================================

    def set_universe(self, tickers: List[str]) -> None:
        """Set the trading universe."""
        self.universe.set_tickers(tickers)

    def add_to_universe(self, ticker: str) -> None:
        """Add ticker to universe."""
        self.universe.add_ticker(ticker)

    def remove_from_universe(self, ticker: str) -> None:
        """Remove ticker from universe."""
        self.universe.remove_ticker(ticker)

    def get_universe_tickers(self) -> List[str]:
        """Get list of all tickers in universe."""
        return self.universe.get_tickers()

    def get_universe_summary(self) -> Dict:
        """Get universe summary."""
        return self.universe.get_summary()

    # ==========================================
    # Portfolio Management (delegates to Portfolio)
    # ==========================================

    def buy(self, ticker: str, quantity: float, price: Optional[float] = None) -> None:
        """
        Buy shares of a stock.

        Args:
            ticker: Stock ticker
            quantity: Number of shares to buy
            price: Purchase price (if None, uses latest price)
        """
        ticker = ticker.upper()

        if price is None:
            price = self.get_latest_price(ticker)
            if price is None:
                raise ValueError(f"No price available for {ticker}")

        self.portfolio.add_position(ticker, quantity, price, update_cash=True)

    def sell(
        self,
        ticker: str,
        quantity: Optional[float] = None,
        price: Optional[float] = None,
    ) -> Optional[float]:
        """
        Sell shares of a stock.

        Args:
            ticker: Stock ticker
            quantity: Number of shares to sell (None = sell all)
            price: Sale price (if None, uses latest price)

        Returns:
            Realized P&L from the sale
        """
        ticker = ticker.upper()

        if price is None:
            price = self.get_latest_price(ticker)
            if price is None:
                raise ValueError(f"No price available for {ticker}")

        return self.portfolio.remove_position(ticker, quantity, price, update_cash=True)

    def get_portfolio_summary(self) -> Dict:
        """Get comprehensive portfolio summary."""
        # Update prices first
        self.update_portfolio_prices()
        return self.portfolio.get_summary()

    def get_portfolio_value(self) -> float:
        """Get total portfolio value."""
        self.update_portfolio_prices()
        return self.portfolio.total_value

    def update_portfolio_prices(self) -> None:
        """Update current prices for all portfolio positions."""
        if not self.portfolio.positions:
            return

        tickers = self.portfolio.get_tickers()
        prices = self.get_latest_prices(tickers)
        self.portfolio.update_prices(prices)

    # ==========================================
    # Data Retrieval & Management
    # ==========================================

    def get_data(
        self,
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        use_cache: bool = True,
    ) -> pd.DataFrame:
        """
        Get historical data for a ticker with caching support.
        """
        ticker = ticker.upper()

        # Check cache first
        if use_cache:
            cached_data = self.data_cache.get(ticker)
            if cached_data is not None:
                logger.debug(f"Using cached data for {ticker}")
                return cached_data

        # Try loading from disk
        df = self.data_manager.load_data(ticker)

        # Download if missing and auto_download is enabled
        if df.empty and self.auto_download:
            logger.info(f"Downloading data for {ticker}")
            req = DownloadRequest(
                ticker=ticker,
                start_date=start_date or self.start_date,
                end_date=end_date or self.end_date,
                save=True,
            )
            df = self.data_manager.download_stock_data(req)

        # # Filter by date range if specified
        # if not df.empty:
        #     start = start_date or self.start_date
        #     end = end_date or self.end_date
        #     if start or end:
        #         df = self.data_manager.filter_by_date(df, start, end)

        # Cache the data
        if use_cache and not df.empty:
            self.data_cache.set(ticker, df)

        return df

    def get_universe_data(self) -> Dict[str, pd.DataFrame]:
        """Get data for all tickers in universe."""
        data = {}
        for ticker in self.universe.tickers:
            df = self.get_data(ticker)
            if not df.empty:
                data[ticker] = df
        return data

    def get_portfolio_data(self) -> Dict[str, pd.DataFrame]:
        """Get data for all tickers in portfolio."""
        data = {}
        for ticker in self.portfolio.get_tickers():
            df = self.get_data(ticker)
            if not df.empty:
                data[ticker] = df
        return data

    def get_close_prices(self, tickers: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Get close prices for multiple tickers as a DataFrame.
        """
        if tickers is None:
            tickers = self.universe.tickers

        prices = {}
        for ticker in tickers:
            df = self.get_data(ticker)
            if not df.empty and "Close" in df.columns:
                prices[ticker] = df["Close"]

        if not prices:
            return pd.DataFrame()

        return pd.DataFrame(prices)

    def get_latest_price(self, ticker: str) -> Optional[float]:
        """Get the most recent price for a ticker."""
        df = self.get_data(ticker)
        if df.empty or "Close" not in df.columns:
            return None
        return float(df["Close"].iloc[-1])

    def get_latest_prices(self, tickers: List[str]) -> Dict[str, float]:
        """Get latest prices for multiple tickers."""
        prices = {}
        for ticker in tickers:
            price = self.get_latest_price(ticker)
            if price is not None:
                prices[ticker] = price
        return prices

    # ==========================================
    # Stock Information
    # ==========================================

    def get_stock_info(
        self, ticker: str, use_cache: bool = True
    ) -> Optional[StockInfo]:
        """Get stock information with caching."""
        ticker = ticker.upper()

        if use_cache and ticker in self.stock_info_cache:
            return self.stock_info_cache[ticker]

        info = self.data_manager.get_stock_info(ticker)
        if info and use_cache:
            self.stock_info_cache[ticker] = info

        return info

    def get_universe_info(self) -> Dict[str, StockInfo]:
        """Get information for all stocks in universe."""
        info_dict = {}
        for ticker in self.universe.tickers:
            info = self.get_stock_info(ticker)
            if info:
                info_dict[ticker] = info
        return info_dict

    def update_universe_metadata(self) -> None:
        """Update universe metadata with stock info."""
        info_dict = self.get_universe_info()
        metadata = {}

        for ticker, info in info_dict.items():
            metadata[ticker] = {
                "sector": info.sector,
                "industry": info.industry,
                "market_cap": info.market_cap,
                "price": info.current_price,
                "volume": info.average_volume,
            }

        self.universe.update_metadata(metadata)
        logger.info(f"Updated metadata for {len(metadata)} tickers")

    # ==========================================
    # Data Quality & Validation
    # ==========================================

    def check_data_quality(self, ticker: str) -> Dict[str, any]:
        """
        Check data quality for a ticker.
        Returns dict with quality metrics.
        """
        df = self.get_data(ticker)

        if df.empty:
            return {"status": "no_data", "ticker": ticker}

        quality = {
            "ticker": ticker,
            "status": "ok",
            "rows": len(df),
            "start_date": str(df.index[0]),
            "end_date": str(df.index[-1]),
            "missing_values": df.isnull().sum().to_dict(),
            "zero_volume_days": int((df["Volume"] == 0).sum()),
            "price_anomalies": 0,
        }

        # Check for price anomalies (e.g., huge gaps)
        if "Close" in df.columns:
            returns = df["Close"].pct_change()
            quality["price_anomalies"] = int(
                (abs(returns) > 0.5).sum()
            )  # >50% daily change

        return quality

    def validate_universe_data(self) -> Dict[str, Dict]:
        """Validate data quality for entire universe."""
        validation = {}
        for ticker in self.universe.tickers:
            validation[ticker] = self.check_data_quality(ticker)
        return validation

    def validate_portfolio_data(self) -> Dict[str, Dict]:
        """Validate data quality for portfolio tickers."""
        validation = {}
        for ticker in self.portfolio.get_tickers():
            validation[ticker] = self.check_data_quality(ticker)
        return validation

    # ==========================================
    # Data Analysis Helpers
    # ==========================================

    def calculate_returns(
        self, tickers: Optional[List[str]] = None, period: str = "1D"
    ) -> pd.DataFrame:
        """
        Calculate returns for tickers.
        period: '1D', '1W', '1M', etc.
        """
        prices = self.get_close_prices(tickers)
        if prices.empty:
            return pd.DataFrame()

        returns: pd.DataFrame = prices.pct_change()
        return returns

    def calculate_correlation_matrix(
        self, tickers: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """Calculate correlation matrix of returns."""
        returns = self.calculate_returns(tickers)
        if returns.empty:
            return pd.DataFrame()

        return returns.corr()

    def get_data_summary(self, ticker: str) -> Dict:
        """Get summary statistics for a ticker."""
        df = self.get_data(ticker)

        if df.empty:
            return {}

        return {
            "ticker": ticker,
            "start": str(df.index[0]),
            "end": str(df.index[-1]),
            "rows": len(df),
            "close_mean": float(df["Close"].mean()),
            "close_std": float(df["Close"].std()),
            "volume_mean": float(df["Volume"].mean()),
            "high": float(df["High"].max()),
            "low": float(df["Low"].min()),
        }

    # ==========================================
    # Export & Reporting
    # ==========================================

    def export_universe_data(self, filename: Optional[str] = None) -> str:
        """Export all universe data to a single file."""
        data = self.get_universe_data()

        if not data:
            logger.warning("No data to export")
            return ""

        # Combine all close prices
        combined = pd.DataFrame({ticker: df["Close"] for ticker, df in data.items()})

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"universe_data_{timestamp}.csv"

        filepath = Path(self.data_manager.data_dir) / filename
        combined.to_csv(filepath)

        logger.info(f"Exported universe data to {filepath}")
        return str(filepath)

    def export_portfolio_data(self, filename: Optional[str] = None) -> str:
        """Export portfolio positions to CSV."""
        df = self.portfolio.to_dataframe()

        if df.empty:
            logger.warning("No portfolio data to export")
            return ""

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"portfolio_{timestamp}.csv"

        filepath = Path(self.data_manager.data_dir) / filename
        df.to_csv(filepath, index=False)

        logger.info(f"Exported portfolio to {filepath}")
        return str(filepath)

    def generate_report(self) -> str:
        """Generate a comprehensive trading report."""
        report_lines = [
            "=" * 60,
            "TRADING REPORT",
            "=" * 60,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "UNIVERSE:",
            "-" * 60,
            f"  Size: {len(self.universe)} tickers",
            f"  Tickers: {', '.join(self.universe.tickers[:10])}{'...' if len(self.universe) > 10 else ''}",
            "",
            "PORTFOLIO:",
            "-" * 60,
        ]

        # Add portfolio summary
        summary = self.get_portfolio_summary()
        report_lines.extend(
            [
                f"  Total Value: ${summary['total_value']:,.2f}",
                f"  Cash: ${summary['cash']:,.2f} ({summary['cash_weight']:.1f}%)",
                f"  Positions Value: ${summary['positions_value']:,.2f}",
                f"  Positions: {summary['num_positions']}",
                f"  Total Return: {self.portfolio.total_return:.2f}%",
                f"  Unrealized P&L: ${summary['total_unrealized_pnl']:,.2f}",
                "",
            ]
        )

        # Add position details
        if summary["positions"]:
            report_lines.append("POSITIONS:")
            report_lines.append("-" * 60)
            for ticker, pos in summary["positions"].items():
                report_lines.append(
                    f"  {ticker}: {pos['quantity']:.0f} shares @ ${pos['avg_entry']:.2f} "
                    f"| Current: ${pos['current_price']:.2f} "
                    f"| P&L: ${pos['unrealized_pnl']:.2f} ({pos['unrealized_pnl_pct']:.1f}%) "
                    f"| Weight: {pos['weight']:.1f}%"
                )

        # Add data quality section
        report_lines.extend(
            [
                "",
                "DATA CACHE:",
                "-" * 60,
                f"  Cached tickers: {len(self.data_cache.cache)}",
                f"  Cache TTL: {self.data_cache.cache_ttl_minutes} minutes",
            ]
        )

        return "\n".join(report_lines)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"Trader(universe={len(self.universe)} tickers, "
            f"portfolio={len(self.portfolio)} positions, "
            f"value=${self.portfolio.total_value:,.2f})"
        )
