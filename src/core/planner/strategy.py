# src/core/planner/strategy.py

from datetime import datetime, timedelta
import random
from typing import Any, List, Dict, Optional, Tuple
from src.core.evaluator.place_scoring import PlaceScoring
from src.core.models.place import PlaceDetail
from src.core.services.time_service import TimeService
from src.core.services.google_maps import GoogleMapsService
from src.core.utils.cache_decorator import cached


class PlanningStrategy:
    """行程規劃策略類別

    負責：
    1. 依據時段選擇適合的景點
    2. 使用評分系統評估選項
    3. 整合路線規劃
    4. 產生行程建議
    """

    def __init__(self,
                 start_time: datetime,
                 end_time: datetime,
                 travel_mode: str = 'transit',
                 distance_threshold: float = 30.0,
                 requirement: dict = None):
        """初始化規劃策略

        輸入:
            start_time: 行程開始時間
            end_time: 行程結束時間
            travel_mode: 交通方式(transit/driving/walking/bicycling)
            distance_threshold: 可接受的最大距離(公里)
            requirement: 使用者需求(包含用餐時間等)
        """
        self.start_time = start_time
        self.end_time = end_time
        self.travel_mode = travel_mode
        self.distance_threshold = distance_threshold
        self.requirement = requirement or {}
        self.time_service = TimeService(
            lunch_time=requirement.get('lunch_time'),
            dinner_time=requirement.get('dinner_time')
        )
        self.place_scoring = PlaceScoring(self.time_service)

        # 初始化 Google Maps 服務
        try:
            from src.config.config import GOOGLE_MAPS_API_KEY
            self.maps_service = GoogleMapsService(GOOGLE_MAPS_API_KEY)
        except Exception as e:
            print(f"警告：Google Maps 服務初始化失敗: {str(e)}")
            self.maps_service = None

    def execute(self,
                current_location: PlaceDetail,
                available_locations: List[PlaceDetail],
                current_time: datetime) -> List[Dict[str, Any]]:
        """執行行程規劃

        輸入：
            current_location: 當前位置
            available_locations: 可選擇的地點列表
            current_time: 當前時間

        回傳：
            List[Dict]: 規劃後的行程清單，每個行程包含：
            - step: 順序編號
            - name: 地點名稱
            - start_time: 到達時間
            - end_time: 離開時間
            - duration: 停留時間（分鐘）
            - transport_details: 交通方式說明
            - travel_time: 交通時間（分鐘）
            - route_info: 路線資訊（選填）
        """
        itinerary = []
        current_loc = current_location
        remaining_locations = available_locations.copy()
        visit_time = current_time

        while remaining_locations and visit_time < self.end_time:
            # 尋找下一個最佳地點
            next_place = self._find_best_next_location(
                current_loc,
                remaining_locations,
                visit_time
            )

            if not next_place:
                break

            location, travel_info = next_place

            # 計算時間
            arrival_time = visit_time + timedelta(minutes=travel_info['time'])
            departure_time = arrival_time + \
                timedelta(minutes=location.duration_min)

            # 檢查是否超過結束時間
            if departure_time > self.end_time:
                break

            # 加入行程
            itinerary.append({
                'step': len(itinerary) + 1,
                'name': location.name,
                'start_time': arrival_time.strftime('%H:%M'),
                'end_time': departure_time.strftime('%H:%M'),
                'duration': location.duration_min,
                'transport_details': travel_info['transport_details'],
                'travel_time': travel_info['time'],
                'route_info': travel_info.get('route_info')
            })

            # 更新狀態
            current_loc = location
            visit_time = departure_time
            remaining_locations.remove(location)

        return itinerary

    def _find_best_next_location(self,
                                 current_loc: PlaceDetail,
                                 available_locations: List[PlaceDetail],
                                 visit_time: datetime) -> Optional[Tuple[PlaceDetail, Dict]]:
        """尋找最佳的下一個地點

        輸入：
            current_loc: 當前位置
            available_locations: 可選擇的地點列表
            visit_time: 當前時間

        回傳：
            Tuple[PlaceDetail, Dict]: (選中的地點, 交通資訊)
            如果沒有合適的地點則回傳 None
        """
        scored_locations = []

        for location in available_locations:
            # 計算交通資訊
            travel_info = self._calculate_travel_info(
                from_lat=current_loc.lat,
                from_lon=current_loc.lon,
                to_lat=location.lat,
                to_lon=location.lon,
                mode=self.travel_mode,
                departure_time=visit_time
            )

            # 計算評分
            score = self.place_scoring.calculate_score(
                place=location,
                current_location=current_loc,
                current_time=visit_time,
                travel_time=travel_info['time']
            )

            if score > float('-inf'):
                scored_locations.append((location, score, travel_info))

        if not scored_locations:
            return None

        # 排序並隨機選擇前3名之一
        scored_locations.sort(key=lambda x: x[1], reverse=True)
        top_locations = scored_locations[:3]
        selected = random.choice(top_locations)

        return selected[0], selected[2]

    def _get_transport_display(self) -> str:
        """取得交通方式的顯示文字"""
        return {
            'transit': '大眾運輸',
            'driving': '開車',
            'walking': '步行',
            'bicycling': '騎車'
        }.get(self.travel_mode, self.travel_mode)

    def _get_estimated_speed(self) -> float:
        """取得預估的移動速度(公里/小時)"""
        return {
            'transit': 30,  # 大眾運輸 30 km/h
            'driving': 40,  # 開車 40 km/h
            'bicycling': 15,  # 騎車 15 km/h
            'walking': 5    # 步行 5 km/h
        }.get(self.travel_mode, 30)


@cached(maxsize=128)
def _calculate_travel_info(self,
                           from_lat: float,
                           from_lon: float,
                           to_lat: float,
                           to_lon: float,
                           mode: str,
                           departure_time: datetime = None) -> Dict:
    """計算交通資訊

    輸入:
        from_lat: 起點緯度
        from_lon: 起點經度
        to_lat: 終點緯度
        to_lon: 終點經度
        mode: 交通方式
        departure_time: 出發時間

    回傳:
        Dict: 交通資訊
    """
    try:
        if self.maps_service:
            # 確保出發時間是未來時間
            current_time = datetime.now()
            if departure_time is None or departure_time < current_time:
                departure_time = current_time + timedelta(minutes=1)

            route = self.maps_service.calculate_travel_time(
                origin=(from_lat, from_lon),
                destination=(to_lat, to_lon),
                mode=mode,
                departure_time=departure_time
            )

            return {
                'time': route['duration_minutes'],
                'distance_km': route['distance_meters'] / 1000,
                'transport_details': self._get_transport_display(),
                'route_info': route
            }
    except Exception as e:
        print(f"警告：Google Maps 路線查詢失敗: {str(e)}")

    # 使用直線距離估算
    from src.core.services.geo_service import GeoService
    distance = GeoService.calculate_distance(
        {'lat': from_lat, 'lon': from_lon},
        {'lat': to_lat, 'lon': to_lon}
    )
    speed = self._get_estimated_speed()
    est_time = (distance / speed) * 60

    return {
        'time': round(est_time),
        'distance_km': distance,
        'transport_details': self._get_transport_display(),
        'route_info': None
    }
