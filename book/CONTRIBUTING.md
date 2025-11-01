# Contributing to the Systematic Trading Book

Thank you for your interest in improving this book! This guide will help you add new content or improve existing chapters.

## 📋 Quick Start for Contributors

### Setting Up

```bash
# Clone and navigate
cd systematic_trading/book

# Install dependencies
pip install -r requirements.txt

# Test the build
make build
```

### Making Changes

1. **Find the relevant file** in `part1/`, `part2/`, etc.
2. **Edit the notebook** using Jupyter Lab or your favorite editor
3. **Test your changes** by running all cells
4. **Rebuild the book** to see how it looks

```bash
make clean
make build
make serve  # View at http://localhost:8000
```

## 📝 Chapter Structure

### Notebook Template

Every chapter should follow this structure:

```markdown
# Chapter N: Title

## Learning Objectives
- What readers will learn
- Specific skills they'll gain

## Section 1: Introduction
[Motivation and context]

## Section 2: Concept Explanation
[Core concept with analogies]

### Interactive Example
[Code cells with visualizations]

## Section 3: Implementation
[Real code from the repository]

## Key Takeaways
[Summary of main points]

## Exercises
[Practice problems for readers]

## Next Steps
[Link to next chapter]
```

### Code Cell Guidelines

1. **Import at the top**
   ```python
   import numpy as np
   import pandas as pd
   import matplotlib.pyplot as plt
   ```

2. **Set reproducible seeds**
   ```python
   np.random.seed(42)
   ```

3. **Use clear variable names**
   ```python
   # Good
   daily_returns = prices.pct_change()

   # Bad
   x = p.pct_change()
   ```

4. **Add comments explaining WHY**
   ```python
   # Normalize by price to make signals comparable across stocks
   normalized_signal = raw_signal / price
   ```

5. **Generate visualizations**
   ```python
   plt.figure(figsize=(12, 6))
   plt.plot(equity_curve)
   plt.title('Strategy Performance')
   plt.xlabel('Days')
   plt.ylabel('Equity ($)')
   plt.grid(alpha=0.3)
   plt.show()
   ```

## 🎨 Writing Style

### Tone
- **Conversational but professional**
- **Assume no prior knowledge**
- **Build complexity gradually**

### Good Example
```markdown
A moving average is simply the average price over a period of time.

For example, the 5-day moving average of Google stock is:
(Day1_price + Day2_price + Day3_price + Day4_price + Day5_price) / 5

This smooths out daily noise and reveals the underlying trend.
```

### Bad Example
```markdown
We compute the n-period SMA using a rolling window function applied to the time series.
```

### Use Analogies

```markdown
Think of volatility like a speedometer:
- Low volatility = Driving at steady 60 mph
- High volatility = Accelerating to 100 mph, braking to 20 mph
```

## 📊 Visualizations

### Requirements
- Every major concept should have a visualization
- Use clear labels, titles, and legends
- Include grid for easier reading
- Use colorblind-friendly palettes

### Example

```python
import matplotlib.pyplot as plt
import seaborn as sns

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)

# Create plot
fig, ax = plt.subplots()
ax.plot(dates, prices, label='Stock Price', linewidth=2)
ax.plot(dates, ma_fast, label='Fast MA', alpha=0.7)
ax.plot(dates, ma_slow, label='Slow MA', alpha=0.7)

# Formatting
ax.set_xlabel('Date', fontsize=12)
ax.set_ylabel('Price ($)', fontsize=12)
ax.set_title('Moving Average Crossover Strategy', fontsize=14, fontweight='bold')
ax.legend(loc='best', fontsize=10)
ax.grid(alpha=0.3)

plt.tight_layout()
plt.show()
```

## 🧪 Testing

### Before Submitting

1. **Run all cells in order**
   ```bash
   # In Jupyter
   Kernel -> Restart & Run All
   ```

2. **Check for errors**
   - No cell should produce errors
   - All outputs should be meaningful

3. **Test the build**
   ```bash
   make clean
   make build
   ```

4. **Review the HTML**
   ```bash
   make serve
   # Check that formatting looks good
   ```

## 📚 Adding a New Chapter

### Step 1: Create the Notebook

```bash
# Copy template
cp templates/chapter_template.ipynb part3/11_my_new_chapter.ipynb
```

### Step 2: Update Table of Contents

Edit `_toc.yml`:

```yaml
- file: part3/overview
  sections:
    - file: part3/10_existing_chapter
    - file: part3/11_my_new_chapter  # Add this line
```

### Step 3: Write Content

Follow the chapter structure above.

### Step 4: Add Cross-References

```markdown
See [Chapter 4](../part2/04_trend_following.ipynb) for more on EWMAC.

Refer back to [volatility calculations](05_understanding_volatility.ipynb#calculating-volatility).
```

### Step 5: Build and Review

```bash
make clean
make build
make serve
```

## 🔗 Linking to Repository Code

When referencing code from the main repository:

```python
# Add parent directory to path
import sys
sys.path.insert(0, '../..')

# Now you can import
from strategy.trend_following import EWMAC
from data.data_manager import DataManager
```

Always show where the code comes from:

```markdown
This implementation is in [`strategy/trend_following.py:118`](../../strategy/trend_following.py#L118)
```

## 📖 Documentation Standards

### Admonitions

Use MyST admonitions for callouts:

```markdown
```{admonition} Key Insight
:class: tip
Volatility targeting ensures equal risk across all positions.
```

```{admonition} Warning
:class: warning
Never use future data in backtests - this creates lookahead bias!
```

```{admonition} Note
:class: note
The Sharpe ratio measures risk-adjusted returns.
```
```

### Math Equations

Use LaTeX for formulas:

```markdown
The Sharpe ratio is calculated as:

$$
\text{Sharpe} = \frac{\mu - r_f}{\sigma}
$$

where:
- $\mu$ = mean return
- $r_f$ = risk-free rate
- $\sigma$ = standard deviation of returns
```

### Code References

```markdown
The position sizer calculates shares as:

```python
shares = (capital * target_vol) / (price * asset_vol)
```

This ensures that each position contributes equal volatility.
```

## 🐛 Common Mistakes to Avoid

### 1. Lookahead Bias
```python
# WRONG - uses future data
signal = (future_price > current_price)

# RIGHT - only uses past data
signal = (fast_ma > slow_ma)
```

### 2. Not Handling NaN
```python
# WRONG - fails on missing data
returns = prices.pct_change()

# RIGHT - handles NaN properly
returns = prices.pct_change().fillna(0)
```

### 3. Forgetting to Set Seeds
```python
# WRONG - non-reproducible
np.random.normal(0, 1, 100)

# RIGHT - reproducible
np.random.seed(42)
np.random.normal(0, 1, 100)
```

### 4. Poor Plot Labels
```python
# WRONG
plt.plot(x)

# RIGHT
plt.plot(equity_curve, label='Strategy Equity')
plt.xlabel('Trading Days')
plt.ylabel('Portfolio Value ($)')
plt.title('Backtest Results: EWMAC 16/64')
plt.legend()
```

## 🎯 Content Priorities

### Essential for Every Chapter
- [ ] Clear learning objectives
- [ ] Interactive code examples
- [ ] Visualizations of key concepts
- [ ] Connection to repository code
- [ ] Key takeaways summary
- [ ] Exercises for practice

### Nice to Have
- Multiple examples
- Advanced variations
- Performance comparisons
- Real-world case studies

## 📬 Submitting Changes

### If Using Git

1. Create a feature branch
   ```bash
   git checkout -b add-chapter-11
   ```

2. Make your changes

3. Test thoroughly
   ```bash
   make clean
   make build
   make test
   ```

4. Commit with clear messages
   ```bash
   git add book/part3/11_my_chapter.ipynb
   git commit -m "Add Chapter 11: Advanced Position Sizing"
   ```

5. Push and create pull request

### If Not Using Git

- Email the notebook file
- Include description of changes
- Note any new dependencies

## 🙏 Questions?

- Open an issue on GitHub
- Ask in discussions
- Email the maintainers

Thank you for contributing to make this book better! 🚀
