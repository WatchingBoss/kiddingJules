# Refactoring for Python 3.7

This version introduces `dataclasses`, a powerful feature from Python 3.7 that simplifies class creation.

## `process_logs.py`

The `LogEntry` class has been converted from a standard class to a dataclass.

### Key Changes:

*   **`dataclasses`:** The `@dataclass` decorator automatically generates special methods like `__init__`, `__repr__`, `__eq__`, and others based on the class's type-annotated attributes. This significantly reduces boilerplate code.

    **Before (Python 3.6):**
    ```python
    class LogEntry:
        def __init__(self, user_id, timestamp, action, product_id, price):
            self.user_id = int(user_id)
            self.timestamp = timestamp
            self.action = action
            self.product_id = product_id
            self.price = float(price) if price else 0.0

        def __repr__(self):
            return f'LogEntry(user_id={self.user_id}, action={self.action}, price={self.price})'
    ```

    **After (Python 3.7):**
    ```python
    from dataclasses import dataclass

    @dataclass
    class LogEntry:
        user_id: int
        timestamp: str
        action: str
        product_id: str
        price: float
    ```
    The data type conversion is now handled cleanly within the `process_logs` function before the `LogEntry` object is created.

### Other Notable Python 3.7 Features:

*   **`breakpoint()`:** Python 3.7 introduced the built-in `breakpoint()` function. You can insert `breakpoint()` anywhere in your code to drop into the Python debugger (`pdb`). This is a more convenient and flexible way to debug than `import pdb; pdb.set_trace()`.
*   **Dictionary Order is Guaranteed:** While this was an implementation detail in CPython 3.6, Python 3.7 made it an official language guarantee that dictionaries preserve insertion order.
