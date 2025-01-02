# src/core/utils/cache_decorator.py

from functools import lru_cache, wraps
from typing import Callable, TypeVar, Any

T = TypeVar('T')


def cached(maxsize: int = 128) -> Callable:
    """快取裝飾器

    輸入:
        maxsize: 快取最大容量，預設128筆

    使用範例:
        @cached(maxsize=128)
        def some_function(arg1, arg2):
            # 函數實作
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # 使用 lru_cache
        cached_func = lru_cache(maxsize=maxsize)(func)

        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                return cached_func(*args, **kwargs)
            except Exception as e:
                # 發生錯誤時清除快取
                cached_func.cache_clear()
                raise e

        # 加入清除快取的方法
        wrapper.cache_clear = cached_func.cache_clear
        return wrapper
    return decorator
