# src/core/utils/cache_decorator.py

from functools import lru_cache, wraps
from typing import Callable, TypeVar, Any

T = TypeVar('T')


def cached(maxsize: int = 128, timeout: int = 3600) -> Callable:
    """快取裝飾器，加入超時機制"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        cached_func = lru_cache(maxsize=maxsize)(func)

        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                return cached_func(*args, **kwargs)
            except Exception as e:
                cached_func.cache_clear()
                raise e

        wrapper.cache_clear = cached_func.cache_clear
        return wrapper
    return decorator
