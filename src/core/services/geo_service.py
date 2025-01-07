# src/core/services/geo_service.py

from datetime import datetime
from typing import Dict, List, Tuple, Optional, Union
import math
import googlemaps
from ..models.place import PlaceDetail
from ..utils.cache_decorator import geo_cache
from ...config import GOOGLE_MAPS_API_KEY


class GeoService:
    """地理服務類別

    這個服務負責處理所有地理位置相關的運算，包括：
    1. 基礎距離計算（使用 Haversine 公式）
    2. Google Maps 路線規劃（包含備用方案）
    3. 座標驗證和區域管理
    4. 智能快取機制

    設計考量：
    - 提供穩定可靠的地理計算功能
    - 在 API 失敗時有合適的備用方案
    - 透過快取減少 API 呼叫次數
    - 支援多種交通方式的路線規劃
    """

    # 地球半徑（公里）
    EARTH_RADIUS = 6371.0087714

    # 預設的移動速度（公里/小時）
    DEFAULT_SPEEDS = {
        'driving': 40,    # 開車
        'transit': 30,    # 大眾運輸
        'walking': 5,     # 步行
        'bicycling': 15   # 騎自行車
    }

    def __init__(self):
        """初始化地理服務"""
        try:
            self.maps_client = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
            self.has_google_maps = True
        except Exception as e:
            print(f"警告：Google Maps 服務初始化失敗: {str(e)}")
            self.has_google_maps = False

    def calculate_distance(self,
                           point1: Dict[str, float],
                           point2: Dict[str, float]) -> float:
        """計算兩點間的直線距離

        使用 Haversine 公式計算地球表面上兩點間的最短距離。
        這個方法總是可用，作為路線規劃的備用方案。

        參數:
            point1: 第一個點的座標 {'lat': float, 'lon': float}
            point2: 第二個點的座標 {'lat': float, 'lon': float}

        回傳:
            float: 兩點間的距離（公里）

        使用範例:
            >>> p1 = {'lat': 25.0, 'lon': 121.5}
            >>> p2 = {'lat': 25.1, 'lon': 121.6}
            >>> distance = geo_service.calculate_distance(p1, p2)
        """
        # 驗證座標
        if not all(self.validate_coordinates(p['lat'], p['lon'])
                   for p in [point1, point2]):
            raise ValueError("無效的座標")

        # 轉換為弧度
        lat1 = math.radians(point1['lat'])
        lon1 = math.radians(point1['lon'])
        lat2 = math.radians(point2['lat'])
        lon2 = math.radians(point2['lon'])

        # Haversine 公式計算
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = (math.sin(dlat/2)**2 +
             math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2)
        c = 2 * math.asin(math.sqrt(a))

        return round(self.EARTH_RADIUS * c, 1)

    @geo_cache(maxsize=256)
    def get_route(self,
                  origin: Dict[str, float],
                  destination: Dict[str, float],
                  mode: str = 'driving',
                  departure_time: Optional[datetime] = None) -> Dict:
        """規劃兩點間的路線

        輸入參數:
            origin: Dict - 起點座標 {'lat': float, 'lon': float}
            destination: Dict - 終點座標 {'lat': float, 'lon': float}
            mode: str - 交通方式('driving'/'transit'/'walking'/'bicycling')
            departure_time: Optional[datetime] - 出發時間，預設為當前時間

        回傳:
            Dict: {
                'distance_km': float,     # 預估距離（公里）
                'duration_minutes': int,   # 預估時間（分鐘）
                'route_info': Dict,       # Google Maps 路線資訊
                'transport_mode': str     # 使用的交通方式
            }

        若 API 呼叫失敗，會使用直線距離預估
        """
        try:
            if self.has_google_maps:
                return self._get_google_maps_route(origin, destination, mode, departure_time)
        except Exception as e:
            print(f"警告：Google Maps 路線規劃失敗，切換到備用方案: {str(e)}")

        # API 失敗時使用預估方式
        return self._calculate_estimated_travel_info(origin, destination, mode)

    def _get_google_maps_route(self,
                               origin: Dict[str, float],
                               destination: Dict[str, float],
                               mode: str,
                               departure_time: Optional[datetime]) -> Dict:
        """使用 Google Maps API 取得路線規劃"""
        # 確保出發時間是未來時間
        if departure_time is None or departure_time < datetime.now():
            departure_time = datetime.now()

        # 轉換座標格式
        origin_str = f"{origin['lat']},{origin['lon']}"
        dest_str = f"{destination['lat']},{destination['lon']}"

        # 呼叫 Google Maps API
        result = self.maps_client.directions(
            origin=origin_str,
            destination=dest_str,
            mode=mode,
            departure_time=departure_time
        )

        if not result:
            raise RuntimeError("無法取得路線資訊")

        # 解析結果
        leg = result[0]['legs'][0]
        return {
            'distance_km': leg['distance']['value'] / 1000,
            'duration_minutes': int(leg['duration']['value'] / 60),
            'route_info': result[0],
            'is_estimated': False,
            'transport_mode': mode
        }

    def _get_estimated_route(self,
                             origin: Dict[str, float],
                             destination: Dict[str, float],
                             mode: str) -> Dict:
        """使用直線距離估算路線"""
        # 計算直線距離
        distance = self.calculate_distance(origin, destination)

        # 根據交通方式計算預估時間
        speed = self.DEFAULT_SPEEDS.get(mode, self.DEFAULT_SPEEDS['driving'])
        duration = (distance / speed) * 60  # 轉換為分鐘

        # 加入路程曲折的修正係數（實際路程通常比直線距離長）
        distance_factor = 1.3 if mode == 'driving' else 1.2
        time_factor = 1.4 if mode == 'driving' else 1.3

        return {
            'distance_km': round(distance * distance_factor, 1),
            'duration_minutes': int(duration * time_factor),
            'route_info': None,
            'is_estimated': True,
            'transport_mode': mode
        }

    def validate_coordinates(self, lat: float, lon: float) -> bool:
        """驗證座標是否有效

        檢查座標值是否在合理範圍內：
        - 緯度：-90 到 90 度
        - 經度：-180 到 180 度

        參數:
            lat: 緯度
            lon: 經度

        回傳:
            bool: True 表示座標有效，False 表示無效
        """
        try:
            return (-90 <= float(lat) <= 90 and
                    -180 <= float(lon) <= 180)
        except (TypeError, ValueError):
            return False

    def calculate_bounds(self,
                         center: Dict[str, float],
                         radius_km: float) -> Dict[str, float]:
        """計算指定半徑的範圍邊界

        給定一個中心點和半徑，計算出一個矩形範圍的邊界座標。
        這個功能通常用於：
        1. 尋找特定範圍內的景點
        2. 限制搜尋範圍來優化查詢
        3. 在地圖上顯示可行的活動範圍

        參數:
            center: 中心點座標 {'lat': float, 'lon': float}
            radius_km: 半徑（公里）

        回傳:
            Dict: {
                'min_lat': float,  # 最小緯度
                'max_lat': float,  # 最大緯度
                'min_lon': float,  # 最小經度
                'max_lon': float   # 最大經度
            }

        使用範例:
            >>> # 計算以台北車站為中心，10公里範圍的邊界
            >>> center = {'lat': 25.0478, 'lon': 121.5170}
            >>> bounds = geo_service.calculate_bounds(center, 10)
        """
        if not self.validate_coordinates(center['lat'], center['lon']):
            raise ValueError(f"無效的中心點座標: {center}")

        if radius_km <= 0:
            raise ValueError(f"半徑必須大於0: {radius_km}")

        # 計算緯度變化（1度緯度約111公里）
        lat_change = radius_km / 111.0

        # 計算經度變化（依據緯度調整）
        # 經度間距會隨著緯度增加而變小
        lon_change = radius_km / \
            (111.0 * math.cos(math.radians(center['lat'])))

        return {
            'min_lat': round(center['lat'] - lat_change, 6),
            'max_lat': round(center['lat'] + lat_change, 6),
            'min_lon': round(center['lon'] - lon_change, 6),
            'max_lon': round(center['lon'] + lon_change, 6)
        }

    def find_points_in_range(self,
                             center: Dict[str, float],
                             points: List[Dict[str, float]],
                             max_distance_km: float) -> List[Dict]:
        """尋找指定範圍內的所有點

        這個方法先使用矩形範圍快速過濾，然後再精確計算距離，
        這種兩階段的策略可以大幅提升處理大量點的效能。

        參數:
            center: 中心點座標 {'lat': float, 'lon': float}
            points: 所有待檢查的點的列表
            max_distance_km: 最大距離（公里）

        回傳:
            List[Dict]: 在範圍內的點的列表，每個點包含原始資料和距離

        使用範例:
            >>> center = {'lat': 25.0478, 'lon': 121.5170}
            >>> points = [{'lat': 25.1, 'lon': 121.6}, ...]
            >>> nearby = geo_service.find_points_in_range(
                    center, points, 5
                )
        """
        # 先計算矩形範圍
        bounds = self.calculate_bounds(center, max_distance_km)

        # 第一階段：快速過濾
        candidates = []
        for point in points:
            if self._is_point_in_bounds(point, bounds):
                # 計算實際距離
                distance = self.calculate_distance(center, point)
                if distance <= max_distance_km:
                    candidates.append({
                        **point,
                        'distance': round(distance, 2)
                    })

        # 依據距離排序
        return sorted(candidates, key=lambda x: x['distance'])

    def _is_point_in_bounds(self,
                            point: Dict[str, float],
                            bounds: Dict[str, float]) -> bool:
        """檢查點是否在範圍內

        這是一個內部方法，用於快速篩選點是否在矩形範圍內。
        相比計算實際距離，這個方法的運算成本更低。
        """
        return (bounds['min_lat'] <= point['lat'] <= bounds['max_lat'] and
                bounds['min_lon'] <= point['lon'] <= bounds['max_lon'])

    def format_coordinates(self, lat: float, lon: float) -> str:
        """格式化座標為字串

        將座標轉換為標準的字串格式，通常用於 API 呼叫或顯示。

        參數:
            lat: 緯度
            lon: 經度

        回傳:
            str: "緯度,經度" 格式的字串

        使用範例:
            >>> coord_str = geo_service.format_coordinates(25.0478, 121.5170)
            >>> print(coord_str)  # "25.0478,121.5170"
        """
        if not self.validate_coordinates(lat, lon):
            raise ValueError(f"無效的座標: lat={lat}, lon={lon}")

        return f"{lat:.6f},{lon:.6f}"

    def parse_coordinates(self, coord_str: str) -> Optional[Dict[str, float]]:
        """解析座標字串

        將各種格式的座標字串轉換為標準的字典格式。
        支援多種常見的座標字串格式：
        - "lat,lon"
        - "lat, lon"
        - "(lat,lon)"

        參數:
            coord_str: 座標字串

        回傳:
            Optional[Dict]: 解析成功返回座標字典，失敗返回 None

        使用範例:
            >>> coord = geo_service.parse_coordinates("25.0478, 121.5170")
            >>> if coord:
            >>>     print(f"緯度: {coord['lat']}, 經度: {coord['lon']}")
        """
        if not coord_str:
            return None

        try:
            # 清理字串
            clean_str = coord_str.replace('(', '').replace(')', '').strip()
            parts = clean_str.replace(' ', '').split(',')

            if len(parts) != 2:
                return None

            lat = float(parts[0])
            lon = float(parts[1])

            if not self.validate_coordinates(lat, lon):
                return None

            return {'lat': lat, 'lon': lon}
        except (ValueError, TypeError):
            return None

    def _calculate_estimated_travel_info(self,
                                         origin: Dict[str, float],
                                         destination: Dict[str, float],
                                         mode: str) -> Dict:
        """計算預估的交通資訊（不需要 API）

        輸入參數:
            origin: 起點座標 {'lat': float, 'lon': float}
            destination: 終點座標 {'lat': float, 'lon': float}
            mode: 交通方式('driving'/'transit'/'walking'/'bicycling')

        回傳:
            Dict: {
                'distance_km': float,     # 預估距離（公里）
                'duration_minutes': int,   # 預估時間（分鐘）
                'is_estimated': True      # 標記為預估資料
            }
        """
        # 計算直線距離
        distance = self.calculate_distance(origin, destination)

        # 根據交通方式選擇預設速度
        speed = self.DEFAULT_SPEEDS.get(mode, 30)  # 預設 30 km/h

        # 計算預估時間（分鐘）
        duration = (distance / speed) * 60

        # 加入路程曲折的修正係數（實際路程通常比直線距離長）
        distance_factor = 1.3 if mode == 'driving' else 1.2  # 開車路線較曲折
        time_factor = 1.4 if mode == 'driving' else 1.3     # 開車考慮紅綠燈等因素

        return {
            'distance_km': round(distance * distance_factor, 1),
            'duration_minutes': int(duration * time_factor),
            'is_estimated': True
        }

    def geocode(self, address: str) -> Dict[str, float]:
        """將地址或地點名稱轉換為座標

        輸入參數:
            address: str - 地址或地點名稱

        回傳:
            Dict[str, float] - 包含經緯度的字典 {'lat': 緯度, 'lon': 經度}

        異常:
            RuntimeError - 如果無法取得座標
        """
        try:
            if not self.has_google_maps:
                raise RuntimeError("Google Maps API 未初始化")

            result = self.maps_client.geocode(address)
            if not result:
                raise RuntimeError(f"找不到地點: {address}")

            location = result[0]['geometry']['location']
            return {
                'lat': location['lat'],
                'lon': location['lng'],
                'duration_min': 0,
                'label': '交通樞紐',
                'period': 'morning',  # 起點預設為早上時段
                'hours': {i: [{'start': '00:00', 'end': '23:59'}] for i in range(1, 8)}
            }
        except Exception as e:
            raise RuntimeError(f"地理編碼錯誤: {str(e)}")
