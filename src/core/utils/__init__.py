# src/core/utils/__init__.py

"""
工具函數模組
此模組整合了所有通用的工具函數，提供了一個統一且易用的介面

這個模組的設計理念是提供一組完整且一致的工具函數，讓開發者可以方便地處理：
1. 地理位置相關的計算
2. 時間相關的運算和驗證
3. 常用的資料轉換和處理

主要功能區塊：
- 地理計算：距離計算、區域範圍判定等
- 時間處理：格式驗證、區間計算、時段判斷等
- 通用工具：資料轉換、格式化輸出等

使用方式：
    from src.core.utils import calculate_distance, TimeHandler
    
    # 計算兩點間距離
    point1 = {"lat": 25.0478, "lon": 121.5170}  # 台北車站
    point2 = {"lat": 25.0339, "lon": 121.5619}  # 台北101
    distance = calculate_distance(point1, point2)
    
    # 驗證時間格式
    if TimeHandler.validate_time_format("09:30"):
        print("時間格式正確")
"""

from datetime import datetime
from typing import Dict, List, Tuple, Optional, Union

from .geo import GeoCalculator
from .time import TimeHandler


def calculate_distance(point1: Dict[str, float],
                       point2: Dict[str, float]) -> float:
    """
    計算兩個地理座標點之間的距離

    這是一個便捷函數，內部使用 GeoCalculator 進行實際計算。
    對於需要更多地理計算功能的場景，建議直接使用 GeoCalculator 類別。

    輸入參數：
        point1: 第一個點的座標，需包含：
            - lat: 緯度（度）
            - lon: 經度（度）
        point2: 第二個點的座標，格式同上

    回傳：
        float: 兩點間的距離（公里）

    使用範例：
        >>> point1 = {"lat": 25.0478, "lon": 121.5170}  # 台北車站
        >>> point2 = {"lat": 25.0339, "lon": 121.5619}  # 台北101
        >>> distance = calculate_distance(point1, point2)
        >>> print(f"距離：{distance:.2f} 公里")
    """
    return GeoCalculator.calculate_distance(point1, point2)


def format_time_range(start_time: Union[str, datetime.time], 
                      end_time: Union[str, datetime.time]) -> str:
    """
    將時間範圍格式化為字串

    這是一個便捷函數，可以接受字串或 time 物件作為輸入，
    自動進行必要的轉換並返回格式化的時間範圍字串。

    輸入參數：
        start_time: 開始時間（HH:MM格式的字串或 time 物件）
        end_time: 結束時間（格式同上）

    回傳：
        str: 格式化後的時間範圍字串（HH:MM-HH:MM）

    使用範例：
        >>> print(format_time_range("09:00", "17:30"))
        "09:00-17:30"
    """
    # 如果輸入是字串，轉換為 time 物件
    if isinstance(start_time, str):
        start_time = datetime.strptime(start_time, '%H:%M').time()
    if isinstance(end_time, str):
        end_time = datetime.strptime(end_time, '%H:%M').time()

    return TimeHandler.format_time_range(start_time, end_time)


def calculate_region_bounds(center: Dict[str, float],
                            radius_km: float) -> Tuple[float, float, float, float]:
    """
    計算指定區域的邊界範圍

    這是一個便捷函數，用於快速獲取搜尋範圍的邊界。
    對於需要更複雜地理運算的場景，建議使用 GeoCalculator 類別。

    輸入參數：
        center: 中心點座標
            - lat: 緯度（度）
            - lon: 經度（度）
        radius_km: 搜尋半徑（公里）

    回傳：
        Tuple[float, float, float, float]: 
            (最小緯度, 最大緯度, 最小經度, 最大經度)

    使用範例：
        >>> center = {"lat": 25.0478, "lon": 121.5170}  # 台北車站
        >>> bounds = calculate_region_bounds(center, 5)
        >>> min_lat, max_lat, min_lon, max_lon = bounds
    """
    return GeoCalculator.calculate_region_bounds(center, radius_km)


# 導出所有需要的類別和函數
__all__ = [
    'GeoCalculator',
    'TimeHandler',
    'calculate_distance',
    'format_time_range',
    'calculate_region_bounds'
]
