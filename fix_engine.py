import polars as pl

# Our previous naive ffill breaks if consecutive buys exist, because
# the second buy overwrites the first buy's entry price before it exits!
# We can fix this by forward filling the entry price only once per trade group.
# How to define a trade group? Buy_Signal.cum_sum() breaks if overlapping buys.
# Let's use a robust way to extract just the FIRST entry price of a sequence.

# Actually, the simplest way is to fill nulls forward, but NOT let new values overwrite!
# Polars doesn't have a direct "don't overwrite" ffill.
# BUT:
# `Trade_ID = pl.when(pl.col("Action") == 1).then(1).when(pl.col("Action") == -1).then(-1).otherwise(0)`
# This requires knowing Action beforehand.

# Let's consider:
# Buy_Signal sparse pulses (our strategy is a crossover, so it only pulses once).
# TripleEMAStrategy generates exactly ONE true value at a crossover.
# The `df_1m` is resampled to 5m, 15m, 1h.
# Let's see if the overlap is practically a problem.
# "The strategies (e.g., TripleEMAStrategy) now return a LazyFrame containing a boolean Buy_Signal."
# Crossovers are sparse.
