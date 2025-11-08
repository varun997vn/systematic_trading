# Systematic Trading Book

An interactive Jupyter Book teaching systematic trading from first principles.

## 📚 Read Online

The book is built using Jupyter Book and can be read online or run locally.

## 🚀 Quick Start

### Option 1: Read Online (No Setup Required)

Simply browse the chapters in your web browser after building.

### Option 2: Run Locally

#### Prerequisites
- Python 3.8 or higher
- pip

#### Installation

```bash
# Clone the repository (if you haven't already)
cd systematic_trading

# Install book dependencies
pip install -r book/requirements.txt

# Build the book
cd book
jupyter-book build .
```

The built HTML will be in `book/_build/html/`. Open `index.html` in your browser.

### Option 3: Run Notebooks Interactively

```bash
# Install dependencies
pip install -r book/requirements.txt

# Launch Jupyter
cd book
jupyter lab

# Navigate to any .ipynb file and run cells
```

### Option 4: Use Google Colab

Click the rocket icon 🚀 at the top of any chapter when viewing online, then select "Colab" to run in Google Colab (free, no setup required).

## 📖 Book Structure

The book is organized into 5 parts:

### Part I: Foundations
- Chapter 1: What is Systematic Trading?
- Chapter 2: Understanding Stock Markets
- Chapter 3: Why Manual Trading Fails

### Part II: Core Concepts
- Chapter 4: Trend Following
- Chapter 5: Understanding Volatility
- Chapter 6: Position Sizing and Risk Management
- Chapter 7: Transaction Costs

### Part III: Implementation
- Chapter 8: Getting Market Data
- Chapter 9: Building Trading Strategies
- Chapter 10: The Backtesting Engine

### Part IV: Analysis
- Chapter 11: Understanding Your Results
- Chapter 12: Performance Metrics
- Chapter 13: Portfolio Approach

### Part V: Practical Application
- Chapter 14: System Capabilities and Limitations
- Chapter 15: Extending the System
- Chapter 16: Real-World Trading

## 🛠️ Building the Book

### Clean Build
```bash
cd book
jupyter-book clean .
jupyter-book build .
```

### Quick Rebuild
```bash
cd book
jupyter-book build .
```

### View Locally
```bash
# After building
cd _build/html
python -m http.server 8000
# Open http://localhost:8000 in browser
```

## ✍️ Contributing

### Adding a New Chapter

1. Create a new `.ipynb` file in the appropriate `partN/` directory
2. Add it to `_toc.yml` in the correct section
3. Follow the existing chapter template structure
4. Rebuild the book to see your changes

### Chapter Template Structure

Each chapter should include:

```python
# Cell 1: Title and learning objectives (markdown)
# Cell 2+: Content sections with code examples
# Last cells: Key takeaways, exercises, next steps
```

### Code Guidelines

- **Always include comments** explaining what code does
- **Use clear variable names** (not `x`, `y` - use `price`, `returns`)
- **Generate visualizations** for key concepts
- **Provide real examples** with actual data when possible
- **Keep cells focused** - one concept per cell

### Writing Style

- **Assume no prior knowledge** - define all terms
- **Use analogies** - relate to everyday experiences
- **Show, don't tell** - visualize concepts
- **Progressive complexity** - start simple, build up
- **Interactive first** - let readers experiment

## 🔧 Troubleshooting

### Build Errors

If you get errors during build:

```bash
# Clear cache and rebuild
jupyter-book clean . --all
jupyter-book build .
```

### Missing Dependencies

```bash
# Reinstall all dependencies
pip install --upgrade -e .
```

### Kernel Issues

```bash
# Install IPython kernel
python -m ipykernel install --user --name=systematic_trading
```

## 📊 Using Real Data

The book uses the main repository's data infrastructure:

```python
import sys
sys.path.insert(0, '..')  # Add parent directory to path

from data.data_manager import DataManager
dm = DataManager()
data = dm.download_stock_data('GOOG')
```

## 🎨 Customization

### Changing Theme

Edit `_config.yml`:

```yaml
sphinx:
  config:
    html_theme: sphinx_book_theme  # or sphinx_rtd_theme, etc.
```

### Adding Extensions

Edit `_config.yml` under `parse.myst_enable_extensions`.

## 📝 Notebook vs Markdown

- Use **notebooks** (`.ipynb`) for chapters with code examples
- Use **markdown** (`.md`) for overview pages and appendices

## 🧪 Testing

Run all notebook cells to ensure they execute without errors:

```bash
cd book
pytest --nbmake part*/*.ipynb
```

## 📄 Exporting

### PDF Export

```bash
cd book
jupyter-book build . --builder pdflatex
```

### Single HTML

```bash
cd book
jupyter-book build . --builder singlehtml
```

## 🔗 Useful Links

- [Jupyter Book Documentation](https://jupyterbook.org/)
- [MyST Markdown Guide](https://myst-parser.readthedocs.io/)
- [Sphinx Book Theme](https://sphinx-book-theme.readthedocs.io/)

## 📜 License

This book is part of the systematic_trading repository and follows the same license.

## 🙏 Acknowledgments

Based on Robert Carver's *"Systematic Trading"* principles and the systematic_trading codebase.

---

**Happy Learning!** 📚✨
