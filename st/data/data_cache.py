from datetime import datetime, timedelta
from typing import Dict, Optional

import pandas as pd
from pydantic import BaseModel, Field

from utils.logger import setup_logger

logger = setup_logger(__name__)


# ==========================================
# Data Cache
# ==========================================

class DataCache(BaseModel):
    """Cache for market data with expiration."""
    cache: Dict[str, pd.DataFrame] = Field(default_factory=dict)
    cache_timestamps: Dict[str, datetime] = Field(default_factory=dict)
    cache_ttl_minutes: int = Field(default=60, description="Cache time-to-live in minutes")

    model_config = {"arbitrary_types_allowed": True}

    def get(self, ticker: str) -> Optional[pd.DataFrame]:
        """Get cached data if not expired."""
        if ticker not in self.cache:
            return None

        timestamp = self.cache_timestamps.get(ticker)
        if timestamp is None:
            return None

        if datetime.now() - timestamp > timedelta(minutes=self.cache_ttl_minutes):
            logger.debug(f"Cache expired for {ticker}")
            del self.cache[ticker]
            del self.cache_timestamps[ticker]
            return None

        return self.cache[ticker]

    def set(self, ticker: str, data: pd.DataFrame) -> None:
        """Cache data with current timestamp."""
        self.cache[ticker] = data
        self.cache_timestamps[ticker] = datetime.now()
        logger.debug(f"Cached data for {ticker}")

    def clear(self, ticker: Optional[str] = None) -> None:
        """Clear cache for specific ticker or all."""
        if ticker:
            self.cache.pop(ticker, None)
            self.cache_timestamps.pop(ticker, None)
        else:
            self.cache.clear()
            self.cache_timestamps.clear()
        logger.info(f"Cache cleared for {ticker if ticker else 'all tickers'}")
