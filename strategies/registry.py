from typing import Type
from strategies.base import BaseStrategy


_REGISTRY: dict[str, Type[BaseStrategy]] = {}


def register(cls: Type[BaseStrategy]) -> Type[BaseStrategy]:
    """Class decorator that auto-registers a strategy."""
    _REGISTRY[cls.name] = cls
    return cls

def get_strategy(name: str) -> BaseStrategy:
    if name not in _REGISTRY:
        raise KeyError(f"Unknown strategy '{name}'. Available: {list(_REGISTRY)}")
    return _REGISTRY[name]()

def all_strategies() -> list[BaseStrategy]:
    return [cls() for cls in _REGISTRY.values()]