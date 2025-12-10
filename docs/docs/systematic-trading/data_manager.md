---
id: data-manager          # unique ID for this doc
title: Data Manager       # this becomes the page title
sidebar_label: Data Manager
---

# **Data Manager**

## **Overview**

`data_manager.py` provides a unified interface for downloading, caching, updating, and retrieving market data (prices,
fundamentals, options, etc.).
It abstracts storage, versioning, API calls, and caching so higher-level code can request data without worrying about
how it is fetched or stored.

---

## Core Responsibilities

| Responsibility                  | Description                                                                                                                                |
|---------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------|
| Download market data            | Price history (daily, intraday), fundamentals, options chain data, additional vendor-specific datasets                                     |
| Manage local storage            | Organizes data by ticker + dataset type, saves to disk (JSON/CSV/parquet), loads cached data, handles safe file operations + error logging |
| Automatically update stale data | Detects outdated files, pulls incremental data only, rebuilds datasets when corruption or missing segments are detected                    |
| Provide a clean public API      | Methods like `get_price_history`, `get_fundamentals`, `get_options_chain`, `list_available_tickers`, `refresh_all`, `export_metadata`      |

# **Important Features**

| Feature                  | Description                                                                                                               |
|--------------------------|---------------------------------------------------------------------------------------------------------------------------|
| Caching Layer            | Reduces API usage and ensures fast repeated access                                                                        |
| Data Validation          | Checks file integrity before returning results, falls back to re-download if needed                                       |
| Logging + Error Handling | Uniform logging for all download and load operations, graceful failures with meaningful error messages                    |
| Extensibility            | Designed so new data providers and dataset types can be added easily, likely via plugin-style or structured class methods |

## **Main Class**

### **`DataManager`**

The central class that orchestrates:

* Path management
* Download logic
* Update rules
* Return of final cleaned datasets

Internally handles:

* Session management (API clients)
* Conversion functions
* Storage utilities

---

# **Typical Usage Pattern**

```python
from st.data import DataManager

dm = DataManager(base_path="data/")

prices = dm.get_price_history("AAPL", period="5y")
funds = dm.get_fundamentals("AAPL")
opt = dm.get_options_chain("AAPL")

dm.refresh_all()  # optional: refresh entire local dataset
```

---

# **Returned Metadata**

A helper method (e.g., `export_metadata()`) summarizes:

* available tickers
* last updated timestamps
* cached dataset types
  Useful for dashboards and diagnostics.

---

# **What This Module Enables**

✔ Faster research workflows
✔ Fewer repeated API calls
✔ Reliable, consistent dataset organization
✔ A single place to manage all market-data logic

---

