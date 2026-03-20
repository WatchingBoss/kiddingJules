1. [Abstract Data Dependency and Validation]
   a. Step 1. `main.py`:`check_source_parquet` (Lines 15-28) | We have: A hardcoded dictionary of tickers (`{'GAZP': 1_812_503, 'SBER': ...}`) and exact expected row counts embedded directly inside the `main.py` validation logic. The system scans the entire dataset synchronously to validate length before running, causing extreme overhead. -> Solution: Extract the static ticker data to `config.yaml`. Implement a separate `DataLoader` class in `utility.py` (or `data.py`) responsible for configuration loading and validation using lazy Polars evaluation (`.select(pl.len())`).

      ```python
      # New DataLoader Example
      import json
      from pathlib import Path
      import polars as pl
      from config import PARQUET_SOURCE_DIR

      class DataLoader:
          def __init__(self, config_path: str):
              with open(config_path, 'r') as f:
                  self.config = json.load(f)

          def load_and_validate(self) -> pl.LazyFrame:
              lf = pl.scan_parquet(f"{PARQUET_SOURCE_DIR}/**/*.parquet")
              for ticker, expected_count in self.config['tickers'].items():
                  count = lf.filter(pl.col("Ticker") == ticker).select(pl.len()).collect().item()
                  if count != expected_count:
                      raise ValueError(f"Data invalid for {ticker}")
              return lf
      ```

   b. Step 2. `main.py`:`main` (Lines 32-35) | We have: The application overrides configuration paths and calls the hardcoded validator directly. -> Solution: Remove the explicit dictionary declaration entirely. Instantiate `DataLoader('config.json')`, call `.load_and_validate()`, and pass the resulting dynamic `LazyFrame` into the `BacktestEngine`.

2. [Parameterize Indicator Generation to Eliminate Hardcoded Strings]
   a. Step 1. `utility.py`:`add_emas` (Lines 29-35) | We have: EMA lengths (10 and 20) are permanently hardcoded inside the F-strings defining the column names (`f"ema10_{timeframe_label}"`). -> Solution: Add `fast_span: int` and `slow_span: int` arguments. Generate dynamic column names inside the method and return them in a dictionary mapping alongside the `LazyFrame`.

      ```python
      def add_emas(df: pl.LazyFrame, timeframe_label: str, fast_span: int, slow_span: int) -> tuple[pl.LazyFrame, dict]:
          fast_col = f"ema{fast_span}_{timeframe_label}"
          slow_col = f"ema{slow_span}_{timeframe_label}"

          df_new = df.with_columns([
              pl.col("Close").ewm_mean(span=fast_span, ignore_nulls=True).alias(fast_col),
              pl.col("Close").ewm_mean(span=slow_span, ignore_nulls=True).alias(slow_col)
          ])
          return df_new, {"fast": fast_col, "slow": slow_col}
      ```

   b. Step 2. `strategies/universal_ema.py`:`generate_signals` (Lines 26-52) | We have: Rigid expressions relying on hardcoded `.col(f"ema10_{self.exec_tf}")`. -> Solution: Update `UniversalEmaStrategy.__init__` to require `fast_span` and `slow_span`. Use the mapping returned by the newly refactored `add_emas` to dynamically construct `buy_expr` and `sell_expr` filters.

   c. Step 3. `strategies/triple_ema_cross.py`:`generate_signals` (Lines 11-66) | We have: The same string rigidity as the Universal strategy, breaking DRY principles. -> Solution: Apply the exact same dependency injection logic here. Pass the spans down into `add_emas`, retrieve the active column strings, and parameterize the boolean mask expressions.

3. [Decouple the Strategy Registry and Dependencies]
   a. Step 1. `strategies/__init__.py`: (Lines 8-14) | We have: Highly obfuscated dynamic file loading utilizing `pkgutil` and `importlib` which bypasses explicit imports and breaks IDE static analysis. -> Solution: Delete the "magic" module iteration block completely. Replace it with explicit static imports that naturally trigger the `@register` decorators.

      ```python
      # strategies/__init__.py
      from .universal_ema import UniversalEmaStrategy
      from .triple_ema_cross import TripleEMAStrategy
      ```

4. [Enhance Configuration Boundaries in Engine Execution]
   a. Step 1. `engine.py`:`BacktestEngine.run` (Line 7) | We have: The engine signature accepts loose primitive values (`tp_pct: float = None, sl_pct: float = None`), tightly coupling the execution loop to those exact parameters. -> Solution: Implement an `ExecutionConfig` Parameter Object pattern. Pass a single typed configuration object containing spans, TP/SL arrays, and timeframe specifications.

      ```python
      from dataclasses import dataclass
      from typing import Optional

      @dataclass
      class ExecutionConfig:
          fast_span: int
          slow_span: int
          tp_pct: Optional[float]
          sl_pct: Optional[float]
          timeframe: str
      ```

   b. Step 2. `engine.py`:`BacktestEngine.run` (Lines 30-41) | We have: Evaluation boolean expressions that read directly from the signature's standalone parameters. -> Solution: Update the internal state machine boolean logic to reference `config.tp_pct` and `config.sl_pct`.

5. [Build the Parameter Permutation Generator]
   a. Step 1. `utility.py`:`generate_ema_grid` (Lines 38-60) | We have: A basic array generator that loops through hardcoded states but lacks any ability to permute EMA spans or varying exit thresholds. -> Solution: Delete the current implementation. Replace it with a robust `GridSearchFactory` utilizing `itertools.product` to yield an exhaustive iterable of `ExecutionConfig` combinations.

      ```python
      import itertools

      def build_parameter_grid() -> list[ExecutionConfig]:
          spans = [(9, 21), (10, 20), (50, 200)]
          tps = [0.005, 0.01]
          sls = [0.002, 0.005]
          timeframes = ["5m", "15m"]

          grid = []
          for (fast, slow), tp, sl, tf in itertools.product(spans, tps, sls, timeframes):
              grid.append(ExecutionConfig(fast_span=fast, slow_span=slow, tp_pct=tp, sl_pct=sl, timeframe=tf))
          return grid
      ```

6. [Abstract Backtest Results and Final Reporting]
   a. Step 1. `engine.py`:`BacktestEngine.run` (Lines 80-100) | We have: The `run` command dumps a raw Polars DataFrame out to `main.py` stripping away vital configuration context. -> Solution: Encapsulate the raw ledger inside a `BacktestResult` DTO mapping the specific `ExecutionConfig` parameters directly to its corresponding trade ledger output.

   b. Step 2. `engine.py`:`report_metrics` (Lines 114-129) | We have: A static method simply printing an isolated strategy's performance to `stdout`. -> Solution: Transition this function into a method on the `BacktestResult` object (`get_metrics()`). Have it return a summarized, single-row `pl.DataFrame` containing the key metrics (Revenue, Pos/Neg) *and* the configuration variables that generated it.

   c. Step 3. `main.py`:`main` (Lines 44-54) | We have: An iteration over a pre-defined subset of 4 manual strategies that blindly calls `engine.report_metrics()`. -> Solution: Import and loop over `build_parameter_grid()`. Execute each permutation natively, track the returned DTO, and append its `.get_metrics()` DataFrame to a master list.

   d. Step 4. `main.py`:`main` (End of file) | We have: The application terminates after printing isolated strategy reports. -> Solution: Concatenate the final aggregated array using `pl.concat(all_metrics)`. Sort the entire table comprehensively by profitability using `.sort("Total_Revenue", descending=True)` to surface the absolute best parameter permutations to the user.

      ```python
      # main.py execution loop
      all_results = []
      grid = build_parameter_grid()

      for config in grid:
          strategy = UniversalEmaStrategy(config)
          result = engine.run(strategy, config)
          all_results.append(result.get_metrics())

      master_leaderboard = pl.concat(all_results).sort("Total_Revenue", descending=True)
      print(master_leaderboard)
      ```