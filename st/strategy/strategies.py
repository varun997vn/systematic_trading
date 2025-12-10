"""
Five Trading Strategies with -20 to 20 Signal Scale
"""

import polars as pl
import numpy as np
from .base import Strategy


class RSIMomentumStrategy(Strategy):
    """
    RSI-based momentum strategy
    - RSI < 30: Oversold (buy signal)
    - RSI > 70: Overbought (sell signal)
    - Combines RSI with price momentum
    """

    def __init__(self, rsi_period: int = 14, rsi_oversold: int = 30, rsi_overbought: int = 70):
        super().__init__(
            name="RSI Momentum",
            parameters={
                "rsi_period": rsi_period,
                "rsi_oversold": rsi_oversold,
                "rsi_overbought": rsi_overbought
            }
        )

    def add_indicators(self, df: pl.DataFrame) -> pl.DataFrame:
        """Calculate RSI and momentum indicators"""
        period = self.parameters["rsi_period"]

        # Calculate price changes
        df = df.with_columns([
            (pl.col("close") - pl.col("close").shift(1)).alias("price_change")
        ])

        # Calculate gains and losses
        df = df.with_columns([
            pl.when(pl.col("price_change") > 0)
            .then(pl.col("price_change"))
            .otherwise(0)
            .alias("gain"),
            pl.when(pl.col("price_change") < 0)
            .then(pl.col("price_change").abs())
            .otherwise(0)
            .alias("loss")
        ])

        # Calculate average gains and losses
        df = df.with_columns([
            pl.col("gain").rolling_mean(window_size=period).alias("avg_gain"),
            pl.col("loss").rolling_mean(window_size=period).alias("avg_loss")
        ])

        # Calculate RSI
        df = df.with_columns([
            (100 - (100 / (1 + pl.col("avg_gain") / pl.col("avg_loss"))))
            .fill_null(50)
            .alias("rsi")
        ])

        # Add momentum (rate of change)
        df = df.with_columns([
            ((pl.col("close") / pl.col("close").shift(period) - 1) * 100)
            .alias("momentum")
        ])

        return df

    def calculate_signal(self, df: pl.DataFrame, index: int) -> int:
        """Generate signal based on RSI and momentum"""
        if index < self.parameters["rsi_period"]:
            return 0

        row = df[index]
        rsi = row["rsi"][0]
        momentum = row["momentum"][0] if row["momentum"][0] is not None else 0

        # Base signal from RSI
        if rsi < 20:
            signal = 20  # Very strong buy
        elif rsi < 30:
            signal = 15  # Strong buy
        elif rsi < 40:
            signal = 10  # Good buy
        elif rsi < 50:
            signal = 5  # Weak buy
        elif rsi > 80:
            signal = -20  # Very strong sell
        elif rsi > 70:
            signal = -15  # Strong sell
        elif rsi > 60:
            signal = -10  # Good sell
        elif rsi > 50:
            signal = -5  # Weak sell
        else:
            signal = 0

        # Adjust based on momentum
        if momentum > 5 and signal > 0:
            signal = min(20, signal + 5)  # Boost buy signals
        elif momentum < -5 and signal < 0:
            signal = max(-20, signal - 5)  # Boost sell signals

        return self.validate_signal(signal)


class MovingAverageCrossoverStrategy(Strategy):
    """
    Dual Moving Average Crossover Strategy
    - Fast MA crosses above Slow MA: Buy signal
    - Fast MA crosses below Slow MA: Sell signal
    - Signal strength based on distance between MAs
    """

    def __init__(self, fast_period: int = 10, slow_period: int = 30):
        super().__init__(
            name="MA Crossover",
            parameters={
                "fast_period": fast_period,
                "slow_period": slow_period
            }
        )

    def add_indicators(self, df: pl.DataFrame) -> pl.DataFrame:
        """Calculate moving averages"""
        fast = self.parameters["fast_period"]
        slow = self.parameters["slow_period"]

        df = df.with_columns([
            pl.col("close").rolling_mean(window_size=fast).alias("ma_fast"),
            pl.col("close").rolling_mean(window_size=slow).alias("ma_slow")
        ])

        # Calculate distance between MAs as percentage
        df = df.with_columns([
            ((pl.col("ma_fast") - pl.col("ma_slow")) / pl.col("ma_slow") * 100)
            .alias("ma_distance_pct")
        ])

        # Detect crossovers
        df = df.with_columns([
            (pl.col("ma_fast") > pl.col("ma_slow")).alias("fast_above_slow")
        ])

        df = df.with_columns([
            (pl.col("fast_above_slow") != pl.col("fast_above_slow").shift(1))
            .alias("crossover")
        ])

        return df

    def calculate_signal(self, df: pl.DataFrame, index: int) -> int:
        """Generate signal based on MA position and crossovers"""
        if index < self.parameters["slow_period"]:
            return 0

        row = df[index]
        prev_row = df[index - 1] if index > 0 else row

        fast_above = row["fast_above_slow"][0]
        prev_fast_above = prev_row["fast_above_slow"][0]
        distance = row["ma_distance_pct"][0] if row["ma_distance_pct"][0] is not None else 0

        # Detect crossover
        crossover = fast_above != prev_fast_above

        if fast_above:
            # Fast MA above slow MA - bullish
            if crossover:
                signal = 15  # Strong buy on fresh crossover
            elif distance > 3:
                signal = 20  # Very strong buy - large separation
            elif distance > 2:
                signal = 15  # Strong buy
            elif distance > 1:
                signal = 10  # Good buy
            else:
                signal = 5  # Weak buy
        else:
            # Fast MA below slow MA - bearish
            if crossover:
                signal = -15  # Strong sell on fresh crossover
            elif distance < -3:
                signal = -20  # Very strong sell
            elif distance < -2:
                signal = -15  # Strong sell
            elif distance < -1:
                signal = -10  # Good sell
            else:
                signal = -5  # Weak sell

        return self.validate_signal(signal)


class BollingerBandStrategy(Strategy):
    """
    Bollinger Band Mean Reversion Strategy
    - Price near lower band: Oversold (buy signal)
    - Price near upper band: Overbought (sell signal)
    - Signal strength based on distance from bands
    """

    def __init__(self, period: int = 20, std_dev: float = 2.0):
        super().__init__(
            name="Bollinger Bands",
            parameters={
                "period": period,
                "std_dev": std_dev
            }
        )

    def add_indicators(self, df: pl.DataFrame) -> pl.DataFrame:
        """Calculate Bollinger Bands"""
        period = self.parameters["period"]
        std_dev = self.parameters["std_dev"]

        df = df.with_columns([
            pl.col("close").rolling_mean(window_size=period).alias("bb_middle"),
            pl.col("close").rolling_std(window_size=period).alias("bb_std")
        ])

        df = df.with_columns([
            (pl.col("bb_middle") + std_dev * pl.col("bb_std")).alias("bb_upper"),
            (pl.col("bb_middle") - std_dev * pl.col("bb_std")).alias("bb_lower")
        ])

        # Calculate position within bands (0 = lower band, 1 = upper band)
        df = df.with_columns([
            ((pl.col("close") - pl.col("bb_lower")) /
             (pl.col("bb_upper") - pl.col("bb_lower")))
            .fill_null(0.5)
            .alias("bb_position")
        ])

        # Band width as percentage
        df = df.with_columns([
            ((pl.col("bb_upper") - pl.col("bb_lower")) / pl.col("bb_middle") * 100)
            .alias("bb_width_pct")
        ])

        return df

    def calculate_signal(self, df: pl.DataFrame, index: int) -> int:
        """Generate signal based on position within Bollinger Bands"""
        if index < self.parameters["period"]:
            return 0

        row = df[index]
        bb_pos = row["bb_position"][0]
        bb_width = row["bb_width_pct"][0] if row["bb_width_pct"][0] is not None else 0

        # Adjust signal strength based on band width (volatility)
        volatility_multiplier = min(1.5, max(0.5, bb_width / 5))

        if bb_pos < 0.1:
            signal = int(20 * volatility_multiplier)  # Very strong buy - at/below lower band
        elif bb_pos < 0.2:
            signal = int(15 * volatility_multiplier)  # Strong buy
        elif bb_pos < 0.3:
            signal = int(10 * volatility_multiplier)  # Good buy
        elif bb_pos < 0.45:
            signal = int(5 * volatility_multiplier)  # Weak buy
        elif bb_pos > 0.9:
            signal = int(-20 * volatility_multiplier)  # Very strong sell - at/above upper band
        elif bb_pos > 0.8:
            signal = int(-15 * volatility_multiplier)  # Strong sell
        elif bb_pos > 0.7:
            signal = int(-10 * volatility_multiplier)  # Good sell
        elif bb_pos > 0.55:
            signal = int(-5 * volatility_multiplier)  # Weak sell
        else:
            signal = 0  # Neutral - middle of bands

        return self.validate_signal(signal)


class MACDStrategy(Strategy):
    """
    MACD (Moving Average Convergence Divergence) Strategy
    - MACD crosses above signal line: Buy
    - MACD crosses below signal line: Sell
    - Signal strength based on histogram and trend
    """

    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        super().__init__(
            name="MACD",
            parameters={
                "fast_period": fast_period,
                "slow_period": slow_period,
                "signal_period": signal_period
            }
        )

    def add_indicators(self, df: pl.DataFrame) -> pl.DataFrame:
        """Calculate MACD indicators"""
        fast = self.parameters["fast_period"]
        slow = self.parameters["slow_period"]
        signal = self.parameters["signal_period"]

        # Calculate EMAs
        df = df.with_columns([
            pl.col("close").ewm_mean(span=fast).alias("ema_fast"),
            pl.col("close").ewm_mean(span=slow).alias("ema_slow")
        ])

        # Calculate MACD line
        df = df.with_columns([
            (pl.col("ema_fast") - pl.col("ema_slow")).alias("macd")
        ])

        # Calculate signal line
        df = df.with_columns([
            pl.col("macd").ewm_mean(span=signal).alias("macd_signal")
        ])

        # Calculate histogram
        df = df.with_columns([
            (pl.col("macd") - pl.col("macd_signal")).alias("macd_histogram")
        ])

        # Detect crossovers
        df = df.with_columns([
            (pl.col("macd") > pl.col("macd_signal")).alias("macd_bullish")
        ])

        return df

    def calculate_signal(self, df: pl.DataFrame, index: int) -> int:
        """Generate signal based on MACD"""
        if index < self.parameters["slow_period"] + self.parameters["signal_period"]:
            return 0

        row = df[index]
        prev_row = df[index - 1] if index > 0 else row

        macd = row["macd"][0] if row["macd"][0] is not None else 0
        signal_line = row["macd_signal"][0] if row["macd_signal"][0] is not None else 0
        histogram = row["macd_histogram"][0] if row["macd_histogram"][0] is not None else 0

        bullish = row["macd_bullish"][0]
        prev_bullish = prev_row["macd_bullish"][0]

        # Detect crossover
        crossover = bullish != prev_bullish

        # Normalize histogram to get signal strength
        hist_strength = abs(histogram) * 100  # Scale factor

        if bullish:
            # MACD above signal line - bullish
            if crossover:
                signal = 15  # Strong buy on fresh crossover
            elif histogram > 0.5:
                signal = 20  # Very strong buy - strong momentum
            elif histogram > 0.2:
                signal = 15  # Strong buy
            elif histogram > 0.05:
                signal = 10  # Good buy
            else:
                signal = 5  # Weak buy
        else:
            # MACD below signal line - bearish
            if crossover:
                signal = -15  # Strong sell on fresh crossover
            elif histogram < -0.5:
                signal = -20  # Very strong sell
            elif histogram < -0.2:
                signal = -15  # Strong sell
            elif histogram < -0.05:
                signal = -10  # Good sell
            else:
                signal = -5  # Weak sell

        return self.validate_signal(signal)


class VolumeWeightedStrategy(Strategy):
    """
    Volume-Weighted Price Momentum Strategy
    - Combines price momentum with volume analysis
    - High volume + price increase: Strong buy
    - High volume + price decrease: Strong sell
    """

    def __init__(self, period: int = 20):
        super().__init__(
            name="Volume Weighted",
            parameters={
                "period": period
            }
        )

    def add_indicators(self, df: pl.DataFrame) -> pl.DataFrame:
        """Calculate volume-weighted indicators"""
        period = self.parameters["period"]

        # Calculate average volume
        df = df.with_columns([
            pl.col("volume").rolling_mean(window_size=period).alias("avg_volume")
        ])

        # Volume ratio
        df = df.with_columns([
            (pl.col("volume") / pl.col("avg_volume")).alias("volume_ratio")
        ])

        # Price change
        df = df.with_columns([
            ((pl.col("close") - pl.col("close").shift(1)) / pl.col("close").shift(1) * 100)
            .alias("price_change_pct")
        ])

        # Price momentum over period
        df = df.with_columns([
            ((pl.col("close") - pl.col("close").shift(period)) / pl.col("close").shift(period) * 100)
            .alias("price_momentum_pct")
        ])

        # VWAP (Volume Weighted Average Price)
        df = df.with_columns([
            (pl.col("close") * pl.col("volume")).alias("price_volume")
        ])

        df = df.with_columns([
            (pl.col("price_volume").rolling_sum(window_size=period) /
             pl.col("volume").rolling_sum(window_size=period))
            .alias("vwap")
        ])

        # Distance from VWAP
        df = df.with_columns([
            ((pl.col("close") - pl.col("vwap")) / pl.col("vwap") * 100)
            .alias("vwap_distance_pct")
        ])

        return df

    def calculate_signal(self, df: pl.DataFrame, index: int) -> int:
        """Generate signal based on volume-weighted price action"""
        if index < self.parameters["period"]:
            return 0

        row = df[index]

        volume_ratio = row["volume_ratio"][0] if row["volume_ratio"][0] is not None else 1.0
        price_change = row["price_change_pct"][0] if row["price_change_pct"][0] is not None else 0
        momentum = row["price_momentum_pct"][0] if row["price_momentum_pct"][0] is not None else 0
        vwap_dist = row["vwap_distance_pct"][0] if row["vwap_distance_pct"][0] is not None else 0

        # Base signal from momentum
        if momentum > 10:
            base_signal = 15
        elif momentum > 5:
            base_signal = 10
        elif momentum > 2:
            base_signal = 5
        elif momentum < -10:
            base_signal = -15
        elif momentum < -5:
            base_signal = -10
        elif momentum < -2:
            base_signal = -5
        else:
            base_signal = 0

        # Adjust based on volume (high volume confirms the move)
        if volume_ratio > 2.0:
            volume_adj = 1.5
        elif volume_ratio > 1.5:
            volume_adj = 1.3
        elif volume_ratio > 1.0:
            volume_adj = 1.1
        elif volume_ratio < 0.5:
            volume_adj = 0.7  # Low volume weakens signal
        else:
            volume_adj = 1.0

        # Adjust based on VWAP (price above VWAP is bullish)
        if vwap_dist > 2:
            vwap_adj = 1.2
        elif vwap_dist < -2:
            vwap_adj = 0.8
        else:
            vwap_adj = 1.0

        signal = int(base_signal * volume_adj * vwap_adj)

        return self.validate_signal(signal)