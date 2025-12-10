# Trading System Frontend

A Next.js frontend for the FastAPI algorithmic trading system backend.

## Prerequisites

- Node.js 18+ and npm
- Python 3.8+ (for FastAPI backend)
- Your FastAPI trading system backend running

## Quick Start

### 1. Install Dependencies

```bash
cd trading-frontend
npm install
```

### 2. Configure Environment

The `.env.local` file is already configured with the default FastAPI URL:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

If your FastAPI server runs on a different port, update this value.

### 3. Start the FastAPI Backend

In your FastAPI project directory:

```bash
# Install FastAPI dependencies if not already installed
pip install fastapi uvicorn

# Run the server
python routes.py
# or
uvicorn routes:app --reload --host 0.0.0.0 --port 8000
```

The backend should now be running at http://localhost:8000

### 4. Start the Next.js Development Server

In the `trading-frontend` directory:

```bash
npm run dev
```

The frontend will be available at http://localhost:3000

## Project Structure

```
trading-frontend/
├── app/
│   ├── page.tsx              # Main dashboard page
│   └── layout.tsx            # Root layout
├── components/
│   ├── PortfolioSummary.tsx  # Portfolio overview component
│   ├── SignalMonitor.tsx     # Trading signal checker
│   └── TickerSearch.tsx      # Data download component
├── lib/
│   └── api.ts                # API client for FastAPI backend
├── .env.local                # Environment variables
└── package.json              # Dependencies
```

## Features

### Dashboard
- Real-time portfolio summary
- Market status indicator
- Active strategies display
- Quick data management

### Portfolio Summary
- Total portfolio value
- Cash and positions breakdown
- Individual holdings with P&L
- Performance metrics

### Signal Monitor
- Check latest trading signals for any ticker
- View signal strength and recommendations
- Individual strategy signals breakdown

### Data Management
- Download single or multiple ticker data
- Background processing
- Easy-to-use interface

## API Client Usage

The API client is located in `lib/api.ts` and provides typed access to all FastAPI endpoints:

```typescript
import api from '@/lib/api';

// Example: Get portfolio summary
const portfolio = await api.portfolio.getSummary();

// Example: Check trading signal
const signal = await api.signals.getLatest('AAPL');

// Example: Download ticker data
await api.data.downloadTicker('MSFT');

// Example: Run backtest
const results = await api.backtest.run({
  ticker: 'GOOGL',
  strategies: ['rsi', 'macd'],
  start_date: '2024-01-01',
  end_date: '2024-12-01',
});
```

## Available API Endpoints

### Data Management
- `GET /api/data/tickers` - List available tickers
- `POST /api/data/download` - Download single ticker
- `POST /api/data/download-multiple` - Download multiple tickers
- `GET /api/data/ticker/{ticker}` - Get OHLCV data
- `DELETE /api/data/ticker/{ticker}` - Delete ticker data

### Portfolio
- `POST /api/portfolio/init` - Initialize portfolio
- `GET /api/portfolio/summary` - Get portfolio summary
- `GET /api/portfolio/positions` - List all positions
- `POST /api/portfolio/positions/add` - Add position
- `POST /api/portfolio/positions/close` - Close position

### Strategies
- `GET /api/strategies/available` - List available strategies
- `GET /api/strategies/active` - List active strategies
- `POST /api/strategies/add` - Add strategy
- `DELETE /api/strategies/{name}` - Remove strategy

### Signals
- `POST /api/signals/generate` - Generate signals
- `GET /api/signals/latest/{ticker}` - Get latest signal
- `GET /api/signals/history/{ticker}` - Get signal history
- `GET /api/signals/buy-sell/{ticker}` - Get buy/sell points

### Backtesting
- `POST /api/backtest/run` - Run backtest
- `GET /api/backtest/results/{id}` - Get backtest results

### Analytics
- `GET /api/analytics/performance/{ticker}` - Get performance metrics
- `GET /api/analytics/correlation` - Get correlation matrix

### Market
- `GET /api/market/status` - Get market status
- `GET /api/market/calendar` - Get trading calendar

## Customization

### Adding New Pages

Create a new page in the `app` directory:

```typescript
// app/backtest/page.tsx
'use client';

import api from '@/lib/api';

export default function BacktestPage() {
  // Your backtest page implementation
  return <div>Backtest Page</div>;
}
```

### Adding New Components

Create components in the `components` directory:

```typescript
// components/BacktestResults.tsx
'use client';

export default function BacktestResults({ results }) {
  return (
    <div>
      {/* Your component implementation */}
    </div>
  );
}
```

### Styling

This project uses Tailwind CSS. You can customize the theme in `tailwind.config.ts`.

## Development

### Running in Development Mode

```bash
npm run dev
```

### Building for Production

```bash
npm run build
npm start
```

### Linting

```bash
npm run lint
```

## Common Issues

### CORS Errors

If you see CORS errors, ensure your FastAPI backend has the correct CORS configuration in routes.py (already included).

### API Connection Issues

1. Verify the FastAPI server is running: `curl http://localhost:8000/health`
2. Check the `NEXT_PUBLIC_API_URL` in `.env.local`
3. Look for errors in the browser console (F12)

### Port Conflicts

If port 3000 is in use, specify a different port:

```bash
npm run dev -- -p 3001
```

## Next Steps

Consider adding:
- Authentication and user management
- Real-time WebSocket updates
- Advanced charting with Recharts or TradingView
- More detailed analytics and reporting
- Mobile responsive improvements
- Dark mode support
