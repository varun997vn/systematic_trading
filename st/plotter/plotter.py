"""
Interactive plotting utility for systematic trading framework.
Minimal implementation with optional strategy signal visualization.
"""

from typing import Optional, Dict, Literal, Any

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pydantic import BaseModel

from st.dto.data import PriceDataDTO


class TradingPlot(BaseModel):
    """Interactive plotter for price data and trading signals."""

    price_data: PriceDataDTO
    plot_type: Literal["candlestick", "line", "ohlc"] = "candlestick"
    height: int = 600
    show_volume: bool = True
    fig: go.Figure = None

    class Config:
        arbitrary_types_allowed = True

    def model_post_init(self, __context: Any):
        self.create_plot()
        # self.add_signals()
        # self.add_forecast()

    def create_plot(self):
        """Create base price plot."""
        df = self.price_data.data

        # Determine subplot configuration
        rows = 2 if self.show_volume else 1
        row_heights = [0.7, 0.3] if self.show_volume else [1.0]

        self.fig = make_subplots(
            rows=rows,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=row_heights,
            subplot_titles=(f"{self.price_data.ticker} Price", "Volume") if self.show_volume else (
                f"{self.price_data.ticker} Price",)
        )

        # Add price trace
        if self.plot_type == "candlestick":
            self.fig.add_trace(
                go.Candlestick(
                    x=df['Date'],
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close'],
                    name="Price",
                    increasing_line_color='#26a69a',
                    decreasing_line_color='#ef5350'
                ),
                row=1, col=1
            )
        elif self.plot_type == "ohlc":
            self.fig.add_trace(
                go.Ohlc(
                    x=df['Date'],
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close'],
                    name="Price"
                ),
                row=1, col=1
            )
        else:  # line
            self.fig.add_trace(
                go.Scatter(
                    x=df['Date'],
                    y=df['Close'],
                    mode='lines',
                    name="Close",
                    line=dict(color='#2962ff', width=1.5)
                ),
                row=1, col=1
            )

        # Add volume
        if self.show_volume:
            colors = ['#ef5350' if close < open_ else '#26a69a'
                      for close, open_ in zip(df['Close'], df['Open'])]

            self.fig.add_trace(
                go.Bar(
                    x=df['Date'],
                    y=df['Volume'],
                    name="Volume",
                    marker_color=colors,
                    opacity=0.5
                ),
                row=2, col=1
            )

        # Update layout
        self.fig.update_layout(
            height=self.height,
            xaxis_rangeslider_visible=False,
            hovermode='x unified',
            template='plotly_white',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        self.fig.update_xaxes(title_text="Date", row=rows, col=1)
        self.fig.update_yaxes(title_text="Price", row=1, col=1)
        if self.show_volume:
            self.fig.update_yaxes(title_text="Volume", row=2, col=1)

        return self.fig

    def add_signals(
            self,
            signals: pd.DataFrame,
            signal_column: str = 'signal',
            long_value: float = 1.0,
            short_value: float = -1.0
    ):
        """
        Add entry/exit signals to the plot.

        Args:
            signals: DataFrame with DatetimeIndex and signal column
            signal_column: Name of column containing signals
            long_value: Value indicating long entry
            short_value: Value indicating short entry
        """
        if self.fig is None:
            self.create_plot()

        df = self.price_data.data

        # Merge signals with price data
        plot_data = df.set_index('Date').join(signals[[signal_column]], how='left')
        plot_data = plot_data.reset_index()

        # Detect entries (signal changes from 0 or opposite sign)
        signal_series = plot_data[signal_column].fillna(0)
        prev_signal = signal_series.shift(1).fillna(0)

        # Long entries
        long_entries = plot_data[
            (signal_series == long_value) & (prev_signal != long_value)
            ]

        # Short entries
        short_entries = plot_data[
            (signal_series == short_value) & (prev_signal != short_value)
            ]

        # Exits (signal goes to 0)
        exits = plot_data[
            (signal_series == 0) & (prev_signal != 0)
            ]

        # Add markers
        if not long_entries.empty:
            self.fig.add_trace(
                go.Scatter(
                    x=long_entries['Date'],
                    y=long_entries['Low'] * 0.995,
                    mode='markers',
                    name='Long Entry',
                    marker=dict(
                        symbol='triangle-up',
                        size=12,
                        color='#00e676',
                        line=dict(color='#00c853', width=1)
                    ),
                    showlegend=True
                ),
                row=1, col=1
            )

        if not short_entries.empty:
            self.fig.add_trace(
                go.Scatter(
                    x=short_entries['Date'],
                    y=short_entries['High'] * 1.005,
                    mode='markers',
                    name='Short Entry',
                    marker=dict(
                        symbol='triangle-down',
                        size=12,
                        color='#ff1744',
                        line=dict(color='#d50000', width=1)
                    ),
                    showlegend=True
                ),
                row=1, col=1
            )

        if not exits.empty:
            self.fig.add_trace(
                go.Scatter(
                    x=exits['Date'],
                    y=exits['Close'],
                    mode='markers',
                    name='Exit',
                    marker=dict(
                        symbol='x',
                        size=10,
                        color='#ffd600',
                        line=dict(color='#ff6f00', width=1)
                    ),
                    showlegend=True
                ),
                row=1, col=1
            )

        return self.fig

    def add_forecast(
            self,
            forecast: pd.Series,
            name: str = "Forecast",
            color: str = "#9c27b0"
    ):
        """
        Add forecast line as subplot.

        Args:
            forecast: Series with DatetimeIndex
            name: Name for the forecast
            color: Line color
        """
        if self.fig is None:
            self.create_plot()

        # Add new subplot for forecast
        current_rows = len(self.fig._grid_ref)
        self.fig.add_trace(
            go.Scatter(
                x=forecast.index,
                y=forecast.values,
                mode='lines',
                name=name,
                line=dict(color=color, width=1.5)
            ),
            row=1, col=1,
            secondary_y=True
        )

        return self.fig

    def show(self):
        """Display the plot."""
        if self.fig is None:
            self.create_plot()
        self.fig.show()

    def save(self, filepath: str):
        """Save plot to HTML file."""
        if self.fig is None:
            self.create_plot()
        self.fig.write_html(filepath)


# Example usage function
def plot_trading_system(
        price_data: PriceDataDTO,
        signals: Optional[pd.DataFrame] = None,
        forecasts: Optional[Dict[str, pd.Series]] = None,
        plot_type: Literal["candlestick", "line", "ohlc"] = "candlestick",
        show_volume: bool = True,
        height: int = 600
):
    """
    Convenience function to plot price data with optional signals and forecasts.

    Args:
        price_data: PriceDataDTO object
        signals: DataFrame with signal column (1=long, -1=short, 0=flat)
        forecasts: Dictionary of forecast name to Series
        plot_type: Type of price plot
        show_volume: Whether to show volume subplot
        height: Plot height in pixels

    Returns:
        Plotly figure
    """
    plotter = TradingPlot(
        price_data=price_data,
        plot_type=plot_type,
        height=height,
        show_volume=show_volume
    )

    plotter.create_plot()

    if signals is not None:
        plotter.add_signals(signals)

    if forecasts is not None:
        for name, forecast in forecasts.items():
            plotter.add_forecast(forecast, name=name)

    return plotter.fig
