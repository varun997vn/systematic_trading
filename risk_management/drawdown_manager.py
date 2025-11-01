"""
Drawdown management and risk controls for systematic trading.

Implements various drawdown monitoring and protection mechanisms.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from datetime import datetime

from config.settings import Settings
from utils.logger import setup_logger


logger = setup_logger(__name__)


class DrawdownManager:
    """
    Manage drawdowns and implement protective mechanisms.

    Carver emphasizes the importance of managing drawdowns to preserve capital
    and maintain psychological discipline.
    """

    def __init__(
        self,
        max_drawdown_threshold: float = 0.20,  # 20%
        stop_trading_threshold: float = 0.30,  # 30%
        scale_down_threshold: float = 0.15,    # 15%
    ):
        """
        Initialize drawdown manager.

        Args:
            max_drawdown_threshold: Warning threshold for drawdown
            stop_trading_threshold: Stop trading if drawdown exceeds this
            scale_down_threshold: Scale down positions if drawdown exceeds this
        """
        self.max_drawdown_threshold = max_drawdown_threshold
        self.stop_trading_threshold = stop_trading_threshold
        self.scale_down_threshold = scale_down_threshold

        logger.info(
            f"DrawdownManager initialized: "
            f"warn={max_drawdown_threshold:.1%}, "
            f"stop={stop_trading_threshold:.1%}, "
            f"scale={scale_down_threshold:.1%}"
        )

    def calculate_drawdown(
        self,
        equity_curve: pd.Series
    ) -> pd.Series:
        """
        Calculate drawdown series from equity curve.

        Args:
            equity_curve: Series of portfolio equity values

        Returns:
            Series of drawdown values (as decimals, e.g., 0.15 for 15% drawdown)
        """
        # Calculate running maximum
        running_max = equity_curve.expanding().max()

        # Calculate drawdown
        drawdown = (equity_curve - running_max) / running_max

        return drawdown

    def calculate_max_drawdown(
        self,
        equity_curve: pd.Series
    ) -> float:
        """
        Calculate maximum drawdown.

        Args:
            equity_curve: Series of portfolio equity values

        Returns:
            Maximum drawdown as decimal (e.g., 0.20 for 20%)
        """
        drawdown = self.calculate_drawdown(equity_curve)
        max_dd = drawdown.min()

        logger.debug(f"Maximum drawdown: {max_dd:.2%}")

        return max_dd

    def calculate_drawdown_duration(
        self,
        equity_curve: pd.Series
    ) -> Dict:
        """
        Calculate drawdown duration statistics.

        Args:
            equity_curve: Series of portfolio equity values

        Returns:
            Dictionary with drawdown duration statistics
        """
        drawdown = self.calculate_drawdown(equity_curve)

        # Identify drawdown periods (when not at peak)
        in_drawdown = drawdown < 0

        # Calculate duration of current drawdown
        if in_drawdown.iloc[-1]:
            # Find last peak
            current_idx = len(equity_curve) - 1
            last_peak_idx = equity_curve[:current_idx].idxmax()

            if isinstance(equity_curve.index, pd.DatetimeIndex):
                current_duration = (equity_curve.index[-1] - last_peak_idx).days
            else:
                current_duration = current_idx - equity_curve.index.get_loc(last_peak_idx)
        else:
            current_duration = 0

        # Find all drawdown periods
        drawdown_starts = in_drawdown & ~in_drawdown.shift(1, fill_value=False)
        drawdown_ends = ~in_drawdown & in_drawdown.shift(1, fill_value=False)

        durations = []
        start_indices = drawdown_starts[drawdown_starts].index

        for start_idx in start_indices:
            # Find corresponding end
            future_ends = drawdown_ends[drawdown_ends.index > start_idx]
            if len(future_ends) > 0:
                end_idx = future_ends.index[0]
                if isinstance(equity_curve.index, pd.DatetimeIndex):
                    duration = (end_idx - start_idx).days
                else:
                    duration = equity_curve.index.get_loc(end_idx) - equity_curve.index.get_loc(start_idx)
                durations.append(duration)

        avg_duration = np.mean(durations) if durations else 0
        max_duration = max(durations) if durations else 0

        results = {
            'current_drawdown_duration': current_duration,
            'average_drawdown_duration': avg_duration,
            'max_drawdown_duration': max_duration,
            'number_of_drawdowns': len(durations),
        }

        logger.debug(
            f"Drawdown durations: current={current_duration}, "
            f"avg={avg_duration:.0f}, max={max_duration:.0f}"
        )

        return results

    def check_risk_limits(
        self,
        equity_curve: pd.Series
    ) -> Dict:
        """
        Check if current drawdown exceeds risk limits.

        Args:
            equity_curve: Series of portfolio equity values

        Returns:
            Dictionary with risk status and recommended actions
        """
        current_equity = equity_curve.iloc[-1]
        peak_equity = equity_curve.max()
        current_drawdown = (current_equity - peak_equity) / peak_equity

        # Determine status and actions
        status = 'normal'
        action = 'none'
        scale_factor = 1.0

        if current_drawdown < -self.stop_trading_threshold:
            status = 'critical'
            action = 'stop_trading'
            scale_factor = 0.0
            logger.warning(
                f"CRITICAL: Drawdown {current_drawdown:.2%} exceeds stop threshold "
                f"{self.stop_trading_threshold:.2%}"
            )
        elif current_drawdown < -self.scale_down_threshold:
            status = 'warning'
            action = 'scale_down'
            # Scale positions proportionally to drawdown severity
            excess_dd = abs(current_drawdown) - self.scale_down_threshold
            max_scale_down = self.stop_trading_threshold - self.scale_down_threshold
            scale_factor = max(0.5, 1.0 - (excess_dd / max_scale_down) * 0.5)
            logger.warning(
                f"WARNING: Drawdown {current_drawdown:.2%} exceeds scale-down threshold "
                f"{self.scale_down_threshold:.2%}. Scaling to {scale_factor:.1%}"
            )
        elif current_drawdown < -self.max_drawdown_threshold:
            status = 'caution'
            action = 'monitor'
            logger.info(
                f"CAUTION: Drawdown {current_drawdown:.2%} exceeds warning threshold "
                f"{self.max_drawdown_threshold:.2%}"
            )

        return {
            'current_drawdown': current_drawdown,
            'status': status,
            'action': action,
            'position_scale_factor': scale_factor,
            'peak_equity': peak_equity,
            'current_equity': current_equity,
        }

    def calculate_calmar_ratio(
        self,
        equity_curve: pd.Series,
        periods_per_year: int = 252
    ) -> float:
        """
        Calculate Calmar ratio (return / max drawdown).

        Higher values indicate better risk-adjusted returns.

        Args:
            equity_curve: Series of portfolio equity values
            periods_per_year: Number of periods per year

        Returns:
            Calmar ratio
        """
        # Calculate annualized return
        total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1
        years = len(equity_curve) / periods_per_year
        annual_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0

        # Calculate max drawdown
        max_dd = abs(self.calculate_max_drawdown(equity_curve))

        # Calmar ratio
        calmar = annual_return / max_dd if max_dd > 0 else 0

        logger.debug(
            f"Calmar ratio: {calmar:.2f} "
            f"(return={annual_return:.2%}, max_dd={max_dd:.2%})"
        )

        return calmar

    def calculate_ulcer_index(
        self,
        equity_curve: pd.Series
    ) -> float:
        """
        Calculate Ulcer Index (measure of downside volatility).

        Lower values indicate less severe drawdowns.

        Args:
            equity_curve: Series of portfolio equity values

        Returns:
            Ulcer Index
        """
        drawdown = self.calculate_drawdown(equity_curve)

        # Square the drawdowns and calculate RMS
        squared_dd = drawdown ** 2
        ulcer_index = np.sqrt(squared_dd.mean())

        logger.debug(f"Ulcer Index: {ulcer_index:.4f}")

        return ulcer_index

    def get_drawdown_summary(
        self,
        equity_curve: pd.Series
    ) -> Dict:
        """
        Get comprehensive drawdown summary.

        Args:
            equity_curve: Series of portfolio equity values

        Returns:
            Dictionary with all drawdown metrics
        """
        drawdown_series = self.calculate_drawdown(equity_curve)
        max_dd = drawdown_series.min()
        duration_stats = self.calculate_drawdown_duration(equity_curve)
        risk_status = self.check_risk_limits(equity_curve)
        calmar = self.calculate_calmar_ratio(equity_curve)
        ulcer = self.calculate_ulcer_index(equity_curve)

        summary = {
            'max_drawdown': max_dd,
            'current_drawdown': drawdown_series.iloc[-1],
            'calmar_ratio': calmar,
            'ulcer_index': ulcer,
            **duration_stats,
            **risk_status,
        }

        return summary
