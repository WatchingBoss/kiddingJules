# Refactoring for Python 3.10

Python 3.10 brought two major new features to the language: structural pattern matching and more precise type hinting. This version refactors the script to use both.

## `process_logs.py`

### Key Changes:

*   **Structural Pattern Matching (`match/case`):** This is one of the most significant syntax additions in Python's recent history. It allows you to match variables against a series of patterns. It's like a super-powered `if/elif/else` chain and is especially useful for handling structured data. We've added a new function, `categorize_entry`, that uses a `match/case` statement to categorize log entries based on their attributes.

    **Example from the script:**
    ```python
    def categorize_entry(entry: LogEntry) -> str:
        """Categorizes a log entry using pattern matching."""
        match entry:
            case LogEntry(action='purchase', price=p) if p > 50.0:
                return "Major Purchase"
            case LogEntry(action='purchase'):
                return "Minor Purchase"
            case LogEntry(action='login' | 'logout'): # Use of | in patterns
                return "Authentication"
            case LogEntry(action='view_item'):
                return "Engagement"
            case _:
                return "Unknown"
    ```
    Note the ability to match object structure, capture values (`price=p`), include guards (`if p > 50.0`), and use `|` to combine patterns.

*   **More Precise Type Hinting:**
    *   **Union Operator (`|`):** You can now use the `|` operator to create union types, which is cleaner than `typing.Union`. For example, `dict | None` instead of `Optional[dict]`.
    *   **Built-in Generic Types:** You no longer need to import `List`, `Dict`, etc., from `typing`. You can use the built-in `list`, `dict`, and `tuple` directly as generic types.

    **Before (Python 3.9-style):**
    ```python
    from typing import List, Dict, Optional, Tuple, DefaultDict

    def analyze_logs(log_entries: List[LogEntry]) -> Tuple[DefaultDict[str, int], float]:
        # ...
    def print_summary(..., config: Optional[Dict] = None) -> None:
        # ...
    ```

    **After (Python 3.10):**
    ```python
    from collections import defaultdict

    # No need for most imports from typing
    def analyze_logs(log_entries: list[LogEntry]) -> tuple[defaultdict[str, int], float, defaultdict[str, int]]:
        # ...
    def print_summary(..., config: dict | None = None) -> None:
        # ...
    ```
