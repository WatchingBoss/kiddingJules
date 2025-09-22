# Legacy Script (Python 3.5 Style)

This directory contains the starting point for our project: a data processing script written in a style common before Python 3.6.

## `process_logs.py`

This script reads user activity data from `../data/user_activity.csv`, processes it, and prints a summary report.

### Key Characteristics:

*   **String Formatting:** Uses the `str.format()` method.
*   **Data Structures:** Uses a standard class (`LogEntry`) to represent data records.
*   **No Type Hints:** The code lacks type annotations.

This script is functional, but as we move through the versions, we will refactor it to use modern Python features to make it more concise, readable, and robust.
