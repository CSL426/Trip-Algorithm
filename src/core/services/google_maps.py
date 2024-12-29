# src/core/services/google_maps.py

from abc import ABC, abstractmethod
from typing import Dict, Tuple, Optional, List
from datetime import datetime
import googlemaps
from functools import lru_cache


class TravelTimeCalculator(ABC):
    """交通時間計算介面

    定義計算兩點間交通時間的標準介面
    可以有不同的實作方式（例如：直線距離估算、Google Maps API、其他地圖服務）
    """

    @abstractmethod
    def calculate_travel_time(self,
                              origin: Tuple[float, float],
                              destination: Tuple[float, float],
                              mode: str,
                              departure_time: datetime) -> Dict:
        """計算兩點間的交通時間和路線資訊

        輸入參數:
            origin: 起點座標 (緯度, 經度)
            destination: 終點座標 (緯度, 經度)
            mode: 交通方式 ('transit', 'driving', 'walking', 'bicycling')
            departure_time: 出發時間

        回傳:
            Dict: {
                'duration_minutes': int,    # 交通時間(分鐘)
                'distance_meters': int,     # 距離(公尺)
                'steps': List[Dict],        # 路線步驟
                'polyline': str            # 路線編碼字串
            }

        異常:
            ValueError: 輸入參數錯誤
            RuntimeError: API 呼叫失敗
        """
        pass


class GoogleMapsService(TravelTimeCalculator):
    """Google Maps API 服務類別

    負責:
    1. 包裝 Google Maps API 的呼叫
    2. 實作交通時間計算介面
    3. 提供快取機制
    4. 處理錯誤情況
    """

    def __init__(self, api_key: str):
        """初始化 Google Maps 客戶端

        輸入參數:
            api_key: Google Maps API 金鑰
        """
        self.client = googlemaps.Client(key=api_key)
        self._init_cache()

    def _init_cache(self):
        """初始化快取裝飾器
        使用 functools.lru_cache 實作記憶體快取
        最多儲存 128 筆查詢結果
        """
        self._cached_directions = lru_cache(maxsize=128)(self._get_directions)

    @staticmethod
    def _format_latlng(lat: float, lng: float) -> str:
        """格式化座標字串

        輸入參數:
            lat: 緯度
            lng: 經度

        回傳:
            str: "緯度,經度" 格式的字串
        """
        return f"{lat},{lng}"

    def _get_directions(self,
                        origin: str,
                        destination: str,
                        mode: str,
                        departure_time: datetime) -> Dict:
        """呼叫 Google Maps Directions API

        這是實際呼叫 API 的方法，會被快取裝飾器包裝

        輸入參數:
            origin: 起點座標字串 ("緯度,經度")
            destination: 終點座標字串 ("緯度,經度")
            mode: 交通方式
            departure_time: 出發時間

        回傳:
            Dict: Google Maps API 的完整回應

        異常:
            RuntimeError: API 呼叫失敗
        """
        try:
            result = self.client.directions(
                origin=origin,
                destination=destination,
                mode=mode,
                departure_time=departure_time
            )

            if not result:
                raise RuntimeError("找不到路線")

            return result[0]

        except Exception as e:
            raise RuntimeError(f"Google Maps API 錯誤: {str(e)}")

    def calculate_travel_time(self,
                              origin: Tuple[float, float],
                              destination: Tuple[float, float],
                              mode: str = 'driving',
                              departure_time: datetime = None) -> Dict:
        """實作交通時間計算介面

        使用 Google Maps API 計算實際交通時間和路線

        輸入參數:
            origin: 起點座標 (緯度, 經度)
            destination: 終點座標 (緯度, 經度)
            mode: 交通方式 ('transit', 'driving', 'walking', 'bicycling')
            departure_time: 出發時間，預設為現在

        回傳:
            Dict: {
                'duration_minutes': int,    # 交通時間(分鐘)
                'distance_meters': int,     # 距離(公尺)
                'steps': List[Dict],        # 路線步驟
                'polyline': str            # 路線編碼字串
            }
        """
        # 驗證座標
        if not (-90 <= origin[0] <= 90 and -180 <= origin[1] <= 180):
            raise ValueError("起點座標超出範圍")
        if not (-90 <= destination[0] <= 90 and -180 <= destination[1] <= 180):
            raise ValueError("終點座標超出範圍")

        # 驗證交通方式
        valid_modes = {'transit', 'driving', 'walking', 'bicycling'}
        if mode not in valid_modes:
            raise ValueError(f"不支援的交通方式: {mode}")

        # 設定出發時間
        if departure_time is None:
            departure_time = datetime.now()

        # 格式化座標
        origin_str = self._format_latlng(origin[0], origin[1])
        destination_str = self._format_latlng(destination[0], destination[1])

        # 使用快取查詢路線
        result = self._cached_directions(
            origin_str,
            destination_str,
            mode,
            departure_time
        )

        # 解析 API 回應
        leg = result['legs'][0]

        return {
            'duration_minutes': int(leg['duration']['value'] / 60),
            'distance_meters': leg['distance']['value'],
            'steps': leg['steps'],
            'polyline': result['overview_polyline']['points']
        }

    def clear_cache(self):
        """清除路線查詢快取"""
        self._cached_directions.cache_clear()
