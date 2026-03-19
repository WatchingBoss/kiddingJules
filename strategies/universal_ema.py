import polars as pl
from strategies.base import BaseStrategy
from strategies.registry import register
from utility import resample_candles, add_emas

@register
class UniversalEmaStrategy(BaseStrategy):
    # To be compatible with the existing registry which instantiates via cls(),
    # we need to provide default arguments, or change how registry instantiates it.
    # The prompt explicitly asked for: `def __init__(self, name: str, exec_tf: str, filters: dict[str, str] = None)`
    # The registry calls `cls()` without arguments.
    # For now, I will add default arguments to satisfy the existing `all_strategies()` call in `main.py`,
    # while strictly adhering to the requested initialization signature parameters.
    def __init__(self, name: str = "UniversalEMA", exec_tf: str = "5m", filters: dict[str, str] = None):
        self._name = name
        self.exec_tf = exec_tf
        self.filters = filters or {}

    @property
    def name(self) -> str:
        return self._name

    def generate_signals(self, df_1m: pl.LazyFrame) -> pl.LazyFrame:
        # 1. Base Execution Timeframe Processing
        base_df = resample_candles(df_1m, timeframe=self.exec_tf)
        base_signals = add_emas(base_df, timeframe_label=self.exec_tf)

        master_df = (
            base_df
            .join(base_signals, on=["Ticker", "Date"])
            .sort(["Ticker", "Date"])
        )

        # 2. Dynamic Resampling and Joining of Higher Timeframe Filters
        for tf in self.filters.keys():
            if tf == self.exec_tf:
                continue # Filter is already on the execution timeframe

            htf_df = resample_candles(df_1m, timeframe=tf)
            htf_signals = add_emas(htf_df, timeframe_label=tf)

            # Shift the higher timeframe forward by its interval to prevent look-ahead bias.
            shifted_htf_signals = (
                htf_signals
                .with_columns(
                    pl.col("Date").dt.offset_by(tf)
                )
                .sort(["Ticker", "Date"])
            )

            master_df = master_df.join_asof(
                shifted_htf_signals,
                on="Date",
                by="Ticker",
                strategy="backward",
                check_sortedness=False
            )

        # 3. Dynamic Expression Building
        buy_expr = (
            (pl.col(f"ema10_{self.exec_tf}") > pl.col(f"ema20_{self.exec_tf}")) &
            (pl.col(f"ema10_{self.exec_tf}").shift(1).over("Ticker") <= pl.col(f"ema20_{self.exec_tf}").shift(1).over("Ticker"))
        )

        sell_expr = (
            (pl.col(f"ema10_{self.exec_tf}") < pl.col(f"ema20_{self.exec_tf}")) &
            (pl.col(f"ema10_{self.exec_tf}").shift(1).over("Ticker") >= pl.col(f"ema20_{self.exec_tf}").shift(1).over("Ticker"))
        )

        # 4. Apply Filters (Asymmetric Logic)
        for tf, state in self.filters.items():
            state = state.lower()
            if state == "bullish":
                filter_expr = (pl.col(f"ema10_{tf}") > pl.col(f"ema20_{tf}"))
            elif state == "bearish":
                filter_expr = (pl.col(f"ema10_{tf}") < pl.col(f"ema20_{tf}"))
            else:
                raise ValueError(f"Unknown filter state: {state}")

            buy_expr = buy_expr & filter_expr

        return master_df.with_columns(
            buy_expr.alias("Buy_Signal"),
            sell_expr.alias("Sell_Signal")
        )
