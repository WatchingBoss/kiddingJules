import polars as pl
from engine import BacktestEngine

df_1m = pl.DataFrame({
    "Date": pl.date_range(pl.datetime(2023, 1, 1), pl.datetime(2023, 1, 10), "1d", eager=True),
    "Ticker": ["BTC"] * 10,
    "Open": [100.0] * 10,
    "High": [100.0] * 10,
    "Low": [100.0] * 10,
    "Close": [100.0] * 10,
    "Volume": [100.0] * 10,
}).lazy()

# Wait, `strategies.triple_ema_cross.py` needs valid df_1m
# It doesn't matter, we are just verifying the engine works as requested.
# Let's check `engine.py` again.
