# src/core/evaluator/distance.py

from typing import Dict, Tuple, Union
import math

from src.core.models.place import PlaceDetail


class DistanceCalculator:
    """
    距離計算工具類別
    負責處理所有地理位置間的距離計算和相關評估

    主要功能：
    1. 計算兩點間的直線距離
    2. 評估距離是否在可接受範圍內
    3. 提供距離相關的評分依據
    """

    EARTH_RADIUS = 6371  # 地球半徑（公里）

    @classmethod
    def calculate_distance(cls,
                           loc1: Union[Dict[str, float], PlaceDetail],
                           loc2: Union[Dict[str, float], PlaceDetail]) -> float:
        """
        計算兩個地理座標點之間的直線距離
        使用 Haversine 公式計算球面上兩點間的最短距離

        輸入參數:
            loc1: 第一個位置，可以是字典或 PlaceDetail 物件
                如果是字典，需包含：
                - lat: 緯度 (度)
                - lon: 經度 (度)
            loc2: 第二個位置，格式同上

        回傳:
            float: 兩點間的距離（公里）

        使用範例:
            # 使用字典
            loc1 = {"lat": 25.0339808, "lon": 121.561964}  # 台北101

            # 或使用 PlaceDetail 物件
            loc1 = PlaceDetail(name="台北101", lat=25.0339808, lon=121.561964, ...)
        """
        # 取得座標值（支援字典和 PlaceDetail 物件）
        lat1 = loc1['lat'] if isinstance(loc1, dict) else loc1.lat
        lon1 = loc1['lon'] if isinstance(loc1, dict) else loc1.lon
        lat2 = loc2['lat'] if isinstance(loc2, dict) else loc2.lat
        lon2 = loc2['lon'] if isinstance(loc2, dict) else loc2.lon

        # 轉換座標為弧度
        lat1, lon1 = math.radians(lat1), math.radians(lon1)
        lat2, lon2 = math.radians(lat2), math.radians(lon2)

        # 計算緯度和經度的差
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        # Haversine 公式計算
        a = math.sin(dlat/2)**2 + math.cos(lat1) * \
            math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))

        return cls.EARTH_RADIUS * c

    @classmethod
    def get_distance_factor(cls,
                            distance: float,
                            threshold: float) -> float:
        """
        計算距離因子，用於評分調整
        距離越接近閾值，評分越低

        輸入參數:
            distance (float): 實際距離（公里）
            threshold (float): 距離閾值（公里）

        回傳:
            float: 0.0~1.0之間的評分因子
                  1.0 表示距離理想
                  0.0 表示距離太遠
        """
        if distance >= threshold:
            return 0.0
        # 使用反比例函數計算因子
        return 1.0 - (distance / threshold)

    @classmethod
    def calculate_region_bounds(cls,
                                center: Dict[str, float],
                                radius_km: float) -> Tuple[float, float, float, float]:
        """
        計算指定中心點和半徑的區域範圍
        用於快速篩選可能的目標地點

        輸入參數:
            center (Dict): 中心點座標
                - lat: 緯度
                - lon: 經度
            radius_km (float): 半徑（公里）

        回傳:
            Tuple[float, float, float, float]: 
                (min_lat, max_lat, min_lon, max_lon)
                表示區域的緯度和經度範圍
        """
        # 緯度 1 度約 111 公里
        lat_delta = radius_km / 111.0

        # 經度 1 度的實際距離隨緯度變化
        # cos(緯度) * 111.32 公里
        lon_delta = radius_km / \
            (111.32 * math.cos(math.radians(center['lat'])))

        return (
            center['lat'] - lat_delta,  # min_lat
            center['lat'] + lat_delta,  # max_lat
            center['lon'] - lon_delta,  # min_lon
            center['lon'] + lon_delta   # max_lon
        )

    @classmethod
    def is_point_in_bounds(cls,
                           point: Dict[str, float],
                           bounds: Tuple[float, float, float, float]) -> bool:
        """
        檢查一個點是否在指定的區域範圍內

        輸入參數:
            point (Dict): 要檢查的點
                - lat: 緯度
                - lon: 經度
            bounds (Tuple): 區域範圍 (min_lat, max_lat, min_lon, max_lon)

        回傳:
            bool: True 表示點在範圍內，False 表示在範圍外
        """
        min_lat, max_lat, min_lon, max_lon = bounds
        return (min_lat <= point['lat'] <= max_lat and
                min_lon <= point['lon'] <= max_lon)
