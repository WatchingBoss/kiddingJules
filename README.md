## Project Overview

This project is a high-performance quantitative backtesting framework built in Python using Polars, NumPy, SciPy. It serves as the core research and validation engine for a live market trading signals service. 

The framework is designed to process massive historical datasets efficiently, evaluate technical analysis patterns, and output mathematically rigorous performance metrics.

**Core Capabilities:**
* **Modular Strategy Registry:** A dynamically loaded library of trading algorithms utilizing the Strategy Pattern. It houses all baseline strategies and allows quantitative developers to drop in new indicator logic with zero changes to the core engine.
* **Configurable Execution Engine:** A strictly decoupled backtesting environment that allows for rapid iteration of execution mechanics (e.g., varying buy/sell rules, Stop-Loss/Take-Profit thresholds, and state alternation) without altering the underlying technical analysis.
* **Live-Signal Pipeline:** Engineered to strictly enforce time-series sortedness and eliminate look-ahead bias, ensuring that backtested performance accurately reflects viable signals for the live trading production environment.