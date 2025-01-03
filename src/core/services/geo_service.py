# src/core/services/geo_service.py

import math
from typing import Dict


class GeoService:
    """地理服務

    功能職責：
    1. 提供所有地理位置相關的計算
    2. 驗證座標的正確性
    3. 管理地理區域範圍

    主要使用場景：
    1. 計算兩地點間距離
    2. 檢查地點是否在指定範圍
    3. 尋找特定範圍內的地點
    """

    EARTH_RADIUS = 6371.0087714  # 地球平均半徑(公里)

    @classmethod
    def validate_coordinates(cls, lat: float, lon: float) -> bool:
        """驗證座標是否有效

        輸入:
            lat: 緯度, 範圍必須是 -90 到 90 度
            lon: 經度, 範圍必須是 -180 到 180 度

        回傳:
            bool: True=有效, False=無效

        使用範例:
            >>> GeoService.validate_coordinates(25.0, 121.5)
            True
            >>> GeoService.validate_coordinates(91.0, 121.5)  
            False
        """
        try:
            return -90 <= float(lat) <= 90 and -180 <= float(lon) <= 180
        except (TypeError, ValueError):
            return False

    @classmethod
    def calculate_distance(cls, point1: Dict[str, float], point2: Dict[str, float]) -> float:
        """計算兩點間直線距離(Haversine公式)

        輸入:
            point1: 第一個點的座標 {'lat': float, 'lon': float}
            point2: 第二個點的座標 {'lat': float, 'lon': float}

        回傳:
            float: 兩點間距離(公里)

        錯誤:
            ValueError: 當座標格式錯誤或超出範圍

        使用範例:
            >>> p1 = {'lat': 25.0, 'lon': 121.5}
            >>> p2 = {'lat': 25.1, 'lon': 121.6}
            >>> GeoService.calculate_distance(p1, p2)
            15.7
        """
        # 驗證座標
        for p in [point1, point2]:
            if not cls.validate_coordinates(p['lat'], p['lon']):
                raise ValueError(f"無效的座標: {p}")

        # 轉換為弧度
        lat1 = math.radians(point1['lat'])
        lon1 = math.radians(point1['lon'])
        lat2 = math.radians(point2['lat'])
        lon2 = math.radians(point2['lon'])

        # Haversine 公式
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = (math.sin(dlat/2)**2 +
             math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2)
        c = 2 * math.asin(math.sqrt(a))

        return round(cls.EARTH_RADIUS * c, 1)

    @classmethod
    def calculate_bounds(cls, center: Dict[str, float], radius_km: float) -> Dict[str, float]:
        """計算指定半徑的範圍邊界

        輸入:
            center: 中心點座標 {'lat': float, 'lon': float}
            radius_km: 半徑(公里)

        回傳:
            dict: {
                'min_lat': float,  # 最小緯度
                'max_lat': float,  # 最大緯度
                'min_lon': float,  # 最小經度
                'max_lon': float   # 最大經度
            }

        錯誤:
            ValueError: 當座標無效或半徑為負

        使用範例:
            >>> center = {'lat': 25.0, 'lon': 121.5}
            >>> GeoService.calculate_bounds(center, 10)
            {
                'min_lat': 24.91, 
                'max_lat': 25.09,
                'min_lon': 121.41,
                'max_lon': 121.59
            }
        """
        if not cls.validate_coordinates(center['lat'], center['lon']):
            raise ValueError(f"無效的中心點座標: {center}")

        if radius_km <= 0:
            raise ValueError(f"半徑必須大於0: {radius_km}")

        # 計算緯度變化(1度緯度約111公里)
        lat_change = radius_km / 111.0

        # 計算經度變化(依據緯度調整)
        lon_change = radius_km / \
            (111.0 * math.cos(math.radians(center['lat'])))

        return {
            'min_lat': round(center['lat'] - lat_change, 6),
            'max_lat': round(center['lat'] + lat_change, 6),
            'min_lon': round(center['lon'] - lon_change, 6),
            'max_lon': round(center['lon'] + lon_change, 6)
        }

    @classmethod
    def is_point_in_bounds(cls, point: Dict[str, float], bounds: Dict[str, float]) -> bool:
        """檢查點是否在範圍內

        輸入:
            point: 要檢查的點 {'lat': float, 'lon': float}
            bounds: 範圍 {
                'min_lat': float,
                'max_lat': float, 
                'min_lon': float,
                'max_lon': float
            }

        回傳:
            bool: True=在範圍內, False=不在範圍內

        使用範例:
            >>> point = {'lat': 25.0, 'lon': 121.5}
            >>> bounds = {
                    'min_lat': 24.9,
                    'max_lat': 25.1,
                    'min_lon': 121.4,
                    'max_lon': 121.6
                }
            >>> GeoService.is_point_in_bounds(point, bounds)
            True
        """
        if not cls.validate_coordinates(point['lat'], point['lon']):
            return False

        return (bounds['min_lat'] <= point['lat'] <= bounds['max_lat'] and
                bounds['min_lon'] <= point['lon'] <= bounds['max_lon'])
