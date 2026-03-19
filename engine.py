import polars as pl
from strategies.base import BaseStrategy

class BacktestEngine():
    def __init__(self, data_source: pl.LazyFrame):
        self.raw_data = data_source

    def run(self, strategy: BaseStrategy, tp_pct: float = None, sl_pct: float = None) -> pl.DataFrame:
        print(f"--- Running Strategy: {strategy.name} ---")

        signals_lf = strategy.generate_signals(self.raw_data)

        # 1. Track Entry Price (Grouped by Ticker to prevent multi-asset contamination)
        # We explicitly follow the required approach:
        # "When Buy_Signal is True, record the Close as the Entry_Price. Forward fill the Entry_Price to track the active trade state."
        df = signals_lf.with_columns(
            pl.when(pl.col("Buy_Signal")).then(pl.col("Close")).otherwise(None).alias("Raw_Entry")
        ).with_columns(
            pl.col("Raw_Entry").forward_fill().over("Ticker")
        ).with_columns(
            # Shift by 1 so we evaluate exits on the candle *after* the entry to prevent look-ahead bias
            pl.col("Raw_Entry").shift(1).over("Ticker").alias("Active_Entry")
        )

        # 2. Evaluate Dynamic Exits
        df = df.with_columns(
            pl.lit(False).alias("Hit_TP"),
            pl.lit(False).alias("Hit_SL")
        )

        if tp_pct is not None:
            df = df.with_columns(
                (pl.col("High") >= pl.col("Active_Entry") * (1 + tp_pct)).alias("Hit_TP")
            )

        if sl_pct is not None:
            df = df.with_columns(
                (pl.col("Low") <= pl.col("Active_Entry") * (1 - sl_pct)).alias("Hit_SL")
            )

        df = df.with_columns(
            (pl.col("Hit_TP") | pl.col("Hit_SL") | pl.col("Sell_Signal")).alias("Any_Exit")
        )

        # 3. State Machine: Compress signals into an 'Action' column
        # CRITICAL: Buy_Signal MUST take precedence over Any_Exit.
        # This completely solves the "Phantom Exit blocking new Buys" bug.
        # If Active_Entry is stale and Any_Exit evaluates to True indefinitely after a trade closes,
        # placing Buy_Signal first ensures that a new valid Buy_Signal flawlessly resets the state to 1.
        trade_events = df.with_columns(
            pl.when(pl.col("Buy_Signal")).then(pl.lit(1))
            .when(pl.col("Any_Exit")).then(pl.lit(-1))
            .otherwise(pl.lit(0))
            .alias("Action")
        )

        executions = trade_events.filter(pl.col("Action") != 0)

        # Keep only strict state transitions per Ticker to ignore consecutive/overlapping signals.
        # This resolves state resets: e.g. Buy(1) -> TP(-1) -> TP(-1) -> Buy(1) -> TP(-1)
        # becomes cleanly Buy(1) -> TP(-1) -> Buy(1) -> TP(-1)
        strict_executions = executions.filter(
            pl.col("Action") != pl.col("Action").shift(1).over("Ticker")
        )

        # 4. Calculate accurate Profit (Pessimistic: SL takes precedence over TP)
        profit_expr = pl.col("Close") - pl.col("Active_Entry") # Default to Strategy Sell

        if tp_pct is not None:
            profit_expr = pl.when(pl.col("Hit_TP")).then(
                pl.col("Active_Entry") * (1 + tp_pct) - pl.col("Active_Entry")
            ).otherwise(profit_expr)

        if sl_pct is not None:
            profit_expr = pl.when(pl.col("Hit_SL")).then(
                pl.col("Active_Entry") * (1 - sl_pct) - pl.col("Active_Entry")
            ).otherwise(profit_expr)

        results = strict_executions.with_columns(
            pl.when(pl.col("Action") == -1)
            .then(profit_expr)
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
