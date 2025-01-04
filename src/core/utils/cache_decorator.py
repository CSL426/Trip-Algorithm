# src/core/utils/cache_decorator.py

from functools import lru_cache, wraps
from typing import Callable, TypeVar, Any

T = TypeVar('T')


def cached(maxsize: int = 128) -> Callable:
    """一般的快取裝飾器"""
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


def geo_cache(maxsize: int = 128) -> Callable:
    """地理位置快取裝飾器，能處理包含座標的字典"""
    def make_cache_key(*args, **kwargs) -> str:
        """生成快取的鍵值"""
        if len(args) >= 3:
            origin, destination, mode = args[1:4]  # 跳過 self 參數
            return f"{origin['lat']},{origin['lon']}_{destination['lat']},{destination['lon']}_{mode}"
        return str(hash(str(args) + str(sorted(kwargs.items()))))

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # 創建快取字典
        cache = {}

        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            key = make_cache_key(*args, **kwargs)

            # 如果結果在快取中，直接返回
            if key in cache:
                return cache[key]

            # 否則執行函數並存入快取
            result = func(*args, **kwargs)
            cache[key] = result

            # 如果快取太大，移除最舊的項目
            if len(cache) > maxsize:
                cache.pop(next(iter(cache)))

            return result

        # 加入清除快取的方法
        def clear_cache():
            cache.clear()

        wrapper.cache_clear = clear_cache
        return wrapper

    return decorator


__all__ = ['cached', 'geo_cache']
