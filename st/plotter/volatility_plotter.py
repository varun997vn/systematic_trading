from typing import Optional

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pydantic import BaseModel, Field

from st.dto.volatility import VolatilityDTO


class VolatilityPlotter(BaseModel):
    """Plotter for volatility data with support for multiple series."""

    volatilities: list[VolatilityDTO] = Field(
        default_factory=list,
        description="Collection of volatility data to plot"
    )
    labels: list[str] = Field(
        default_factory=list,
        description="Labels for each volatility series"
    )

    class Config:
        arbitrary_types_allowed = True

    def add(
            self,
            volatility: VolatilityDTO,
            label: Optional[str] = None
    ) -> "VolatilityPlotter":
        """
        Add a VolatilityDTO to the plotter.

        Args:
            volatility: VolatilityDTO instance to add
            label: Optional label for this series (auto-generated if not provided)

        Returns:
            Self for method chaining
        """
        self.volatilities.append(volatility)
        label = label or volatility.returns.price_data.ticker
        self.labels.append(label)

        return self

    def _show_daily(
            self,
            width: int = 900,
            height: int = 450,
            title: str = "Daily Volatility"
    ) -> go.Figure:
        """Plot daily volatility for all added series."""
        fig = go.Figure()

        for vol, label in zip(self.volatilities, self.labels):
            if vol.daily_vol is not None:
                fig.add_trace(go.Scatter(
                    x=vol.returns.price_data.data['Date'],
                    y=vol.daily_vol.values,
                    mode='lines',
                    name=label,
                    opacity=0.7
                ))

        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title="Daily Volatility",
            hovermode='x unified',
            width=width,
            height=height,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )

        return fig

    def _show_annual(
            self,
            width: int = 900,
            height: int = 450,
            title: str = "Annualized Volatility"
    ) -> go.Figure:
        """Plot annualized volatility for all added series."""
        fig = go.Figure()

        for vol, label in zip(self.volatilities, self.labels):
            if vol.annual_vol is not None:
                fig.add_trace(go.Scatter(
                    x=vol.returns.price_data.data['Date'],
                    y=vol.annual_vol.values,
                    mode='lines',
                    name=label,
                    opacity=0.7
                ))

        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title="Annualized Volatility (%)",
            hovermode='x unified',
            width=width,
            height=height,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )

        return fig

    def _show_both(
            self,
            width: int = 900,
            height: int = 700
    ) -> go.Figure:
        """Plot both daily and annualized volatility in subplots."""
        fig = make_subplots(
            rows=2,
            cols=1,
            subplot_titles=("Daily Volatility", "Annualized Volatility"),
            vertical_spacing=0.12
        )

        # Daily volatility
        for vol, label in zip(self.volatilities, self.labels):
            if vol.daily_vol is not None:
                fig.add_trace(
                    go.Scatter(
                        x=vol.returns.price_data.data['Date'],
                        y=vol.daily_vol.values,
                        mode='lines',
                        name=label,
                        opacity=0.7,
                        legendgroup=label,
                        showlegend=True
                    ),
                    row=1,
                    col=1
                )

        # Annualized volatility
        for vol, label in zip(self.volatilities, self.labels):
            if vol.annual_vol is not None:
                fig.add_trace(
                    go.Scatter(
                        x=vol.returns.price_data.data['Date'],
                        y=vol.annual_vol.values,
                        mode='lines',
                        name=label,
                        opacity=0.7,
                        legendgroup=label,
                        showlegend=False
                    ),
                    row=2,
                    col=1
                )

        fig.update_xaxes(title_text="Date", row=1, col=1)
        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Daily Volatility", row=1, col=1)
        fig.update_yaxes(title_text="Annualized Volatility (%)", row=2, col=1)

        fig.update_layout(
            hovermode='x unified',
            width=width,
            height=height,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )

        return fig

    def show(self, plot_type: str = 'daily') -> None:
        """
        Display interactive plot with toggleable tickers.

        Args:
            plot_type: Type of plot to show
                - 'daily': daily volatility over time
                - 'annual': annual volatility over time
                - 'both': Both plots in subplots
        """
        if plot_type == 'both':
            fig = self._show_both()
        elif plot_type == 'annual':
            fig = self._show_annual()
        elif plot_type == 'daily':
            fig = self._show_daily()
        else:
            raise ValueError(f"Invalid plot_type: {plot_type}. Must be 'daily', 'annual', or 'both'")

        fig.show()

    def clear(self) -> "VolatilityPlotter":
        """Clear all volatility data."""
        self.volatilities.clear()
        self.labels.clear()
        return self

    def __str__(self) -> str:
        if not self.volatilities:
            return f"{self.__class__.__name__}(empty)"

        return (
            f"{self.__class__.__name__}({self.labels})"
        )

    __repr__ = __str__
