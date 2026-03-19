import os
from pathlib import Path
from datetime import datetime

import polars as pl

from config import DATA_DIR, PARQUET_SOURCE_DIR
from engine import BacktestEngine
from strategies.registry import all_strategies


parquet_source_path = Path(PARQUET_SOURCE_DIR)


def check_source_parquet(tickers: dict) -> bool:
    files = list(parquet_source_path.glob('**/*.parquet'))
    if not files:
        print("Tell human to convert his csv history candles to parquet.")
        return False

    for ticker, row_count in tickers.items():
        df = (
            pl.scan_parquet(os.path.join(PARQUET_SOURCE_DIR, "**/*.parquet"))
            .filter(pl.col("Ticker") == ticker)
            .collect()
        )
        if not df.shape[0] == row_count:
            print(f"Tell human row count of {ticker} is unexpected.")
            return False
    return True


def main():
    tickers = {'GAZP': 1_812_503, 'SBER': 1_824_297}
    if not check_source_parquet(tickers):
        return

    raw_1m_candles_lf = pl.scan_parquet(os.path.join(PARQUET_SOURCE_DIR, "**/*.parquet"))
    engine = BacktestEngine(raw_1m_candles_lf)

    strategies = all_strategies()
    print(f"{len(strategies)} strategies loaded.")

    for strategy in strategies:
        completed_trades = engine.run(strategy)
        engine.report_metrics(completed_trades)

if __name__ == "__main__":
    main()
