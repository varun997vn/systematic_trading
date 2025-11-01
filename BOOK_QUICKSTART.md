# Systematic Trading Book - Quick Start Guide

This repository now includes a comprehensive interactive book teaching systematic trading from first principles!

## 📚 What's Included

An interactive Jupyter Book with:
- **16 planned chapters** organized into 5 parts
- **Interactive code examples** you can run and modify
- **Rich visualizations** of all key concepts
- **Real market data** and working examples
- **Progressive complexity** - no prior knowledge required

## 🚀 Getting Started

### Option 1: Build and Read Locally (Recommended)

```bash
# Navigate to book directory
cd book

# Install dependencies
pip install -r requirements.txt

# Build the book
make build

# Serve locally and open in browser
make serve
# Opens at http://localhost:8000
```

### Option 2: Run Notebooks Interactively

```bash
# Install dependencies
cd book
pip install -r requirements.txt

# Launch Jupyter Lab
jupyter lab

# Navigate to any .ipynb file in part1/, part2/, etc.
# Run cells interactively!
```

### Option 3: Read Without Building

Simply browse the `.ipynb` files in GitHub or VS Code - they render as notebooks!

## 📖 Book Structure

```
book/
├── intro.md                  # Book introduction
├── part1/                    # Foundations
│   ├── 01_what_is_systematic_trading.ipynb ✅ COMPLETE
│   ├── 02_understanding_stock_markets.ipynb
│   └── 03_why_manual_trading_fails.ipynb
├── part2/                    # Core Concepts  
│   ├── 04_trend_following.ipynb
│   ├── 05_understanding_volatility.ipynb
│   ├── 06_position_sizing.ipynb
│   └── 07_transaction_costs.ipynb
├── part3/                    # Implementation
│   ├── 08_getting_data.ipynb
│   ├── 09_building_strategies.ipynb
│   └── 10_backtesting_engine.ipynb
├── part4/                    # Analysis
│   ├── 11_understanding_results.ipynb
│   ├── 12_performance_metrics.ipynb
│   └── 13_portfolio_approach.ipynb
└── part5/                    # Practical
    ├── 14_system_capabilities.ipynb
    ├── 15_extending_system.ipynb
    └── 16_real_world_trading.ipynb
```

## ✨ Chapter 1 is Complete!

**Chapter 1: What is Systematic Trading?** is fully implemented with:
- Interactive coin flip simulation (emotional vs systematic trader)
- Consistency demonstration
- Backtesting preview
- Volatility targeting visualization
- Repository structure overview
- Real code examples

Try it out:
```bash
cd book
jupyter lab part1/01_what_is_systematic_trading.ipynb
```

## 🛠️ Make Commands

```bash
make help      # Show all commands
make install   # Install dependencies
make build     # Build the book
make clean     # Clean build artifacts
make serve     # Build and serve locally
make pdf       # Build PDF (requires LaTeX)
make test      # Test all notebooks
```

## 📝 Chapter Template

Each chapter includes:
1. **Learning objectives** - What you'll master
2. **Interactive examples** - Run code, see results
3. **Visualizations** - Charts and graphs
4. **Real code** - Links to repository implementation
5. **Key takeaways** - Summary of main points
6. **Exercises** - Practice problems
7. **Next steps** - Links to continue learning

## 🎨 Technology Stack

- **Jupyter Book** - Interactive book framework
- **MyST Markdown** - Enhanced markdown with features
- **Matplotlib/Seaborn** - Visualizations
- **Real repository code** - Links to actual implementation

## 🚧 Current Status

**Completed:**
- ✅ Full Jupyter Book framework setup
- ✅ Table of contents and configuration
- ✅ Chapter 1 with interactive examples
- ✅ Requirements and dependencies
- ✅ Build system (Makefile)
- ✅ Contributing guidelines

**Next Steps:**
- 📝 Chapter 2: Understanding Stock Markets (with real Yahoo Finance data)
- 📝 Chapter 3: Why Manual Trading Fails (psychological bias simulations)
- 📝 Chapter 4: Trend Following (EWMAC implementation walkthrough)
- 📝 Chapter 5: Understanding Volatility (volatility calculations)
- 📝 Chapters 6-16: Complete coverage of all topics

## 💡 Why This Approach?

### Advantages of Jupyter Book

1. **Interactive Learning**
   - Run code in your browser
   - Modify examples to experiment
   - See results immediately

2. **Rich Content**
   - Mix markdown, code, and visualizations
   - Math equations with LaTeX
   - Admonitions (tips, warnings, notes)

3. **Easy Maintenance**
   - Version control friendly (`.ipynb` files)
   - Automated builds
   - Easy to extend with new chapters

4. **Multiple Formats**
   - HTML (web browsing)
   - PDF (offline reading)
   - Notebooks (interactive)

5. **Integration with Code**
   - Import actual repository code
   - Show real implementations
   - No duplication

## 📚 For Learners

Start with Chapter 1 and work sequentially. Each chapter builds on previous concepts.

**Prerequisites:** None! The book assumes no prior knowledge of:
- Finance or trading
- Python programming
- Statistics or math

Everything is explained from scratch with examples.

## 👩‍💻 For Contributors

Want to add a chapter or improve existing content?

1. Read [`book/CONTRIBUTING.md`](book/CONTRIBUTING.md)
2. Follow the chapter template
3. Test your changes with `make build`
4. Submit a pull request!

## 🎯 Learning Path

**Week 1: Foundations**
- Read Part I (Chapters 1-3)
- Run all interactive examples
- Complete exercises

**Week 2: Core Concepts**
- Read Part II (Chapters 4-7)
- Implement simple moving average strategy
- Calculate volatility for real stocks

**Week 3: Implementation**
- Read Part III (Chapters 8-10)
- Build your own backtest
- Test different parameters

**Week 4: Analysis & Practice**
- Read Parts IV & V (Chapters 11-16)
- Create multi-stock portfolio
- Extend system with your ideas

## 🔗 Quick Links

- **Book README:** [`book/README.md`](book/README.md)
- **Contributing Guide:** [`book/CONTRIBUTING.md`](book/CONTRIBUTING.md)
- **Main README:** [`README.md`](README.md)
- **Requirements:** [`book/requirements.txt`](book/requirements.txt)

## 🙏 Acknowledgments

This book is based on:
- **Robert Carver's** "Systematic Trading" principles
- The **systematic_trading** codebase in this repository
- Open source tools: Jupyter Book, Python scientific stack

## 📜 License

Same license as the main repository. For educational purposes only.

---

**Happy Learning!** 📚✨

Start your journey: `cd book && make serve`
