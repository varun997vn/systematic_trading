"""
Interactive Plotter for Systematic Trading Framework
Generates interactive Plotly visualizations for trading signals, forecasts, and portfolio analysis.
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils.logger import setup_logger

logger = setup_logger(__name__)


class Plotter:
    """
    Interactive plotting class for systematic trading analysis.

    Initializes with a Trader object and extracts all necessary data
    for comprehensive visualization of trading signals, forecasts, and positions.
    """

    def __init__(self, trader):
        """
        Initialize plotter with a Trader object.

        Args:
            trader: Trader instance with executed pipeline
        """
        self.trader = trader
        self.pipeline_output = trader.pipeline_output

        if self.pipeline_output is None:
            raise ValueError(
                "Trader must have executed pipeline (call generate_trades() first)"
            )

        logger.info(
            f"Plotter initialized for {len(trader.tickers)} instruments"
            )

    def plot_prices_with_signals(
            self,
            ticker: str,
            show_ema: bool = True,
            show_forecast: bool = True,
            height: int = 800
    ) -> go.Figure:
        """
        Plot price with trading signals and optional EMA overlays.

        Args:
            ticker: Instrument ticker
            show_ema: Show EMA lines from EWMAC rules
            show_forecast: Show combined forecast in subplot
            height: Figure height

        Returns:
            Plotly figurel
        """
        if ticker not in self.trader.tickers:
            raise ValueError(f"Ticker {ticker} not in trader portfolio")

        # Get price data
        prices = self.pipeline_output.prices[ticker]

        # Create subplots
        rows = 2 if show_forecast else 1
        fig = make_subplots(
            rows=rows, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.7, 0.3] if show_forecast else [1.0],
            subplot_titles=(f'{ticker} Price & Signals',
                            'Combined Forecast') if show_forecast else (
            f'{ticker} Price & Signals',)
        )

        # Plot price
        fig.add_trace(
            go.Scatter(
                x=prices.index,
                y=prices.values,
                name='Price',
                line=dict(color='black', width=2),
                hovertemplate='%{x}<br>Price: $%{y:.2f}<extra></extra>'
            ),
            row=1, col=1
        )

        # Plot EMAs if requested and EWMAC rules exist
        if show_ema:
            self._add_ema_lines(fig, ticker, prices, row=1, col=1)

        # Get current position and forecast
        if ticker in self.pipeline_output.position_set.positions:
            position = self.pipeline_output.position_set.positions[ticker]
            current_forecast = self.pipeline_output.current_forecasts.get(
                ticker, 0
                )

            # Add position marker
            last_price = prices.iloc[-1]
            last_date = prices.index[-1]

            if position.contracts and abs(position.contracts) > 0.01:
                marker_color = 'green' if position.contracts > 0 else 'red'
                marker_symbol = 'triangle-up' if position.contracts > 0 else 'triangle-down'

                fig.add_trace(
                    go.Scatter(
                        x=[last_date],
                        y=[last_price],
                        mode='markers',
                        name=f'Position: {position.contracts:.2f}',
                        marker=dict(
                            size=15,
                            color=marker_color,
                            symbol=marker_symbol,
                            line=dict(width=2, color='white')
                        ),
                        hovertemplate=f'Forecast: {current_forecast:.2f}<br>Position: {position.contracts:.2f} contracts<extra></extra>'
                    ),
                    row=1, col=1
                )

        # Plot forecast in subplot
        if show_forecast:
            forecast_series = self.pipeline_output.combined_forecasts[ticker]

            # Create color based on forecast value
            colors = ['red' if x < 0 else 'green' for x in
                      forecast_series.values]

            fig.add_trace(
                go.Scatter(
                    x=forecast_series.index,
                    y=forecast_series.values,
                    name='Combined Forecast',
                    line=dict(color='blue', width=1.5),
                    fill='tozeroy',
                    fillcolor='rgba(0, 123, 255, 0.2)',
                    hovertemplate='%{x}<br>Forecast: %{y:.2f}<extra></extra>'
                ),
                row=2, col=1
            )

            # Add zero line
            fig.add_hline(
                y=0, line_dash="dash", line_color="gray", row=2, col=1
                )

            # Add forecast thresholds
            fig.add_hline(
                y=10, line_dash="dot", line_color="lightgray", row=2, col=1
                )
            fig.add_hline(
                y=-10, line_dash="dot", line_color="lightgray", row=2, col=1
                )

        # Update layout
        fig.update_xaxes(title_text="Date", row=rows, col=1)
        fig.update_yaxes(title_text="Price ($)", row=1, col=1)
        if show_forecast:
            fig.update_yaxes(
                title_text="Forecast", row=2, col=1, range=[-22, 22]
                )

        fig.update_layout(
            height=height,
            title_text=f"{ticker} - Price & Trading Signals",
            hovermode='x unified',
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )

        return fig

    def plot_individual_forecasts(
            self,
            ticker: str,
            height: int = 600
    ) -> go.Figure:
        """
        Plot all individual rule forecasts for a ticker.

        Args:
            ticker: Instrument ticker
            height: Figure height

        Returns:
            Plotly figure
        """
        if ticker not in self.trader.tickers:
            raise ValueError(f"Ticker {ticker} not in trader portfolio")

        # Get forecasts for this ticker
        ticker_forecasts = self.pipeline_output.forecasts[ticker]

        fig = go.Figure()

        # Plot each rule's forecast
        for rule_name, forecast in ticker_forecasts.items():
            fig.add_trace(
                go.Scatter(
                    x=forecast.scaled_forecast.index,
                    y=forecast.scaled_forecast.values,
                    name=rule_name,
                    mode='lines',
                    hovertemplate=f'{rule_name}<br>%{{x}}<br>Forecast: %{{y:.2f}}<extra></extra>'
                )
            )

        # Add combined forecast
        combined = self.pipeline_output.combined_forecasts[ticker]
        fig.add_trace(
            go.Scatter(
                x=combined.index,
                y=combined.values,
                name='Combined',
                line=dict(color='black', width=3, dash='dash'),
                hovertemplate='Combined<br>%{x}<br>Forecast: %{y:.2f}<extra></extra>'
            )
        )

        # Add reference lines
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        fig.add_hline(y=10, line_dash="dot", line_color="lightgray")
        fig.add_hline(y=-10, line_dash="dot", line_color="lightgray")
        fig.add_hline(y=20, line_dash="dot", line_color="red", opacity=0.5)
        fig.add_hline(y=-20, line_dash="dot", line_color="red", opacity=0.5)

        fig.update_layout(
            title=f"{ticker} - Individual Rule Forecasts",
            xaxis_title="Date",
            yaxis_title="Forecast",
            height=height,
            hovermode='x unified',
            yaxis=dict(range=[-22, 22])
        )

        return fig

    def plot_forecast_weights(self) -> go.Figure:
        """
        Plot forecast weights distribution.

        Returns:
            Plotly figure
        """
        weights = self.trader.trading_rules_config.get_weights()

        fig = go.Figure(
            data=[
                go.Bar(
                    x=list(weights.keys()),
                    y=list(weights.values()),
                    text=[f'{v * 100:.1f}%' for v in weights.values()],
                    textposition='auto',
                    marker_color='steelblue'
                )
            ]
        )

        fig.update_layout(
            title="Trading Rule Weights",
            xaxis_title="Rule",
            yaxis_title="Weight",
            height=400,
            yaxis=dict(tickformat='.0%')
        )

        return fig

    def plot_volatility(
            self,
            ticker: str,
            show_price: bool = True,
            height: int = 600
    ) -> go.Figure:
        """
        Plot volatility over time with optional price overlay.

        Args:
            ticker: Instrument ticker
            show_price: Show price in secondary y-axis
            height: Figure height

        Returns:
            Plotly figure
        """
        if ticker not in self.trader.tickers:
            raise ValueError(f"Ticker {ticker} not in trader portfolio")

        vol_result = self.pipeline_output.volatilities[ticker]
        vol_series = vol_result.price_volatility

        fig = make_subplots(specs=[[{"secondary_y": show_price}]])

        # Plot volatility
        fig.add_trace(
            go.Scatter(
                x=vol_series.index,
                y=vol_series.values,
                name='Volatility',
                line=dict(color='purple', width=2),
                fill='tozeroy',
                fillcolor='rgba(128, 0, 128, 0.2)',
                hovertemplate='%{x}<br>Volatility: %{y:.4f}<extra></extra>'
            ),
            secondary_y=False
        )

        # Add current volatility line
        current_vol = vol_result.current_annual_vol
        fig.add_hline(
            y=current_vol,
            line_dash="dash",
            line_color="purple",
            annotation_text=f"Current: {current_vol:.4f}",
            annotation_position="right",
            secondary_y=False
        )

        # Plot price on secondary axis if requested
        if show_price:
            prices = self.pipeline_output.prices[ticker]
            fig.add_trace(
                go.Scatter(
                    x=prices.index,
                    y=prices.values,
                    name='Price',
                    line=dict(color='black', width=1, dash='dot'),
                    opacity=0.5,
                    hovertemplate='%{x}<br>Price: $%{y:.2f}<extra></extra>'
                ),
                secondary_y=True
            )

        fig.update_xaxes(title_text="Date")
        fig.update_yaxes(title_text="Volatility", secondary_y=False)
        if show_price:
            fig.update_yaxes(title_text="Price ($)", secondary_y=True)

        fig.update_layout(
            title=f"{ticker} - Volatility Over Time",
            height=height,
            hovermode='x unified'
        )

        return fig

    def plot_portfolio_forecasts(
            self,
            height: int = 500
    ) -> go.Figure:
        """
        Plot current forecast for all instruments in portfolio.

        Args:
            height: Figure height

        Returns:
            Plotly figure
        """
        forecasts = self.pipeline_output.current_forecasts
        tickers = list(forecasts.keys())
        values = list(forecasts.values())

        # Color based on direction
        colors = ['green' if v > 0 else 'red' for v in values]

        fig = go.Figure(
            data=[
                go.Bar(
                    x=tickers,
                    y=values,
                    text=[f'{v:.2f}' for v in values],
                    textposition='outside',
                    marker_color=colors,
                    hovertemplate='%{x}<br>Forecast: %{y:.2f}<extra></extra>'
                )
            ]
        )

        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        fig.add_hline(y=10, line_dash="dot", line_color="lightgray")
        fig.add_hline(y=-10, line_dash="dot", line_color="lightgray")

        fig.update_layout(
            title="Portfolio Forecasts (Current)",
            xaxis_title="Instrument",
            yaxis_title="Forecast",
            height=height,
            yaxis=dict(range=[-22, 22])
        )

        return fig

    def plot_positions(
            self,
            height: int = 500
    ) -> go.Figure:
        """
        Plot current positions for all instruments.

        Args:
            height: Figure height

        Returns:
            Plotly figure
        """
        positions = {}
        for ticker, pos in self.pipeline_output.position_set.positions.items():
            if pos.contracts:
                positions[ticker] = pos.contracts

        if not positions:
            logger.warning("No positions to plot")
            return go.Figure().add_annotation(
                text="No current positions",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )

        tickers = list(positions.keys())
        values = list(positions.values())
        colors = ['green' if v > 0 else 'red' for v in values]

        fig = go.Figure(
            data=[
                go.Bar(
                    x=tickers,
                    y=values,
                    text=[f'{v:.2f}' for v in values],
                    textposition='outside',
                    marker_color=colors,
                    hovertemplate='%{x}<br>Contracts: %{y:.2f}<extra></extra>'
                )
            ]
        )

        fig.add_hline(y=0, line_dash="dash", line_color="gray")

        fig.update_layout(
            title="Current Positions (Contracts)",
            xaxis_title="Instrument",
            yaxis_title="Contracts",
            height=height
        )

        return fig

    def plot_ewmac_components(
            self,
            ticker: str,
            fast_span: int = 16,
            slow_span: int = 64,
            height: int = 800
    ) -> go.Figure:
        """
        Plot EWMAC components: price, fast EMA, slow EMA, and raw signal.

        Args:
            ticker: Instrument ticker
            fast_span: Fast EMA span
            slow_span: Slow EMA span
            height: Figure height

        Returns:
            Plotly figure
        """
        if ticker not in self.trader.tickers:
            raise ValueError(f"Ticker {ticker} not in trader portfolio")

        prices = self.pipeline_output.prices[ticker]

        # Calculate EMAs
        fast_ema = prices.ewm(span=fast_span, min_periods=fast_span).mean()
        slow_ema = prices.ewm(span=slow_span, min_periods=slow_span).mean()
        raw_signal = fast_ema - slow_ema

        # Create subplots
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.7, 0.3],
            subplot_titles=(f'{ticker} Price & EMAs',
                            f'Raw EWMAC Signal ({fast_span}/{slow_span})')
        )

        # Plot price and EMAs
        fig.add_trace(
            go.Scatter(
                x=prices.index,
                y=prices.values,
                name='Price',
                line=dict(color='black', width=2),
                hovertemplate='Price: $%{y:.2f}<extra></extra>'
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=fast_ema.index,
                y=fast_ema.values,
                name=f'Fast EMA ({fast_span})',
                line=dict(color='blue', width=1.5),
                hovertemplate='Fast EMA: $%{y:.2f}<extra></extra>'
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=slow_ema.index,
                y=slow_ema.values,
                name=f'Slow EMA ({slow_span})',
                line=dict(color='red', width=1.5),
                hovertemplate='Slow EMA: $%{y:.2f}<extra></extra>'
            ),
            row=1, col=1
        )

        # Plot raw signal
        colors = ['red' if x < 0 else 'green' for x in raw_signal.values]

        fig.add_trace(
            go.Scatter(
                x=raw_signal.index,
                y=raw_signal.values,
                name='Raw Signal',
                line=dict(color='purple', width=1.5),
                fill='tozeroy',
                fillcolor='rgba(128, 0, 128, 0.2)',
                hovertemplate='Signal: %{y:.4f}<extra></extra>'
            ),
            row=2, col=1
        )

        fig.add_hline(y=0, line_dash="dash", line_color="gray", row=2, col=1)

        # Update layout
        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Price ($)", row=1, col=1)
        fig.update_yaxes(title_text="Raw Signal", row=2, col=1)

        fig.update_layout(
            height=height,
            title_text=f"{ticker} - EWMAC Components ({fast_span}/{slow_span})",
            hovermode='x unified',
            showlegend=True
        )

        return fig

    def plot_turtle_breakout(
            self,
            ticker: str,
            entry_window: int = 20,
            exit_window: int = 10,
            height: int = 600
    ) -> go.Figure:
        """
        Plot Turtle Trading breakout channels.

        Args:
            ticker: Instrument ticker
            entry_window: Entry breakout window
            exit_window: Exit breakout window
            height: Figure height

        Returns:
            Plotly figure
        """
        if ticker not in self.trader.tickers:
            raise ValueError(f"Ticker {ticker} not in trader portfolio")

        prices = self.pipeline_output.prices[ticker]

        # Calculate channels
        entry_upper = prices.rolling(window=entry_window).max()
        entry_lower = prices.rolling(window=entry_window).min()
        exit_upper = prices.rolling(window=exit_window).max()
        exit_lower = prices.rolling(window=exit_window).min()

        fig = go.Figure()

        # Plot price
        fig.add_trace(
            go.Scatter(
                x=prices.index,
                y=prices.values,
                name='Price',
                line=dict(color='black', width=2),
                hovertemplate='Price: $%{y:.2f}<extra></extra>'
            )
        )

        # Plot entry channels
        fig.add_trace(
            go.Scatter(
                x=entry_upper.index,
                y=entry_upper.values,
                name=f'Entry Upper ({entry_window}d)',
                line=dict(color='green', width=1.5, dash='dash'),
                hovertemplate='Entry Upper: $%{y:.2f}<extra></extra>'
            )
        )

        fig.add_trace(
            go.Scatter(
                x=entry_lower.index,
                y=entry_lower.values,
                name=f'Entry Lower ({entry_window}d)',
                line=dict(color='red', width=1.5, dash='dash'),
                hovertemplate='Entry Lower: $%{y:.2f}<extra></extra>'
            )
        )

        # Plot exit channels
        fig.add_trace(
            go.Scatter(
                x=exit_upper.index,
                y=exit_upper.values,
                name=f'Exit Upper ({exit_window}d)',
                line=dict(color='lightgreen', width=1, dash='dot'),
                opacity=0.7,
                hovertemplate='Exit Upper: $%{y:.2f}<extra></extra>'
            )
        )

        fig.add_trace(
            go.Scatter(
                x=exit_lower.index,
                y=exit_lower.values,
                name=f'Exit Lower ({exit_window}d)',
                line=dict(color='lightcoral', width=1, dash='dot'),
                opacity=0.7,
                hovertemplate='Exit Lower: $%{y:.2f}<extra></extra>'
            )
        )

        fig.update_layout(
            title=f"{ticker} - Turtle Trading Breakout Channels",
            xaxis_title="Date",
            yaxis_title="Price ($)",
            height=height,
            hovermode='x unified'
        )

        return fig

    def plot_mean_reversion(
            self,
            ticker: str,
            lookback: int = 30,
            height: int = 800
    ) -> go.Figure:
        """
        Plot mean reversion components: price, moving average, and z-score.

        Args:
            ticker: Instrument ticker
            lookback: Lookback period
            height: Figure height

        Returns:
            Plotly figure
        """
        if ticker not in self.trader.tickers:
            raise ValueError(f"Ticker {ticker} not in trader portfolio")

        prices = self.pipeline_output.prices[ticker]

        # Calculate components
        rolling_mean = prices.rolling(window=lookback).mean()
        rolling_std = prices.rolling(window=lookback).std()
        z_score = (prices - rolling_mean) / rolling_std
        upper_band = rolling_mean + 2 * rolling_std
        lower_band = rolling_mean - 2 * rolling_std

        # Create subplots
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.7, 0.3],
            subplot_titles=(
            f'{ticker} Price & Bands', f'Z-Score ({lookback}d)')
        )

        # Plot price and bands
        fig.add_trace(
            go.Scatter(
                x=prices.index,
                y=prices.values,
                name='Price',
                line=dict(color='black', width=2),
                hovertemplate='Price: $%{y:.2f}<extra></extra>'
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=rolling_mean.index,
                y=rolling_mean.values,
                name=f'Mean ({lookback}d)',
                line=dict(color='blue', width=1.5),
                hovertemplate='Mean: $%{y:.2f}<extra></extra>'
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=upper_band.index,
                y=upper_band.values,
                name='Upper Band (+2σ)',
                line=dict(color='red', width=1, dash='dash'),
                hovertemplate='Upper: $%{y:.2f}<extra></extra>'
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=lower_band.index,
                y=lower_band.values,
                name='Lower Band (-2σ)',
                line=dict(color='green', width=1, dash='dash'),
                hovertemplate='Lower: $%{y:.2f}<extra></extra>'
            ),
            row=1, col=1
        )

        # Plot z-score
        fig.add_trace(
            go.Scatter(
                x=z_score.index,
                y=z_score.values,
                name='Z-Score',
                line=dict(color='purple', width=1.5),
                fill='tozeroy',
                fillcolor='rgba(128, 0, 128, 0.2)',
                hovertemplate='Z-Score: %{y:.2f}<extra></extra>'
            ),
            row=2, col=1
        )

        # Add reference lines to z-score
        fig.add_hline(y=0, line_dash="dash", line_color="gray", row=2, col=1)
        fig.add_hline(y=2, line_dash="dot", line_color="red", row=2, col=1)
        fig.add_hline(y=-2, line_dash="dot", line_color="green", row=2, col=1)

        # Update layout
        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Price ($)", row=1, col=1)
        fig.update_yaxes(title_text="Z-Score", row=2, col=1)

        fig.update_layout(
            height=height,
            title_text=f"{ticker} - Mean Reversion Components ({lookback}d)",
            hovermode='x unified',
            showlegend=True
        )

        return fig

    def plot_portfolio_summary(
            self,
            height: int = 900
    ) -> go.Figure:
        """
        Plot comprehensive portfolio summary with multiple panels.

        Args:
            height: Figure height

        Returns:
            Plotly figure
        """
        # Create subplots
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                'Current Forecasts',
                'Current Positions',
                'Forecast Weights',
                'Instrument Volatilities',
                'Capital Allocation',
                'Portfolio Metrics'
            ),
            specs=[
                [{"type": "bar"}, {"type": "bar"}],
                [{"type": "bar"}, {"type": "bar"}],
                [{"type": "bar"}, {"type": "table"}]
            ],
            vertical_spacing=0.12,
            horizontal_spacing=0.1
        )

        # 1. Current Forecasts
        forecasts = self.pipeline_output.current_forecasts
        tickers = list(forecasts.keys())
        forecast_values = list(forecasts.values())
        forecast_colors = ['green' if v > 0 else 'red' for v in
                           forecast_values]

        fig.add_trace(
            go.Bar(
                x=tickers,
                y=forecast_values,
                marker_color=forecast_colors,
                name='Forecast',
                showlegend=False
            ),
            row=1, col=1
        )

        # 2. Current Positions
        positions = {}
        for ticker, pos in self.pipeline_output.position_set.positions.items():
            if pos.contracts:
                positions[ticker] = pos.contracts

        if positions:
            pos_tickers = list(positions.keys())
            pos_values = list(positions.values())
            pos_colors = ['green' if v > 0 else 'red' for v in pos_values]

            fig.add_trace(
                go.Bar(
                    x=pos_tickers,
                    y=pos_values,
                    marker_color=pos_colors,
                    name='Position',
                    showlegend=False
                ),
                row=1, col=2
            )

        # 3. Forecast Weights
        weights = self.trader.trading_rules_config.get_weights()

        fig.add_trace(
            go.Bar(
                x=list(weights.keys()),
                y=list(weights.values()),
                marker_color='steelblue',
                name='Weight',
                showlegend=False
            ),
            row=2, col=1
        )

        # 4. Volatilities
        vols = {
            ticker: vol.current_annual_vol
            for ticker, vol in self.pipeline_output.volatilities.items()
        }

        fig.add_trace(
            go.Bar(
                x=list(vols.keys()),
                y=list(vols.values()),
                marker_color='purple',
                name='Volatility',
                showlegend=False
            ),
            row=2, col=2
        )

        # 5. Capital Allocation
        capital_alloc = self.pipeline_output.capital_allocation

        fig.add_trace(
            go.Bar(
                x=list(capital_alloc.keys()),
                y=list(capital_alloc.values()),
                marker_color='orange',
                name='Capital',
                showlegend=False
            ),
            row=3, col=1
        )

        # 6. Portfolio Metrics Table
        metrics_data = {
            'Metric': [
                'Total Capital',
                'Portfolio Leverage',
                'Diversification Multiplier (IDM)',
                'Number of Instruments',
                'Number of Trades',
                'Total Notional'
            ],
            'Value':  [
                f'${self.trader.capital:,.0f}',
                f'{self.pipeline_output.position_set.portfolio_leverage:.2f}x',
                f'{self.pipeline_output.portfolio_weights.diversification_multiplier:.2f}',
                f'{len(self.trader.tickers)}',
                f'{self.pipeline_output.trade_set.num_trades}',
                f'${self.pipeline_output.trade_set.total_notional:,.0f}'
            ]
        }

        fig.add_trace(
            go.Table(
                header=dict(
                    values=['<b>Metric</b>', '<b>Value</b>'],
                    fill_color='steelblue',
                    font=dict(color='white', size=12),
                    align='left'
                ),
                cells=dict(
                    values=[metrics_data['Metric'], metrics_data['Value']],
                    fill_color='lavender',
                    align='left',
                    height=25
                )
            ),
            row=3, col=2
        )

        # Update axes
        fig.update_yaxes(title_text="Forecast", row=1, col=1)
        fig.update_yaxes(title_text="Contracts", row=1, col=2)
        fig.update_yaxes(title_text="Weight", row=2, col=1, tickformat='.0%')
        fig.update_yaxes(title_text="Ann. Vol", row=2, col=2, tickformat='.2%')
        fig.update_yaxes(title_text="Capital ($)", row=3, col=1)

        fig.update_layout(
            height=height,
            title_text="Portfolio Summary Dashboard",
            showlegend=False
        )

        return fig

    def _add_ema_lines(
            self,
            fig: go.Figure,
            ticker: str,
            prices: pd.Series,
            row: int,
            col: int
    ):
        """Helper to add EMA lines to a figure."""
        # Find EWMAC rules in forecasts
        ticker_forecasts = self.pipeline_output.raw_forecasts[ticker]

        # Extract EWMAC parameters
        ewmac_params = []
        for rule_name in ticker_forecasts.keys():
            if 'ewmac' in rule_name.lower():
                # Parse spans from rule name (e.g., 'ewmac_16_64_normalized')
                parts = rule_name.split('_')
                if len(parts) >= 3 and parts[1].isdigit() and parts[
                    2].isdigit():
                    fast_span = int(parts[1])
                    slow_span = int(parts[2])
                    ewmac_params.append((fast_span, slow_span))

        # Remove duplicates and limit to 3 most important
        ewmac_params = list(set(ewmac_params))[:3]

        # Plot EMAs
        colors = ['blue', 'red', 'green', 'orange', 'purple']
        for i, (fast, slow) in enumerate(ewmac_params):
            fast_ema = prices.ewm(span=fast, min_periods=fast).mean()
            slow_ema = prices.ewm(span=slow, min_periods=slow).mean()

            color_idx = i % len(colors)

            fig.add_trace(
                go.Scatter(
                    x=fast_ema.index,
                    y=fast_ema.values,
                    name=f'EMA {fast}',
                    line=dict(color=colors[color_idx], width=1, dash='dot'),
                    opacity=0.6,
                    hovertemplate=f'EMA {fast}: $%{{y:.2f}}<extra></extra>'
                ),
                row=row, col=col
            )

            fig.add_trace(
                go.Scatter(
                    x=slow_ema.index,
                    y=slow_ema.values,
                    name=f'EMA {slow}',
                    line=dict(color=colors[color_idx], width=1.5, dash='dash'),
                    opacity=0.6,
                    hovertemplate=f'EMA {slow}: $%{{y:.2f}}<extra></extra>'
                ),
                row=row, col=col
            )
