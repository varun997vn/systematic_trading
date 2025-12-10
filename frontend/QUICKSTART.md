# Quick Start Guide

## 🚀 Getting Started in 3 Steps

### Step 1: Install Dependencies

```bash
cd trading-frontend
npm install
```

### Step 2: Start Your FastAPI Backend

In your FastAPI project directory (where routes.py is located):

```bash
python routes.py
# OR
uvicorn routes:app --reload
```

The backend should start at: http://localhost:8000

### Step 3: Start the Next.js Frontend

```bash
npm run dev
```

The frontend will be available at: http://localhost:3000

---

## 🎯 Alternative: Use the Startup Script

We've included a convenient startup script that runs both servers:

```bash
cd trading-frontend
./start.sh
```

This will automatically start:

- FastAPI backend on port 8000
- Next.js frontend on port 3000

Press `Ctrl+C` to stop both servers.

---

## ✅ Verify Everything Works

1. **Check FastAPI is running:**
    - Open http://localhost:8000/health
    - You should see: `{"status": "healthy", ...}`

2. **Check the API docs:**
    - Open http://localhost:8000/docs
    - You'll see the interactive Swagger UI

3. **Check the Next.js frontend:**
    - Open http://localhost:3000
    - You should see the Trading System Dashboard

---

## 🎨 What You'll See

The dashboard includes:

1. **Header** - Shows app title and market status
2. **Data Management** - Download ticker data
3. **Active Strategies** - View currently active trading strategies
4. **Portfolio Summary** - See your portfolio value, positions, and P&L
5. **Signal Monitor** - Check trading signals for any ticker

---

## 🔧 Configuration

### API URL

The frontend is configured to connect to `http://localhost:8000` by default.

To change this, edit `.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://your-api-url:port
```

---

## 📝 Common Commands

```bash
# Development
npm run dev          # Start development server

# Production
npm run build        # Build for production
npm start           # Start production server

# Maintenance
npm run lint        # Run linter
```

---

## 🐛 Troubleshooting

### CORS Errors?

Your FastAPI backend already has CORS configured for `localhost:3000`. If you change the frontend port, update the CORS
settings in `routes.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    ...
)
```

### Port Already in Use?

Run on a different port:

```bash
npm run dev -- -p 3001
```

### Can't Connect to Backend?

1. Ensure FastAPI is running: `curl http://localhost:8000/health`
2. Check the console for errors (F12 in browser)
3. Verify `.env.local` has the correct API URL

---

## 📚 Next Steps

Check out the full `README.md` for:

- Complete API documentation
- Adding new pages and components
- Customization options
- Advanced features

---

## 🆘 Need Help?

- Check the browser console (F12) for errors
- Look at the terminal output for both servers
- Review the API documentation at http://localhost:8000/docs
