# Refactoring for Python 3.8

This version introduces the "walrus operator" (`:=`), a new syntax in Python 3.8 for assigning variables as part of an expression.

## `process_logs.py`

The `print_summary` function has been updated to use the walrus operator to simplify the code.

### Key Changes:

*   **Assignment Expressions (The Walrus Operator):** The walrus operator `:=` allows you to assign a value to a variable within an expression. This is useful for avoiding redundant calculations and making code more concise. In our case, we use it to get the number of action types, check if it's greater than zero, and use the value in the print statement, all in one line.

    **Before (Python 3.7-style):**
    ```python
    def print_summary(action_counts, total_revenue):
        # We might check len(action_counts) and then use it again
        if len(action_counts) > 0:
            print(f'--- Activity Summary ---')
            # ... loop ...
    ```

    **After (Python 3.8):**
    ```python
    def print_summary(action_counts, total_revenue):
        if (num_actions := len(action_counts)) > 0:
            print(f'--- Activity Summary ({num_actions} types) ---')
            for action, count in sorted(action_counts.items()):
                print(f'Action: "{action}", Count: {count}')
        # ...
    ```

### Other Notable Python 3.8 Features:

*   **Positional-Only Arguments:** Python 3.8 introduced a new syntax (`/`) in function definitions to specify that some arguments must be specified positionally and cannot be used as keyword arguments. This is useful for library authors who want to prevent users from relying on the name of an argument, allowing it to be renamed in the future without breaking code.

    **Example:**
    ```python
    def my_func(a, b, /):
        # a and b are positional-only
        pass

    my_func(10, 20)      # Valid
    # my_func(a=10, b=20)  # Invalid, raises TypeError
    ```
