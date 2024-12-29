# src/core/utils/geo.py

"""
地理位置工具模組
此模組提供所有與地理位置計算相關的工具函數

主要功能：
1. 計算地理座標間的距離
2. 地理區域範圍的計算
3. 路徑和路線相關的運算
"""

import math
from typing import Dict, Tuple, List, Union

from src.core.models.place import PlaceDetail


class GeoCalculator:
    """
    地理計算工具類別
    提供各種地理位置相關的計算功能

    這個類別使用了地球橢球體模型來進行各種地理計算，
    確保在實際應用中有足夠的精確度
    """

    # 地球的參數（WGS84橢球體模型）
    EARTH_RADIUS = 6371.0087714  # 地球平均半徑（公里）

    @staticmethod
    def _validate_coordinate(lat: float, lon: float) -> None:
        """
        驗證座標的有效性

        輸入參數:
            lat (float): 緯度，必須在 -90 到 90 度之間
            lon (float): 經度，必須在 -180 到 180 度之間

        異常:
            ValueError: 當座標超出有效範圍時拋出錯誤
        """
        if not -90 <= lat <= 90:
            raise ValueError(f"緯度必須在 -90 到 90 度之間：{lat}")
        if not -180 <= lon <= 180:
            raise ValueError(f"經度必須在 -180 到 180 度之間：{lon}")

    @classmethod
    def calculate_distance(cls, loc1: Union[Dict[str, float], PlaceDetail],
                           loc2: Union[Dict[str, float], PlaceDetail]) -> float:
        """
        計算兩個地理座標點之間的距離
        使用 Haversine 公式計算球面上的最短距離

        運作原理：
        1. 將經緯度轉換為弧度
        2. 使用 Haversine 公式計算球面距離
        3. 考慮地球曲率進行修正

        輸入參數：
            loc1: 第一個位置 (PlaceDetail物件或包含lat/lon的字典)
            loc2: 第二個位置 (PlaceDetail物件或包含lat/lon的字典)

        回傳：
            float: 兩點間的距離（公里）

        使用範例：
            >>> loc1 = {"lat": 25.0478, "lon": 121.5170}  # 台北車站
            >>> loc2 = {"lat": 25.0339, "lon": 121.5619}  # 台北101
            >>> distance = GeoCalculator.calculate_distance(loc1, loc2)
            >>> print(f"距離：{distance:.2f} 公里")
        """
        # 取得座標值（支援字典和PlaceDetail物件）
        lat1 = loc1['lat'] if isinstance(loc1, dict) else loc1.lat
        lon1 = loc1['lon'] if isinstance(loc1, dict) else loc1.lon
        lat2 = loc2['lat'] if isinstance(loc2, dict) else loc2.lat
        lon2 = loc2['lon'] if isinstance(loc2, dict) else loc2.lon

        # 驗證座標
        cls._validate_coordinate(lat1, lon1)
        cls._validate_coordinate(lat2, lon2)

        # 轉換為弧度
        lat1, lon1 = math.radians(lat1), math.radians(lon1)
        lat2, lon2 = math.radians(lat2), math.radians(lon2)

        # 計算差值
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        # Haversine 公式
        a = (math.sin(dlat/2)**2 +
             math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        return cls.EARTH_RADIUS * c

    @classmethod
    def calculate_region_bounds(cls,
                                center: Dict[str, float],
                                radius_km: float) -> Tuple[float, float, float, float]:
        """
        計算以指定點為中心的區域範圍

        運作原理：
        1. 考慮地球曲率影響
        2. 計算緯度和經度的變化範圍
        3. 產生一個矩形的邊界範圍

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
            >>> bounds = GeoCalculator.calculate_region_bounds(center, 5)
            >>> print(f"搜尋範圍：北緯 {bounds[0]:.4f} 到 {bounds[1]:.4f}")
            >>> print(f"          東經 {bounds[2]:.4f} 到 {bounds[3]:.4f}")
        """
        # 緯度 1 度約 111 公里
        lat_change = radius_km / 111.0

        # 經度 1 度的實際距離隨緯度變化
        # cos(緯度) * 111.32 公里
        lon_change = radius_km / (111.32 *
                                  math.cos(math.radians(center['lat'])))

        return (
            center['lat'] - lat_change,  # 最小緯度
            center['lat'] + lat_change,  # 最大緯度
            center['lon'] - lon_change,  # 最小經度
            center['lon'] + lon_change   # 最大經度
        )

    @classmethod
    def is_point_in_bounds(cls,
                           point: Dict[str, float],
                           bounds: Tuple[float, float, float, float]) -> bool:
        """
        檢查一個點是否在指定的區域範圍內

        運作原理：
        檢查點的緯度和經度是否都在邊界範圍內

        輸入參數：
            point: 要檢查的點座標
                - lat: 緯度（度）
                - lon: 經度（度）
            bounds: 區域範圍 (min_lat, max_lat, min_lon, max_lon)

        回傳：
            bool: True 表示點在範圍內，False 表示在範圍外

        使用範例：
            >>> point = {"lat": 25.0339, "lon": 121.5619}  # 台北101
            >>> bounds = GeoCalculator.calculate_region_bounds(
            ...     {"lat": 25.0478, "lon": 121.5170}, 5)
            >>> if GeoCalculator.is_point_in_bounds(point, bounds):
            ...     print("地點在搜尋範圍內")
        """
        min_lat, max_lat, min_lon, max_lon = bounds
        return (min_lat <= point['lat'] <= max_lat and
                min_lon <= point['lon'] <= max_lon)

    @classmethod
    def calculate_midpoint(cls,
                           points: List[Dict[str, float]]) -> Dict[str, float]:
        """
        計算多個地理座標點的中心點

        運作原理：
        1. 將所有點轉換為 3D 笛卡爾座標
        2. 計算平均位置
        3. 轉換回地理座標

        輸入參數：
            points: 地理座標點列表，每個點需包含：
                - lat: 緯度（度）
                - lon: 經度（度）

        回傳：
            Dict[str, float]: 中心點座標
                - lat: 緯度（度）
                - lon: 經度（度）

        使用範例：
            >>> points = [
            ...     {"lat": 25.0478, "lon": 121.5170},  # 台北車站
            ...     {"lat": 25.0339, "lon": 121.5619},  # 台北101
            ...     {"lat": 25.0330, "lon": 121.5400}   # 大安森林公園
            ... ]
            >>> center = GeoCalculator.calculate_midpoint(points)
            >>> print(f"中心點：北緯 {center['lat']:.4f}, 東經 {center['lon']:.4f}")
        """
        if not points:
            raise ValueError("點位列表不能為空")

        # 將經緯度轉換為弧度
        points_rad = [(math.radians(p['lat']), math.radians(p['lon']))
                      for p in points]

        # 轉換為 3D 笛卡爾座標
        x = y = z = 0
        for lat, lon in points_rad:
            x += math.cos(lat) * math.cos(lon)
            y += math.cos(lat) * math.sin(lon)
            z += math.sin(lat)

        # 計算平均位置
        x /= len(points)
        y /= len(points)
        z /= len(points)

        # 轉換回地理座標
        center_lon = math.atan2(y, x)
        hyp = math.sqrt(x * x + y * y)
        center_lat = math.atan2(z, hyp)

        return {
            'lat': math.degrees(center_lat),
            'lon': math.degrees(center_lon)
        }
