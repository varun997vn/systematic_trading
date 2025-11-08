"""
Data management module for systematic trading system.
Handles downloading, storing, and retrieving market data.
"""

from .data_manager import DataManager, DownloadRequest

__all__ = ['DataManager', "DownloadRequest"]
