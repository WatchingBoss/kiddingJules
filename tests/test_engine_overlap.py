import polars as pl
from engine import BacktestEngine

# Mock BaseStrategy
class MockStrategy:
    name = "Mock"
    def generate_signals(self, raw_data: pl.LazyFrame) -> pl.LazyFrame:
        # Provide Buy_Signal overlapping during an active trade
        # Row 0: No Signal
        # Row 1: Buy (Entry = 100)
        # Row 2: Buy again (Entry would be 102 but we want to ignore it since we're in a trade)
        # Row 3: Hit TP for Entry 100
        # Row 4: No Signal
        # Row 5: Buy (Entry = 100)
        # Row 6: Sell
        return raw_data.with_columns(
            pl.Series("Buy_Signal", [False, True, True, False, False, True, False]),
            pl.Series("Sell_Signal", [False, False, False, False, False, False, True])
        )

mock_data = pl.DataFrame({
    "Ticker": ["AAPL"] * 7,
    "Date": ["D0", "D1", "D2", "D3", "D4", "D5", "D6"],
    "Open": [100, 100, 100, 100, 100, 100, 100],
    "High": [100, 100, 103, 106, 100, 100, 100],
    "Low":  [100, 100, 100, 100, 95, 100, 95],
    "Close": [100, 100, 102, 102, 98, 100, 98]
}).lazy()

engine = BacktestEngine(mock_data)

print(engine.run(MockStrategy(), tp_pct=0.05))
