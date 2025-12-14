"""
Plotter class for visualizing trading system components.
Supports both matplotlib and plotly backends with plotly as default.
"""

from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import pandas as pd
from pydantic import BaseModel, Field

from utils.logger import setup_logger

logger = setup_logger(__name__)


# ==========================================
# Enums and Constants
# ==========================================


class PlotBackend(str, Enum):
    """Available plotting backends."""

    MATPLOTLIB = "matplotlib"
    PLOTLY = "plotly"


class PlotTheme(str, Enum):
    """Plot themes/styles."""

    DEFAULT = "default"
    DARK = "dark"
    LIGHT = "light"
    SEABORN = "seaborn"


# ==========================================
# Abstract Base Plotter
# ==========================================


class BasePlotter(ABC):
    """Abstract base class for plotting backends."""

    @abstractmethod
    def plot_price_history(
            self, data: pd.DataFrame, title: str = "Price History", **kwargs
    ) -> Any:
        """Plot price history."""
        pass

    @abstractmethod
    def plot_portfolio_value(
            self, history: pd.DataFrame, title: str = "Portfolio Value", **kwargs
    ) -> Any:
        """Plot portfolio value over time."""
        pass

    @abstractmethod
    def plot_portfolio_composition(
            self, weights: Dict[str, float], title: str = "Portfolio Composition", **kwargs
    ) -> Any:
        """Plot portfolio composition as pie chart."""
        pass

    @abstractmethod
    def plot_returns(
            self, returns: pd.Series, title: str = "Returns Distribution", **kwargs
    ) -> Any:
        """Plot returns distribution."""
        pass

    @abstractmethod
    def plot_drawdown(
            self, equity_curve: pd.Series, title: str = "Drawdown", **kwargs
    ) -> Any:
        """Plot drawdown over time."""
        pass

    @abstractmethod
    def plot_multiple_series(
            self, data: Dict[str, pd.Series], title: str = "Multiple Series", **kwargs
    ) -> Any:
        """Plot multiple time series."""
        pass

    @abstractmethod
    def save(self, fig: Any, filename: str, **kwargs) -> None:
        """Save figure to file."""
        pass


# ==========================================
# Matplotlib Backend
# ==========================================


class MatplotlibPlotter(BasePlotter):
    """Matplotlib plotting backend."""

    def __init__(
            self, theme: PlotTheme = PlotTheme.DEFAULT, figsize: Tuple[int, int] = (12, 6)
    ):
        try:
            import matplotlib.dates as mdates
            import matplotlib.pyplot as plt
            from matplotlib.figure import Figure

            self.plt = plt
            self.mdates = mdates
            self.Figure = Figure
            self.figsize = figsize

            # Apply theme
            self._apply_theme(theme)

        except ImportError:
            raise ImportError(
                "matplotlib is required for this backend. Install with: pip install matplotlib"
            )

    def _apply_theme(self, theme: PlotTheme) -> None:
        """Apply theme to matplotlib."""
        if theme == PlotTheme.DARK:
            self.plt.style.use("dark_background")
        elif theme == PlotTheme.SEABORN:
            try:
                import seaborn as sns

                sns.set_theme()
            except ImportError:
                logger.warning("Seaborn not installed, using default theme")
        elif theme == PlotTheme.LIGHT:
            self.plt.style.use("default")

    def plot_price_history(
            self,
            data: pd.DataFrame,
            title: str = "Price History",
            columns: Optional[List[str]] = None,
            **kwargs,
    ) -> Any:
        """Plot price history with optional volume."""
        fig, axes = self.plt.subplots(
            2,
            1,
            figsize=kwargs.get("figsize", self.figsize),
            gridspec_kw={"height_ratios": [3, 1]},
            sharex=True,
        )

        # Price plot
        if columns is None:
            if "Close" in data.columns:
                columns = ["Close"]
            else:
                columns = [col for col in data.columns if col not in ["Volume"]]

        for col in columns:
            if col in data.columns:
                axes[0].plot(data.index, data[col], label=col, linewidth=1.5)

        axes[0].set_ylabel("Price ($)", fontsize=10)
        axes[0].set_title(title, fontsize=12, fontweight="bold")
        axes[0].legend(loc="upper left")
        axes[0].grid(True, alpha=0.3)

        # Volume plot
        if "Volume" in data.columns:
            axes[1].bar(data.index, data["Volume"], alpha=0.5, color="gray")
            axes[1].set_ylabel("Volume", fontsize=10)
            axes[1].set_xlabel("Date", fontsize=10)
            axes[1].grid(True, alpha=0.3)
        else:
            fig.delaxes(axes[1])

        self.plt.tight_layout()
        return fig

    def plot_portfolio_value(
            self, history: pd.DataFrame, title: str = "Portfolio Value", **kwargs
    ) -> Any:
        """Plot portfolio value over time."""
        fig, ax = self.plt.subplots(figsize=kwargs.get("figsize", self.figsize))

        if "total_value" in history.columns:
            ax.plot(
                history.index,
                history["total_value"],
                linewidth=2,
                color="#2E86AB",
                label="Total Value",
            )

        if "cash" in history.columns:
            ax.plot(
                history.index,
                history["cash"],
                linewidth=1.5,
                color="#A23B72",
                alpha=0.7,
                label="Cash",
            )

        if "positions_value" in history.columns:
            ax.plot(
                history.index,
                history["positions_value"],
                linewidth=1.5,
                color="#F18F01",
                alpha=0.7,
                label="Positions",
            )

        ax.set_xlabel("Date", fontsize=10)
        ax.set_ylabel("Value ($)", fontsize=10)
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.legend(loc="upper left")
        ax.grid(True, alpha=0.3)

        # Format y-axis as currency
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x:,.0f}"))

        self.plt.tight_layout()
        return fig

    def plot_portfolio_composition(
            self, weights: Dict[str, float], title: str = "Portfolio Composition", **kwargs
    ) -> Any:
        """Plot portfolio composition as pie chart."""
        fig, ax = self.plt.subplots(figsize=kwargs.get("figsize", (8, 8)))

        # Filter out very small weights
        min_weight = kwargs.get("min_weight", 0.5)
        filtered_weights = {k: v for k, v in weights.items() if v >= min_weight}

        if len(filtered_weights) < len(weights):
            other_weight = sum(
                v for k, v in weights.items() if k not in filtered_weights
            )
            if other_weight > 0:
                filtered_weights["Other"] = other_weight

        labels = list(filtered_weights.keys())
        sizes = list(filtered_weights.values())

        colors = self.plt.cm.Set3(range(len(labels)))

        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, autopct="%1.1f%%", startangle=90, colors=colors
        )

        # Enhance text
        for text in texts:
            text.set_fontsize(10)
        for autotext in autotexts:
            autotext.set_color("white")
            autotext.set_fontweight("bold")
            autotext.set_fontsize(9)

        ax.set_title(title, fontsize=12, fontweight="bold")
        self.plt.tight_layout()
        return fig

    def plot_returns(
            self, returns: pd.Series, title: str = "Returns Distribution", **kwargs
    ) -> Any:
        """Plot returns distribution."""
        fig, axes = self.plt.subplots(1, 2, figsize=kwargs.get("figsize", (14, 5)))

        # Histogram
        axes[0].hist(
            returns.dropna(), bins=50, alpha=0.7, color="#2E86AB", edgecolor="black"
        )
        axes[0].axvline(
            returns.mean(),
            color="red",
            linestyle="--",
            linewidth=2,
            label=f"Mean: {returns.mean():.2%}",
        )
        axes[0].set_xlabel("Returns", fontsize=10)
        axes[0].set_ylabel("Frequency", fontsize=10)
        axes[0].set_title("Returns Histogram", fontsize=11, fontweight="bold")
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)

        # Time series
        axes[1].plot(
            returns.index, returns.values, linewidth=1, alpha=0.7, color="#2E86AB"
        )
        axes[1].axhline(0, color="black", linestyle="-", linewidth=0.5)
        axes[1].set_xlabel("Date", fontsize=10)
        axes[1].set_ylabel("Returns", fontsize=10)
        axes[1].set_title("Returns Over Time", fontsize=11, fontweight="bold")
        axes[1].grid(True, alpha=0.3)

        fig.suptitle(title, fontsize=12, fontweight="bold", y=1.02)
        self.plt.tight_layout()
        return fig

    def plot_drawdown(
            self, equity_curve: pd.Series, title: str = "Drawdown", **kwargs
    ) -> Any:
        """Plot drawdown over time."""
        # Calculate drawdown
        running_max = equity_curve.expanding().max()
        drawdown = (equity_curve - running_max) / running_max * 100

        fig, axes = self.plt.subplots(
            2, 1, figsize=kwargs.get("figsize", self.figsize), sharex=True
        )

        # Equity curve
        axes[0].plot(
            equity_curve.index, equity_curve.values, linewidth=2, color="#2E86AB"
        )
        axes[0].set_ylabel("Portfolio Value ($)", fontsize=10)
        axes[0].set_title("Equity Curve", fontsize=11, fontweight="bold")
        axes[0].grid(True, alpha=0.3)

        # Drawdown
        axes[1].fill_between(
            drawdown.index, drawdown.values, 0, alpha=0.5, color="#A23B72"
        )
        axes[1].set_xlabel("Date", fontsize=10)
        axes[1].set_ylabel("Drawdown (%)", fontsize=10)
        axes[1].set_title("Drawdown", fontsize=11, fontweight="bold")
        axes[1].grid(True, alpha=0.3)

        fig.suptitle(title, fontsize=12, fontweight="bold", y=1.01)
        self.plt.tight_layout()
        return fig

    def plot_multiple_series(
            self, data: Dict[str, pd.Series], title: str = "Multiple Series", **kwargs
    ) -> Any:
        """Plot multiple time series."""
        fig, ax = self.plt.subplots(figsize=kwargs.get("figsize", self.figsize))

        for label, series in data.items():
            ax.plot(series.index, series.values, label=label, linewidth=1.5, alpha=0.8)

        ax.set_xlabel("Date", fontsize=10)
        ax.set_ylabel("Value", fontsize=10)
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.legend(loc="best")
        ax.grid(True, alpha=0.3)

        self.plt.tight_layout()
        return fig

    def save(self, fig: Any, filename: str, **kwargs) -> None:
        """Save figure to file."""
        dpi = kwargs.get("dpi", 150)
        bbox_inches = kwargs.get("bbox_inches", "tight")

        fig.savefig(filename, dpi=dpi, bbox_inches=bbox_inches)
        logger.info(f"Saved plot to {filename}")


# ==========================================
# Plotly Backend
# ==========================================


class PlotlyPlotter(BasePlotter):
    """Plotly plotting backend."""

    def __init__(self, theme: PlotTheme = PlotTheme.DEFAULT):
        try:
            import plotly.express as px
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots

            self.go = go
            self.px = px
            self.make_subplots = make_subplots

            # Set theme template
            self.template = self._get_template(theme)

        except ImportError:
            raise ImportError(
                "plotly is required for this backend. Install with: pip install plotly"
            )

    def _get_template(self, theme: PlotTheme) -> str:
        """Get plotly template for theme."""
        theme_map = {
            PlotTheme.DEFAULT: "plotly",
            PlotTheme.DARK: "plotly_dark",
            PlotTheme.LIGHT: "plotly_white",
            PlotTheme.SEABORN: "seaborn",
        }
        return theme_map.get(theme, "plotly")

    def plot_price_history(
            self,
            data: pd.DataFrame,
            title: str = "Price History",
            columns: Optional[List[str]] = None,
            **kwargs,
    ) -> Any:
        """Plot price history with optional volume."""
        if columns is None:
            if "Close" in data.columns:
                columns = ["Close"]
            else:
                columns = [col for col in data.columns if col not in ["Volume"]]

        # Create subplot with volume
        has_volume = "Volume" in data.columns
        specs = (
            [[{"secondary_y": False}], [{"secondary_y": False}]]
            if has_volume
            else [[{"secondary_y": False}]]
        )
        row_heights = [0.7, 0.3] if has_volume else [1.0]

        fig = self.make_subplots(
            rows=2 if has_volume else 1,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=row_heights,
            subplot_titles=(["Price", "Volume"] if has_volume else ["Price"]),
        )

        # Add price traces
        for col in columns:
            if col in data.columns:
                fig.add_trace(
                    self.go.Scatter(
                        x=data.index,
                        y=data[col],
                        mode="lines",
                        name=col,
                        line=dict(width=2),
                    ),
                    row=1,
                    col=1,
                )

        # Add volume trace
        if has_volume:
            fig.add_trace(
                self.go.Bar(
                    x=data.index,
                    y=data["Volume"],
                    name="Volume",
                    marker_color="rgba(158, 158, 158, 0.5)",
                ),
                row=2,
                col=1,
            )

        fig.update_xaxes(title_text="Date", row=2 if has_volume else 1, col=1)
        fig.update_yaxes(title_text="Price ($)", row=1, col=1)
        if has_volume:
            fig.update_yaxes(title_text="Volume", row=2, col=1)

        fig.update_layout(
            title=title,
            template=self.template,
            hovermode="x unified",
            height=kwargs.get("height", 600),
        )

        return fig

    def plot_portfolio_value(
            self, history: pd.DataFrame, title: str = "Portfolio Value", **kwargs
    ) -> Any:
        """Plot portfolio value over time."""
        fig = self.go.Figure()

        if "total_value" in history.columns:
            fig.add_trace(
                self.go.Scatter(
                    x=history.index,
                    y=history["total_value"],
                    mode="lines",
                    name="Total Value",
                    line=dict(width=3, color="#2E86AB"),
                )
            )

        if "cash" in history.columns:
            fig.add_trace(
                self.go.Scatter(
                    x=history.index,
                    y=history["cash"],
                    mode="lines",
                    name="Cash",
                    line=dict(width=2, color="#A23B72"),
                    opacity=0.7,
                )
            )

        if "positions_value" in history.columns:
            fig.add_trace(
                self.go.Scatter(
                    x=history.index,
                    y=history["positions_value"],
                    mode="lines",
                    name="Positions",
                    line=dict(width=2, color="#F18F01"),
                    opacity=0.7,
                )
            )

        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title="Value ($)",
            template=self.template,
            hovermode="x unified",
            height=kwargs.get("height", 500),
        )

        return fig

    def plot_portfolio_composition(
            self, weights: Dict[str, float], title: str = "Portfolio Composition", **kwargs
    ) -> Any:
        """Plot portfolio composition as pie chart."""
        # Filter out very small weights
        min_weight = kwargs.get("min_weight", 0.5)
        filtered_weights = {k: v for k, v in weights.items() if v >= min_weight}

        if len(filtered_weights) < len(weights):
            other_weight = sum(
                v for k, v in weights.items() if k not in filtered_weights
            )
            if other_weight > 0:
                filtered_weights["Other"] = other_weight

        labels = list(filtered_weights.keys())
        values = list(filtered_weights.values())

        fig = self.go.Figure(
            data=[
                self.go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.3,
                    textposition="inside",
                    textinfo="label+percent",
                )
            ]
        )

        fig.update_layout(
            title=title, template=self.template, height=kwargs.get("height", 500)
        )

        return fig

    def plot_returns(
            self, returns: pd.Series, title: str = "Returns Distribution", **kwargs
    ) -> Any:
        """Plot returns distribution."""
        fig = self.make_subplots(
            rows=1, cols=2, subplot_titles=("Returns Histogram", "Returns Over Time")
        )

        # Histogram
        fig.add_trace(
            self.go.Histogram(
                x=returns.dropna(),
                nbinsx=50,
                name="Returns",
                marker_color="#2E86AB",
                opacity=0.7,
            ),
            row=1,
            col=1,
        )

        # Add mean line
        mean_return = returns.mean()
        fig.add_vline(
            x=mean_return,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Mean: {mean_return:.2%}",
            row=1,
            col=1,
        )

        # Time series
        fig.add_trace(
            self.go.Scatter(
                x=returns.index,
                y=returns.values,
                mode="lines",
                name="Returns",
                line=dict(width=1, color="#2E86AB"),
                opacity=0.7,
            ),
            row=1,
            col=2,
        )

        # Add zero line
        fig.add_hline(
            y=0, line_dash="solid", line_color="black", line_width=0.5, row=1, col=2
        )

        fig.update_xaxes(title_text="Returns", row=1, col=1)
        fig.update_xaxes(title_text="Date", row=1, col=2)
        fig.update_yaxes(title_text="Frequency", row=1, col=1)
        fig.update_yaxes(title_text="Returns", row=1, col=2)

        fig.update_layout(
            title=title,
            template=self.template,
            showlegend=False,
            height=kwargs.get("height", 500),
        )

        return fig

    def plot_drawdown(
            self, equity_curve: pd.Series, title: str = "Drawdown", **kwargs
    ) -> Any:
        """Plot drawdown over time."""
        # Calculate drawdown
        running_max = equity_curve.expanding().max()
        drawdown = (equity_curve - running_max) / running_max * 100

        fig = self.make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=("Equity Curve", "Drawdown"),
            row_heights=[0.6, 0.4],
        )

        # Equity curve
        fig.add_trace(
            self.go.Scatter(
                x=equity_curve.index,
                y=equity_curve.values,
                mode="lines",
                name="Equity",
                line=dict(width=2, color="#2E86AB"),
            ),
            row=1,
            col=1,
        )

        # Drawdown
        fig.add_trace(
            self.go.Scatter(
                x=drawdown.index,
                y=drawdown.values,
                mode="lines",
                name="Drawdown",
                fill="tozeroy",
                line=dict(width=0),
                fillcolor="rgba(162, 59, 114, 0.5)",
            ),
            row=2,
            col=1,
        )

        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Value ($)", row=1, col=1)
        fig.update_yaxes(title_text="Drawdown (%)", row=2, col=1)

        fig.update_layout(
            title=title,
            template=self.template,
            hovermode="x unified",
            height=kwargs.get("height", 600),
            showlegend=False,
        )

        return fig

    def plot_multiple_series(
            self, data: Dict[str, pd.Series], title: str = "Multiple Series", **kwargs
    ) -> Any:
        """Plot multiple time series."""
        fig = self.go.Figure()

        for label, series in data.items():
            fig.add_trace(
                self.go.Scatter(
                    x=series.index,
                    y=series.values,
                    mode="lines",
                    name=label,
                    line=dict(width=2),
                    opacity=0.8,
                )
            )

        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title="Value",
            template=self.template,
            hovermode="x unified",
            height=kwargs.get("height", 500),
        )

        return fig

    def save(self, fig: Any, filename: str, **kwargs) -> None:
        """Save figure to file."""
        if filename.endswith(".html"):
            fig.write_html(filename)
        elif filename.endswith(".png"):
            fig.write_image(filename, **kwargs)
        elif filename.endswith(".jpg") or filename.endswith(".jpeg"):
            fig.write_image(filename, **kwargs)
        elif filename.endswith(".svg"):
            fig.write_image(filename, format="svg", **kwargs)
        else:
            # Default to HTML
            fig.write_html(filename + ".html")

        logger.info(f"Saved plot to {filename}")


# ==========================================
# Main Plotter Class
# ==========================================


class Plotter(BaseModel):
    """
    Main plotter class that supports multiple backends.

    Features:
    - Multiple backends: matplotlib, plotly (default)
    - Comprehensive trading visualizations
    - Portfolio and universe analysis
    - Performance metrics plotting
    """

    backend: PlotBackend = Field(
        default=PlotBackend.PLOTLY, description="Plotting backend"
    )
    theme: PlotTheme = Field(default=PlotTheme.DEFAULT, description="Plot theme")
    output_dir: Optional[str] = Field(None, description="Directory for saving plots")

    # Backend instance (not serialized)
    _plotter: Optional[BasePlotter] = None

    model_config = {"arbitrary_types_allowed": True}

    def __init__(self, **data):
        """Initialize plotter with selected backend."""
        super().__init__(**data)
        self._initialize_backend()

        if self.output_dir:
            Path(self.output_dir).mkdir(parents=True, exist_ok=True)

    def _initialize_backend(self) -> None:
        """Initialize the plotting backend."""
        if self.backend == PlotBackend.MATPLOTLIB:
            self._plotter = MatplotlibPlotter(theme=self.theme)
        elif self.backend == PlotBackend.PLOTLY:
            self._plotter = PlotlyPlotter(theme=self.theme)
        else:
            raise ValueError(f"Unknown backend: {self.backend}")

        logger.info(f"Initialized {self.backend} plotter with {self.theme} theme")

    def change_backend(self, backend: PlotBackend) -> None:
        """Change plotting backend."""
        self.backend = backend
        self._initialize_backend()

    def change_theme(self, theme: PlotTheme) -> None:
        """Change plot theme."""
        self.theme = theme
        self._initialize_backend()

    # ==========================================
    # Core Plotting Methods
    # ==========================================

    def plot_price_history(
            self,
            data: Union[pd.DataFrame, Dict[str, pd.DataFrame]],
            title: str = "Price History",
            **kwargs,
    ) -> Any:
        """
        Plot price history for single or multiple tickers.

        Args:
            data: DataFrame with OHLCV data or dict of {ticker: DataFrame}
            title: Plot title
            **kwargs: Additional arguments passed to backend
        """
        if isinstance(data, dict):
            # Multiple tickers - combine close prices
            close_prices = {}
            for ticker, df in data.items():
                if "Close" in df.columns:
                    close_prices[ticker] = df["Close"]

            if close_prices:
                combined_df = pd.DataFrame(close_prices)
                return self._plotter.plot_multiple_series(
                    {ticker: series for ticker, series in combined_df.items()},
                    title=title,
                    **kwargs,
                )
        else:
            return self._plotter.plot_price_history(data, title=title, **kwargs)

    def plot_portfolio_value(
            self, history: pd.DataFrame, title: str = "Portfolio Value Over Time", **kwargs
    ) -> Any:
        """
        Plot portfolio value over time.

        Args:
            history: DataFrame with columns: total_value, cash, positions_value
            title: Plot title
        """
        return self._plotter.plot_portfolio_value(history, title=title, **kwargs)

    def plot_portfolio_composition(
            self,
            portfolio,  # Portfolio object
            title: str = "Portfolio Composition",
            **kwargs,
    ) -> Any:
        """
        Plot portfolio composition.

        Args:
            portfolio: Portfolio object
            title: Plot title
        """
        weights = portfolio.get_position_weights()

        # Add cash as a position
        if portfolio.cash_weight > 0:
            weights["Cash"] = portfolio.cash_weight

        return self._plotter.plot_portfolio_composition(weights, title=title, **kwargs)

    def plot_returns(
            self, returns: pd.Series, title: str = "Returns Analysis", **kwargs
    ) -> Any:
        """
        Plot returns distribution and time series.

        Args:
            returns: Series of returns
            title: Plot title
        """
        return self._plotter.plot_returns(returns, title=title, **kwargs)

    def plot_drawdown(
            self, equity_curve: pd.Series, title: str = "Drawdown Analysis", **kwargs
    ) -> Any:
        """
        Plot equity curve and drawdown.

        Args:
            equity_curve: Series of portfolio values
            title: Plot title
        """
        return self._plotter.plot_drawdown(equity_curve, title=title, **kwargs)

    def plot_multiple_series(
            self, data: Dict[str, pd.Series], title: str = "Comparison", **kwargs
    ) -> Any:
        """
        Plot multiple time series.

        Args:
            data: Dict of {label: Series}
            title: Plot title
        """
        return self._plotter.plot_multiple_series(data, title=title, **kwargs)

    # ==========================================
    # Specialized Trading Plots
    # ==========================================

    def plot_correlation_matrix(
            self, returns: pd.DataFrame, title: str = "Correlation Matrix", **kwargs
    ) -> Any:
        """Plot correlation matrix of returns."""
        corr = returns.corr()

        if self.backend == PlotBackend.PLOTLY:
            fig = self._plotter.go.Figure(
                data=self._plotter.go.Heatmap(
                    z=corr.values,
                    x=corr.columns,
                    y=corr.columns,
                    colorscale="RdBu",
                    zmid=0,
                )
            )
            fig.update_layout(title=title, template=self._plotter.template)
            return fig
        else:
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=(10, 8))
            im = ax.imshow(corr, cmap="RdBu", vmin=-1, vmax=1)
            ax.set_xticks(range(len(corr.columns)))
            ax.set_yticks(range(len(corr.columns)))
            ax.set_xticklabels(corr.columns, rotation=45, ha="right")
            ax.set_yticklabels(corr.columns)
            plt.colorbar(im, ax=ax)
            ax.set_title(title)
            plt.tight_layout()
            return fig

    def plot_performance_summary(
            self, metrics: Dict[str, float], title: str = "Performance Metrics", **kwargs
    ) -> Any:
        """Plot performance metrics as a bar chart."""
        if self.backend == PlotBackend.PLOTLY:
            fig = self._plotter.go.Figure(
                data=[
                    self._plotter.go.Bar(
                        x=list(metrics.keys()),
                        y=list(metrics.values()),
                        marker_color="#2E86AB",
                    )
                ]
            )
            fig.update_layout(
                title=title,
                xaxis_title="Metric",
                yaxis_title="Value",
                template=self._plotter.template,
            )
            return fig
        else:
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=(10, 6))
            ax.bar(metrics.keys(), metrics.values(), color="#2E86AB")
            ax.set_xlabel("Metric")
            ax.set_ylabel("Value")
            ax.set_title(title)
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()
            return fig

    def plot_universe_analysis(
            self,
            universe,  # Universe object
            data_manager,  # DataManager object
            metric: str = "price",
            title: Optional[str] = None,
            **kwargs,
    ) -> Any:
        """
        Plot analysis of universe tickers.

        Args:
            universe: Universe object
            data_manager: DataManager object
            metric: Metric to plot ('price', 'volume', 'volatility')
        """
        if title is None:
            title = f"Universe Analysis - {metric.title()}"

        tickers = universe.get_tickers()
        values = []
        labels = []

        for ticker in tickers:
            df = data_manager.load_data(ticker)
            if not df.empty:
                if metric == "price":
                    values.append(df["Close"].iloc[-1])
                elif metric == "volume":
                    values.append(df["Volume"].mean())
                elif metric == "volatility":
                    returns = df["Close"].pct_change()
                    values.append(returns.std() * 100)
                labels.append(ticker)

        if self.backend == PlotBackend.PLOTLY:
            fig = self._plotter.go.Figure(
                data=[self._plotter.go.Bar(x=labels, y=values, marker_color="#F18F01")]
            )
            fig.update_layout(
                title=title,
                xaxis_title="Ticker",
                yaxis_title=metric.title(),
                template=self._plotter.template,
            )
            return fig
        else:
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=(12, 6))
            ax.bar(labels, values, color="#F18F01")
            ax.set_xlabel("Ticker")
            ax.set_ylabel(metric.title())
            ax.set_title(title)
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()
            return fig

    # ==========================================
    # Utility Methods
    # ==========================================

    def save(self, fig: Any, filename: str, **kwargs) -> None:
        """
        Save figure to file.

        Args:
            fig: Figure object from plotting backend
            filename: Output filename
        """
        if self.output_dir:
            filepath = Path(self.output_dir) / filename
        else:
            filepath = Path(filename)

        self._plotter.save(fig, str(filepath), **kwargs)

    def show(self, fig: Any) -> None:
        """Display figure (backend-dependent)."""
        if self.backend == PlotBackend.MATPLOTLIB:
            self._plotter.plt.show()
        elif self.backend == PlotBackend.PLOTLY:
            fig.show()

    def __repr__(self) -> str:
        """String representation."""
        return f"Plotter(backend={self.backend.value}, theme={self.theme.value})"
