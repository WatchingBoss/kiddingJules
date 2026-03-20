import os
from pathlib import Path
from datetime import datetime

import polars as pl

from config import DATA_DIR, PARQUET_SOURCE_DIR
from engine import BacktestEngine
from strategies.registry import get_strategy_class


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

    UniversalEMA = get_strategy_class("UniversalEmaStrategy")

    strategies_to_test = [
        UniversalEMA(name="Pure_5m_Cross", exec_tf="5m"),
        UniversalEMA(name="Cross_5m_Filter_15m_Bull", exec_tf="5m", filters={"15m": "bullish"}),
        UniversalEMA(name="Cross_5m_Filter_1h_Bull", exec_tf="5m", filters={"1h": "bullish"}),
        UniversalEMA(name="Cross_5m_Heavy_Trend", exec_tf="5m", filters={"15m": "bullish", "1h": "bullish"}),
    ]

    print(f"{len(strategies_to_test)} strategies loaded.")

    for strategy in strategies_to_test:
        completed_trades = engine.run(strategy, tp_pct=0.005, sl_pct=0.002)
        engine.log_trades(completed_trades)
        engine.report_metrics(completed_trades)

if __name__ == "__main__":
    main()
