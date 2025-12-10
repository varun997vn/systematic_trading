#!/bin/bash

# Trading System Startup Script
# This script starts both the FastAPI backend and Next.js frontend

set -e

echo "==================================="
echo "Trading System Startup"
echo "==================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if FastAPI routes.py exists
if [ ! -f "../routes.py" ] && [ ! -f "routes.py" ]; then
    echo -e "${YELLOW}Warning: routes.py not found in current or parent directory${NC}"
    echo "Please ensure your FastAPI backend is set up correctly"
    echo ""
fi

# Check if Node modules are installed
if [ ! -d "node_modules" ]; then
    echo -e "${BLUE}Installing Node.js dependencies...${NC}"
    npm install
    echo ""
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down servers...${NC}"
    kill $FASTAPI_PID 2>/dev/null || true
    kill $NEXTJS_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start FastAPI backend
echo -e "${BLUE}Starting FastAPI backend on port 8000...${NC}"
if [ -f "../routes.py" ]; then
    cd ..
    python -m uvicorn routes:app --host 0.0.0.0 --port 8000 --reload &
    FASTAPI_PID=$!
    cd trading-frontend
elif [ -f "routes.py" ]; then
    python -m uvicorn routes:app --host 0.0.0.0 --port 8000 --reload &
    FASTAPI_PID=$!
else
    echo -e "${YELLOW}FastAPI backend not found. Please start it manually.${NC}"
fi

sleep 2

# Start Next.js frontend
echo -e "${BLUE}Starting Next.js frontend on port 3000...${NC}"
npm run dev &
NEXTJS_PID=$!

sleep 3

echo ""
echo -e "${GREEN}==================================="
echo "Servers are running!"
echo "===================================${NC}"
echo ""
echo -e "${GREEN}FastAPI Backend:${NC}  http://localhost:8000"
echo -e "${GREEN}API Documentation:${NC} http://localhost:8000/docs"
echo -e "${GREEN}Next.js Frontend:${NC} http://localhost:3000"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop both servers${NC}"
echo ""

# Wait for both processes
wait
