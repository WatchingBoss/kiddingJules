import polars as pl
from test_engine2 import mock_data, MockStrategy

strategy = MockStrategy()
signals_lf = strategy.generate_signals(mock_data)
tp_pct = 0.05
sl_pct = None

df = signals_lf.with_columns(
    pl.when(pl.col("Buy_Signal")).then(pl.col("Close")).otherwise(None).alias("Raw_Entry")
).with_columns(
    pl.col("Raw_Entry").forward_fill()
).with_columns(
    pl.col("Raw_Entry").shift(1).alias("Active_Entry")
)

df = df.with_columns(
    pl.lit(False).alias("Hit_TP"),
    pl.lit(False).alias("Hit_SL")
)

df = df.with_columns(
    (pl.col("High") >= pl.col("Active_Entry") * (1 + tp_pct)).alias("Hit_TP")
)

df = df.with_columns(
    (pl.col("Hit_TP") | pl.col("Hit_SL") | pl.col("Sell_Signal")).alias("Any_Exit")
)

trade_events = df.with_columns(
    pl.when(pl.col("Any_Exit")).then(pl.lit(-1))
    .when(pl.col("Buy_Signal")).then(pl.lit(1))
    .otherwise(pl.lit(0))
    .alias("Action")
)

executions = trade_events.filter(pl.col("Action") != 0)
strict_executions = executions.filter(
    pl.col("Action") != pl.col("Action").shift(1)
)

print(trade_events.select("Date", "Buy_Signal", "Raw_Entry", "Active_Entry", "High", "Hit_TP", "Any_Exit", "Action").collect())
print(strict_executions.select("Date", "Action").collect())
