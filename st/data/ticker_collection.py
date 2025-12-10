from abc import ABC, abstractmethod
from typing import List, Dict

from pydantic import BaseModel, Field, field_validator

from utils.logger import setup_logger

logger = setup_logger(__name__)


# ==========================================
# Base Classes
# ==========================================

class TickerCollection(BaseModel, ABC):
    """
    Abstract base class for collections of tickers (Universe and Portfolio).
    Provides common functionality for managing ticker lists.
    """
    tickers: List[str] = Field(default_factory=list, description="List of stock tickers")

    model_config = {"arbitrary_types_allowed": True}

    @field_validator("tickers")
    @classmethod
    def validate_tickers(cls, v):
        """Ensure tickers are uppercase and unique."""
        return list(set(ticker.upper() for ticker in v))

    def add_ticker(self, ticker: str) -> None:
        """Add a ticker to the collection."""
        ticker = ticker.upper()
        if ticker not in self.tickers:
            self.tickers.append(ticker)
            logger.info(f"Added {ticker} to {self.__class__.__name__}")

    def remove_ticker(self, ticker: str) -> None:
        """Remove a ticker from the collection."""
        ticker = ticker.upper()
        if ticker in self.tickers:
            self.tickers.remove(ticker)
            logger.info(f"Removed {ticker} from {self.__class__.__name__}")

    def has_ticker(self, ticker: str) -> bool:
        """Check if ticker exists in collection."""
        return ticker.upper() in self.tickers

    def get_tickers(self) -> List[str]:
        """Get all tickers in the collection."""
        return self.tickers.copy()

    def clear(self) -> None:
        """Clear all tickers."""
        self.tickers.clear()
        logger.info(f"Cleared all tickers from {self.__class__.__name__}")

    def __len__(self) -> int:
        """Number of tickers in collection."""
        return len(self.tickers)

    def __contains__(self, ticker: str) -> bool:
        """Support 'ticker in collection' syntax."""
        return self.has_ticker(ticker)

    @abstractmethod
    def get_summary(self) -> Dict:
        """Get summary information about the collection."""
        pass
