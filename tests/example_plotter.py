"""
Example usage of the TradingPlot utility.
"""

from datetime import datetime

import numpy as np
import pandas as pd

from st.dto.data import PriceDataDTO
from st.plotter import TradingPlot, plot_trading_system


# Example 1: Simple price plot
def example_basic():
    """Basic price visualization."""
    price_data = PriceDataDTO(
        ticker="AAPL",
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2024, 1, 1)
    )

    plotter = TradingPlot(price_data=price_data, plot_type="candlestick")
    plotter.show()


# Example 2: Price plot with signals
def example_with_signals():
    """Price with entry/exit signals."""
    price_data = PriceDataDTO(
        ticker="AAPL",
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2024, 1, 1)
    )

    # Create mock signals (replace with your actual strategy signals)
    df = price_data.data.copy()
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)

    # Mock signal: simple moving average crossover
    df['sma_20'] = df['Close'].rolling(20).mean()
    df['sma_50'] = df['Close'].rolling(50).mean()
    df['signal'] = 0
    df.loc[df['sma_20'] > df['sma_50'], 'signal'] = 1  # Long
    df.loc[df['sma_20'] < df['sma_50'], 'signal'] = -1  # Short

    plotter = TradingPlot(price_data=price_data, plot_type="candlestick")
    plotter.add_signals(df, signal_column='signal')
    plotter.show()


# Example 3: Using convenience function
def example_convenience():
    """Using the convenience function."""
    price_data = PriceDataDTO(
        ticker="BTC-USD",
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2024, 1, 1)
    )

    # Mock signals
    df = price_data.data.copy()
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)
    df['signal'] = np.random.choice([0, 1, -1], size=len(df), p=[0.7, 0.15, 0.15])

    # Mock forecast
    forecast = pd.Series(
        np.random.randn(len(df)) * 10,
        index=df.index
    )

    fig = plot_trading_system(
        price_data=price_data,
        signals=df[['signal']],
        forecasts={'EWMAC': forecast},
        plot_type="line",
        show_volume=True
    )
    fig.show()


if __name__ == "__main__":
    # Run examples
    print("Running basic example...")
    # example_basic()

    # Uncomment to run other examples
    # example_with_signals()
    example_convenience()
