# Refactoring for Python 3.6

This directory demonstrates the first step in our refactoring journey, applying key features introduced in Python 3.6.

## `process_logs.py`

The script has been updated from the legacy version to incorporate f-strings for better readability.

### Key Changes:

*   **Formatted String Literals (f-Strings):** The `str.format()` calls have been replaced with f-strings, which are more concise and less error-prone.

    **Before (Python 3.5):**
    ```python
    print('Total Revenue: ${:.2f}'.format(total_revenue))
    ```

    **After (Python 3.6):**
    ```python
    print(f'Total Revenue: ${total_revenue:.2f}')
    ```

### Other Notable Python 3.6 Features:

*   **Dictionary Version Ordering:** In CPython 3.6+, dictionaries preserve their insertion order. This became an official language feature in Python 3.7. This means that when you iterate over `action_counts.items()`, the actions will appear in the order they were first encountered. While our script previously used `sorted()` for deterministic output, for many use cases this new behavior removes the need for `collections.OrderedDict` or manual sorting.
