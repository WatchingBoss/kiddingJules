## 1. Executive Summary

The `StockStatBacktester` framework is a highly functional and performant quantitative backtesting engine built with Polars. It benefits from a modular Strategy Registry that cleanly separates logic from execution mechanics. However, several critical architectural flaws are hindering its scalability, maintainability, and robustness.

The primary bottlenecks include:
1.  **Hardcoded System Configuration and Data Dependency in Core Files:** Core logic files like `main.py` tightly couple test execution with hardcoded ticker dictionaries, hardcoded row counts, and static file paths.
2.  **Lack of State and Configuration Abstractions:** The `BacktestEngine` accepts raw Polars DataFrames and loosely defined primitives (`tp_pct`, `sl_pct`), missing a formal configuration object or a dedicated Result abstraction.
3.  **Inflexible Strategy Signal Generation:** The base strategy relies heavily on hardcoded string interpolations for column names (e.g., `"Buy_Signal"`, `"Sell_Signal"`, `"ema10_..."`), leading to brittle logic that limits adaptability to different indicators.
4.  **Implicit Dependency Resolution:** The auto-registration pattern in `strategies/__init__.py` using `pkgutil` and `importlib` obfuscates dependencies and execution order.

Addressing these technical debts will elevate this from a research script to a production-grade enterprise testing framework.

## 2. Architecture & System Design

### Issue: Hardcoded Data Validation in Entry Point
* **Location:** `main.py:15-28`
* **Severity:** High
* **Description:** The `check_source_parquet` function in `main.py` hardcodes ticker symbols (`GAZP`, `SBER`) and their exact row counts (`1_812_503`, `1_824_297`). This tightly couples the generic testing framework to a specific dataset, rendering the application entirely useless for any other asset or timeframe without manual source code modification. Furthermore, the validation logic loads the *entire* dataset for a single check before running the strategy, leading to severe performance penalties and potential Out-Of-Memory errors on larger datasets.

**Current Implementation:**
```python
def check_source_parquet(tickers: dict) -> bool:
    files = list(parquet_source_path.glob('**/*.parquet'))
    if not files:
        print("Tell human to convert his csv history candles to parquet.")
        return False

    for ticker, row_count in tickers.items():
        df = (
            pl.scan_parquet(os.path.join(PARQUET_SOURCE_DIR, "**/*.parquet"))
            .filter(pl.col("Ticker") == ticker)
            .collect()
        )
        if not df.shape[0] == row_count:
            print(f"Tell human row count of {ticker} is unexpected.")
            return False
    return True

def main():
    tickers = {'GAZP': 1_812_503, 'SBER': 1_824_297}
    if not check_source_parquet(tickers):
        return
```

Proposed Solution / Pattern:
Extract the dataset metadata verification into an external configuration file (e.g., `config.yaml` or a JSON schema). Implement a generic `DataLoader` class responsible for abstracting the underlying dataset, validating its integrity via lazy evaluation properties (e.g., `.select(pl.len()).collect().item()`), and yielding chunks or complete LazyFrames to the engine.

Refactored Code:
```python
# Create a dedicated Config or Metadata Validation module
import json
from pathlib import Path
import polars as pl
from config import PARQUET_SOURCE_DIR

class DatasetValidator:
    def __init__(self, source_dir: str, metadata_path: str):
        self.source_dir = source_dir
        self.metadata_path = Path(metadata_path)

    def validate(self) -> bool:
        if not list(Path(self.source_dir).glob('**/*.parquet')):
            raise FileNotFoundError("Source parquet files not found.")

        with open(self.metadata_path, 'r') as f:
            expected_tickers = json.load(f)

        lf = pl.scan_parquet(f"{self.source_dir}/**/*.parquet")

        for ticker, expected_count in expected_tickers.items():
            actual_count = (
                lf.filter(pl.col("Ticker") == ticker)
                .select(pl.len())
                .collect()
                .item()
            )
            if actual_count != expected_count:
                print(f"Validation failed for {ticker}: Expected {expected_count}, got {actual_count}")
                return False
        return True
```

### Issue: Weak Configuration Boundaries in Core Engine
* **Location:** `engine.py:7`
* **Severity:** Medium
* **Description:** The `run()` method inside `BacktestEngine` accepts loose primitive arguments (`tp_pct: float = None, sl_pct: float = None`). This design violates the Open-Closed Principle (SOLID). If future quantitative models require Trailing Stops, Time-Based Exits, or dynamic sizing, the core engine's method signature and underlying state machine logic must be continuously rewritten to accommodate new parameters.

**Current Implementation:**
```python
    def run(self, strategy: BaseStrategy, tp_pct: float = None, sl_pct: float = None) -> pl.DataFrame:
```

Proposed Solution / Pattern:
Introduce a Parameter Object (or Options Pattern) using `dataclasses` or `pydantic`. The engine should accept an `ExecutionConfig` object, fully encapsulating risk management rules, slippage assumptions, and commission models.

Refactored Code:
```python
from dataclasses import dataclass
from typing import Optional
import polars as pl
from strategies.base import BaseStrategy

@dataclass
class ExecutionConfig:
    tp_pct: Optional[float] = None
    sl_pct: Optional[float] = None
    trailing_sl_pct: Optional[float] = None
    commission_pct: float = 0.0

class BacktestEngine:
    def __init__(self, data_source: pl.LazyFrame):
        self.raw_data = data_source

    def run(self, strategy: BaseStrategy, config: ExecutionConfig) -> pl.DataFrame:
        # State machine logic uses config.tp_pct, config.sl_pct
        pass
```

## 3. Design Patterns

### Issue: Obfuscated Dependency Resolution (Magic Imports)
* **Location:** `strategies/__init__.py:8-14`
* **Severity:** Medium
* **Description:** The use of `pkgutil.iter_modules` and `importlib.import_module` to auto-discover and implicitly invoke `@register` decorators creates an obfuscated Initialization Pattern. It acts as "Magic" code that obscures the actual available strategies, prevents static analysis tools (like MyPy) from resolving dependencies, and can inadvertently mask import errors or circular dependencies inside individual strategy files.

**Current Implementation:**
```python
for _, module_name, _ in pkgutil.iter_modules([str(package_dir)]):
    if module_name not in ('base', 'registry'):
        importlib.import_module(f"strategies.{module_name}")
```

Proposed Solution / Pattern:
Implement an explicit Factory Registry or utilize Python Entry Points (`importlib.metadata`) if extending across packages. For an internal project, explicit imports in `__init__.py` or the registry file are vastly superior for maintainability, IDE autocompletion, and explicit failure surfacing.

Refactored Code:
```python
# strategies/__init__.py
from .universal_ema import UniversalEmaStrategy
from .triple_ema_cross import TripleEMAStrategy

# The above explicit imports naturally trigger the @register decorators in those files.
# Static analyzers can easily trace the codebase.
```

## 4. Implementation Flaws

### Issue: Hardcoded Indicator Column Suffixes
* **Location:** `strategies/universal_ema.py:46-52`, `utility.py:33-35`
* **Severity:** High
* **Description:** Indicator logic and signal generation rely on tightly coupled, hardcoded string constructions (e.g., `f"ema10_{self.exec_tf}"`). This breaks DRY principles and makes the strategy rigid. If the underlying utility function `add_emas` changes its naming convention, the strategy breaks silently. This also prevents parameterizing the EMA spans (e.g., using a 9/21 cross instead of 10/20) without modifying both the utility file and the strategy file.

**Current Implementation:**
```python
# In strategies/universal_ema.py
        buy_expr = (
            (pl.col(f"ema10_{self.exec_tf}") > pl.col(f"ema20_{self.exec_tf}")) &
            (pl.col(f"ema10_{self.exec_tf}").shift(1).over("Ticker") <= pl.col(f"ema20_{self.exec_tf}").shift(1).over("Ticker"))
        )

# In utility.py
def add_emas(df: pl.LazyFrame, timeframe_label: str) -> pl.LazyFrame:
    return df.with_columns([
        pl.col("Close").ewm_mean(span=10, ignore_nulls=True).alias(f"ema10_{timeframe_label}"),
        pl.col("Close").ewm_mean(span=20, ignore_nulls=True).alias(f"ema20_{timeframe_label}")
    ])
```

Proposed Solution / Pattern:
Utilize a dynamic feature generation pattern where indicator configuration defines the resulting column names, and those names are programmatically referenced in the strategy. Alternatively, `add_emas` should return a dictionary or configuration object mapping the logical indicator (e.g., `fast_ma`, `slow_ma`) to the physical column name.

Refactored Code:
```python
# utility.py
def add_emas(df: pl.LazyFrame, timeframe_label: str, fast_span: int = 10, slow_span: int = 20) -> tuple[pl.LazyFrame, dict[str, str]]:
    fast_col = f"ema{fast_span}_{timeframe_label}"
    slow_col = f"ema{slow_span}_{timeframe_label}"

    df_new = df.with_columns([
        pl.col("Close").ewm_mean(span=fast_span, ignore_nulls=True).alias(fast_col),
        pl.col("Close").ewm_mean(span=slow_span, ignore_nulls=True).alias(slow_col)
    ])

    return df_new, {"fast": fast_col, "slow": slow_col}

# strategies/universal_ema.py
# (Inside generate_signals)
    base_signals, cols = add_emas(base_df, timeframe_label=self.exec_tf, fast_span=10, slow_span=20)
    fast_col = cols["fast"]
    slow_col = cols["slow"]

    buy_expr = (
        (pl.col(fast_col) > pl.col(slow_col)) &
        (pl.col(fast_col).shift(1).over("Ticker") <= pl.col(slow_col).shift(1).over("Ticker"))
    )
```

## 5. Maintainability

### Issue: Weak Result Abstraction and Missing Trade State Logging
* **Location:** `engine.py:68-80`
* **Severity:** Medium
* **Description:** The core engine's execution loop returns a raw Polars DataFrame with four columns: `Ticker`, `Date`, `Close`, `Profit`. While extremely efficient, it entirely drops the actual Trade Execution context (e.g., Entry Date, Entry Price, Exit Reason (TP/SL/Signal), Duration). Without this granular data, deep quantitative analysis, slippage reconciliation, and strategy debugging are incredibly difficult. The system prints a basic metrics report (`Total_Trades`, `Average`, `Median`), but the raw return value limits integration with external reporting tools or dashboards.

**Current Implementation:**
```python
        return results.filter(pl.col("Profit").is_not_null()).select(
            "Ticker", "Date", "Close", "Profit"
        ).collect()
```

Proposed Solution / Pattern:
Enhance the internal Polars state machine to preserve `Entry_Date`, `Entry_Price`, and the `Exit_Reason`. Return a rich `BacktestResult` Domain Object (DTO) containing the underlying trade ledger dataframe and properties to lazily calculate metrics.

Refactored Code:
```python
# engine.py
from dataclasses import dataclass

@dataclass
class BacktestResult:
    strategy_name: str
    trade_ledger: pl.DataFrame

    def get_metrics(self) -> pl.DataFrame:
        return self.trade_ledger.group_by("Ticker").agg(
            pl.len().alias("Total_Trades"),
            pl.col("Profit").mean().alias("Average_Profit")
        )

# Inside BacktestEngine.run()
        # Retain comprehensive execution state:
        results = strict_executions.with_columns(
            pl.when(pl.col("Action") == -1)
            .then(profit_expr)
            .otherwise(None)
            .alias("Profit"),
            pl.when(pl.col("Hit_TP")).then(pl.lit("TP"))
            .when(pl.col("Hit_SL")).then(pl.lit("SL"))
            .otherwise(pl.lit("Signal"))
            .alias("Exit_Reason")
        )

        final_ledger = results.filter(pl.col("Profit").is_not_null()).select(
            "Ticker", "Active_Entry", "Close", "Profit", "Exit_Reason"
        ).collect()

        return BacktestResult(strategy_name=strategy.name, trade_ledger=final_ledger)
```