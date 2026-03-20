# Project Overview & State
The current project is a Polars-based, highly efficient vectorized Python backtesting engine focused on EMA crossover logic. It consists of a decoupled `BacktestEngine`, a Strategy Registry pattern for defining and discovering strategies (`UniversalEMAStrategy`, `TripleEMAStrategy`), and helper functions (`utility.py`) for data resampling and indicator generation. The system correctly evaluates strict execution states (handling intraday race conditions pessimistically), tracks granular trade metrics (Open/Close Dates, Profits, Exit Reasons), and returns aggregate performance metrics per ticker. However, the current execution flow in `main.py` is rigid, testing only a small, hardcoded list of strategy variations with a fixed 0.5% Take Profit (TP) and 0.2% Stop Loss (SL).

## 1. Percentage of Completion
**Estimated Completion: 70%**

- **Implemented:** The core high-performance evaluation engine (vectorized signal generation, strict state machine transitions, exact profit calculation, and multi-timeframe alignment) is built, accurate, and robust. The framework also properly abstracts indicator calculation and logging.
- **Missing:** The system lacks an automated parameter permutation sweeping mechanism (grid search) for variable EMA lengths, configurable TP/SL combinations, and dynamic timeframe injection.
- **Missing:** The final reporting layer does not yet aggregate the results from all executed permutations into a global leaderboard sorted by Total Revenue.

## 2. Big Tasks to Solve
- **Dynamic Indicator Configuration:** Refactor `utility.py` (`add_emas`) and the strategy implementations to accept parameterized fast and slow EMA spans (e.g., 9/21, 10/20, 50/200) instead of hardcoding `ema10` and `ema20` string names.
- **Parameter Permutation Generator:** Build a robust Grid Search or combinatorial factory using `itertools.product` that can systematically yield all desired combinations of EMA spans, TP/SL percentages, and execution timeframes.
- **Execution Loop Overhaul:** Modify `main.py` to iterate over the generated permutations rather than a hardcoded list, capturing the resulting metrics (`Total_Revenue`, `Pos/Neg_Ratio`, etc.) for every single combination.
- **Global Result Aggregation & Ranking:** Abstract the metrics output returned by `engine.report_metrics` so that results from individual strategy runs can be concatenated into a master DataFrame. Finally, sort this global DataFrame by `Total_Revenue` in descending order to identify the most profitable strategy combinations.

## 3. Vision & Architecture Implementation

- **Design Patterns:**
  - **Strategy Pattern:** Already partially implemented via `BaseStrategy`. Continue using this to encapsulate the distinct technical analysis logic.
  - **Parameter Object/DTO Pattern:** Implement an `ExecutionConfig` or `StrategyParams` `dataclass` to cleanly pass combinations of parameters (EMA fast, EMA slow, TP pct, SL pct, execution timeframe) into both the strategies and the engine, decoupling the engine's signature from arbitrary arguments.
  - **Factory Pattern:** Enhance `utility.py`'s existing `generate_ema_grid` (or create a new `ParameterGridFactory`) to yield instantiated strategy objects paired with their specific `ExecutionConfig` to feed into the testing loop.

- **Architecture:**
  - **Data Flow:** The engine should remain strictly vectorized. To handle the parameter sweep efficiently, ensure the raw underlying 1m Parquet dataset is loaded lazily (`pl.scan_parquet`) and only collected exactly when required by a specific permutation.
  - **Result Management:** Instead of printing metrics continuously in the `main` loop, the `engine.run()` method should return a domain object (e.g., `BacktestResult`). A dedicated `ReportGenerator` component should collect these results, build a global Polars DataFrame, and execute the final sorting operations (`.sort("Total_Revenue", descending=True)`).

- **Best Practices:**
  - **Performance:** For massive parameter sweeps, evaluating every permutation sequentially can be slow. Utilize Python's `concurrent.futures.ProcessPoolExecutor` to parallelize the backtest runs across multiple CPU cores, passing each strategy combination to an isolated worker process.
  - **Look-ahead Bias Prevention:** Maintain the strict forward-shifting mechanisms already implemented in `resample_candles` and the `engine.py` execution logic. Ensure any new parameterized higher-timeframe filters continue to shift indicator data before performing `join_asof`.
  - **Separation of Concerns:** Keep configuration (`config.py` or `.yaml`) entirely distinct from execution logic. Extract the hardcoded tickers (`GAZP`, `SBER`) in `main.py` into a data loader configuration so the system scales dynamically to any asset list.