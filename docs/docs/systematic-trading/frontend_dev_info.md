---
id: frontend-dev-info
title: Frontend Dev Info
sidebar_label: Frontend Dev Info
---

# Frontend Overview

> Prioritize Server Side Rendering, faster performance and UX

## Technology Stack

- **Next.js** (app router)
- **Material UI** (UI components and styling)
- **Prisma** (ORM)
- **React Query** (server state, fetching, caching)
- **React Hook Form** (forms)
- **Zod** (schema validation)
- **Plotly.js** (charts)

---

# Application Pages

## 1. Dashboard (`/dashboard`)

Purpose: High-level portfolio overview.

Key elements:

- Portfolio summary: total value, P&L, cash balance
- Open positions overview list
- Recent trades summary
- Market status indicator
- Quick actions: create trade, generate signals

---

## 2. Chart Analysis (`/charts`)

Purpose: Main charting and signal visualization page.

Features:

- Ticker selector (dropdown/autocomplete)
- Plotly.js candlestick chart
- Buy/sell signal markers
- Strategy indicator overlays
- Date range selector
- Volume subplot below price
- Signal strength filter
- MUI controls: DatePicker, Select, Buttons

---

## 3. Positions (`/positions`)

Purpose: View and manage open positions.

Features:

- Table of current positions (MUI DataGrid)
- Real-time P&L
- Actions: close position, update
- Metrics: avg price, current price, P&L %

---

## 4. Trades (`/trades`)

Purpose: Display and filter trade history.

Features:

- Trade table with filters (strategy, symbol, status)
- Trade details modal
- Performance metrics: win rate, average P&L
- Filter by open/closed status
- Create new trade form

---

## 5. Strategies (`/strategies`)

Purpose: Create and manage trading strategies.

Features:

- Strategy list
- Create/Edit forms
- Strategy performance metrics
- Enable/disable strategies
- Configure parameters
- View available strategy types

---

## 6. Data Management (`/data`)

Purpose: Manage downloaded market data.

Features:

- List of stored tickers
- Download new ticker data
- Storage usage information
- Delete ticker data
- Select date range for downloading

---

## 7. Signals (`/signals`)

Purpose: Generate and review trading signals.

Features:

- Generate signals for selected tickers
- Signal history table
- Latest signals summary
- Signal strength indicators
- Integration with chart visualization

---

## 8. Settings (`/settings`)

Purpose: System configuration.

Features:

- Broker configuration (API keys, live/paper mode)
- Cash balance management
- Initial capital settings
- System health check display

---

# Recommended Directory / Page Structure

```text
/
├── dashboard
├── charts
├── trading/
│   ├── positions
│   ├── trades
│   └── signals
├── strategies
├── data
└── settings
