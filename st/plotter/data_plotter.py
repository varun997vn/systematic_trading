from typing import Dict, Optional

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pydantic import BaseModel
from pydantic import Field

from st.dto.data import PriceDataDTO, ReturnsDTO
from utils.logger import setup_logger

logger = setup_logger(__name__)


class PriceDataPlotter(BaseModel):
    """
    Interactive plotter for PriceDataDTO objects.

    Features:
    - Add multiple tickers
    - Interactive toggling of tickers via legend
    - Candlestick charts
    - Synchronized zoom and pan
    """

    title: str = Field(default="Price Data Visualization")
    price_data: Dict[str, PriceDataDTO] = Field(default_factory=dict)
    fig: go.Figure = None

    class Config:
        arbitrary_types_allowed = True

    def add(self, price_data: PriceDataDTO) -> 'PriceDataPlotter':
        """
        Add a PriceDataDTO to the plotter.

        Args:
            price_data: PriceDataDTO object to add

        Returns:
            Self for method chaining
        """
        if price_data.ticker in self.price_data:
            logger.warning(f"Warning: Overwriting existing data for {price_data.ticker}")

        self.price_data[price_data.ticker] = price_data
        logger.info(f"Added {price_data.ticker} with {len(price_data.data)} data points")
        return self

    def _create_figure(self):
        """Create the plotly figure with candlestick charts."""
        self.fig = go.Figure()

        # Color palette for different tickers
        colors = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ]

        for idx, (ticker, price_data) in enumerate(self.price_data.items()):
            df = price_data.data.copy()
            color = colors[idx % len(colors)]

            # Ensure Date column is datetime
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])

            # Add candlestick chart
            self.fig.add_trace(
                go.Candlestick(
                    x=df['Date'],
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close'],
                    name=ticker,
                    increasing_line_color=color,
                    decreasing_line_color=color,
                )
            )

        # Update layout
        self.fig.update_layout(
            title=self.title,
            xaxis_title="Date",
            yaxis_title="Price",
            xaxis_rangeslider_visible=False,
            height=600,
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

    def show(self):
        """Display the interactive plot."""
        if not self.price_data:
            logger.warning("No data to plot. Use add() to add PriceDataDTO objects first.")
            return

        self._create_figure()
        self.fig.show()

    def save(self, filename: str = "price_chart.html"):
        """
        Save the plot as an HTML file.

        Args:
            filename: Output filename
        """
        if not self.price_data:
            logger.warning("No data to plot. Use add() to add PriceDataDTO objects first.")
            return

        if self.fig is None:
            self._create_figure()

        self.fig.write_html(filename)
        logger.info(f"Plot saved to {filename}")

    def __str__(self):
        return f"PriceDataPlotter: title={self.title}, price_data={self.price_data.keys()}"

    __repr__ = __str__


class ReturnsPlotter(BaseModel):
    """
    Interactive returns plotter for multiple tickers.

    Allows adding price data and creating interactive plots with
    toggleable tickers.
    """
    price_data: Dict[str, 'PriceDataDTO'] = {}
    returns_data: Dict[str, 'ReturnsDTO'] = {}
    return_type: str = 'log'  # 'log' or 'percentage'
    periods: int = 1
    title: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True

    def add(self, price_dto: 'PriceDataDTO') -> 'ReturnsPlotter':
        """
        Add price data and calculate returns.

        Args:
            price_dto: PriceDataDTO object containing price data

        Returns:
            Self for method chaining
        """
        ticker = price_dto.ticker

        # Store price data
        self.price_data[ticker] = price_dto

        # Calculate returns
        returns_dto = ReturnsDTO(
            ticker=ticker,
            data=price_dto.data,
            return_type=self.return_type,
            periods=self.periods
        )

        self.returns_data[ticker] = returns_dto

        logger.info(f"Added {ticker}: {len(returns_dto.returns)} returns calculated")
        return self

    def show(self, plot_type: str = 'both') -> None:
        """
        Display interactive plot with toggleable tickers.

        Args:
            plot_type: Type of plot to show
                - 'cumulative': Cumulative returns over time
                - 'returns': Raw returns over time
                - 'both': Both plots in subplots
        """
        if not self.returns_data:
            logger.warning("No data to plot. Use add() to add price data first.")
            return

        if plot_type == 'both':
            self._show_both()
        elif plot_type == 'cumulative':
            self._show_cumulative()
        elif plot_type == 'returns':
            self._show_returns()
        else:
            raise ValueError(f"Invalid plot_type: {plot_type}. Must be 'cumulative', 'returns', or 'both'")

    def _show_cumulative(self) -> None:
        """Show cumulative returns plot."""
        fig = go.Figure()

        for ticker, returns_dto in self.returns_data.items():
            price_dto = self.price_data[ticker]
            dates = price_dto.data['Date']

            # Calculate cumulative returns
            cumulative_returns = (returns_dto.returns + 1).cumprod() - 1

            fig.add_trace(go.Scatter(
                x=dates,
                y=cumulative_returns * 100,  # Convert to percentage
                mode='lines',
                name=ticker,
                hovertemplate=f'{ticker}<br>Date: %{{x}}<br>Cumulative Return: %{{y:.2f}}%<extra></extra>'
            ))

        title = self.title or f'Cumulative Returns ({self.return_type.capitalize()}, {self.periods}-period)'

        fig.update_layout(
            title=title,
            xaxis_title='Date',
            yaxis_title='Cumulative Return (%)',
            hovermode='x unified',
            template='plotly_white',
            width=1200,
            height=600,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.01
            )
        )

        fig.show()

    def _show_returns(self) -> None:
        """Show raw returns plot."""
        fig = go.Figure()

        for ticker, returns_dto in self.returns_data.items():
            price_dto = self.price_data[ticker]
            dates = price_dto.data['Date']

            fig.add_trace(go.Scatter(
                x=dates,
                y=returns_dto.returns * 100,  # Convert to percentage
                mode='lines',
                name=ticker,
                hovertemplate=f'{ticker}<br>Date: %{{x}}<br>Return: %{{y:.2f}}%<extra></extra>'
            ))

        title = self.title or f'Returns ({self.return_type.capitalize()}, {self.periods}-period)'

        fig.update_layout(
            title=title,
            xaxis_title='Date',
            yaxis_title='Return (%)',
            hovermode='x unified',
            template='plotly_white',
            width=1200,
            height=600,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.01
            )
        )

        fig.show()

    def _show_both(self) -> None:
        """Show both cumulative returns and raw returns in subplots."""
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=(
                f'Cumulative Returns ({self.return_type.capitalize()})',
                f'Period Returns ({self.return_type.capitalize()})'
            ),
            vertical_spacing=0.12,
            row_heights=[0.6, 0.4]
        )

        for ticker, returns_dto in self.returns_data.items():
            price_dto = self.price_data[ticker]
            dates = price_dto.data['Date']

            # Calculate cumulative returns
            cumulative_returns = (returns_dto.returns + 1).cumprod() - 1

            # Add cumulative returns trace
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=cumulative_returns * 100,
                    mode='lines',
                    name=ticker,
                    legendgroup=ticker,
                    hovertemplate=f'{ticker}<br>Date: %{{x}}<br>Cumulative: %{{y:.2f}}%<extra></extra>'
                ),
                row=1, col=1
            )

            # Add raw returns trace
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=returns_dto.returns * 100,
                    mode='lines',
                    name=ticker,
                    legendgroup=ticker,
                    showlegend=False,
                    hovertemplate=f'{ticker}<br>Date: %{{x}}<br>Return: %{{y:.2f}}%<extra></extra>'
                ),
                row=2, col=1
            )

        title = self.title or f'Returns Analysis ({self.return_type.capitalize()}, {self.periods}-period)'

        fig.update_xaxes(title_text='Date', row=2, col=1)
        fig.update_yaxes(title_text='Cumulative Return (%)', row=1, col=1)
        fig.update_yaxes(title_text='Period Return (%)', row=2, col=1)

        fig.update_layout(
            title_text=title,
            hovermode='x unified',
            template='plotly_white',
            width=1200,
            height=900,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.01
            )
        )

        fig.show()

    def show_distribution(self) -> None:
        """
        Display distribution of returns with skew annotation.
        """
        if not self.returns_data:
            logger.warning("No data to plot. Use add() to add price data first.")
            return

        fig = go.Figure()

        for ticker, returns_dto in self.returns_data.items():
            returns = returns_dto.returns * 100  # Convert to percentage

            fig.add_trace(go.Histogram(
                x=returns,
                name=ticker,
                opacity=0.5,
                histnorm='probability density',
                hovertemplate=f'{ticker}<br>Return: %{{x:.2f}}%<br>Density: %{{y:.4f}}<extra></extra>'
            ))

        # Add annotations for skew
        annotations = []
        for i, (ticker, returns_dto) in enumerate(self.returns_data.items()):
            annotations.append(
                dict(
                    x=0.9,
                    y=0.98 - (i * 0.05),
                    xref='paper',
                    yref='paper',
                    text=f'{ticker} Skew: {returns_dto.skew:.3f}',
                    showarrow=False,
                    xanchor='right',
                    bgcolor='white',
                    bordercolor='black',
                    borderwidth=1
                )
            )

        fig.update_layout(
            title=f'Returns Distribution with Skewness',
            xaxis_title='Return (%)',
            yaxis_title='Density',
            template='plotly_white',
            width=1200,
            height=600,
            barmode='overlay',
            annotations=annotations
        )

        fig.show()

    def show_skew_comparison(self) -> None:
        """
        Display bar chart comparing skewness across tickers.
        """
        if not self.returns_data:
            logger.warning("No data to plot. Use add() to add price data first.")
            return

        tickers = list(self.returns_data.keys())
        skews = [self.returns_data[ticker].skew for ticker in tickers]

        # Color bars based on skew direction
        colors = ['green' if s > 0 else 'red' for s in skews]

        fig = go.Figure(data=[
            go.Bar(
                x=tickers,
                y=skews,
                marker_color=colors,
                text=[f'{s:.3f}' for s in skews],
                textposition='outside',
                hovertemplate='%{x}<br>Skewness: %{y:.3f}<extra></extra>'
            )
        ])

        fig.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.5)

        fig.update_layout(
            title='Skewness Comparison',
            xaxis_title='Ticker',
            yaxis_title='Skewness',
            template='plotly_white',
            width=800,
            height=500
        )

        fig.show()

    def get_summary_stats(self) -> pd.DataFrame:
        """
        Get summary statistics for all tickers.

        Returns:
            DataFrame with summary statistics
        """
        stats = []

        for ticker, returns_dto in self.returns_data.items():
            returns = returns_dto.returns
            cumulative = (returns + 1).cumprod() - 1

            stats.append({
                'Ticker': ticker,
                'Mean Return (%)': returns.mean() * 100,
                'Std Dev (%)': returns.std() * 100,
                'Skewness': returns_dto.skew,
                'Cumulative Return (%)': cumulative.iloc[-1] * 100,
                'Sharpe Ratio': returns.mean() / returns.std() if returns.std() > 0 else 0,
                'Min Return (%)': returns.min() * 100,
                'Max Return (%)': returns.max() * 100,
                'Observations': len(returns)
            })

        return pd.DataFrame(stats)

    def __str__(self) -> str:
        tickers = list(self.returns_data.keys())
        return (f"ReturnsPlotter(tickers={tickers}, "
                f"return_type={self.return_type}, "
                f"periods={self.periods})")

    __repr__ = __str__
