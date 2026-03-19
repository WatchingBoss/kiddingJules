import polars as pl
from engine import BacktestEngine

# Testing the edge case where Buy_Signal and Hit_TP are on the SAME candle.
class SameCandleStrategy:
    name = "SameCandle"
    def generate_signals(self, raw_data: pl.LazyFrame) -> pl.LazyFrame:
        # Row 0: No Signal
        # Row 1: Buy (Entry = 100)
        # Row 2: No Signal, High = 110 (Hits TP 105 for Entry 100), AND Buy_Signal = True
        return raw_data.with_columns(
            pl.Series("Buy_Signal", [False, True, True, False]),
            pl.Series("Sell_Signal", [False, False, False, False])
        )

mock_data = pl.DataFrame({
    "Ticker": ["AAPL"] * 4,
    "Date": ["D0", "D1", "D2", "D3"],
    "Open": [100, 100, 100, 100],
    "High": [100, 100, 110, 100],
    "Low":  [100, 100, 100, 100],
    "Close": [100, 100, 102, 100]
}).lazy()

engine = BacktestEngine(mock_data)

print("Same Candle Buy and Exit:")
print(engine.run(SameCandleStrategy(), tp_pct=0.05))
