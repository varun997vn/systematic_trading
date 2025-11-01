"""
Centralized configuration management for the systematic trading system.
Based on Robert Carver's principles for US equity markets.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """
    Configuration settings for the systematic trading system.

    Follows Carver's principles:
    - Volatility targeting for position sizing
    - Transaction cost awareness
    - Risk management parameters
    """

    # Project paths
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data" / "historical"
    LOGS_DIR = BASE_DIR / "logs"

    # Data configuration
    DATA_START_DATE = os.getenv("DATA_START_DATE", "2018-01-01")
    DATA_END_DATE = os.getenv("DATA_END_DATE", datetime.now().strftime("%Y-%m-%d"))

    # Risk management parameters (Carver's approach)
    INITIAL_CAPITAL = float(os.getenv("INITIAL_CAPITAL", "100000"))
    MAX_POSITION_SIZE = float(os.getenv("MAX_POSITION_SIZE", "0.10"))  # 10% max
    VOLATILITY_TARGET = float(os.getenv("VOLATILITY_TARGET", "0.20"))  # 20% annual vol target
    RISK_FREE_RATE = float(os.getenv("RISK_FREE_RATE", "0.03"))  # 3%

    # Strategy parameters
    MA_FAST = int(os.getenv("MA_FAST", "16"))  # Carver's recommendation
    MA_SLOW = int(os.getenv("MA_SLOW", "64"))

    # Trading costs (US market-specific)
    TRANSACTION_COST = float(os.getenv("TRANSACTION_COST", "0.001"))  # 0.1%
    SLIPPAGE = float(os.getenv("SLIPPAGE", "0.0005"))  # 0.05%

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # US stocks to trade
    US_STOCKS = os.getenv("US_STOCKS", "GOOG,MSFT,TSLA").split(",")

    # Annualization factor (Carver uses 256 for trading days)
    BUSINESS_DAYS_PER_YEAR = 256

    @classmethod
    def get_data_path(cls, filename: str) -> Path:
        """Get full path for a data file."""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        return cls.DATA_DIR / filename

    @classmethod
    def get_log_path(cls, filename: str) -> Path:
        """Get full path for a log file."""
        cls.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        return cls.LOGS_DIR / filename

    @classmethod
    def validate(cls) -> bool:
        """Validate configuration parameters."""
        assert 0 < cls.MAX_POSITION_SIZE <= 1, "MAX_POSITION_SIZE must be between 0 and 1"
        assert cls.VOLATILITY_TARGET > 0, "VOLATILITY_TARGET must be positive"
        assert cls.INITIAL_CAPITAL > 0, "INITIAL_CAPITAL must be positive"
        assert cls.MA_FAST < cls.MA_SLOW, "MA_FAST must be less than MA_SLOW"
        return True
