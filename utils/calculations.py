"""
Financial calculations and metrics for systematic trading.
Based on Robert Carver's methods.
"""

import numpy as np
import pandas as pd
from typing import Union

from config.settings import Settings


def calculate_returns(
    prices: Union[pd.Series, pd.DataFrame],
    method: str = 'log'
) -> Union[pd.Series, pd.DataFrame]:
    """
    Calculate returns from price series.

    Carver typically uses log returns for their mathematical properties,
    but simple returns are also supported.

    Args:
        prices: Price series or DataFrame
        method: 'log' for log returns, 'simple' for simple returns

    Returns:
        Returns series or DataFrame
    """
    if method == 'log':
        return np.log(prices / prices.shift(1))
    elif method == 'simple':
        return prices.pct_change()
    else:
        raise ValueError(f"Unknown method: {method}. Use 'log' or 'simple'")


def calculate_volatility(
    returns: Union[pd.Series, pd.DataFrame],
    window: int = 25,
    annualize: bool = True,
) -> Union[pd.Series, pd.DataFrame]:
    """
    Calculate rolling volatility (standard deviation of returns).

    Carver uses exponentially weighted volatility in production, but
    rolling window is simpler for initial implementation.

    Args:
        returns: Returns series or DataFrame
        window: Rolling window size (Carver often uses 25 days)
        annualize: If True, annualize the volatility

    Returns:
        Volatility series or DataFrame
    """
    vol = returns.rolling(window=window).std()

    if annualize:
        vol = vol * np.sqrt(Settings.BUSINESS_DAYS_PER_YEAR)

    return vol


def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = None,
    annualize: bool = True,
) -> float:
    """
    Calculate Sharpe ratio.

    Carver emphasizes this as a key performance metric.

    Args:
        returns: Returns series
        risk_free_rate: Annual risk-free rate (uses Settings if None)
        annualize: If True, annualize the Sharpe ratio

    Returns:
        Sharpe ratio
    """
    if risk_free_rate is None:
        risk_free_rate = Settings.RISK_FREE_RATE

    excess_returns = returns - (risk_free_rate / Settings.BUSINESS_DAYS_PER_YEAR)
    mean_excess = excess_returns.mean()
    std_excess = excess_returns.std()

    if std_excess == 0:
        return 0.0

    sharpe = mean_excess / std_excess

    if annualize:
        sharpe = sharpe * np.sqrt(Settings.BUSINESS_DAYS_PER_YEAR)

    return sharpe


def calculate_max_drawdown(equity_curve: pd.Series) -> dict:
    """
    Calculate maximum drawdown and related metrics.

    Args:
        equity_curve: Cumulative equity curve

    Returns:
        Dictionary with max_drawdown, peak, trough, and duration
    """
    # Calculate running maximum
    running_max = equity_curve.expanding().max()

    # Calculate drawdown series
    drawdown = (equity_curve - running_max) / running_max

    # Find maximum drawdown
    max_dd = drawdown.min()

    # Find the peak and trough
    trough_idx = drawdown.idxmin()
    peak_idx = equity_curve[:trough_idx].idxmax()

    # Calculate duration
    duration = (trough_idx - peak_idx).days if hasattr(trough_idx, 'days') else 0

    return {
        'max_drawdown': max_dd,
        'peak_date': peak_idx,
        'trough_date': trough_idx,
        'duration_days': duration,
    }


def exponential_weights(window: int, min_periods: int = None) -> np.ndarray:
    """
    Generate exponential weights for EWMA calculations.

    Carver uses EWMA extensively for smoother estimates.

    Args:
        window: Span for exponential weighting
        min_periods: Minimum periods required

    Returns:
        Array of exponential weights
    """
    alpha = 2 / (window + 1)
    weights = (1 - alpha) ** np.arange(window)
    return weights[::-1] / weights.sum()
