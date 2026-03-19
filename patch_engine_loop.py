import polars as pl
from strategies.base import BaseStrategy

class BacktestEngine():
    def __init__(self, data_source: pl.LazyFrame):
        self.raw_data = data_source

    def run(self, strategy: BaseStrategy, tp_pct: float = None, sl_pct: float = None) -> pl.DataFrame:
        print(f"--- Running Strategy: {strategy.name} ---")

        # Collect raw signals to memory for fast slicing
        df = strategy.generate_signals(self.raw_data).collect()

        # If no risk parameters, fall back to native strategy logic
        if tp_pct is None and sl_pct is None:
            trade_events = df.with_columns(
                pl.when(pl.col("Buy_Signal")).then(pl.lit(1))
                .when(pl.col("Sell_Signal")).then(pl.lit(-1))
                .otherwise(pl.lit(0))
                .alias("Action")
            )
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
            )

        # To strictly enforce State Resets and ignore mid-trade overlapping Buy_Signals
        # without circular dependency forward-fills, we iterate trade-by-trade.
        # We do NOT iterate row-by-row to find exits; instead we use fast vectorized Polars filters.

        # Add a Row_Idx to efficiently slice the dataframe after each trade completes.
        df = df.with_row_index("Row_Idx")
        total_rows = df.height

        # Extract all potential entry points
        buys = df.filter(pl.col("Buy_Signal")).select("Row_Idx", "Date", "Close", "Ticker")

        results = []
        next_valid_idx = 0  # Tracks the state reset

        for buy_row in buys.iter_rows(named=True):
            buy_idx = buy_row["Row_Idx"]

            # State Reset: Ignore overlapping Buy_Signals if an active trade is open
            if buy_idx < next_valid_idx:
                continue

            entry_price = buy_row["Close"]
            ticker = buy_row["Ticker"]

            # Slice the dataframe starting from the candle AFTER the entry.
            # This prevents look-ahead bias (we cannot exit on the same candle's high/low if we bought at its close).
            search_df = df.slice(buy_idx + 1, total_rows - buy_idx - 1)

            if search_df.height == 0:
                break # Trade opened on the very last bar, no exit possible

            # Vectorized search for the first valid exit for this specific trade
            exit_cond = pl.col("Sell_Signal")
            if tp_pct is not None:
                exit_cond = exit_cond | (pl.col("High") >= entry_price * (1 + tp_pct))
            if sl_pct is not None:
                exit_cond = exit_cond | (pl.col("Low") <= entry_price * (1 - sl_pct))

            # Use idiomatic Polars expression to instantly find the exit
            exits = search_df.filter(exit_cond).head(1)

            if exits.height == 0:
                break # Trade remains open indefinitely at the end of the dataset

            exit_row = exits.row(0, named=True)
            exit_idx = exit_row["Row_Idx"]

            # Pessimistic execution: we evaluate Stop Loss FIRST if both thresholds are breached on the exit row.
            profit = exit_row["Close"] - entry_price # Default assumption: Strategy Sell

            if sl_pct is not None and exit_row["Low"] <= entry_price * (1 - sl_pct):
                profit = entry_price * (1 - sl_pct) - entry_price
            elif tp_pct is not None and exit_row["High"] >= entry_price * (1 + tp_pct):
                profit = entry_price * (1 + tp_pct) - entry_price

            results.append({
                "Ticker": ticker,
                "Date": exit_row["Date"],
                "Close": exit_row["Close"],
                "Profit": float(profit)
            })

            # State Reset: The next valid trade can only start AFTER this exit completes.
            next_valid_idx = exit_idx + 1

        # Return results in identical format to original
        schema = {"Ticker": pl.Utf8, "Date": df.schema["Date"], "Close": df.schema["Close"], "Profit": pl.Float64}
        if not results:
            return pl.DataFrame(schema=schema)

        return pl.DataFrame(results, schema=schema)

    @staticmethod
    def report_metrics(trades_df: pl.DataFrame):
        metrics = trades_df.group_by("Ticker").agg(
            pl.len().alias("Total_Trades"),
            pl.col("Profit").mean().alias("Average"),
            pl.col("Profit").median().alias("Median"),
            (pl.col("Profit") > 0).sum().alias("Positive"),
            (pl.col("Profit") < 0).sum().alias("Negative")
        ).sort("Ticker")
        print(metrics)
