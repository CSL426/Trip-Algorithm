# src/core/services/google_maps.py

from abc import ABC, abstractmethod
from typing import Dict, Tuple, Optional, List
from datetime import datetime
import googlemaps
from ..utils.cache_decorator import cached


class GoogleMapsService:
    """Google Maps API 服務類別

    負責:
    1. Google Maps API 的呼叫
    2. 路線規劃與距離計算
    3. 異常處理
    4. 快取管理
    """

    def __init__(self, api_key: str):
        """初始化

        輸入:
            api_key: Google Maps API 金鑰
        """
        self.client = googlemaps.Client(key=api_key)

    def calculate_travel_time(self,
                              origin: Tuple[float, float],
                              destination: Tuple[float, float],
                              mode: str = 'driving',
                              departure_time: datetime = None) -> Dict:
        """計算交通時間和路線

        輸入:
            origin: 起點座標 (緯度, 經度)
            destination: 終點座標 (緯度, 經度)
            mode: 交通方式
            departure_time: 出發時間

        回傳:
            Dict: {
                'duration_minutes': int,    # 交通時間(分鐘)
                'distance_meters': int,     # 距離(公尺)
                'steps': List[Dict],        # 路線步驟
                'polyline': str            # 路線編碼字串
            }

        異常:
            ValueError: 座標超出範圍
            RuntimeError: API 呼叫失敗
        """
        # 驗證座標
        self._validate_coordinates(origin, destination)
        self._validate_transport_mode(mode)

        departure_time = departure_time or datetime.now()

        try:
            result = self.client.directions(
                origin=self._format_coordinates(*origin),
                destination=self._format_coordinates(*destination),
                mode=mode,
                departure_time=departure_time
            )

            if not result:
                raise RuntimeError("找不到路線")

            leg = result[0]['legs'][0]

            return {
                'duration_minutes': int(leg['duration']['value'] / 60),
                'distance_meters': leg['distance']['value'],
                'steps': leg['steps'],
                'polyline': result[0]['overview_polyline']['points']
            }

        except Exception as e:
            raise RuntimeError(f"Google Maps API 錯誤: {str(e)}")

    def geocode(self, address: str) -> Dict[str, float]:
        """地址轉座標

        輸入:
            address: 地址或地點名稱

        回傳:
            Dict: {'lat': 緯度, 'lon': 經度}
        """
        try:
            result = self.client.geocode(address)
            if not result:
                raise RuntimeError(f"找不到地點: {address}")

            location = result[0]['geometry']['location']
            return {
                'lat': location['lat'],
                'lon': location['lon']
            }
        except Exception as e:
            raise RuntimeError(f"地理編碼錯誤: {str(e)}")

    @staticmethod
    def _format_coordinates(lat: float, lon: float) -> str:
        """格式化座標字串"""
        return f"{lat},{lon}"

    @staticmethod
    def _validate_coordinates(origin: Tuple[float, float],
                              destination: Tuple[float, float]) -> None:
        """驗證座標範圍"""
        for lat, lon in [origin, destination]:
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                raise ValueError("座標超出範圍")

    @staticmethod
    def _validate_transport_mode(mode: str) -> None:
        """驗證交通方式"""
        valid_modes = {'transit', 'driving', 'walking', 'bicycling'}
        if mode not in valid_modes:
            raise ValueError(f"不支援的交通方式: {mode}")
