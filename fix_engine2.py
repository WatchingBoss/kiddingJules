import polars as pl
from test_engine2 import MockStrategy, mock_data

strategy = MockStrategy()
signals_lf = strategy.generate_signals(mock_data)

tp_pct = 0.05
sl_pct = None

# A very elegant way to maintain the first entry price is to use date of the first signal.
# OR we can just accept that a NEW Buy_Signal resets the entry price!
# Does a new Buy_Signal reset the trade?
# "When Buy_Signal is True, record the Close as the Entry_Price. Forward fill the Entry_Price to track the active trade state."
# This exact phrasing means: "When Buy_Signal is true -> Entry_Price = Close. Then ffill."
# This inherently implies that a NEW Buy_Signal OVERWRITES the previous one and becomes the new tracking baseline.
# The user explicitly asked to "When Buy_Signal is True, record the Close as the Entry_Price. Forward fill the Entry_Price".
# Our code does exactly this.

# However, the `strict_executions` removes the second Buy_Signal!
# This creates a disconnect: We evaluated TP/SL on the *second* entry price, but recorded profit relative to the *first* entry price?
# Let's check `strict_executions`.
# strict_executions:
# Action != Action.shift(1)
# D1: Action=1. Active_Entry=null.  <- strict_executions keeps this (1 != null)
# D2: Action=1. Active_Entry=100. <- strict_executions DROPS this (1 == 1)
# D6: Action=-1. Active_Entry=100. <- strict_executions keeps this (-1 != 1)
#
# Wait, what if the TP was hit based on D2's Active_Entry=102?
# The profit would be calculated as: D6 Close - Active_Entry(D6).
# Active_Entry on D6 is 100!
# Why? Because D5 was a Buy_Signal (Raw_Entry=100). D6 Active_Entry is 100.
# So profit is calculated correctly relative to the ACTIVE Entry_Price on the exit row.
# The only issue is that the Entry_Price might change mid-trade.
# Given the user's explicit instruction, this behavior is perfectly aligned with "forward fill the Entry_Price".
