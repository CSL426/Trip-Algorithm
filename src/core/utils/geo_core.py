# src/core/utils/geo_core.py

import math
from typing import Dict, Tuple, Union


class GeoCore:
    """地理位置計算核心類別

    負責所有基礎的地理運算：
    1. 距離計算
    2. 座標驗證
    3. 區域範圍計算
    """

    EARTH_RADIUS = 6371.0087714  # 地球平均半徑(公里)

    @classmethod
    def validate_coordinate(cls, lat: float, lon: float) -> None:
        """驗證座標有效性

        輸入:
            lat: 緯度(-90到90)
            lon: 經度(-180到180)

        異常:
            ValueError: 座標超出範圍
        """
        if not -90 <= lat <= 90:
            raise ValueError(f"緯度必須在-90到90度之間：{lat}")
        if not -180 <= lon <= 180:
            raise ValueError(f"經度必須在-180到180度之間：{lon}")

    @classmethod
    def calculate_distance(cls, loc1: Dict[str, float], loc2: Dict[str, float]) -> float:
        """計算兩點間距離

        輸入:
            loc1: 第一個位置，需包含 lat 和 lon
            loc2: 第二個位置，需包含 lat 和 lon

        回傳:
            float: 距離(公里)
        """
        # 取得座標
        lat1 = loc1['lat']
        lon1 = loc1['lon']
        lat2 = loc2['lat']
        lon2 = loc2['lon']

        # 驗證座標
        cls.validate_coordinate(lat1, lon1)
        cls.validate_coordinate(lat2, lon2)

        # 轉弧度
        lat1, lon1 = math.radians(lat1), math.radians(lon1)
        lat2, lon2 = math.radians(lat2), math.radians(lon2)

        # Haversine 公式
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = (math.sin(dlat/2)**2 +
             math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2)
        c = 2 * math.asin(math.sqrt(a))

        return cls.EARTH_RADIUS * c

    @classmethod
    def calculate_region_bounds(cls,
                                center: Dict[str, float],
                                radius_km: float) -> Tuple[float, float, float, float]:
        """計算搜尋區域範圍

        輸入:
            center: 中心點座標
            radius_km: 搜尋半徑(公里)

        回傳:
            Tuple[float, float, float, float]: (min_lat, max_lat, min_lon, max_lon)
        """
        lat_delta = radius_km / 111.0
        lon_delta = radius_km / \
            (111.32 * math.cos(math.radians(center['lat'])))

        return (
            center['lat'] - lat_delta,
            center['lat'] + lat_delta,
            center['lon'] - lon_delta,
            center['lon'] + lon_delta
        )
