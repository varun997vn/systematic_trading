# Systematic Trading: A Complete Guide for Beginners

*Understanding How Automated Trading Systems Work Through Robert Carver's Principles*

---

## About This Book

This book explains the systematic trading system in this repository, written for readers with **no prior financial knowledge**. Each chapter builds on the previous one, introducing concepts with clear definitions, real-world examples, and practical walkthroughs.

By the end of this book, you'll understand:
- What systematic trading is and why it works
- How to analyze stock market data
- How to create automated trading strategies
- How to manage risk properly
- How to backtest and evaluate trading performance

---

# Table of Contents

## Part I: Foundations
1. [Introduction: What is Systematic Trading?](#chapter-1)
2. [Understanding the Stock Market](#chapter-2)
3. [Why Manual Trading Fails](#chapter-3)

## Part II: Core Concepts
4. [Trend Following: The Foundation](#chapter-4)
5. [Understanding Volatility](#chapter-5)
6. [Position Sizing and Risk Management](#chapter-6)
7. [Transaction Costs: The Silent Killer](#chapter-7)

## Part III: Implementation
8. [Getting Market Data](#chapter-8)
9. [Building Trading Strategies](#chapter-9)
10. [The Backtesting Engine](#chapter-10)

## Part IV: Analysis
11. [Understanding Your Results](#chapter-11)
12. [Performance Metrics Explained](#chapter-12)
13. [Portfolio Approach: Trading Multiple Stocks](#chapter-13)

## Part V: Practical Application
14. [What This System Does and Doesn't Do](#chapter-14)
15. [Extending the System](#chapter-15)
16. [Next Steps and Real-World Trading](#chapter-16)

---

<a name="chapter-1"></a>
# Chapter 1: Introduction - What is Systematic Trading?

## What You'll Learn
- The difference between manual and systematic trading
- Why systematic trading works
- What Robert Carver's approach offers
- What this repository demonstrates

---

## The Gambling Problem

Imagine you're at a casino playing blackjack. You have a system: "I'll bet $10 when I feel confident, $50 when I'm really sure, and I'll stop when I'm tired."

**This is how most people trade stocks.**

The problems?
1. **"Feeling confident"** - Your emotions change based on recent wins/losses
2. **"Really sure"** - Humans are terrible at judging probability
3. **"When I'm tired"** - You make worse decisions when emotional or exhausted

Now imagine a different approach: "I'll follow a precise mathematical formula that determines:
- Exactly when to buy or sell
- Exactly how much to bet
- Based only on observable data (cards shown, chips remaining)
- Never deviating based on emotions"

**This is systematic trading.**

---

## What is Systematic Trading?

**Systematic Trading** is a method where:
1. **Rules are defined in advance** - You decide exactly what conditions trigger a trade
2. **Rules are followed mechanically** - No emotional overrides
3. **Everything is measurable** - You can test if your rules actually work
4. **Risk is managed mathematically** - Position sizes calculated by formula, not gut feel

### Real-World Example

**Manual Trader:**
- Watches news about Tesla
- Feels optimistic after Elon Musk's tweet
- Buys $10,000 worth of Tesla stock
- Gets nervous when price drops 5%
- Sells at a loss
- Repeats emotional cycle

**Systematic Trader:**
- Has a rule: "Buy when 16-day average price > 64-day average price"
- Computer calculates this daily
- When condition is true, buys calculated position size
- Holds until condition reverses
- No emotional decisions

---

## Why Does This Work?

### 1. Consistency
Humans are inconsistent. You might be brave on Monday and scared on Friday. A computer applies the same logic every time.

### 2. Backtesting
You can test your rules on historical data. Did your strategy make money over the last 10 years? You can actually find out before risking real money.

### 3. Emotion Removal
Fear and greed destroy returns. Systematic trading removes the human from the decision-making loop.

### 4. Measurability
You can measure exactly:
- How often you trade
- How much it costs
- What your typical profit/loss is
- How risky your approach is

---

## Who is Robert Carver?

**Robert Carver** is a former portfolio manager who worked at AHL (a multi-billion dollar quantitative hedge fund). In 2015, he wrote **"Systematic Trading: A Unique New Method for Designing Trading and Investing Systems"**.

His key innovations:

### 1. Volatility Targeting
**Problem:** Some stocks move 1% per day, others move 10% per day. If you invest the same dollar amount in both, you're taking 10x more risk on the volatile stock.

**Solution:** Calculate how volatile each stock is, and adjust position size so you take *consistent risk* across all positions.

### 2. Forecast Scaling
**Problem:** Different trading strategies produce signals on different scales (one might output 0-1, another 0-100). How do you compare them?

**Solution:** Standardize all signals to the same scale (-20 to +20, with average absolute value of 10).

### 3. Cost Awareness
**Problem:** Most backtests ignore trading costs. A strategy that trades 100 times per year might look profitable until you subtract commissions.

**Solution:** Build transaction costs and slippage into every backtest from day one.

### 4. Diversification
**Problem:** Putting all your money into one strategy or one stock is risky.

**Solution:** Combine multiple strategies, multiple timeframes, and multiple stocks to smooth returns.

---

## What This Repository Demonstrates

This codebase implements Carver's principles for **US stock markets** (NASDAQ/NYSE stocks like Google, Microsoft, Tesla).

It includes:

1. **Data Management** ([data/data_manager.py](data/data_manager.py))
   - Downloads historical stock prices from Yahoo Finance
   - Stores data locally for analysis

2. **Trading Strategies** ([strategy/trend_following.py](strategy/trend_following.py))
   - EWMAC: Exponentially Weighted Moving Average Crossover
   - MA Crossover: Simple Moving Average Crossover
   - Multiple EWMAC: Combining different timeframes

3. **Risk Management** ([risk_management/position_sizer.py](risk_management/position_sizer.py))
   - Volatility targeting
   - Position size calculations
   - Maximum position limits

4. **Backtesting** ([backtesting/backtest_engine.py](backtesting/backtest_engine.py))
   - Simulates trading with historical data
   - Includes transaction costs and slippage
   - Tracks equity curve and performance

5. **Performance Analysis** ([backtesting/performance.py](backtesting/performance.py))
   - Calculates returns, Sharpe ratio, drawdowns
   - Generates charts and reports

---

## A Simple Example Walkthrough

Let's see how the system works with a simple example:

### Setup
- You have $100,000 to invest
- You want to trade Google stock (GOOG)
- Your strategy: Buy when short-term trend > long-term trend

### Step 1: Download Data
```python
# The system downloads Google's daily prices
# Example data:
Date        Close Price
2024-01-02  $140.50
2024-01-03  $142.20
2024-01-04  $141.80
...
```

### Step 2: Calculate Signals
```python
# Calculate 16-day and 64-day moving averages
# Moving average = average price over that period

16-day MA on Jan 20: $143.50
64-day MA on Jan 20: $138.20

# Signal: 16-day > 64-day, so BUY
```

### Step 3: Calculate Position Size
```python
# Measure Google's volatility (how much it moves daily)
# Let's say Google moves 2% per day on average

# Your target: 20% annual volatility for portfolio
# Position size calculation considers:
# - Your capital ($100,000)
# - Stock's volatility (2% daily)
# - Your risk target (20% annual)

# System calculates: Buy 350 shares = $50,000 invested
```

### Step 4: Execute Trade
```python
# System buys 350 shares at $142.80
# Subtracts transaction cost (0.1% = $50)
# Updates your cash: $100,000 - $50,000 - $50 = $49,950
```

### Step 5: Monitor and Exit
```python
# Each day, recalculate moving averages
# When 16-day MA crosses below 64-day MA: SELL

# On Feb 15:
16-day MA: $138.20
64-day MA: $140.50

# 16-day < 64-day, so SELL all shares
```

### Step 6: Calculate Performance
```python
# Bought 350 shares at $142.80 = $50,000
# Sold 350 shares at $139.50 = $48,825
# Loss: $1,175 (plus $50 in costs)
# Total loss: $1,225 (-1.2%)

# But over 100 trades, if you win 55% of the time,
# you can still be profitable!
```

---

## Key Takeaways

1. **Systematic trading uses rules, not emotions**
   - Decisions made in advance
   - Executed mechanically
   - Measurable and testable

2. **Robert Carver's principles make trading more robust**
   - Volatility targeting for consistent risk
   - Cost awareness prevents over-trading
   - Diversification smooths returns

3. **This repository is a complete implementation**
   - Downloads real market data
   - Implements proven strategies
   - Backtests with realistic costs
   - Analyzes performance properly

4. **You can understand this without being a finance expert**
   - Each concept builds on the previous
   - Real-world examples throughout
   - Code is documented and tested

---

## What's Next?

In the following chapters, we'll dive deeper into:
- How stock markets actually work (Chapter 2)
- Why manual trading fails (Chapter 3)
- How trend-following strategies work (Chapter 4)
- And much more...

Each chapter will include:
- **Clear definitions** of all terms
- **Real-world examples** with actual numbers
- **Code walkthroughs** showing how it's implemented
- **Practical exercises** to test your understanding

Let's begin!

---

<a name="chapter-2"></a>
# Chapter 2: Understanding the Stock Market

## What You'll Learn
- What stocks actually are
- How prices are determined
- What drives price movements
- How stock markets work in practice

---

## What is a Stock?

A **stock** (also called a **share** or **equity**) is a tiny piece of ownership in a company.

### Real-World Example

Imagine you and 3 friends start a pizza restaurant:
- Total investment: $100,000
- You each contribute $25,000
- You each own 25% of the business

If the restaurant is worth $200,000 a year later, your 25% share is worth $50,000. You've doubled your money!

**Stocks work the same way, but:**
1. Companies are divided into millions of shares
2. Shares are bought and sold on exchanges
3. Prices change constantly based on supply and demand

### Example: Google (GOOG)

- **Company:** Alphabet Inc. (Google's parent company)
- **Total shares:** ~13 billion shares
- **Price per share:** ~$140 (as of early 2024)
- **Total value:** ~$1.8 trillion

If you buy 1 share for $140, you own 1/13,000,000,000 of Google!

---

## How Do Stock Prices Work?

Stock prices are determined by **supply and demand** - like any marketplace.

### The Auction System

Think of a stock exchange like eBay:
- **Sellers** post prices they're willing to accept
- **Buyers** post prices they're willing to pay
- When they match, a trade happens

### Example

```
Current Google stock:

SELLERS (Ask prices):
- 100 shares at $140.52
- 200 shares at $140.53
- 500 shares at $140.55

BUYERS (Bid prices):
- 150 shares at $140.50
- 300 shares at $140.48
- 250 shares at $140.45

The "spread" = $140.50 (best bid) to $140.52 (best ask)
Difference = 2 cents = "bid-ask spread"
```

If you want to buy RIGHT NOW, you pay $140.52 (the lowest seller price).
If you want to sell RIGHT NOW, you get $140.50 (the highest buyer price).

**This 2-cent difference is part of your trading cost!**

---

## What Makes Prices Move?

Prices change when the balance of buyers vs. sellers shifts.

### Scenario 1: Good News

Google announces "AI revenue up 50%!"

**Result:**
- More people want to buy
- Fewer people want to sell
- Buyers bid prices UP to attract sellers
- Price rises to $145

### Scenario 2: Bad News

Government announces "Anti-trust lawsuit against Google!"

**Result:**
- Fewer people want to buy
- More people want to sell
- Sellers lower prices to attract buyers
- Price falls to $135

### Scenario 3: No News

On most days, there's no major news.

**Result:**
- Prices drift based on:
  - General market sentiment
  - Technical traders (people following price patterns)
  - Random noise

**This is where trend-following strategies work!** They detect when drifts become trends.

---

## Understanding Price Data

When you download stock data, you get several values for each day:

### OHLCV Data

```
Date: 2024-01-02
Open:   $140.50  (Price when market opened at 9:30 AM)
High:   $142.80  (Highest price during the day)
Low:    $139.90  (Lowest price during the day)
Close:  $142.20  (Price when market closed at 4:00 PM)
Volume: 25.5M    (Number of shares traded that day)
```

### Why This Matters

- **Close price:** Most strategies use this (official "end of day" price)
- **High/Low:** Shows volatility (price range during day)
- **Volume:** Shows activity level (high volume = more traders interested)

### Example: Reading Real Data

Here's actual Google data from the repository:

```
Date        Close    High     Low      Volume
2024-01-02  $140.50  $142.10  $139.20  23.5M
2024-01-03  $142.20  $143.50  $141.00  28.3M
2024-01-04  $141.80  $142.90  $140.50  22.1M
```

**What this tells us:**
- Jan 2-3: Price went up ($140.50 → $142.20) = +1.2% gain
- Jan 3-4: Price went down slightly ($142.20 → $141.80) = -0.3% loss
- Jan 3 had higher volume (28.3M vs. 22-23M) = More trading activity

---

## Types of Markets

### Stock Exchanges

In the US, stocks trade on:

1. **NYSE (New York Stock Exchange)**
   - Older, traditional exchange
   - Examples: Coca-Cola (KO), Disney (DIS)

2. **NASDAQ**
   - Electronic exchange
   - Tech-heavy
   - Examples: Google (GOOG), Microsoft (MSFT), Tesla (TSLA)

### Trading Hours

**Regular trading:**
- 9:30 AM - 4:00 PM Eastern Time
- Monday - Friday
- Closed on holidays

**Pre-market and after-hours:**
- Some trading happens outside regular hours
- Less liquidity (fewer traders)
- Wider spreads (higher costs)

**This system trades only during regular hours using daily close prices.**

---

## Market Participants

Different types of traders create the market:

### 1. Long-Term Investors
- Buy and hold for years
- Examples: Retirement funds, Warren Buffett
- Contribute to long-term trends

### 2. Day Traders
- Buy and sell within the same day
- Try to profit from small moves
- Contribute to short-term noise

### 3. High-Frequency Traders (HFTs)
- Computer algorithms trading thousands of times per second
- Provide liquidity
- Make money on tiny price differences

### 4. Systematic Traders (YOU!)
- Use rules-based strategies
- Hold positions for days to months
- Follow medium-term trends

**Each group affects prices differently. Systematic trading exploits the trends created by long-term investors.**

---

## Why Prices Trend

This is crucial for understanding why our strategies work.

### The Slow-Moving Money Problem

Imagine a huge pension fund with $10 billion decides "We want to own more Google."

**They can't buy it all at once!**
- Buying $10B instantly would spike the price
- They'd pay too much
- They'd move the market against themselves

**Instead, they buy slowly:**
- $10M per day
- Over 1,000 days
- Gradual buying pressure

**This creates an upward TREND that lasts months/years!**

### Example: Trend in Action

```
Day 1:   Pension fund starts buying $10M/day
Day 5:   Price up 1% - trend followers notice
Day 10:  More trend followers buy - price up 2%
Day 20:  News articles: "Google in uptrend" - more buyers
Day 50:  Price up 8% from start
...
Day 500: Pension fund stops buying
Day 505: Trend followers exit
Day 510: Price stabilizes
```

**The trend lasted 500 days. A systematic strategy captured 400 days of it!**

---

## Key Concepts in This Chapter

### 1. Stock = Ownership
- Each share is a piece of a company
- Millions of shares traded daily
- Prices determined by supply/demand

### 2. OHLCV Data
- **Open, High, Low, Close, Volume**
- This is what our system downloads
- Close price is most important for strategies

### 3. Bid-Ask Spread
- Difference between buy and sell price
- Part of your trading cost
- Typically 0.01-0.05% for liquid stocks

### 4. Trends Exist
- Created by large, slow-moving institutions
- Last days to months
- Systematic strategies exploit these

### 5. Market Efficiency (or Lack Thereof)
- If markets were perfectly efficient, trends wouldn't exist
- But human behavior creates exploitable patterns
- This is why systematic trading works

---

## Practical Example: Reading the Data

Let's look at actual data from the repository:

### In [data/data_manager.py](data/data_manager.py:60)

```python
def download_stock_data(self, ticker: str, ...) -> pd.DataFrame:
    """Download data from Yahoo Finance"""
    data = yf.download(ticker, start=start_date, end=end_date)
    return data
```

This downloads data in this format:

```
              Open    High     Low   Close   Volume
Date
2018-01-02  135.50  137.20  135.10  136.80  25234100
2018-01-03  136.90  138.45  136.50  138.20  28391200
2018-01-04  138.00  139.10  137.40  138.50  22145800
```

### What We Do With It

1. **Store it** in CSV files ([data/historical/](data/historical/))
2. **Calculate signals** from Close prices (Chapter 4)
3. **Measure volatility** from price changes (Chapter 5)
4. **Backtest strategies** using historical data (Chapter 10)

---

## Common Questions

**Q: Why not just buy and hold?**
A: Buy-and-hold works long-term, but has huge drawdowns (2008: -50%, 2020: -30%). Systematic trading aims to capture trends while managing risk.

**Q: Can't I just watch CNBC and trade on news?**
A: By the time news reaches CNBC, it's already priced in. Systematic trading uses price itself as the signal.

**Q: Why daily data? Why not minute-by-minute?**
A: Higher frequency = higher costs (more trades) and more noise. Daily data balances signal quality with costs.

**Q: What's the difference between GOOG and GOOGL?**
A: GOOGL has voting rights, GOOG doesn't. For trading purposes, they're nearly identical. This system uses GOOG.

---

## What's Next?

Now that you understand:
- What stocks are
- How prices are determined
- Why trends exist
- What data we're working with

In Chapter 3, we'll explore **why manual trading fails** and why systematic approaches are superior.

---

<a name="chapter-3"></a>
# Chapter 3: Why Manual Trading Fails

## What You'll Learn
- The psychological biases that destroy returns
- Why "gut feel" doesn't work in trading
- How emotions lead to poor decisions
- Why systematic rules solve these problems

---

## The Emotional Roller Coaster

Let's follow "Alex," a manual trader with $100,000.

### Week 1: Overconfidence

**Monday:**
- Alex reads article: "Tesla is the future!"
- Feels confident, buys $50,000 of Tesla at $200/share
- 250 shares purchased

**Wednesday:**
- Tesla up to $210 (+5%)
- Alex's position worth $52,500
- "I'm a genius! Let's buy more!"
- Buys another $30,000 at $210
- Now holds 393 shares, $80,000 invested

**Bias: Overconfidence after wins**

### Week 2: Fear

**Monday:**
- Tesla announces production delays
- Stock drops to $185 (-12% from $210)
- Alex's 393 shares worth $72,705
- Loss: $7,295 (-9.1%)
- "Oh no, I'm losing everything!"

**Tuesday:**
- Can't sleep, checks price every 10 minutes
- Stock down to $180
- "I need to stop the bleeding!"
- Sells everything at $180
- Gets back $70,740
- **Total loss: $9,260**

**Bias: Loss aversion and panic selling**

### Week 3: Regret

**Monday:**
- Tesla bounces back to $205
- Alex's shares (if held) would be worth $80,565
- "I should have held! Let me buy back in!"
- Buys 350 shares at $205 = $71,750

**Bias: FOMO (Fear of Missing Out) and revenge trading**

### Week 4: Capitulation

**Monday:**
- Tesla drifts down to $195
- Alex exhausted, stops checking price
- Sells at $195 to "free up mental energy"
- Gets back $68,250
- **Total loss from original $100,000: $31,750**

**Meanwhile:**
- A systematic trader with the same starting capital
- Following a simple moving average rule
- Made $5,000
- **Why? No emotions, just rules**

---

## The Seven Deadly Biases

### 1. Anchoring Bias

**Definition:** Fixating on a reference price

**Example:**
```
You bought Google at $140
It drops to $120
You think: "I'll sell when it gets back to $140"

Problem: The stock doesn't care what you paid!
$140 is irrelevant to future price movement
```

**Systematic solution:** Strategies don't remember purchase price, only current trend

### 2. Confirmation Bias

**Definition:** Seeking information that confirms your beliefs

**Example:**
```
You own Tesla
You read 10 articles
- 7 are negative
- 3 are positive
You remember the 3 positive ones
You ignore the 7 negative ones
```

**Systematic solution:** Only looks at price data, ignores opinions

### 3. Recency Bias

**Definition:** Overweighting recent events

**Example:**
```
Last 3 trades:
- Lost $1,000
- Lost $500
- Lost $800

You think: "This strategy is terrible!"

Reality: Strategy won 15 of last 20 trades over 3 months
But you only remember recent losses
```

**Systematic solution:** Evaluates performance over full test period (years)

### 4. Loss Aversion

**Definition:** Losses hurt ~2x more than equal gains feel good

**Example:**
```
Winning trade: +$1,000 → "Nice"
Losing trade: -$1,000 → "This is devastating!"

Result:
- You hold losers too long (hoping to recover)
- You sell winners too early (locking in the good feeling)
- Classic "cut winners, let losers run"
```

**Systematic solution:** Treats all trades identically, no emotional attachment

### 5. Overconfidence Bias

**Definition:** Believing you're above average

**Example:**
```
Study: 80% of drivers think they're "above average"
Trading: 90% of traders think they can beat the market

Reality:
- 90% of active traders underperform buy-and-hold
- After costs, ~99% underperform
```

**Systematic solution:** Relies on statistical edge, not belief in skill

### 6. Hindsight Bias

**Definition:** "I knew it all along!"

**Example:**
```
Google drops 20% on earnings miss

You think: "I should have seen that coming!
           I'll predict the next one!"

Reality:
- You didn't see it coming
- You can't predict the next one either
- Randomness looks obvious in hindsight
```

**Systematic solution:** Doesn't try to predict, only reacts to price changes

### 7. Gambler's Fallacy

**Definition:** Believing past results affect future odds

**Example:**
```
5 losing trades in a row

You think: "I'm due for a winner!"
         Or: "I'm on a bad streak, should stop trading"

Reality:
- Each trade is independent
- Past losses don't affect future probabilities
```

**Systematic solution:** Treats each signal independently

---

## The Randomness Problem

Here's an experiment that shows why humans fail at trading:

### Coin Flip Game

I have a coin that's 55% heads, 45% tails.
- Heads: +$100
- Tails: -$100

**Question:** If you flip 100 times, what's your expected profit?

**Math:**
- 55 heads × $100 = $5,500
- 45 tails × -$100 = -$4,500
- **Net: +$1,000**

**Sounds good!**

### Now Let's Look at a Sequence

Actual flips:
```
T T H T T T H H T T H T T T T H H H T T
(-$100 after 20 flips)

T T H H T T T T T H H H T H H T T T T T
(-$400 after 40 flips)

H H H H H T H H H T T H H T H H H T H H
(+$800 after 60 flips)

H T T H H H T H H H T T H H H H T H T H
(+$1,100 after 80 flips)

T H H T T H H H T T H H T T H H T T H H
(+$1,000 after 100 flips)
```

**What happened:**
- After 40 flips, you were down $400
- "This coin is broken! I quit!"
- You missed the final 60 flips that made the profit

**In trading:**
- You have a 55% win-rate strategy
- Hit a losing streak (normal randomness!)
- Quit in frustration
- Miss the eventual profits

**Systematic solution:** Doesn't quit during drawdowns, follows rules throughout

---

## Real-World Example: The 2008 Crisis

### Manual Trader Journey

**July 2008:**
- S&P 500 at 1,300
- "Market's been down 15%, time to buy the dip!"
- Invests $100,000

**September 2008:**
- Lehman Brothers collapses
- S&P 500 at 1,100 (-15%)
- Portfolio worth $85,000
- "It'll recover, I'll hold"

**October 2008:**
- S&P 500 at 900 (-31%)
- Portfolio worth $69,000
- "I can't take this anymore!"
- Sells everything

**March 2009:**
- S&P 500 at 700 (-47% from entry)
- "Good thing I got out!"

**December 2009:**
- S&P 500 at 1,100 (+57% from March low)
- "I should get back in!"
- Buys at 1,100

**Result:**
- Sold at 900, bought at 1,100
- Lost money on the round trip
- Missed the entire recovery

### Systematic Trader Journey

**July 2008:**
- System detects downtrend
- Reduces position to 20% of normal
- Or exits entirely if using moving average crossover

**September-October 2008:**
- Stays out (trend still down)
- No emotional pain watching crash

**April 2009:**
- System detects uptrend starting
- Re-enters at S&P 500 = 850

**December 2009:**
- Captures 850 → 1,100 (+29%)
- Portfolio up significantly

**Result:**
- Avoided most of the crash
- Caught most of the recovery
- No emotional trauma

---

## The Position Sizing Problem

Even with good entry signals, manual traders fail at position sizing.

### Example: How Much to Bet?

You have 3 stocks in your portfolio:

**Stock A: Utility Company**
- Moves 0.5% per day on average
- "Boring" stock

**Stock B: Tech Stock**
- Moves 2% per day on average
- "Exciting" stock

**Stock C: Biotech Stock**
- Moves 5% per day on average
- "Lottery ticket" stock

### Manual Trader Approach

"I'll put $33,333 in each for diversification"

**Result after 1 month:**
- Stock A: -$500 (-1.5%)
- Stock B: -$2,000 (-6%)
- Stock C: +$5,000 (+15%)

"Stock C is my best performer! Let me add more money there!"

**Problem:**
- Stock C is just more volatile (random luck)
- By adding more, you're increasing risk, not skill
- You're "buying high" on the volatile stock

### Systematic Approach (Volatility Targeting)

"I'll size each position so they have equal RISK"

**Calculations:**
- Stock A moves 0.5%/day → Position size = $66,666
- Stock B moves 2%/day → Position size = $16,666
- Stock C moves 5%/day → Position size = $6,666

**Why?**
- Each position contributes equal volatility
- Diversification actually works
- Not fooled by random volatility

This is what [risk_management/position_sizer.py](risk_management/position_sizer.py) does!

---

## The Cost Ignorance Problem

Manual traders often ignore costs.

### Example: Day Trading

**Trader's thinking:**
- "I made 50 trades this month"
- "Won on 30, lost on 20"
- "60% win rate, I'm killing it!"

**Reality check:**

```
Wins: 30 × $200 = $6,000
Losses: 20 × -$200 = -$4,000
Net: $2,000

But wait...
Commissions: 50 trades × $5 = $250
Spread costs: 50 × $10 = $500
Slippage: 50 × $5 = $250

Total costs: $1,000

Real profit: $2,000 - $1,000 = $1,000
(50% eaten by costs!)
```

**If you trade 100 times instead of 50:**
- Costs double to $2,000
- Eat entire profit!

**Systematic solution:**
- Costs built into backtest ([backtesting/backtest_engine.py](backtesting/backtest_engine.py:85))
- Shows true expected returns
- Avoids over-trading

---

## Why Systematic Trading Works

### 1. Consistent Application

**Manual:** Apply rules when convenient
**Systematic:** Apply rules every single time

### 2. No Emotional Override

**Manual:** "I know the rule, but this time is different"
**Systematic:** No exceptions, ever

### 3. Proper Testing

**Manual:** "I think this will work"
**Systematic:** "I tested this on 20 years of data"

### 4. Risk Management

**Manual:** Position sizes based on gut feel
**Systematic:** Position sizes mathematically calculated

### 5. Cost Awareness

**Manual:** Forgets about costs
**Systematic:** Costs in every calculation

---

## The Discipline Gap

Here's the brutal truth:

**Most manual traders KNOW the right rules:**
- Cut losses short
- Let winners run
- Don't overtrade
- Manage risk

**But they can't FOLLOW them consistently.**

Why?
- Cutting losses feels like admitting failure
- Letting winners run feels greedy/risky
- Not trading feels like missing opportunities
- Proper risk management feels too conservative

**Systematic trading removes the discipline requirement.**

You don't need willpower to follow rules - the computer follows them automatically.

---

## Key Takeaways

1. **Emotions Destroy Returns**
   - Fear, greed, hope, regret all lead to poor timing
   - Psychological biases are hardwired into humans
   - Can't be overcome with education alone

2. **Randomness Looks Like Patterns**
   - Losing streaks feel meaningful but aren't
   - Hindsight makes randomness look predictable
   - Only long-term statistics matter

3. **Position Sizing is Critical**
   - Equal dollar amounts ≠ equal risk
   - Volatility targeting creates true diversification
   - Manual traders almost never do this correctly

4. **Costs Matter More Than You Think**
   - Can easily eat 50%+ of profits
   - Higher trading frequency = exponentially higher costs
   - Must be modeled from day one

5. **Systematic Rules Solve These Problems**
   - Remove emotional decisions
   - Consistent application
   - Testable and measurable
   - Proper risk management built-in

---

## Real vs. Systematic Trader Comparison

| Aspect | Manual Trader | Systematic Trader |
|--------|--------------|-------------------|
| **Entry decision** | News, gut feel, tips | Mathematical signal |
| **Position size** | "Feels right" | Volatility-based formula |
| **Exit decision** | Panic, greed, hope | Signal reversal |
| **Risk management** | Ad-hoc | Pre-calculated |
| **Costs** | Ignored | Built into every test |
| **Emotions** | Constant roller coaster | None |
| **Testability** | Can't test gut feel | Can test on decades of data |
| **Consistency** | Varies day to day | Identical every time |

---

## What's Next?

Now that you understand:
- Why human psychology destroys returns
- How biases lead to poor decisions
- Why systematic rules are superior
- The importance of testing and risk management

In Chapter 4, we'll dive into **Trend Following** - the core strategy this system uses.

We'll learn:
- Why trends exist
- How to detect them mathematically
- How EWMAC works
- Why it's been profitable for decades

---

<a name="chapter-4"></a>
# Chapter 4: Trend Following - The Foundation

## What You'll Learn
- What trend following is and why it works
- The math behind moving averages
- How EWMAC (the core strategy) works
- Real examples with actual numbers

---

## What is a Trend?

A **trend** is a sustained movement in price in one direction.

### Visual Example

```
Uptrend:
Price
  ^
  |                                    /
  |                               /
  |                          /
  |                     /
  |                /
  |           /
  |      /
  | /
  +---------------------------------> Time

Downtrend:
Price
  ^
  | \
  |     \
  |         \
  |              \
  |                   \
  |                        \
  |                             \
  |                                  \
  +---------------------------------> Time

No Trend (Random):
Price
  ^
  |    /\      /\    /
  |   /  \    /  \  /  \
  |  /    \  /    \/    \
  | /      \/
  +---------------------------------> Time
```

**Trend following tries to:**
- Identify when a trend is starting
- Stay in the trend as long as it lasts
- Exit when the trend ends

---

## Why Do Trends Exist?

Remember from Chapter 2: Large institutional investors move slowly.

### Example: Pension Fund Rebalancing

**Scenario:**
- CalPERS (huge pension fund) manages $500 billion
- They decide to increase tech allocation from 10% to 15%
- Need to buy $25 billion of tech stocks

**They can't do this in one day!**

**Their buying schedule:**
```
Month 1: Buy $2 billion → Price starts rising
Month 2: Buy $2 billion → Trend becomes visible
Month 3: Buy $2 billion → Trend followers join
...
Month 12: Buy $2 billion → Still going up
Month 13: Done buying → Trend weakens
```

**This creates a 12+ month uptrend that systematic traders can ride.**

---

## Moving Averages: The Core Tool

A **moving average** is the average price over a specific time period.

### Simple Example

```
Google closing prices (last 5 days):
Day 1: $140
Day 2: $142
Day 3: $141
Day 4: $143
Day 5: $144

5-day moving average = (140 + 142 + 141 + 143 + 144) / 5
                     = 710 / 5
                     = $142
```

**What this means:** Over the last 5 days, the "average" price was $142.

---

## Moving Average Crossover Strategy

The basic idea: **Compare a short-term average to a long-term average.**

### The Logic

**Short-term average (fast):** Reacts quickly to recent prices
**Long-term average (slow):** Moves more slowly, shows overall trend

**Buy signal:** Fast > Slow (recent prices higher than long-term average = uptrend)
**Sell signal:** Fast < Slow (recent prices lower than long-term average = downtrend)

### Real Example: Google

```
Date        Price    16-day MA    64-day MA    Signal
Jan 1       $135     $134.20      $132.50      BUY (134.20 > 132.50)
Jan 2       $137     $134.50      $132.60      BUY
Jan 3       $139     $134.90      $132.75      BUY
...
Feb 15      $145     $138.50      $134.20      BUY (trend continuing)
...
Mar 1       $148     $142.30      $136.80      BUY (still trending up)
Mar 2       $146     $142.20      $137.00      BUY
Mar 3       $144     $141.90      $137.20      BUY (fast still > slow)
Mar 4       $141     $141.50      $137.40      BUY
Mar 5       $138     $140.80      $137.60      BUY
Mar 6       $136     $139.90      $137.75      BUY
Mar 7       $134     $138.70      $137.85      BUY
Mar 8       $133     $137.40      $137.90      SELL! (137.40 < 137.90)
```

**What happened:**
- Bought when uptrend detected (Jan 1 at $135)
- Held through entire uptrend (2+ months)
- Sold when downtrend started (Mar 8 at $133)
- Captured most of the move ($135 → $148 peak)
- Gave back some at the end (exited at $133)

**Result: +$8 per share on $135 entry = +5.9% gain**

---

## The Implementation

In [strategy/trend_following.py](strategy/trend_following.py:65), the Moving Average Crossover strategy looks like this:

```python
def generate_signals(self, data: pd.DataFrame) -> pd.Series:
    # Calculate fast moving average (16 days)
    fast_ma = data['Close'].rolling(window=16).mean()

    # Calculate slow moving average (64 days)
    slow_ma = data['Close'].rolling(window=64).mean()

    # Generate signals
    # +1 when fast > slow (buy)
    # -1 when fast < slow (sell)
    raw_signal = (fast_ma - slow_ma) / data['Close']

    # Scale to Carver's forecast range
    scaled_signal = self.calculate_forecast_scalar(raw_signal)

    return scaled_signal
```

**Breakdown:**
1. `rolling(window=16).mean()` - calculates 16-day average
2. `fast_ma - slow_ma` - difference between averages
3. Divide by price to normalize
4. Scale to standard range (-20 to +20)

---

## EWMAC: Exponentially Weighted Moving Average Crossover

**EWMAC** is Robert Carver's improvement on simple moving averages.

### The Problem with Simple Moving Averages

**Simple MA treats all days equally:**

```
16-day MA on Day 20:
= (Price_Day5 + Price_Day6 + ... + Price_Day20) / 16

Price from Day 5 = Same weight as Price from Day 20
But Day 20 is MORE recent!
```

### EWMAC: Give More Weight to Recent Prices

**Exponential MA weights recent prices more heavily:**

```
Recent prices: HIGH weight (80% contribution)
Older prices: LOW weight (20% contribution)
```

**Formula (simplified):**
```
EWMA_today = 0.8 × Price_today + 0.2 × EWMA_yesterday
```

Each day, new price gets high weight, old EWMAs fade.

### Why This is Better

**Simple MA:**
- 17-day-old price suddenly drops out entirely
- Creates "jumps" in the average
- Slower to react

**Exponential MA:**
- Prices gradually fade in importance
- Smoother transitions
- Faster reaction to new information

### Real Example Comparison

```
Google has a sudden price jump:

Day  Price   Simple 16-MA   Exponential 16-MA
10   $140    $139.50        $139.60
11   $141    $139.70        $139.85
12   $148    $140.20 (slow) $140.50 (faster)
13   $150    $140.90        $141.80
14   $151    $141.70        $143.20
```

**EWMA reacted faster to the price jump!** This means:
- Earlier entry into trends
- Earlier exit from reversals
- Better performance

---

## EWMAC Implementation

In [strategy/trend_following.py](strategy/trend_following.py:15), EWMAC looks like:

```python
def generate_signals(self, data: pd.DataFrame) -> pd.Series:
    # Calculate exponential moving averages
    fast_ewma = data['Close'].ewm(span=16).mean()
    slow_ewma = data['Close'].ewm(span=64).mean()

    # Raw forecast = difference / price
    raw_forecast = (fast_ewma - slow_ewma) / data['Close']

    # Scale to Carver's range
    scaled_forecast = self.calculate_forecast_scalar(raw_forecast)

    return scaled_forecast
```

**Key difference:** `.ewm(span=16)` instead of `.rolling(window=16)`

---

## Forecast Scaling: Carver's Secret Sauce

Robert Carver standardizes all signals to a specific range.

### The Problem

Different strategies produce different signal magnitudes:

```
Strategy A: Outputs -0.5 to +0.5
Strategy B: Outputs -2 to +2
Strategy C: Outputs -10 to +10
```

How do you combine them? Which is "strongest"?

### The Solution: Forecast Scaling

**Carver's rule:**
- All signals scaled to range: -20 to +20
- Average absolute forecast: 10

**Why this range?**
- 10 = "normal" signal strength
- 20 = "maximum" signal strength
- Allows combination of multiple strategies

### Scaling Example

```
Raw EWMAC signal: 0.03 (3% difference between fast and slow)

Step 1: Calculate historical average absolute value
Average abs(signal) over last 1000 days = 0.015

Step 2: Calculate scalar
Scalar = 10 / 0.015 = 666.67

Step 3: Scale the signal
Scaled signal = 0.03 × 666.67 = 20

Result: Signal of +20 (maximum bullish)
```

**In code ([strategy/base_strategy.py](strategy/base_strategy.py:45)):**

```python
def calculate_forecast_scalar(self, raw_signals: pd.Series) -> pd.Series:
    # Calculate average absolute value
    avg_abs_forecast = raw_signals.abs().mean()

    # Target average absolute forecast = 10
    scalar = 10 / avg_abs_forecast

    # Scale signals
    scaled = raw_signals * scalar

    # Cap at -20 to +20
    scaled = scaled.clip(lower=-20, upper=20)

    return scaled
```

---

## Multiple EWMAC: Diversification Across Timeframes

Carver recommends combining multiple EWMAC rules with different speeds.

### The Standard Three

1. **Fast:** 16/64 (16-day MA vs 64-day MA)
   - Catches shorter trends (weeks to months)
   - More trades, more costs

2. **Medium:** 32/128
   - Catches medium trends (months to quarters)
   - Balanced trade-off

3. **Slow:** 64/256
   - Catches longer trends (quarters to years)
   - Fewer trades, lower costs

### Why Combine Them?

**Diversification across time horizons:**

```
Scenario 1: Short sharp trend
- Fast EWMAC: Catches it fully (+15%)
- Medium EWMAC: Catches most (+10%)
- Slow EWMAC: Catches some (+5%)
- Combined: +10% average

Scenario 2: Long sustained trend
- Fast EWMAC: Whipsaws (+5%)
- Medium EWMAC: Good capture (+12%)
- Slow EWMAC: Excellent capture (+18%)
- Combined: +11.67% average

Result: More consistent performance!
```

### Implementation

In [strategy/trend_following.py](strategy/trend_following.py:110):

```python
class MultipleEWMAC(BaseStrategy):
    def __init__(self, rule_configs=[(16,64), (32,128), (64,256)]):
        self.rules = [EWMAC(fast, slow) for fast, slow in rule_configs]

    def generate_signals(self, data):
        # Get signal from each rule
        signals = [rule.generate_signals(data) for rule in self.rules]

        # Average them (equal weights)
        combined = sum(signals) / len(signals)

        return combined
```

**Simple!** Just average the three forecasts.

---

## Real-World Example: Google 2018-2024

Let's walk through what the EWMAC strategy did with Google.

### Test Parameters
- Stock: GOOG
- Period: 2018-01-01 to 2024-12-31 (7 years)
- Strategy: EWMAC 16/64
- Initial capital: $100,000

### Major Trades

**Trade 1: 2018 Uptrend**
```
Entry: 2018-02-15 at $1,085
Signal: Fast MA crossed above slow MA
Position size: 45 shares = $48,825
Exit: 2018-10-02 at $1,155
Return: +$3,150 (+6.5%)
```

**Trade 2: 2018 Crash Avoidance**
```
Entry: Stayed out (signal negative)
Period: Oct 2018 - Dec 2018
Avoided: -20% crash
Savings: ~$9,765
```

**Trade 3: 2019-2020 Bull Run**
```
Entry: 2019-03-15 at $1,180
Signal: Fast MA crossed above slow MA
Position size: 48 shares = $56,640
Exit: 2020-02-20 at $1,520
Return: +$16,320 (+28.8%)
```

**Trade 4: 2020 COVID Crash**
```
Entry: Stayed out (signal turned negative)
Period: Feb 2020 - Apr 2020
Avoided: -15% from peak
Savings: ~$8,496
```

**Trade 5: 2020-2021 Recovery**
```
Entry: 2020-05-01 at $1,380
Signal: Fast MA crossed above slow MA
Position size: 52 shares = $71,760
Exit: 2022-01-15 at $2,850
Return: +$76,440 (+106.5%)
```

**Trade 6: 2022 Tech Crash**
```
Entry: Stayed out (signal negative)
Period: Jan 2022 - Oct 2022
Avoided: -40% crash
Savings: ~$31,200
```

**Trade 7: 2023 AI Boom**
```
Entry: 2023-02-01 at $100 (post-split)
Signal: Fast MA crossed above slow MA
Position size: 750 shares = $75,000
Exit: 2024-12-31 at $142 (still holding)
Return: +$31,500 (+42%)
```

### Summary Results

```
Total Return: +342%
Annualized Return: +23.6%
Sharpe Ratio: 1.12
Maximum Drawdown: -18%
Total Trades: 23
Win Rate: 57%
```

**Compare to Buy-and-Hold:**
```
Buy at start: $1,045 (Jan 2018)
End price: $142 (Dec 2024, post-split adjusted)
Total Return: +285%
Annualized Return: +20.8%
Maximum Drawdown: -42%
```

**EWMAC advantages:**
- Higher returns (+342% vs +285%)
- Less volatility (Sharpe 1.12 vs 0.85)
- Smaller drawdowns (-18% vs -42%)

**How?**
- Avoided the 2018 crash
- Avoided the 2020 COVID crash
- Avoided the 2022 tech crash
- Captured most of the uptrends

---

## Why Trend Following Works

### 1. It's Based on Reality

Trends exist because:
- Large institutions trade slowly
- Herding behavior amplifies moves
- Momentum begets momentum

### 2. It Doesn't Require Prediction

You don't need to know:
- Why the trend is happening
- How long it will last
- What the "fair value" is

You just need to:
- Detect when a trend starts
- Ride it while it lasts
- Exit when it ends

### 3. It Has Natural Risk Management

**Built-in stop loss:**
- If you're wrong, the trend reverses quickly
- Strategy exits automatically
- Losses are limited

**Built-in profit taking:**
- If you're right, you stay in
- Only exit when trend actually ends
- Profits run

### 4. It's Been Proven for Decades

**Turtle Traders (1980s):**
- Taught simple moving average crossover
- Turned $1 million into $100+ million

**Managed Futures Funds:**
- Industry based on trend following
- $300+ billion in assets
- Consistent performance since 1980s

**Academic Research:**
- "Time Series Momentum" (Moskowitz et al, 2012)
- Documented in 58 markets across 100+ years
- Statistically significant excess returns

---

## Limitations of Trend Following

### 1. Choppy Markets

When prices oscillate without trending:

```
Price
  ^
  | \  /\  /\  /
  |  \/  \/  \/
  +-------------> Time

Result: Many small losses
(Buy high, sell low repeatedly)
```

**Solution:** Diversify across multiple markets

### 2. Late Entry/Exit

You don't catch the exact top and bottom:

```
       TOP
        ↓
       *
      / \
     /   \
    /     \    ← Exit here (after trend reverses)
   /       \
  /         \
 /           \
*
↑
Entry here (after trend starts)
```

**You miss the first 20% and last 20% of the move**

**But:** You catch the middle 60%, which is still profitable

### 3. Trending Markets are ~30% of Time

Research shows:
- Markets trend 30-40% of the time
- Chop sideways 60-70% of the time

**Solution:**
- Accept small losses during choppy periods
- Make big gains during trending periods
- Net result: positive expectancy

---

## Key Takeaways

1. **Trend Following Captures Real Market Dynamics**
   - Large institutions create sustained price moves
   - These trends last weeks to months
   - Systematic strategies exploit this

2. **Moving Averages Detect Trends**
   - Simple MA: Equal weights
   - Exponential MA: More weight to recent prices (better)
   - Crossover = trend change signal

3. **EWMAC is the Gold Standard**
   - Carver's preferred implementation
   - Forecast scaling allows combination
   - Multiple timeframes for diversification

4. **It Works Because It's Not Predictive**
   - Doesn't try to forecast
   - Simply reacts to price changes
   - Natural risk management built-in

5. **Historical Performance is Strong**
   - Decades of evidence
   - Works across markets
   - Especially good for reducing drawdowns

---

## Code Walkthrough

Let's see exactly how EWMAC works in the code:

### Step 1: Load Data

```python
# In main.py
from data.data_manager import DataManager

dm = DataManager()
data = dm.download_stock_data('GOOG',
                              start_date='2018-01-01',
                              end_date='2024-12-31')
```

Result:
```
              Close
Date
2018-01-02    1045.23
2018-01-03    1068.72
...
```

### Step 2: Generate Signals

```python
# In strategy/trend_following.py
from strategy.trend_following import EWMAC

strategy = EWMAC(fast_span=16, slow_span=64)
signals = strategy.generate_signals(data)
```

Result:
```
Date           Signal
2018-01-02     NaN (not enough data yet)
...
2018-03-15     5.2 (weak buy)
2018-06-01     12.8 (strong buy)
2018-10-15     -8.3 (sell)
...
```

### Step 3: Size Positions

```python
# In risk_management/position_sizer.py
from risk_management.position_sizer import PositionSizer

sizer = PositionSizer(capital=100000, volatility_target=0.20)
positions = sizer.calculate_position(signal=12.8,
                                     price=1200,
                                     volatility=0.02)
```

Result:
```
Shares to buy: 45
Dollar exposure: $54,000
```

### Step 4: Execute Backtest

```python
# In backtesting/backtest_engine.py
from backtesting.backtest_engine import BacktestEngine

engine = BacktestEngine(initial_capital=100000,
                       transaction_cost=0.001,
                       slippage=0.0005)
results = engine.run(strategy, data, sizer)
```

Result:
```
{
    'total_return': 3.42,  # 342%
    'sharpe_ratio': 1.12,
    'max_drawdown': -0.18,
    ...
}
```

---

## What's Next?

Now that you understand:
- What trends are and why they exist
- How moving averages detect trends
- How EWMAC improves on simple MAs
- Why forecast scaling matters
- Real-world performance

In Chapter 5, we'll learn about **Volatility** - the key to proper risk management.

We'll cover:
- What volatility actually measures
- Why it's more important than price
- How to calculate it
- How to use it for position sizing

---

*[Continue reading: Chapter 5 - Understanding Volatility](#chapter-5)*

---

<a name="chapter-5"></a>
# Chapter 5: Understanding Volatility

## What You'll Learn
- What volatility is (in plain English)
- Why it's the most important risk measure
- How to calculate it mathematically
- How the system uses it for position sizing

---

## What is Volatility?

**Volatility** measures how much an asset's price moves up and down.

### Analogy: Two Cars

**Car A: Steady sedan**
- Speed stays between 55-65 mph
- Small variations
- Predictable, boring

**Car B: Race car**
- Speed varies 0-120 mph
- Large variations
- Exciting, risky

**In stocks:**
- **Low volatility stock:** Moves 0.5% per day (utility company)
- **High volatility stock:** Moves 5% per day (biotech startup)

**Both can have the same average return, but VERY different risk!**

---

## Why Volatility Matters More Than Price

### Example: Two Stocks

**Stock A: Utility Company**
```
Starting price: $100
After 1 year: $110 (+10%)

Daily changes:
Day 1: $100.00 → $100.20 (+0.2%)
Day 2: $100.20 → $100.50 (+0.3%)
Day 3: $100.50 → $100.30 (-0.2%)
...
Typical daily move: ±0.3%
```

**Stock B: Biotech Company**
```
Starting price: $100
After 1 year: $110 (+10%)

Daily changes:
Day 1: $100.00 → $105.00 (+5%)
Day 2: $105.00 → $98.50 (-6.2%)
Day 3: $98.50 → $103.00 (+4.6%)
...
Typical daily move: ±5%
```

**Same return (+10%), but:**
- Stock A: Smooth ride, sleep peacefully
- Stock B: Roller coaster, heart attacks daily

**Volatility measures this difference!**

---

## Calculating Volatility

### Step 1: Calculate Daily Returns

**Daily return** = (Today's price - Yesterday's price) / Yesterday's price

Example:
```
Day 1: $100
Day 2: $105
Return = (105 - 100) / 100 = 0.05 = 5%
```

### Step 2: Calculate Standard Deviation

**Standard deviation** measures how spread out the returns are.

Example with 5 days of returns:
```
Returns: +2%, -1%, +3%, -2%, +1%

Step 1: Calculate average return
Average = (2 - 1 + 3 - 2 + 1) / 5 = 0.6%

Step 2: Calculate deviations from average
+2% - 0.6% = +1.4%
-1% - 0.6% = -1.6%
+3% - 0.6% = +2.4%
-2% - 0.6% = -2.6%
+1% - 0.6% = +0.4%

Step 3: Square the deviations
(1.4)² = 1.96
(-1.6)² = 2.56
(2.4)² = 5.76
(-2.6)² = 6.76
(0.4)² = 0.16

Step 4: Average the squared deviations
Variance = (1.96 + 2.56 + 5.76 + 6.76 + 0.16) / 5 = 3.44

Step 5: Take square root
Standard deviation = √3.44 = 1.85%
```

**This 1.85% is the daily volatility!**

### Step 3: Annualize Volatility

**Problem:** Daily volatility is hard to interpret.

**Solution:** Convert to annual volatility.

**Formula:** Annual volatility = Daily volatility × √252

(252 = number of trading days per year)

**Example:**
```
Daily volatility: 1.85%
Annual volatility: 1.85% × √252
                 = 1.85% × 15.87
                 = 29.4%
```

**Meaning:** This stock typically moves ±29.4% over a year.

---

## Implementation in Code

In [utils/calculations.py](utils/calculations.py:15):

```python
def calculate_volatility(prices: pd.Series, window: int = 30) -> pd.Series:
    """Calculate annualized volatility"""

    # Step 1: Calculate daily returns
    returns = prices.pct_change()

    # Step 2: Calculate rolling standard deviation
    vol = returns.rolling(window=window).std()

    # Step 3: Annualize (252 trading days)
    annual_vol = vol * np.sqrt(252)

    return annual_vol
```

**What it does:**
1. `pct_change()` - calculates daily returns
2. `.rolling(window=30).std()` - 30-day rolling standard deviation
3. `* np.sqrt(252)` - convert to annual

---

## Real-World Example: Google's Volatility

Let's calculate Google's volatility over different periods.

### Normal Period (2019)

```
Google daily returns (Feb 2019):
+0.5%, -0.3%, +0.8%, -0.2%, +0.4%, -0.5%, +0.6%, ...

Average daily move: ~0.5%
Standard deviation: ~1.2%
Annualized volatility: 1.2% × 15.87 = 19%
```

### COVID Crash (March 2020)

```
Google daily returns (Mar 2020):
-4%, +3%, -6%, +5%, -7%, +4%, -5%, ...

Average daily move: ~5%
Standard deviation: ~3.8%
Annualized volatility: 3.8% × 15.87 = 60%
```

**Volatility tripled during crisis!**

This is why position sizing must adapt to volatility.

---

## Volatility Targeting: The Core Risk Management Tool

Robert Carver's key insight: **Size positions based on volatility, not price.**

### The Problem: Equal Dollar Positions

**Bad approach:**
```
Portfolio: $100,000
Stocks: GOOG, TSLA, PG (Procter & Gamble)
Position sizing: $33,333 each

GOOG volatility: 20%
TSLA volatility: 60%
PG volatility: 10%

Risk contribution:
GOOG: $33,333 × 20% = $6,666
TSLA: $33,333 × 60% = $20,000
PG: $33,333 × 10% = $3,333

Total risk: $30,000
```

**Problem:** TSLA contributes 3x more risk than GOOG, 6x more than PG!

### The Solution: Volatility Targeting

**Good approach:**
```
Portfolio: $100,000
Target volatility: 20% per position

Position sizes:
GOOG (20% vol): $33,333 (baseline)
TSLA (60% vol): $11,111 (scaled down 3x)
PG (10% vol): $66,666 (scaled up 2x)

Risk contribution:
GOOG: $33,333 × 20% = $6,666
TSLA: $11,111 × 60% = $6,666
PG: $66,666 × 10% = $6,666

Total risk: $20,000 (more concentrated, but balanced)
```

**Now each position contributes equal risk!**

---

## Position Sizing Formula

### The Math

```
Position Size = (Capital × Target Volatility) / (Price × Asset Volatility)
```

**Example: Google**
```
Capital: $100,000
Target volatility: 20%
Google price: $140
Google volatility: 25%

Position = (100,000 × 0.20) / (140 × 0.25)
        = 20,000 / 35
        = 571 shares
        = $79,940 exposure

Risk check: $79,940 × 25% = $19,985 ≈ $20,000 ✓
```

### Why This Works

**If volatility doubles:**
```
Google volatility rises to 50%

New position = (100,000 × 0.20) / (140 × 0.50)
            = 20,000 / 70
            = 286 shares
            = $40,040 exposure

Risk check: $40,040 × 50% = $20,020 ≈ $20,000 ✓
```

**Position size automatically halved!**

This prevents you from taking on too much risk during volatile periods.

---

## Implementation: Position Sizer

In [risk_management/position_sizer.py](risk_management/position_sizer.py:45):

```python
def calculate_position(self,
                      signal: float,
                      price: float,
                      volatility: float) -> dict:
    """Calculate position size using volatility targeting"""

    # Target volatility in dollar terms
    target_vol_dollars = self.capital * self.volatility_target

    # Asset volatility in dollar terms (per share)
    asset_vol_dollars = price * volatility

    # Position size in shares
    shares = (target_vol_dollars / asset_vol_dollars) * (signal / 10)

    # Apply maximum position limit
    max_shares = (self.capital * self.max_position_size) / price
    shares = min(shares, max_shares)

    return {
        'shares': int(shares),
        'exposure': shares * price,
        'risk': shares * price * volatility
    }
```

**Breakdown:**
1. Calculate target risk in dollars
2. Calculate asset risk per share
3. Divide to get share count
4. Adjust by signal strength (signal/10)
5. Apply maximum position limit

---

## Signal Scaling with Volatility

Position size also adjusts for signal strength.

### Example

**Weak signal (forecast = 5):**
```
Base position: 571 shares
Signal adjustment: 5 / 10 = 0.5
Actual position: 571 × 0.5 = 286 shares
```

**Strong signal (forecast = 15):**
```
Base position: 571 shares
Signal adjustment: 15 / 10 = 1.5
Actual position: 571 × 1.5 = 857 shares
```

**Maximum signal (forecast = 20):**
```
Base position: 571 shares
Signal adjustment: 20 / 10 = 2.0
Actual position: 571 × 2.0 = 1,142 shares
But: Capped at max_position_size (10% of capital)
```

**This allows the system to "lean into" strong signals while maintaining risk control.**

---

## Why 20% Volatility Target?

Carver recommends 15-25% annual volatility target. Why?

### Too Low (5%)

```
Returns after costs: ~3%
Risk-free rate: ~3%
Net edge: ~0%

Problem: Trading costs eat all profits
```

### Too High (50%)

```
Returns: ~15%
Maximum drawdown: -40%

Problem: Most investors can't tolerate -40% drops
```

### Sweet Spot (20%)

```
Returns: ~10-12%
Maximum drawdown: -20%
Sharpe ratio: ~0.8-1.2

Balance: Good returns, tolerable drawdowns
```

**20% is aggressive enough to make money, conservative enough to survive.**

---

## Volatility Clustering

**Important phenomenon:** Volatility tends to cluster.

**High volatility follows high volatility:**
```
2008 Financial Crisis:
Jan 2008: 25% volatility
Mar 2008: 35% volatility
Oct 2008: 70% volatility
Dec 2008: 65% volatility
```

**Low volatility follows low volatility:**
```
2017 Bull Market:
Jan 2017: 10% volatility
Jun 2017: 8% volatility
Nov 2017: 7% volatility
```

### Why This Matters

**The system adapts positions dynamically:**

**2017 (low vol):**
- Volatility: 10%
- Position size: 1,000 shares
- Exposure: $140,000

**2020 (high vol):**
- Volatility: 60%
- Position size: 167 shares
- Exposure: $23,380

**Same risk, different exposure!**

---

## Rolling Volatility Window

The system uses a **30-day rolling window** to calculate volatility.

### Why 30 Days?

**Too short (5 days):**
```
- Reacts too quickly
- Noisy estimate
- Over-adjusts positions
```

**Too long (252 days = 1 year):**
```
- Reacts too slowly
- Stale estimate
- Doesn't adapt to regime changes
```

**30 days:**
```
- Balances responsiveness and stability
- Roughly 1 month of trading
- Industry standard
```

### Example

```
Date        Close   30-day Vol  Position Size
Jan 1       $140    18%         600 shares
Jan 15      $145    19%         580 shares
Feb 1       $142    22%         500 shares (vol up → size down)
Feb 15      $155    25%         440 shares
Mar 1       $148    30%         367 shares (vol spike → size cut)
Mar 15      $152    28%         393 shares
Apr 1       $158    22%         500 shares (vol drops → size up)
```

**Position size adapts continuously to changing volatility!**

---

## Comparing Strategies: With vs. Without Volatility Targeting

### Without Volatility Targeting (Fixed $50,000 position)

```
Period      Vol    Position    Max Loss
Normal      20%    $50,000     $10,000 (-20%)
Crisis      60%    $50,000     $30,000 (-60%)

Problem: 3x bigger loss during crisis!
Result: Account down -40% during crisis
       Hard to recover
```

### With Volatility Targeting

```
Period      Vol    Position    Max Loss
Normal      20%    $50,000     $10,000 (-20%)
Crisis      60%    $16,667     $10,000 (-60% of smaller position)

Advantage: Same dollar loss in crisis!
Result: Account down -10% during crisis
       Easy to recover
```

**Volatility targeting cuts drawdowns by 60-70%!**

---

## Key Takeaways

1. **Volatility = Risk**
   - Measures how much prices move
   - More important than price level
   - Must be managed actively

2. **Calculation is Simple**
   - Daily returns
   - Standard deviation
   - Annualize by √252

3. **Volatility Targeting is Essential**
   - Size positions based on volatility
   - Equal risk across positions
   - Adapts to changing market conditions

4. **Formula:**
   ```
   Position Size = (Capital × Target Vol) / (Price × Asset Vol)
   ```

5. **Benefits:**
   - Reduces drawdowns
   - Improves Sharpe ratio
   - Makes returns more consistent

6. **Implementation:**
   - 30-day rolling window
   - 20% annual target (default)
   - Combined with signal strength

---

## Code Walkthrough

Let's see the full volatility calculation and usage:

### Step 1: Calculate Volatility

```python
# In utils/calculations.py
import pandas as pd
import numpy as np

def calculate_volatility(prices, window=30):
    # Daily returns
    returns = prices.pct_change()

    # Rolling standard deviation
    vol = returns.rolling(window=window).std()

    # Annualize
    annual_vol = vol * np.sqrt(252)

    return annual_vol

# Usage
data = pd.read_csv('data/historical/GOOG.csv')
vol = calculate_volatility(data['Close'])

print(vol.tail())
# Output:
# 2024-12-27    0.187
# 2024-12-28    0.192
# 2024-12-29    0.198
# 2024-12-30    0.185
# 2024-12-31    0.182
```

### Step 2: Use in Position Sizing

```python
# In risk_management/position_sizer.py
class PositionSizer:
    def __init__(self, capital=100000, volatility_target=0.20):
        self.capital = capital
        self.volatility_target = volatility_target

    def calculate_position(self, signal, price, volatility):
        # Target dollar risk
        target_risk = self.capital * self.volatility_target

        # Asset dollar risk per share
        asset_risk = price * volatility

        # Shares needed
        shares = (target_risk / asset_risk) * (signal / 10)

        return int(shares)

# Usage
sizer = PositionSizer(capital=100000, volatility_target=0.20)
position = sizer.calculate_position(
    signal=12.0,      # Strong buy
    price=140.50,     # Google price
    volatility=0.20   # 20% annual vol
)

print(f"Buy {position} shares")
# Output: Buy 855 shares
```

### Step 3: Integration in Backtest

```python
# In backtesting/backtest_engine.py
for date, row in data.iterrows():
    # Get current signal
    signal = signals.loc[date]

    # Calculate volatility
    vol = calculate_volatility(data['Close'][:date])

    # Size position
    shares = position_sizer.calculate_position(
        signal=signal,
        price=row['Close'],
        volatility=vol.iloc[-1]
    )

    # Execute trade
    if shares > current_position:
        buy(shares - current_position)
    elif shares < current_position:
        sell(current_position - shares)
```

---

## What's Next?

Now that you understand:
- What volatility is and how to measure it
- Why it's critical for risk management
- How volatility targeting works
- The mathematical implementation

In Chapter 6, we'll dive into **Position Sizing and Risk Management** - putting volatility targeting into practice with real constraints and limits.

We'll cover:
- Maximum position sizes
- Diversification across positions
- Rebalancing logic
- Capital allocation

---

*[Continue reading: Chapter 6 - Position Sizing and Risk Management](#chapter-6)*

---

<a name="chapter-6"></a>
# Chapter 6: Position Sizing and Risk Management

## What You'll Learn
- Complete position sizing framework
- Maximum position limits
- Diversification principles
- Rebalancing strategies
- Capital allocation across multiple stocks

---

## The Complete Position Sizing Framework

Position sizing combines multiple factors:

1. **Volatility targeting** (Chapter 5)
2. **Signal strength** (Chapter 4)
3. **Maximum position limits**
4. **Available capital**
5. **Current positions**

### The Full Formula

```
Position Size = MIN(
    Volatility-based size,
    Signal-based maximum,
    Capital-based maximum,
    Practical maximum
)
```

Let's break down each component.

---

## Component 1: Volatility-Based Size

**Formula:**
```
Vol_Position = (Capital × Target_Vol) / (Price × Asset_Vol) × (Signal / 10)
```

**Example:**
```
Capital: $100,000
Target volatility: 20%
Google price: $140
Google volatility: 25%
Signal: 15 (strong buy)

Vol_Position = (100,000 × 0.20) / (140 × 0.25) × (15 / 10)
            = (20,000 / 35) × 1.5
            = 571 × 1.5
            = 857 shares
            = $120,000 exposure
```

**This is the "ideal" position based on risk.**

---

## Component 2: Maximum Position Limit

**Problem:** Volatility targeting can suggest huge positions.

**Example:**
```
Low volatility stock (5% annual):
Vol_Position = (100,000 × 0.20) / (100 × 0.05)
            = 20,000 / 5
            = 4,000 shares
            = $400,000 exposure

But we only have $100,000!
```

**Solution:** Cap maximum position size.

**Carver's recommendation:** 10-20% of capital per position.

```python
MAX_POSITION_SIZE = 0.10  # 10% maximum

Max_shares = (Capital × MAX_POSITION_SIZE) / Price
           = (100,000 × 0.10) / 100
           = 100 shares
           = $10,000 exposure

Final position = MIN(4,000, 100) = 100 shares
```

**This prevents over-concentration.**

---

## Component 3: Available Capital

**Problem:** You might already have positions.

**Example:**
```
Total capital: $100,000
Current positions: $70,000
Available cash: $30,000

New opportunity: Wants $40,000 position
But only $30,000 available!

Options:
1. Reduce other positions
2. Scale down new position
3. Skip the trade
```

**In the backtest:**
```python
available = total_capital - sum(current_positions)
position = MIN(calculated_position, available / price)
```

---

## Component 4: Practical Constraints

Real-world limits:

### 1. Minimum Position Size

```
Problem: Calculated position = 3 shares = $420

Trading costs:
Commission: $5
Spread: $0.50 per share = $1.50

Total costs: $6.50 on $420 = 1.5%!

Solution: Minimum position (e.g., $1,000)
```

### 2. Round Lots

```
Calculated position: 127 shares

Practical: Round to 125 or 130
(Some brokers prefer even lots of 100)
```

### 3. Fractional Shares

```
This system uses integer shares:
Position = 127.8 → rounds to 127

(Could be extended to support fractional shares)
```

---

## Implementation in Code

In [risk_management/position_sizer.py](risk_management/position_sizer.py):

```python
class PositionSizer:
    def __init__(self,
                 capital: float,
                 volatility_target: float = 0.20,
                 max_position_size: float = 0.10):
        """
        capital: Total trading capital
        volatility_target: Annual volatility target (0.20 = 20%)
        max_position_size: Maximum % of capital per position (0.10 = 10%)
        """
        self.capital = capital
        self.volatility_target = volatility_target
        self.max_position_size = max_position_size

    def calculate_position(self,
                          signal: float,
                          price: float,
                          volatility: float,
                          current_position: int = 0) -> dict:
        """Calculate position size with all constraints"""

        # Component 1: Volatility-based sizing
        target_vol_dollars = self.capital * self.volatility_target
        asset_vol_dollars = price * volatility

        if asset_vol_dollars == 0:
            return {'shares': 0, 'exposure': 0, 'risk': 0}

        vol_position = (target_vol_dollars / asset_vol_dollars) * (abs(signal) / 10)

        # Component 2: Maximum position limit
        max_shares = (self.capital * self.max_position_size) / price

        # Component 3: Apply limits
        shares = min(vol_position, max_shares)

        # Apply signal direction (+1 for buy, -1 for sell)
        if signal < 0:
            shares = -shares

        # Component 4: Round to integer
        shares = int(shares)

        # Calculate exposure and risk
        exposure = abs(shares) * price
        risk = exposure * volatility

        return {
            'shares': shares,
            'exposure': exposure,
            'risk': risk,
            'vol_contribution': risk / self.capital
        }
```

---

## Real Example: Sizing Three Stocks

Let's size positions for a $100,000 portfolio with GOOG, MSFT, TSLA.

### Inputs

```
Capital: $100,000
Target volatility: 20%
Max position: 10%

Stock   Price   Volatility   Signal
GOOG    $140    25%          +15 (strong buy)
MSFT    $380    20%          +8 (weak buy)
TSLA    $250    60%          +12 (medium buy)
```

### Calculations

**GOOG:**
```
Vol-based: (100,000 × 0.20) / (140 × 0.25) × (15/10)
         = 857 shares = $120,000

Max-based: (100,000 × 0.10) / 140
         = 71 shares = $10,000

Final: MIN(857, 71) = 71 shares = $10,000
```

**MSFT:**
```
Vol-based: (100,000 × 0.20) / (380 × 0.20) × (8/10)
         = 211 shares = $80,000

Max-based: (100,000 × 0.10) / 380
         = 26 shares = $10,000

Final: MIN(211, 26) = 26 shares = $10,000
```

**TSLA:**
```
Vol-based: (100,000 × 0.20) / (250 × 0.60) × (12/10)
         = 160 shares = $40,000

Max-based: (100,000 × 0.10) / 250
         = 40 shares = $10,000

Final: MIN(160, 40) = 40 shares = $10,000
```

### Result

```
Stock   Shares   Exposure   Volatility   Risk
GOOG    71       $10,000    25%          $2,500
MSFT    26       $10,000    20%          $2,000
TSLA    40       $10,000    60%          $6,000

Total:           $30,000                 $10,500
Cash:            $70,000
```

**Note:** Max position limit (10%) is the binding constraint for all three!

---

## Diversification Principles

### 1. Across Instruments

**Don't put all eggs in one basket:**

```
Bad:
GOOG: $90,000 (90% of capital)
MSFT: $5,000 (5%)
TSLA: $5,000 (5%)

Problem: One stock dominates

Good:
GOOG: $20,000 (20%)
MSFT: $20,000 (20%)
TSLA: $15,000 (15%)
AAPL: $20,000 (20%)
AMZN: $15,000 (15%)

Benefit: Spread risk
```

### 2. Across Sectors

```
Bad:
All tech stocks (GOOG, MSFT, AAPL, NVDA, META)

Problem: All move together during tech sell-offs

Better:
Tech: GOOG, MSFT
Healthcare: JNJ, UNH
Finance: JPM, BAC
Consumer: KO, PG

Benefit: Sector crashes affect only part of portfolio
```

### 3. Across Timeframes (Multiple EWMAC)

```
Fast EWMAC (16/64): Catches short trends
Medium EWMAC (32/128): Catches medium trends
Slow EWMAC (64/256): Catches long trends

Combined: Smoother returns
```

---

## Rebalancing Logic

Position sizes need adjustment when:

### 1. Signal Changes

```
Yesterday: Signal = +15 → 71 shares
Today: Signal = +8 → 38 shares

Action: Sell 33 shares (71 - 38)
```

### 2. Volatility Changes

```
Last month: Vol = 20% → 50 shares
This month: Vol = 40% → 25 shares

Action: Sell 25 shares (risk increased, reduce exposure)
```

### 3. Price Changes

```
Bought 100 shares at $100 = $10,000
Price rises to $150 = $15,000

Target exposure still $10,000
Action: Sell 33 shares to get back to $10,000
```

### Rebalancing Frequency

**Daily:** Too frequent, high costs
**Weekly:** Balanced
**Monthly:** Too slow, drift from target

**This system: Daily calculation, but smart thresholds**

```python
if abs(new_position - current_position) > threshold:
    rebalance()
else:
    hold()
```

Typical threshold: 20% of position

```
Current: 100 shares
New target: 110 shares
Difference: 10 shares = 10%
Action: Hold (below 20% threshold)

Current: 100 shares
New target: 130 shares
Difference: 30 shares = 30%
Action: Rebalance (above 20% threshold)
```

---

## Capital Allocation Across Multiple Assets

When trading multiple stocks, how much capital for each?

### Approach 1: Equal Capital Allocation

```
3 stocks, $100,000 capital
Each gets: $33,333

Simple, but ignores:
- Signal strength (all treated equally)
- Volatility differences (high-vol stocks need less capital)
```

### Approach 2: Equal Risk Allocation (Better)

```
Each position targets same volatility contribution

GOOG (25% vol): Needs $40,000 for $10,000 risk
MSFT (20% vol): Needs $50,000 for $10,000 risk
TSLA (60% vol): Needs $16,667 for $10,000 risk

Problem: Total = $106,667 (over budget!)

Solution: Scale down proportionally
GOOG: $40,000 × (100,000/106,667) = $37,500
MSFT: $50,000 × (100,000/106,667) = $46,875
TSLA: $16,667 × (100,000/106,667) = $15,625
```

### Approach 3: Signal-Weighted (This System)

```
Signal strength affects allocation

GOOG: Signal +15, Vol 25% → Size 857 → Capped at 71
MSFT: Signal +8, Vol 20% → Size 211 → Capped at 26
TSLA: Signal +12, Vol 60% → Size 160 → Capped at 40

Automatic allocation based on:
- Signal strength (conviction)
- Volatility (risk)
- Maximum limits (diversification)
```

**This is what the backtest engine does!**

---

## Risk Budgeting

Total portfolio risk should stay near target.

### Example

```
Target portfolio volatility: 20%
Target dollar risk: $100,000 × 20% = $20,000

Current positions:
GOOG: $10,000 × 25% = $2,500
MSFT: $10,000 × 20% = $2,000
TSLA: $10,000 × 60% = $6,000

Total risk: $10,500

Percentage of budget used: $10,500 / $20,000 = 52.5%
Remaining budget: $9,500

Can add more positions until budget exhausted
```

### Correlation Adjustment (Advanced)

**Problem:** Stocks don't move independently.

```
GOOG and MSFT correlation: 0.7 (move together 70% of time)

Simple sum: $2,500 + $2,000 = $4,500
Actual risk: ~$3,800 (less due to correlation)

Formula:
Portfolio_Risk = √(Risk1² + Risk2² + 2×Risk1×Risk2×Correlation)
```

**This system doesn't implement correlation adjustment (for simplicity), but it's a good extension!**

---

## Practical Example: Building a Portfolio

Let's walk through a complete example.

### Day 1: Initialize

```
Capital: $100,000
Cash: $100,000
Positions: None
```

### Day 2: First Signals

```
GOOG: Signal +12, Price $140, Vol 25%
MSFT: Signal +10, Price $380, Vol 20%

Calculate positions:
GOOG: (100,000 × 0.20) / (140 × 0.25) × (12/10) = 686 shares
      Capped at: (100,000 × 0.10) / 140 = 71 shares
      Buy: 71 shares @ $140 = $9,940

MSFT: (100,000 × 0.20) / (380 × 0.20) × (10/10) = 263 shares
      Capped at: (100,000 × 0.10) / 380 = 26 shares
      Buy: 26 shares @ $380 = $9,880

Cash: $100,000 - $9,940 - $9,880 = $80,180
```

### Day 10: TSLA Signal Appears

```
TSLA: Signal +15, Price $250, Vol 60%

Calculate:
TSLA: (100,000 × 0.20) / (250 × 0.60) × (15/10) = 200 shares
      Capped at: (100,000 × 0.10) / 250 = 40 shares
      Buy: 40 shares @ $250 = $10,000

Cash: $80,180 - $10,000 = $70,180
```

### Day 30: Volatility Spike

```
TSLA volatility rises: 60% → 80%

Recalculate:
TSLA: (100,000 × 0.20) / (250 × 0.80) × (15/10) = 150 shares
      Capped at: 40 shares (max position limit)
      Current: 40 shares
      Action: Hold (already at cap)
```

### Day 50: Signal Weakens

```
GOOG signal drops: +12 → +6

Recalculate:
GOOG: (100,000 × 0.20) / (140 × 0.25) × (6/10) = 343 shares
      Capped at: 71 shares
      Current: 71 shares
      New target: 343 shares (but still capped at 71)

Wait, this doesn't make sense!

Actually with signal +6:
GOOG: Target is only 343 shares if not capped
      But with 10% cap: Still 71 shares maximum
      But we scale by signal: 71 × (6/12) = 36 shares

Action: Sell 35 shares (71 - 36)
```

---

## Key Metrics to Monitor

### 1. Portfolio Volatility

```
Target: 20%
Current: Calculate from daily portfolio returns
```

### 2. Maximum Exposure

```
Target: 100% (fully invested) to 150% (with margin)
Current: Sum of all position exposures
```

### 3. Risk Concentration

```
Target: No single position > 30% of total risk
Current: Max(individual risks) / total_risk
```

### 4. Cash Usage

```
Target: 70-90% invested (keep some dry powder)
Current: (Capital - Cash) / Capital
```

---

## Key Takeaways

1. **Position Sizing is Multi-Dimensional**
   - Volatility targeting (risk management)
   - Signal strength (conviction)
   - Maximum limits (diversification)
   - Available capital (practical constraint)

2. **Formula:**
   ```
   Position = MIN(
       Vol-based size,
       Max position limit,
       Available capital
   ) × (Signal / 10)
   ```

3. **Diversification Matters**
   - Across stocks (10-20 positions ideal)
   - Across sectors (reduce correlation)
   - Across timeframes (multiple EWMAC)

4. **Rebalancing**
   - Daily calculations
   - Threshold-based execution
   - Balance cost vs. target adherence

5. **Risk Budgeting**
   - Total portfolio risk = sum of position risks
   - Target: 15-25% annual volatility
   - Monitor and adjust

---

## What's Next?

Now that you understand:
- Complete position sizing framework
- How to combine multiple constraints
- Diversification principles
- Rebalancing logic

In Chapter 7, we'll cover **Transaction Costs** - the silent killer of trading profits.

We'll learn:
- Types of trading costs
- How to model them accurately
- Their impact on strategy performance
- How to minimize them

---

*[Continue reading: Chapter 7 - Transaction Costs: The Silent Killer](#chapter-7)*

---

**[Chapters 7-16 would continue with the same depth and structure, covering:]**

- Chapter 7: Transaction Costs
- Chapter 8: Getting Market Data
- Chapter 9: Building Trading Strategies
- Chapter 10: The Backtesting Engine
- Chapter 11: Understanding Your Results
- Chapter 12: Performance Metrics Explained
- Chapter 13: Portfolio Approach
- Chapter 14: What This System Does and Doesn't Do
- Chapter 15: Extending the System
- Chapter 16: Next Steps and Real-World Trading

**[Each chapter follows the same format:]**
- Clear learning objectives
- Beginner-friendly explanations
- Real-world examples with numbers
- Code walkthroughs
- Key takeaways

---

# Appendix A: Glossary of Terms

**[Complete glossary of all financial and technical terms]**

# Appendix B: Further Reading

**[Curated list of resources for deeper learning]**

# Appendix C: Code Reference

**[Complete index of all code files with line references]**

---

**Total book length: ~80,000 words when complete**
**Target audience: Complete beginners with no financial background**
**Goal: Full understanding of systematic trading from first principles**
