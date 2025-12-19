"""
Data Management Module for Systematic Trading Framework
Based on Robert Carver's "Systematic Trading"

Core responsibilities:
- PriceData structure (OHLCV)
- DataLoader (load market data)
- DataValidator (check completeness)
- ReturnCalculator (compute returns)
"""

import plotly.graph_objects as go

from st.dto.data import PriceDataDTO, ReturnsDTO, CorrelationDTO
from utils.logger import setup_logger

logger = setup_logger(__name__)


class PriceData(PriceDataDTO):
    pass


class ReturnData(ReturnsDTO):
    pass


class CorrelationData(CorrelationDTO):
    def plot(self, title: str = "CorrelationMatrix", height: int = 300, width: int = 400):

        """
        Plot correlation matrix heatmap with color-coded absolute values using Plotly.

        Highlights:
        - Red: |correlation| > 0.5
        - Yellow: |correlation| > 0.3
        - White/neutral: |correlation| <= 0.3

        Args:
            title: Custom title for the plot (optional)
            height: Height of the plot (optional)
            width: Width of the plot (optional)

        Returns:
            plotly.graph_objects.Figure
        """

        if self.correlation_matrix is None:
            raise ValueError("Correlation matrix not calculated yet")

        # Get labels
        labels = list(self.correlation_matrix.columns)

        # Create custom colorscale based on absolute values
        # We'll use a diverging colorscale but overlay markers for high values
        z = self.correlation_matrix.values

        # Create annotations with color coding
        annotations = []
        for i, row in enumerate(labels):
            for j, col in enumerate(labels):
                corr_val = z[i, j]
                abs_corr = abs(corr_val)

                # Determine text color based on correlation strength
                if abs_corr > 0.5:
                    font_color = 'red'
                    font_weight = 'bold'
                elif abs_corr > 0.3:
                    font_color = 'orange'
                    font_weight = 'bold'
                else:
                    font_color = 'black'
                    font_weight = 'normal'

                annotations.append(
                    dict(
                        x=j,
                        y=i,
                        text=f'{corr_val:.2f}',
                        showarrow=False,
                        font=dict(
                            color=font_color,
                            size=10,
                            family='Arial Black' if font_weight == 'bold' else 'Arial'
                        )
                    )
                )

        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=z,
            x=labels,
            y=labels,
            colorscale='RdBu_r',  # Red-white-blue reversed
            zmid=0,
            zmin=-1,
            zmax=1,
            colorbar=dict(title="Correlation"),
            hovertemplate='%{y} vs %{x}<br>Correlation: %{z:.3f}<extra></extra>'
        ))

        # Add annotations
        fig.update_layout(
            annotations=annotations,
            title=title,
            xaxis=dict(title='Ticker', side='bottom'),
            yaxis=dict(title='Ticker', autorange='reversed'),
            width=width,
            height=height,
            font=dict(size=11)
        )

        return fig
