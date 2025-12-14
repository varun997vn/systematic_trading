"""
Configuration settings for systematic trading system.
Based on Robert Carver's "Systematic Trading" principles.
"""

import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Core configuration for systematic trading."""

    # --- Paths --- #
    BASE_DIR = Path(__file__).parent.parent.parent
    DATA_DIR = BASE_DIR / "data"
    LOGS_DIR = BASE_DIR / "logs"

    # Data configuration
    DATA_START_DATE = os.getenv("DATA_START_DATE", "2000-01-01")
    DATA_END_DATE = os.getenv("DATA_END_DATE", datetime.now().strftime("%Y-%m-%d"))

    # --- Risk Parameters (Carver) --- #
    VOLATILITY_TARGET = float(os.getenv("VOLATILITY_TARGET", "0.20"))  # 20% annual
    MAX_POSITION_SIZE = float(os.getenv("MAX_POSITION_SIZE", "0.10"))  # 10% max
    MAX_LEVERAGE = float(os.getenv("MAX_LEVERAGE", "2.0"))  # 2x max leverage
    INITIAL_CAPITAL = float(os.getenv("INITIAL_CAPITAL", "100000"))

    # --- Trading Costs --- #
    TRANSACTION_COST = float(os.getenv("TRANSACTION_COST", "0.001"))  # 0.1%
    SLIPPAGE = float(os.getenv("SLIPPAGE", "0.0005"))  # 0.05%

    # --- System Parameters --- #
    BUSINESS_DAYS_PER_YEAR = 256  # Carver's convention
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls) -> bool:
        """Validate configuration."""
        assert 0 < cls.MAX_POSITION_SIZE <= 1, "MAX_POSITION_SIZE must be (0, 1]"
        assert cls.VOLATILITY_TARGET > 0, "VOLATILITY_TARGET must be positive"
        assert cls.INITIAL_CAPITAL > 0, "INITIAL_CAPITAL must be positive"
        return True