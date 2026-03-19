import polars as pl
from strategies.base import BaseStrategy
from strategies.registry import register
from utility import resample_candles, add_emas


@register
class TripleEMAStrategy(BaseStrategy):
    @property
    def name(self) -> str:
        return "Triple_EMA_5m_15m_1h"

    def generate_signals(self, df_1m: pl.LazyFrame) -> pl.LazyFrame:
        lf_5m = resample_candles(df_1m, timeframe='5m')
        lf_15m = resample_candles(df_1m, timeframe='15m')
        lf_1h = resample_candles(df_1m, timeframe='1h')
        signals_5m = add_emas(lf_5m, timeframe_label='5m')
        signals_15m = add_emas(lf_15m, timeframe_label='15m')
        signals_1h = add_emas(lf_1h, timeframe_label='1h')

        master_signals = (
            lf_5m
            .join(signals_5m, on=["Ticker", "Date"])
            .sort(["Ticker", "Date"])
        )

        # We shift the higher timeframes forward by 1 period before joining.
        # Why? Because a 1h candle labeled "10:00" contains data up to 10:59.
        # The 10:00 1h indicators shouldn't be visible to a 5m candle until 11:00.
        # Without this shift, a 10:05 candle will see the close price of 10:59.
        shifted_15m = (
            signals_15m
            .with_columns(
                pl.col("Date").dt.offset_by("15m")
            )
            .sort(["Ticker", "Date"])
        )

        shifted_1h = (
            signals_1h
            .with_columns(
                pl.col("Date").dt.offset_by("1h")
            )
            .sort(["Ticker", "Date"])
        )

        master_lf = (
            master_signals
            .join_asof(
                shifted_15m,
                on="Date",
                by="Ticker",
                strategy="backward",
                check_sortedness=False
            )
            .join_asof(
                shifted_1h,
                on="Date",
                by="Ticker",
                strategy="backward",
                check_sortedness=False
            )
        )

        return master_lf.with_columns(
        (
            (pl.col("ema10_5m") > pl.col("ema20_5m")) &
            (pl.col("ema10_5m").shift(1) <= pl.col("ema20_5m").shift(1)) &  # The Cross
            (pl.col("ema10_15m") > pl.col("ema20_15m")) &  # 1D Trend Filter
            (pl.col("ema10_1h") > pl.col("ema20_1h"))  # 1h Trend Filter
        ).alias("Buy_Signal"),
        (
            (pl.col("ema10_5m") < pl.col("ema20_5m")) &
            (pl.col("ema10_5m").shift(1) >= pl.col("ema20_5m").shift(1)) &  # The Cross
            (pl.col("ema10_15m") > pl.col("ema20_15m")) &  # 1D Trend Filter
            (pl.col("ema10_1h") > pl.col("ema20_1h"))  # 1h Trend Filter
        ).alias("Sell_Signal"),
    )
