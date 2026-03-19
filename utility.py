import itertools
from typing import Type
import polars as pl
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from strategies.base import BaseStrategy


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


def generate_ema_grid(blueprint: Type['BaseStrategy'], exec_tfs: list[str], htfs: list[str]) -> list['BaseStrategy']:
    """Generates a comprehensive grid of strategy instances across varying execution timeframes, higher timeframe filters, and trend states."""
    strategies = []
    states = ["bullish", "bearish"]

    for exec_tf in exec_tfs:
        # Tier 1 (Base): NO filters
        strategies.append(blueprint(name=f"EMA_{exec_tf}_Base", exec_tf=exec_tf, filters={}))

        # Tier 2 (Single Filter): exactly one higher timeframe filter
        for htf, state in itertools.product(htfs, states):
            strategies.append(
                blueprint(
                    name=f"EMA_{exec_tf}_Filter_{htf}_{state[:4]}",
                    exec_tf=exec_tf,
                    filters={htf: state}
                )
            )

        # Tier 3 (Dual Filter): unique pairs of higher timeframes, all trend alignments
        for (tf1, tf2) in itertools.combinations(htfs, 2):
            for state1, state2 in itertools.product(states, repeat=2):
                strategies.append(
                    blueprint(
                        name=f"EMA_{exec_tf}_F1_{tf1}_{state1[:4]}_F2_{tf2}_{state2[:4]}",
                        exec_tf=exec_tf,
                        filters={tf1: state1, tf2: state2}
                    )
                )

    return strategies
