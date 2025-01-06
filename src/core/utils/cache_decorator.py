# src/core/utils/cache_decorator.py

from functools import wraps
from typing import Callable, TypeVar, Any, Dict
from datetime import datetime

T = TypeVar('T')  # 定義泛型型別，用於函數回傳值


def cached(maxsize: int = 128) -> Callable:
    """一般用途的快取裝飾器

    用於快取一般函數的回傳值，適用於輸入參數簡單的情況

    輸入參數:
        maxsize: int - 快取的最大容量，超過此容量將移除最舊的項目

    回傳:
        Callable - 裝飾過的函數
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        cache = {}  # 使用字典儲存快取

        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # 產生快取的鍵值
            key = str(args) + str(sorted(kwargs.items()))

            # 如果結果在快取中，直接返回
            if key in cache:
                return cache[key]

            # 執行函數並存入快取
            try:
                result = func(*args, **kwargs)
                cache[key] = result

                # 如果快取太大，移除最舊的項目
                if len(cache) > maxsize:
                    oldest_key = next(iter(cache))
                    del cache[oldest_key]

                return result
            except Exception as e:
                # 如果執行出錯，清除快取並重新拋出異常
                cache.clear()
                raise e

        # 加入清除快取的方法
        wrapper.cache_clear = lambda: cache.clear()
        return wrapper
    return decorator


def geo_cache(maxsize: int = 256):
    """地理位置專用的快取裝飾器"""

    def make_cache_key(func_args: tuple, func_kwargs: dict) -> str:
        """從函數參數建立快取鍵值

        輸入參數:
            func_args: 原始函數的位置參數
            func_kwargs: 原始函數的關鍵字參數

        回傳:
            str: 由座標和交通方式組成的唯一鍵值
        """
        try:
            # 確認是否有足夠的參數（self, origin, destination, ...）
            if len(func_args) < 3:
                return f"default_key_{datetime.now().timestamp()}"

            # 解析座標參數
            origin = func_args[1]
            destination = func_args[2]
            mode = func_args[3] if len(func_args) > 3 else 'driving'

            # 檢查座標格式
            if not isinstance(origin, dict) or not isinstance(destination, dict):
                return f"invalid_format_key_{datetime.now().timestamp()}"

            if 'lat' not in origin or 'lon' not in origin or \
               'lat' not in destination or 'lon' not in destination:
                return f"missing_coord_key_{datetime.now().timestamp()}"

            # 建立標準化的鍵值
            key = (f"{float(origin['lat']):.6f},{float(origin['lon']):.6f}_"
                   f"{float(destination['lat']):.6f},{float(destination['lon']):.6f}_"
                   f"{mode}")

            return key

        except Exception as e:
            print(f"建立快取鍵值時發生錯誤: {str(e)}")
            return f"error_key_{datetime.now().timestamp()}"

    def decorator(func):
        # 使用字典儲存快取
        cache = {}

        @wraps(func)
        def wrapper(*args, **kwargs):
            # 使用 make_cache_key 建立鍵值
            cache_key = make_cache_key(args, kwargs)

            # 檢查快取
            if cache_key in cache:
                print(f"使用快取的路線資訊: {cache_key}")
                return cache[cache_key]

            # 執行原始函數
            result = func(*args, **kwargs)

            # 存入快取
            cache[cache_key] = result
            # print(f"新增路線資訊到快取: {cache_key}")

            # 管理快取大小
            if len(cache) > maxsize:
                oldest_key = next(iter(cache))
                del cache[oldest_key]

            return result

        # 加入輔助方法
        wrapper.cache_clear = lambda: cache.clear()
        wrapper.cache_info = lambda: {
            'size': len(cache),
            'maxsize': maxsize,
            'keys': list(cache.keys())
        }

        return wrapper

    return decorator


# 匯出可用的裝飾器
__all__ = ['cached', 'geo_cache']
