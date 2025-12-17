"""
Data Management Module for Systematic Trading Framework
Based on Robert Carver's "Systematic Trading"

Core responsibilities:
- PriceData structure (OHLCV)
- DataLoader (load market data)
- DataValidator (check completeness)
- ReturnCalculator (compute returns)
"""

from st.dto.data import PriceDataDTO, ReturnsDTO, CorrelationDTO
from utils.logger import setup_logger

logger = setup_logger(__name__)


class PriceData(PriceDataDTO):
    pass


class ReturnData(ReturnsDTO):
    pass


class CorrelationData(CorrelationDTO):
    pass
