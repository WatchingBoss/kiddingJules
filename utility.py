import polars as pl


def resample_candles(df_1m: pl.LazyFrame, timeframe: str) -> pl.LazyFrame:
    """
    Resamples 1m OHLCV data to a higher timeframe.
    timeframe: Polars duration string (e.g., '5m', '1h', '1d', '1w')
    """
    return (
        df_1m.sort("Date")
        .group_by_dynamic(
            "Date",
            every=timeframe,
            group_by="Ticker",
            closed="left",  # Crucial: determines which interval boundary is inclusive
            label="left"    # Crucial: labels the candle with the start time
        )
        .agg([
            pl.col("Open").first(),
            pl.col("High").max(),
            pl.col("Low").min(),
            pl.col("Close").last(),
            pl.col("Volume").sum()
        ])
    )


def add_emas(df: pl.LazyFrame, timeframe_label: str) -> pl.LazyFrame:
    return df.with_columns([
        pl.col("Close").ewm_mean(span=10, ignore_nulls=True).alias(f"ema10_{timeframe_label}"),
        pl.col("Close").ewm_mean(span=20, ignore_nulls=True).alias(f"ema20_{timeframe_label}")
    ]).select(["Ticker", "Date", f"ema10_{timeframe_label}", f"ema20_{timeframe_label}"])
