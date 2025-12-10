---
id: strategies          # unique ID for this doc
title: Strategies       # this becomes the page title
sidebar_label: Strategies
---

# Strategies

## Overview

This codebase defines a **strategy framework** for generating trading signals.
It consists of:

1. **`BaseStrategy`** – A parent class providing shared structure, validation, and utilities.
2. **`strategies.py`** – Several concrete strategy implementations, each producing a numerical signal for trading.

The overall pattern:
Each strategy takes a `DataFrame` of market data → computes features → produces a signal → returns a cleaned/validated
output.

### Strategies Available

| Strategy Name           | Description                                                                                                                                     |
|-------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|
| **SimpleMeanReversion** | Compares the latest price to its rolling mean. Price above average → negative signal; below average → positive. Normalized to the signal scale. |
| **MomentumStrategy**    | Uses recent price changes or returns to detect trends. Strong positive returns → positive signal; negative returns → negative.                  |
| **VolatilityBreakout**  | Based on price range expansion. Large breakouts relative to average volatility produce stronger signals.                                        |
| **RSIReversion**        | Uses RSI (Relative Strength Index). Overbought (high RSI) → negative signal; oversold (low RSI) → positive.                                     |
| **VWAPStrategy**        | Compares price to VWAP (Volume-Weighted Average Price). Price below VWAP → positive signal; above VWAP → negative.                              |

---

# 1. `base.py`

### **Purpose**

Defines the foundation for all trading strategies. It standardizes naming, initialization, input handling, and signal
validation.

### **Key Components**

#### **`BaseStrategy`**

* **Attributes**

    * `name`: Name of the strategy instance.
    * `config`: Optional external configuration.

* **Core Methods**

    * **`__init__(name, config)`**
      Stores the strategy identity and configuration.

    * **`prepare(df)`**
      Hook for preprocessing data before generating signals (default: returns `df` unchanged).

    * **`create_signal(df)`**
      Abstract method that all strategies must implement to compute a signal.

    * **`validate_signal(signal)`**
      Ensures that:

        * The signal is finite (no `NaN`, `inf`)
        * Values fall within the allowed range (typically -20 to 20)

    * **`run(df)`**
      Main pipeline:

        1. Prepare data
        2. Generate raw signal
        3. Validate signal
        4. Return the final numeric output

    * **`__repr__()`**
      Clean string representation, e.g.:
      `MomentumStrategy(name='momentum')`

---

# 2. `strategies.py`

### **Purpose**

Implements **five concrete trading strategies**, each with its own logic.
Each strategy inherits from `BaseStrategy` and must implement `create_signal()`.

### **Common Pattern**

Each strategy follows:

```
df = self.prepare(df)
signal = <computed value>
return self.validate_signal(signal)
```

---

# Summary

| File              | Purpose                                                        |
|-------------------|----------------------------------------------------------------|
| **base.py**       | Defines strategy structure, utilities, and signal validation.  |
| **strategies.py** | Implements 5 specific trading strategies using that structure. |

The system is modular, easy to extend, and ensures consistent, validated signals across different strategy types.

---