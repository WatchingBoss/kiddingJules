from abc import ABC, abstractmethod
import polars as pl


class BaseStrategy(ABC):
    """Abstract Base Class defining the contract for all trading strategies."""
    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the strategy for reporting."""
        pass

    @abstractmethod
    def generate_signals(self, df_1m: pl.LazyFrame) -> pl.LazyFrame:
        """
        Takes raw 1m OHLCV data, calculates indicators, applies rules,
        and returns a LazyFrame with 'Buy_Signal' and 'Sell_Signal' boolean columns.
        """
        pass
