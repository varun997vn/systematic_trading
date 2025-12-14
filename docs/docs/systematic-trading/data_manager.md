---
id: data-manager          # unique ID for this doc
title: Data Manager       # this becomes the page title
sidebar_label: Data Manager
---

# **Data Manager**

## **Overview**

`data_manager.py` provides a unified interface for downloading, validating, and retrieving OHLCV market data for
systematic trading based on Robert Carver's methodology. It uses Yahoo Finance as the data source and implements robust
validation and return calculation functionality.

---

## Core Responsibilities

| Component            | Description                                                                                                   |
|----------------------|---------------------------------------------------------------------------------------------------------------|
| **PriceData**        | Pydantic model wrapping OHLCV DataFrame with validation and convenient properties for close prices and volume |
| **DataLoader**       | Downloads data from Yahoo Finance (single/batch), loads from CSV cache, manages local file storage            |
| **DataValidator**    | Validates data completeness (minimum rows, missing values, price sanity checks, OHLC consistency)             |
| **ReturnCalculator** | Computes log returns, percentage returns, and multi-period returns for systematic trading analysis            |
| **DataManager**      | Main interface coordinating all components, provides unified API for data retrieval with auto-download        |

# **Important Features**

| Feature             | Description                                                                                |
|---------------------|--------------------------------------------------------------------------------------------|
| CSV Caching         | Automatically saves downloaded data to CSV files, loads from cache when available          |
| Data Validation     | Comprehensive checks: minimum rows, missing values, zero/negative prices, OHLC consistency |
| Batch Downloads     | Efficiently download multiple tickers in a single Yahoo Finance API call                   |
| Return Calculations | Built-in support for log returns, percentage returns, and multi-period returns             |
| Auto-adjustment     | Uses Yahoo Finance's auto-adjusted prices for accurate historical analysis                 |
| Logging             | Structured logging throughout for monitoring downloads, validations, and errors            |
| Date Filtering      | Apply custom date ranges to loaded data while preserving cached files                      |
| Pydantic Validation | Type-safe data structures with automatic validation of OHLCV columns                       |

## **Main Classes**

### **`DataManager`**

The central class providing a high-level interface for:

* Loading data from CSV cache or auto-downloading from Yahoo Finance
* Applying date range filters
* Running validation checks
* Computing returns (log or percentage)
* Retrieving close prices for multiple tickers as DataFrame

**Key Methods:**

* `get_data(ticker, start_date, end_date, validate)` - Get validated OHLCV data
* `get_returns(ticker, return_type, start_date, end_date)` - Get computed returns
* `get_close_prices(tickers, start_date, end_date)` - Get multi-ticker close price DataFrame

### **`PriceData`**

Pydantic model wrapping OHLCV data with:

* Automatic validation of required columns (Open, High, Low, Close, Volume)
* Convenient properties: `.close`, `.volume`
* Type-safe structure using Pydantic

### **`DataLoader`**

Handles all data I/O:

* `load_csv(ticker)` - Load from local CSV cache
* `download(ticker, start_date, end_date)` - Download single ticker from Yahoo Finance
* `download_batch(tickers, start_date, end_date)` - Download multiple tickers efficiently

### **`DataValidator`**

Ensures data quality:

* `check(price_data, min_rows)` - Comprehensive validation suite
* `get_missing_dates(price_data)` - Identify gaps in trading days

### **`ReturnCalculator`**

Computes returns for analysis:

* `log_returns(price_data)` - Natural log returns
* `percentage_returns(price_data)` - Simple percentage returns
* `multi_period_returns(price_data, periods, return_type)` - Multi-period returns

---

## **Typical Usage Pattern**

```python
from st.data.data_manager import DataManager, ReturnCalculator

# Initialize DataManager
dm = DataManager(data_dir="data/")

# Get OHLCV data (auto-downloads if not cached)
price_data = dm.get_data("AAPL", start_date="2020-01-01", end_date="2024-12-31")

# Access close prices and volume
close_prices = price_data.close
volume = price_data.volume

# Get returns
log_returns = dm.get_returns("AAPL", return_type="log")
pct_returns = dm.get_returns("AAPL", return_type="percentage")

# Get close prices for multiple tickers
tickers = ["AAPL", "MSFT", "GOOGL"]
close_df = dm.get_close_prices(tickers, start_date="2020-01-01")

# Compute multi-period returns
returns_5d = ReturnCalculator.multi_period_returns(price_data, periods=5, return_type="log")

# Batch download
loader = DataLoader()
data_dict = loader.download_batch(["AAPL", "MSFT", "GOOGL"], start_date="2020-01-01")
```

---

## **Data Validation**

The `DataValidator` performs comprehensive checks:

* **Minimum rows**: Ensures sufficient data points (default 100 rows)
* **Missing values**: Detects null/NaN values in any column
* **Price sanity**: Checks for zero or negative prices
* **OHLC consistency**: Verifies High >= Low relationship
* **Date gaps**: Identifies missing business days using `get_missing_dates()`

Failed validation triggers warnings in logs but can be bypassed by setting `validate=False`.

---

## **What This Module Enables**

✓ Systematic trading data workflows based on Robert Carver's methodology  
✓ Automatic CSV caching to minimize API calls  
✓ Robust data validation for reliable backtesting  
✓ Built-in return calculations (log, percentage, multi-period)  
✓ Batch downloads for portfolio-level analysis  
✓ Type-safe data structures with Pydantic validation  
✓ Forward-fill handling for missing data in multi-ticker DataFrames

---

## **Technology Stack**

* **Data Source**: Yahoo Finance (`yfinance`)
* **Data Model**: Pydantic for type-safe structures
* **Data Processing**: Pandas DataFrames (OHLCV with DatetimeIndex)
* **Storage**: CSV files organized by ticker
* **Logging**: Structured logging via custom logger

---

## **Configuration**

Uses `Settings` from `st.config.settings` for:

* `DATA_DIR`: Base directory for CSV storage
* `DATA_START_DATE`: Default start date for downloads
* `DATA_END_DATE`: Default end date for downloads

---
