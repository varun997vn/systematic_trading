---
id: package-architecture          # unique ID for this doc
title: Package Architecture       # this becomes the page title
sidebar_label: Package Architecture
---

# Systematic Trading Framework Guide

**Based on Robert Carver's "Systematic Trading"**

## System Overview

This framework implements a complete systematic trading pipeline with 6 core modules and 24 components.

---

## Core Modules

### 1. Data Management

**Purpose:** Handle price data, returns calculation, and data validation  
**Key Components:**

- `PriceData` - OHLCV data structure
- `DataLoader` - Load market data from files
- `DataValidator` - Check data completeness
- `ReturnCalculator` - Compute log/percentage returns

**Usage:**

```python
data = DataLoader.load_csv('prices.csv')
validated = DataValidator.check(data)
returns = ReturnCalculator.log_returns(validated)
```

---

### 2. Volatility

**Purpose:** Estimate and forecast instrument volatility  
**Key Components:**

- `VolatilityEstimator` - Base volatility calculations
- `EWMAVolatility` - Exponentially weighted moving average
- `VolatilityTargeting` - Risk normalization

**Usage:**

```python
vol_estimator = EWMAVolatility(span=36)
daily_vol = vol_estimator.calculate(returns)
annual_vol = daily_vol * sqrt(256)
```

---

### 3. Forecasting

**Purpose:** Trading rules that generate forecast signals  
**Key Components:**

- `TrendFollowing` - EWMAC and trend strategies
- `Carry` - Carry-based signals
- `MeanReversion` - Mean reversion strategies
- `ForecastScaler` - Scale forecasts to -20 to +20

**Usage:**

```python
ewmac = TrendFollowing.ewmac(fast=16, slow=64)
forecast = ForecastScaler.scale(ewmac, target=10)
# Output range: -20 to +20
```

---

### 4. Portfolio

**Purpose:** Combine forecasts and manage multiple instruments  
**Key Components:**

- `ForecastCombiner` - Aggregate multiple signals
- `PortfolioOptimizer` - Optimize weights
- `DiversificationMultiplier` - Account for diversification

**Usage:**

```python
combined = ForecastCombiner.weighted_average(
  forecasts={'ewmac_16_64': 10, 'carry': 5},
  weights={'ewmac_16_64': 0.6, 'carry': 0.4}
)
```

---

### 5. Position Sizing

**Purpose:** Calculate optimal position sizes based on volatility and risk  
**Key Components:**

- `PositionSizer` - Core position calculations
- `VolatilityScaling` - Risk-adjusted sizing
- `InstrumentWeight` - Capital allocation per instrument

**Usage:**

```python
position = PositionSizer.calculate(
  forecast=10,
  volatility=0.15,
  capital=100000,
  target_risk=0.20
)
```

---

### 6. Risk Management

**Purpose:** Monitor and control portfolio risk  
**Key Components:**

- `RiskCalculator` - Portfolio risk metrics
- `CorrelationEstimator` - Cross-instrument correlations
- `CapitalAllocation` - Capital distribution

**Usage:**

```python
risk = RiskCalculator.portfolio_risk(
  positions=positions,
  correlations=corr_matrix,
  volatilities=vols
)
```

---

## Execution Pipeline

### Step 1: Data Ingestion & Validation

Load historical price data, validate for completeness, and calculate returns  
**Outputs:** OHLCV Data, Log Returns, Percentage Returns

### Step 2: Volatility Estimation

Calculate EWMA volatility for each instrument to normalize risk  
**Outputs:** Daily Volatility, Annual Volatility, Vol Forecast

### Step 3: Forecast Generation

Apply trading rules (trend, carry, mean reversion) to generate signals  
**Outputs:** Raw Forecasts, Scaled Forecasts (-20 to +20)

### Step 4: Forecast Combination

Combine multiple forecasts using weighted averaging or optimization  
**Outputs:** Combined Forecast, Diversification Multiplier

### Step 5: Position Sizing

Convert forecasts to positions using volatility targeting  
**Outputs:** Target Positions, Risk-Adjusted Sizes, Capital Allocation

### Step 6: Risk Management & Execution

Apply risk limits, calculate portfolio metrics, and execute trades  
**Outputs:** Final Positions, Portfolio Risk, Trade Orders

---

## Data Flow Diagram

```
Market Data → Data Module
Data Module → Volatility Module
Data Module → Forecast Module
Forecast Module → Portfolio Module
Volatility Module → Position Module
Portfolio Module → Position Module
Position Module → Risk Module
Risk Module → Trade Execution
```

---

## System Statistics

- **Total Modules:** 6
- **Components:** 24
- **Pipeline Steps:** 6
- **Integration Points:** 8

---

## Key Principles

1. **Standardized Forecasts:** All trading rules scaled to -20 to +20 range
2. **Volatility Targeting:** Positions sized for consistent risk across instruments
3. **Diversification:** Combine multiple rules and instruments
4. **Risk Management:** Continuous monitoring and position limits
5. **Modularity:** Each component has clear inputs/outputs

---

## Quick Start Workflow

1. Load and validate price data
2. Calculate instrument volatilities
3. Generate forecasts from trading rules
4. Combine forecasts across strategies
5. Size positions based on volatility targets
6. Apply risk controls and execute