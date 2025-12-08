from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set, Tuple
from pathlib import Path
from abc import ABC, abstractmethod

import pandas as pd
import numpy as np
from pydantic import BaseModel, Field, field_validator, model_validator

from st.config.settings import Settings
from .portfolio import TickerCollection
from utils.logger import setup_logger

logger = setup_logger(__name__)


# ==========================================
# Universe
# ==========================================

class Universe(TickerCollection):
    """
    Trading universe configuration and management.
    Defines the set of stocks available for trading.
    """
    sectors: Optional[List[str]] = Field(None, description="Sector filters")
    min_volume: Optional[float] = Field(None, description="Minimum average daily volume")
    min_price: Optional[float] = Field(None, description="Minimum price filter")
    max_price: Optional[float] = Field(None, description="Maximum price filter")
    metadata: Dict[str, Dict] = Field(default_factory=dict, description="Additional ticker metadata")

    def set_tickers(self, tickers: List[str]) -> None:
        """Set the complete list of tickers."""
        self.tickers = [t.upper() for t in tickers]
        logger.info(f"Universe set with {len(self.tickers)} tickers")

    def add_tickers(self, tickers: List[str]) -> None:
        """Add multiple tickers at once."""
        for ticker in tickers:
            self.add_ticker(ticker)

    def remove_tickers(self, tickers: List[str]) -> None:
        """Remove multiple tickers at once."""
        for ticker in tickers:
            self.remove_ticker(ticker)

    def filter_by_sector(self, sectors: List[str]) -> List[str]:
        """
        Filter tickers by sector.
        Requires metadata to be populated with sector information.
        """
        if not self.metadata:
            logger.warning("No metadata available for sector filtering")
            return []

        sectors_upper = [s.upper() for s in sectors]
        filtered = [
            ticker for ticker in self.tickers
            if self.metadata.get(ticker, {}).get('sector', '').upper() in sectors_upper
        ]

        logger.info(f"Filtered to {len(filtered)} tickers in sectors {sectors}")
        return filtered

    def filter_by_price(
            self,
            min_price: Optional[float] = None,
            max_price: Optional[float] = None
    ) -> List[str]:
        """
        Filter tickers by price range.
        Requires metadata to be populated with price information.
        """
        if not self.metadata:
            logger.warning("No metadata available for price filtering")
            return []

        min_p = min_price if min_price is not None else self.min_price
        max_p = max_price if max_price is not None else self.max_price

        filtered = []
        for ticker in self.tickers:
            price = self.metadata.get(ticker, {}).get('price')
            if price is None:
                continue

            if min_p is not None and price < min_p:
                continue
            if max_p is not None and price > max_p:
                continue

            filtered.append(ticker)

        logger.info(f"Filtered to {len(filtered)} tickers by price range")
        return filtered

    def filter_by_volume(self, min_volume: Optional[float] = None) -> List[str]:
        """
        Filter tickers by minimum volume.
        Requires metadata to be populated with volume information.
        """
        if not self.metadata:
            logger.warning("No metadata available for volume filtering")
            return []

        min_vol = min_volume if min_volume is not None else self.min_volume
        if min_vol is None:
            return self.tickers.copy()

        filtered = [
            ticker for ticker in self.tickers
            if self.metadata.get(ticker, {}).get('volume', 0) >= min_vol
        ]

        logger.info(f"Filtered to {len(filtered)} tickers by volume")
        return filtered

    def apply_filters(
            self,
            sectors: Optional[List[str]] = None,
            min_price: Optional[float] = None,
            max_price: Optional[float] = None,
            min_volume: Optional[float] = None
    ) -> List[str]:
        """Apply multiple filters and return filtered ticker list."""
        filtered = self.tickers.copy()

        if sectors:
            filtered = [t for t in filtered if t in self.filter_by_sector(sectors)]

        if min_price is not None or max_price is not None:
            price_filtered = self.filter_by_price(min_price, max_price)
            filtered = [t for t in filtered if t in price_filtered]

        if min_volume is not None:
            volume_filtered = self.filter_by_volume(min_volume)
            filtered = [t for t in filtered if t in volume_filtered]

        logger.info(f"Applied filters, {len(filtered)} tickers remaining")
        return filtered

    def set_metadata(self, ticker: str, metadata: Dict) -> None:
        """Set metadata for a specific ticker."""
        ticker = ticker.upper()
        self.metadata[ticker] = metadata

    def update_metadata(self, metadata_dict: Dict[str, Dict]) -> None:
        """Update metadata for multiple tickers."""
        for ticker, data in metadata_dict.items():
            self.set_metadata(ticker, data)

    def get_metadata(self, ticker: str) -> Optional[Dict]:
        """Get metadata for a specific ticker."""
        return self.metadata.get(ticker.upper())

    def get_summary(self) -> Dict:
        """Get universe summary."""
        summary = {
            "num_tickers": len(self.tickers),
            "tickers": self.tickers.copy(),
            "sectors": self.sectors,
            "filters": {
                "min_volume": self.min_volume,
                "min_price": self.min_price,
                "max_price": self.max_price
            },
            "has_metadata": len(self.metadata) > 0,
            "metadata_count": len(self.metadata)
        }
        return summary

    def to_dataframe(self) -> pd.DataFrame:
        """Convert universe metadata to DataFrame."""
        if not self.metadata:
            return pd.DataFrame({"ticker": self.tickers})

        data = []
        for ticker in self.tickers:
            row = {"ticker": ticker}
            if ticker in self.metadata:
                row.update(self.metadata[ticker])
            data.append(row)

        return pd.DataFrame(data)

    def __repr__(self) -> str:
        """String representation."""
        return f"Universe(tickers={len(self.tickers)}, sectors={self.sectors})"
