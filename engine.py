import polars as pl
from strategies.base import BaseStrategy


class BacktestEngine():
    def __init__(self, data_source: pl.LazyFrame):
        self.raw_data = data_source

    def run(self, strategy: BaseStrategy) -> pl.DataFrame:
        print(f"--- Running Strategy: {strategy.name} ---")

        signals_lf = strategy.generate_signals(self.raw_data)

        # Compress signals into a single 'Action' column (1 = Buy, -1 = Sell, 0 = Hold)
        trade_events = signals_lf.with_columns(
            pl.when(pl.col("Buy_Signal")).then(pl.lit(1))
            .when(pl.col("Sell_Signal")).then(pl.lit(-1))
            .otherwise(pl.lit(0))
            .alias("Action")
        )

        # Drop all the "Hold" rows. We only care about execution moments.
        # Drop overlapping consecutive signals
        executions = trade_events.filter(pl.col("Action") != 0)
        strict_executions = executions.filter(
            pl.col("Action") != pl.col("Action").shift(1)
        )

        results = strict_executions.with_columns(
            pl.when(pl.col("Action") == -1)
            .then(pl.col("Close") - pl.col("Close").shift(1))
            .otherwise(None)
            .alias("Profit")
        )

        return results.filter(pl.col("Profit").is_not_null()).select(
            "Ticker", "Date", "Close", "Profit"
        ).collect()

    @staticmethod
    def report_metrics(trades_df: pl.DataFrame):
        """Universal metrics reporter"""
        metrics = trades_df.group_by("Ticker").agg(
            pl.len().alias("Total_Trades"),
            pl.col("Profit").mean().alias("Average"),
            pl.col("Profit").median().alias("Median"),
            (pl.col("Profit") > 0).sum().alias("Positive"),
            (pl.col("Profit") < 0).sum().alias("Negative")
        ).sort("Ticker")
        print(metrics)
