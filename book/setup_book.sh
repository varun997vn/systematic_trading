#!/bin/bash
# Setup script for Systematic Trading Book

set -e  # Exit on error

echo "================================================"
echo "Systematic Trading Book - Setup Script"
echo "================================================"
echo ""

# Check Python version
echo "[1/5] Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "  Found Python $python_version"

required_version="3.8"
if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "  ❌ Error: Python 3.8+ required"
    exit 1
fi
echo "  ✓ Python version OK"
echo ""

# Install dependencies
echo "[2/5] Installing dependencies..."
pip install -q -r requirements.txt
echo "  ✓ Dependencies installed"
echo ""

# Test Jupyter Book
echo "[3/5] Testing Jupyter Book installation..."
jupyter-book --version > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "  ✓ Jupyter Book installed"
else
    echo "  ❌ Error: Jupyter Book not found"
    exit 1
fi
echo ""

# Build the book
echo "[4/5] Building the book..."
jupyter-book build . --quiet
if [ $? -eq 0 ]; then
    echo "  ✓ Book built successfully"
else
    echo "  ❌ Error: Build failed"
    exit 1
fi
echo ""

# Summary
echo "[5/5] Setup complete!"
echo ""
echo "================================================"
echo "Next Steps:"
echo "================================================"
echo ""
echo "1. View the book:"
echo "   make serve"
echo "   (Opens at http://localhost:8000)"
echo ""
echo "2. Run notebooks interactively:"
echo "   jupyter lab"
echo ""
echo "3. Read the docs:"
echo "   - README.md (usage guide)"
echo "   - CONTRIBUTING.md (for contributors)"
echo ""
echo "4. Start learning:"
echo "   Open part1/01_what_is_systematic_trading.ipynb"
echo ""
echo "================================================"
echo "Happy Learning! 📚✨"
echo "================================================"
