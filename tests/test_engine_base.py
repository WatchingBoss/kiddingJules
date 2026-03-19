import polars as pl
from engine import BacktestEngine

# Mock BaseStrategy
class MockStrategy:
    name = "Mock"
    def generate_signals(self, raw_data: pl.LazyFrame) -> pl.LazyFrame:
        # Mock signals dataframe
        return raw_data.with_columns(
            pl.Series("Buy_Signal", [False, True, False, False, False, True, False]),
            pl.Series("Sell_Signal", [False, False, False, True, False, False, False])
        )

# Create some mock data
mock_data = pl.DataFrame({
    "Ticker": ["AAPL"] * 7,
    "Date": ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04", "2023-01-05", "2023-01-06", "2023-01-07"],
    "Open": [100, 100, 100, 100, 100, 100, 100],
    "High": [100, 100, 106, 100, 100, 100, 100],  # Day 3 high is 106
    "Low":  [100, 100, 100, 100, 95, 100, 95],   # Day 5 low is 95
    "Close": [100, 100, 102, 100, 98, 100, 98]   # Day 2 Buy_Signal enters at Close=100
}).lazy()

engine = BacktestEngine(mock_data)

print("Test 1: Default execution (only strategy Sell_Signal)")
print(engine.run(MockStrategy()))

print("\nTest 2: With TP=0.05 (Hits High=106 on Day 3)")
print(engine.run(MockStrategy(), tp_pct=0.05))

print("\nTest 3: With SL=0.04 (Hits Low=95 on Day 5, Day 3 TP removed)")
# Update mock_data to remove Day 3 TP so we can hit SL on Day 5
mock_data_sl = mock_data.with_columns(pl.Series("High", [100, 100, 102, 100, 100, 100, 100]))
engine_sl = BacktestEngine(mock_data_sl)
print(engine_sl.run(MockStrategy(), sl_pct=0.04))

print("\nTest 4: With TP and SL (Hits TP on Day 3 first)")
print(engine.run(MockStrategy(), tp_pct=0.05, sl_pct=0.04))

print("\nTest 5: Pessimistic TP/SL same day")
mock_data_same_day = mock_data.with_columns(
    pl.Series("High", [100, 100, 106, 100, 100, 100, 100]),
    pl.Series("Low", [100, 100, 95, 100, 100, 100, 100])
)
engine_same_day = BacktestEngine(mock_data_same_day)
print(engine_same_day.run(MockStrategy(), tp_pct=0.05, sl_pct=0.04))
