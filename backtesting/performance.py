"""
Performance analysis and reporting for backtests.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, Optional
from pathlib import Path

from utils.calculations import calculate_max_drawdown
from config.settings import Settings
from utils.logger import setup_logger


logger = setup_logger(__name__)


class PerformanceAnalyzer:
    """
    Analyze and visualize backtest performance.

    Provides Carver-style performance analysis and reporting.
    """

    def __init__(self, results: Dict):
        """
        Initialize performance analyzer.

        Args:
            results: Backtest results dictionary
        """
        self.results = results
        logger.info("PerformanceAnalyzer initialized")

    def print_summary(self) -> None:
        """Print summary statistics of backtest performance."""
        print("\n" + "=" * 60)
        print("BACKTEST PERFORMANCE SUMMARY")
        print("=" * 60)

        # Basic metrics
        print(f"\nPeriod: {self.results['start_date']} to {self.results['end_date']}")
        print(f"Initial Capital: ${Settings.INITIAL_CAPITAL:,.2f}")
        print(f"Final Equity: ${self.results['final_equity']:,.2f}")
        print(f"\nTotal Return: {self.results['total_return']:.2%}")
        print(f"Annualized Return: {self.results['annualized_return']:.2%}")
        print(f"Annualized Volatility: {self.results['annualized_volatility']:.2%}")
        print(f"Sharpe Ratio: {self.results['sharpe_ratio']:.2f}")

        # Trading statistics
        print(f"\nTotal Trades: {self.results['total_trades']}")
        print(f"Total Costs: ${self.results['total_costs']:,.2f}")

        # Drawdown analysis
        if 'equity_curve' in self.results:
            dd_stats = calculate_max_drawdown(self.results['equity_curve'])
            print(f"\nMaximum Drawdown: {dd_stats['max_drawdown']:.2%}")
            print(f"Peak Date: {dd_stats['peak_date']}")
            print(f"Trough Date: {dd_stats['trough_date']}")

        print("=" * 60 + "\n")

    def plot_equity_curve(
        self,
        save_path: Optional[Path] = None,
        show: bool = True
    ) -> None:
        """
        Plot equity curve.

        Args:
            save_path: Path to save figure
            show: If True, display the plot
        """
        if 'equity_curve' not in self.results:
            logger.warning("No equity curve in results")
            return

        equity = self.results['equity_curve']

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

        # Equity curve
        ax1.plot(equity.index, equity.values, label='Strategy Equity', linewidth=2)
        ax1.axhline(y=Settings.INITIAL_CAPITAL, color='r', linestyle='--',
                    label='Initial Capital', alpha=0.7)
        ax1.set_title('Equity Curve', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Equity ($)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Drawdown
        running_max = equity.expanding().max()
        drawdown = (equity - running_max) / running_max

        ax2.fill_between(drawdown.index, drawdown.values, 0,
                         alpha=0.3, color='red', label='Drawdown')
        ax2.set_title('Drawdown', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Date')
        ax2.set_ylabel('Drawdown (%)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Saved equity curve plot to {save_path}")

        if show:
            plt.show()
        else:
            plt.close()

    def plot_positions(
        self,
        save_path: Optional[Path] = None,
        show: bool = True
    ) -> None:
        """
        Plot positions over time.

        Args:
            save_path: Path to save figure
            show: If True, display the plot
        """
        if 'positions' not in self.results or 'signals' not in self.results:
            logger.warning("No positions or signals in results")
            return

        positions = self.results['positions']
        signals = self.results['signals']

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

        # Signals
        ax1.plot(signals.index, signals.values, label='Trading Signal', linewidth=1.5)
        ax1.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax1.set_title('Trading Signals', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Signal Strength')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Positions
        ax2.plot(positions.index, positions.values, label='Position Size',
                linewidth=1.5, color='green')
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax2.set_title('Position Sizes', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Date')
        ax2.set_ylabel('Shares')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Saved positions plot to {save_path}")

        if show:
            plt.show()
        else:
            plt.close()

    def generate_report(self, output_dir: Optional[Path] = None) -> None:
        """
        Generate comprehensive performance report.

        Args:
            output_dir: Directory to save reports
        """
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            # Save plots
            self.plot_equity_curve(
                save_path=output_dir / 'equity_curve.png',
                show=False
            )
            self.plot_positions(
                save_path=output_dir / 'positions.png',
                show=False
            )

            logger.info(f"Performance report saved to {output_dir}")

        # Print summary
        self.print_summary()
