"""
Trader Class - Main Trading System
Loads data, applies strategies, generates signals
"""

import polars as pl
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from st.strategy import Strategy


class Trader:
    """
    Main trading class that:
    1. Loads OHLCV data from CSV
    2. Applies multiple strategies
    3. Generates consolidated buy/sell signals (-20 to 20)
    """

    def __init__(self, strategies: List[Strategy] = None):
        """
        Initialize Trader with strategies

        Args:
            strategies: List of Strategy objects to apply
        """
        self.strategies = strategies or []
        self.data: Optional[pl.DataFrame] = None
        self.signals: Optional[pl.DataFrame] = None

    def load_data(self, csv_path: str) -> pl.DataFrame:
        """
        Load OHLCV data from CSV using Polars

        Expected CSV format: date, open, high, low, close, volume

        Args:
            csv_path: Path to CSV file

        Returns:
            DataFrame with loaded data
        """
        # Load CSV with Polars
        df = pl.read_csv(csv_path)

        # Standardize column names (lowercase)
        df = df.rename({col: col.lower() for col in df.columns})

        # Parse date column (try multiple formats)
        try:
            df = df.with_columns([
                pl.col("date").str.strptime(pl.Date, format="%Y-%m-%d").alias("date")
            ])
        except:
            try:
                df = df.with_columns([
                    pl.col("date").str.strptime(pl.Date, format="%m/%d/%Y").alias("date")
                ])
            except:
                # If date is already datetime, keep as is
                pass

        # Sort by date
        df = df.sort("date")

        # Store data
        self.data = df

        print(f"✓ Loaded {len(df)} rows of data from {csv_path}")
        print(f"  Date range: {df['date'][0]} to {df['date'][-1]}")
        print(f"  Columns: {df.columns}")

        return df

    def add_strategy(self, strategy: Strategy):
        """Add a strategy to the trader"""
        self.strategies.append(strategy)
        print(f"✓ Added strategy: {strategy.name}")

    def prepare_data(self) -> pl.DataFrame:
        """
        Prepare data by adding all indicators from all strategies

        Returns:
            DataFrame with all indicators added
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")

        df = self.data.clone()

        print("\nPreparing data with indicators...")
        for strategy in self.strategies:
            print(f"  - Adding indicators for: {strategy.name}")
            df = strategy.add_indicators(df)

        print(f"✓ Data prepared with {len(df.columns)} columns")
        return df

    def generate_signals(self, mode: str = "aggregate") -> pl.DataFrame:
        """
        Generate trading signals using all strategies

        Args:
            mode: "aggregate" (average all), "max" (strongest), "consensus" (majority)

        Returns:
            DataFrame with signals for each strategy and final signal
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")

        if not self.strategies:
            raise ValueError("No strategies added. Add strategies first.")

        # Prepare data with all indicators
        df = self.prepare_data()

        print(f"\nGenerating signals using {len(self.strategies)} strategies...")
        print(f"Signal aggregation mode: {mode}")

        # Create signals dataframe
        signals = pl.DataFrame({
            "date": df["date"],
            "close": df["close"]
        })

        # Generate signals for each strategy
        for strategy in self.strategies:
            strategy_signals = []

            for i in range(len(df)):
                signal = strategy.calculate_signal(df, i)
                strategy_signals.append(signal)

            # Add strategy signals to dataframe
            column_name = f"signal_{strategy.name.lower().replace(' ', '_')}"
            signals = signals.with_columns([
                pl.Series(name=column_name, values=strategy_signals)
            ])

            print(f"  ✓ {strategy.name}: {len([s for s in strategy_signals if s != 0])} non-zero signals")

        # Calculate final signal based on mode
        strategy_columns = [col for col in signals.columns if col.startswith("signal_")]

        if mode == "aggregate":
            # Average of all strategy signals
            signals = signals.with_columns([
                pl.concat_list(strategy_columns)
                .list.mean()
                .round()
                .cast(pl.Int32)
                .alias("final_signal")
            ])

        elif mode == "max":
            # Take strongest signal (furthest from 0)
            signals = signals.with_columns([
                pl.concat_list(strategy_columns)
                .list.eval(pl.element().abs().arg_max())
                .list.first()
                .alias("max_idx")
            ])

            # Get the actual signal at max index
            for i, col in enumerate(strategy_columns):
                if i == 0:
                    signals = signals.with_columns([
                        pl.when(pl.col("max_idx") == i)
                        .then(pl.col(col))
                        .otherwise(0)
                        .alias("final_signal")
                    ])
                else:
                    signals = signals.with_columns([
                        pl.when(pl.col("max_idx") == i)
                        .then(pl.col(col))
                        .otherwise(pl.col("final_signal"))
                        .alias("final_signal")
                    ])

            signals = signals.drop("max_idx")

        elif mode == "consensus":
            # Majority voting with strength
            signals = signals.with_columns([
                pl.concat_list(strategy_columns)
                .list.eval(pl.element().sign())  # Get direction only
                .list.mean()  # Average of directions
                .alias("consensus_direction")
            ])

            # Get average strength
            signals = signals.with_columns([
                pl.concat_list(strategy_columns)
                .list.eval(pl.element().abs())
                .list.mean()
                .alias("consensus_strength")
            ])

            # Combine direction and strength
            signals = signals.with_columns([
                (pl.col("consensus_direction") * pl.col("consensus_strength"))
                .round()
                .cast(pl.Int32)
                .alias("final_signal")
            ])

            signals = signals.drop(["consensus_direction", "consensus_strength"])

        else:
            raise ValueError(f"Unknown mode: {mode}. Use 'aggregate', 'max', or 'consensus'")

        # Add signal interpretation
        signals = signals.with_columns([
            pl.when(pl.col("final_signal") >= 15)
            .then(pl.lit("VERY STRONG BUY"))
            .when(pl.col("final_signal") >= 10)
            .then(pl.lit("STRONG BUY"))
            .when(pl.col("final_signal") >= 5)
            .then(pl.lit("BUY"))
            .when(pl.col("final_signal") <= -15)
            .then(pl.lit("VERY STRONG SELL"))
            .when(pl.col("final_signal") <= -10)
            .then(pl.lit("STRONG SELL"))
            .when(pl.col("final_signal") <= -5)
            .then(pl.lit("SELL"))
            .otherwise(pl.lit("NEUTRAL"))
            .alias("signal_label")
        ])

        self.signals = signals

        # Print summary
        buy_signals = len(signals.filter(pl.col("final_signal") > 0))
        sell_signals = len(signals.filter(pl.col("final_signal") < 0))
        neutral_signals = len(signals.filter(pl.col("final_signal") == 0))

        print(f"\n✓ Signal generation complete!")
        print(f"  Buy signals: {buy_signals}")
        print(f"  Sell signals: {sell_signals}")
        print(f"  Neutral: {neutral_signals}")

        return signals

    def get_latest_signal(self) -> Dict[str, Any]:
        """Get the most recent trading signal"""
        if self.signals is None:
            raise ValueError("No signals generated. Call generate_signals() first.")

        latest = self.signals[-1]

        return {
            "date": latest["date"][0],
            "close": latest["close"][0],
            "signal": latest["final_signal"][0],
            "label": latest["signal_label"][0],
            "individual_signals": {
                col.replace("signal_", ""): latest[col][0]
                for col in self.signals.columns
                if col.startswith("signal_") and col != "signal_label"
            }
        }

    def get_signal_history(self, last_n: int = None) -> pl.DataFrame:
        """
        Get signal history

        Args:
            last_n: Number of recent signals to return (None for all)

        Returns:
            DataFrame with signal history
        """
        if self.signals is None:
            raise ValueError("No signals generated. Call generate_signals() first.")

        if last_n:
            return self.signals.tail(last_n)
        return self.signals

    def get_buy_sell_points(self, min_signal_strength: int = 10) -> Dict[str, pl.DataFrame]:
        """
        Get distinct buy and sell points above a threshold

        Args:
            min_signal_strength: Minimum absolute signal strength (default 10)

        Returns:
            Dictionary with 'buy' and 'sell' DataFrames
        """
        if self.signals is None:
            raise ValueError("No signals generated. Call generate_signals() first.")

        buy_points = self.signals.filter(pl.col("final_signal") >= min_signal_strength)
        sell_points = self.signals.filter(pl.col("final_signal") <= -min_signal_strength)

        return {
            "buy": buy_points,
            "sell": sell_points
        }

    def save_signals(self, output_path: str):
        """Save signals to CSV"""
        if self.signals is None:
            raise ValueError("No signals generated. Call generate_signals() first.")

        self.signals.write_csv(output_path)
        print(f"✓ Signals saved to {output_path}")

    def print_summary(self):
        """Print detailed summary of trading signals"""
        if self.signals is None:
            print("No signals generated yet.")
            return

        print("\n" + "="*60)
        print("TRADER SUMMARY")
        print("="*60)

        print(f"\nStrategies ({len(self.strategies)}):")
        for i, strategy in enumerate(self.strategies, 1):
            print(f"  {i}. {strategy.name}")

        print(f"\nData Range:")
        print(f"  Start: {self.signals['date'][0]}")
        print(f"  End: {self.signals['date'][-1]}")
        print(f"  Total days: {len(self.signals)}")

        print(f"\nSignal Distribution:")
        for label in ["VERY STRONG BUY", "STRONG BUY", "BUY", "NEUTRAL", "SELL", "STRONG SELL", "VERY STRONG SELL"]:
            count = len(self.signals.filter(pl.col("signal_label") == label))
            pct = count / len(self.signals) * 100
            print(f"  {label:20s}: {count:4d} ({pct:5.1f}%)")

        # Latest signal
        latest = self.get_latest_signal()
        print(f"\nLatest Signal:")
        print(f"  Date: {latest['date']}")
        print(f"  Price: ${latest['close']:.2f}")
        print(f"  Signal: {latest['signal']} ({latest['label']})")
        print(f"  Individual strategies:")
        for strategy, signal in latest['individual_signals'].items():
            print(f"    - {strategy}: {signal}")

        print("\n" + "="*60)

    def __repr__(self):
        return f"Trader(strategies={len(self.strategies)}, data_loaded={self.data is not None})"