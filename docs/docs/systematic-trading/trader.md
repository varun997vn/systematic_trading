# **📘 Trader Class — Documentation**

The `Trader` class provides a complete pipeline for loading market data, applying trading strategies, and generating
consolidated trading signals. It acts as the orchestrator between data ingestion (`DataManager`) and multiple plug-in
strategies (`Strategy`).

---

## **Overview**

**Responsibilities of the Trader class**

* Load OHLCV market data (from CSV or downloaded via `DataManager`)
* Add indicators from multiple strategies
* Generate buy/sell signals (range: **-20 to +20**)
* Aggregate multiple strategies using:

    * `"aggregate"` → average of all signals
    * `"max"` → strongest absolute signal
    * `"consensus"` → majority vote with strength
* Provide utilities to inspect, save, and summarize signals

---

## **Initialization**

```python
Trader(strategies: List[Strategy] = None,
data_manager: DataManager = None)
```

**Args**

* `strategies` — list of strategy instances
* `data_manager` — optional `DataManager`; created automatically if omitted

---

## **1. Data Loading**

### `load_data(...) → DataFrame`

Load market data either via ticker (using `DataManager`) or directly from a CSV file.

**Features**

* Automatic download if data is missing or outdated
* Standardizes column names
* Normalizes date formats
* Stores the resulting Polars DataFrame in `self.data`

---

## **2. Strategy Management**

### `add_strategy(strategy)`

Registers an additional strategy to the trader.

### `get_available_tickers() → List[str]`

Returns all tickers present in local storage.

### `get_data_info(ticker=None)`

Returns metadata such as date range and whether data is stale.

### `update_data(ticker=None, force=False)`

Refreshes existing data if stale or forced.

---

## **3. Data Preparation**

### `prepare_data() → DataFrame`

Clones the loaded data and applies all strategy‐specific indicator transformations.

Each strategy must implement:

* `add_indicators(df)` → DataFrame

---

## **4. Signal Generation**

### `generate_signals(mode="aggregate") → DataFrame`

Runs all strategies and produces:

* individual strategy signal columns
* a single `final_signal`
* a human-readable `signal_label`

**Supported modes**

| Mode          | Description                           |
|---------------|---------------------------------------|
| `"aggregate"` | Average of all strategy signals       |
| `"max"`       | The strongest absolute signal         |
| `"consensus"` | Majority direction × average strength |

The output is stored as:
`self.signals`

---

## **5. Signal Retrieval**

### `get_latest_signal() → Dict`

Returns the most recent signal, including individual strategy outputs.

### `get_signal_history(last_n=None)`

Returns all signals, or the last N rows.

### `get_buy_sell_points(min_signal_strength=10)`

Extracts only strong buy/sell events.

---

## **6. Saving & Summaries**

### `save_signals(output_path)`

Exports signals to CSV.

### `print_summary()`

Prints a detailed overview:

* strategies used
* date range
* distribution of labels
* latest signal breakdown

---

## **7. Representation**

### `__repr__()`

Provides a quick diagnostic string showing number of strategies, whether data is loaded, and active ticker.

---

# **Summary**

The `Trader` class is designed as a **modular, extensible trading engine** that cleanly separates:

* Data handling
* Strategy execution
* Signal generation
* Reporting

You can plug in new strategies, swap data sources, and choose different aggregation modes without changing the core
workflow.

---

