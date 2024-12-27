# src\core\planners\advanced_planner.py

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from .base_planner import BaseTripPlanner
from .location_evaluator import LocationEvaluator
from .business_hours import BusinessHours
from src.core.utils import calculate_travel_time, calculate_distance
from src.core.models import PlaceDetail


class AdvancedTripPlanner(BaseTripPlanner):
    """進階行程規劃器，負責根據各種條件產生最佳行程"""

    def __init__(self, start_time='09:00', end_time='20:00', travel_mode='transit',
                 distance_threshold=30, efficiency_threshold=0.1,
                 custom_start=None, custom_end=None):
        """
        初始化行程規劃器
        
        參數：
            start_time (str): 開始時間，格式為 'HH:MM'
            end_time (str): 結束時間，格式為 'HH:MM'
            travel_mode (str): 交通方式，可選 'transit', 'driving', 'walking', 'bicycling'
            distance_threshold (float): 可接受的最大距離（公里）
            efficiency_threshold (float): 最低效率閾值
            custom_start (Dict): 自訂起點資訊
            custom_end (Dict): 自訂終點資訊
        """
        print(f"初始化時間：開始={start_time}, 結束={end_time}")

        # 轉換時間字串為 datetime 物件
        today = datetime.now().date()
        self.start_datetime = datetime.combine(
            today, datetime.strptime(start_time, '%H:%M').time())
        self.end_datetime = datetime.combine(
            today, datetime.strptime(end_time, '%H:%M').time())

        # 交通和距離設定
        self.travel_mode = travel_mode
        self.distance_threshold = distance_threshold
        self.efficiency_threshold = efficiency_threshold

        # 用餐狀態追蹤
        self.had_lunch = False
        self.had_dinner = False

        # 地點資訊
        self.start_location = None
        self.end_location = None
        self.available_locations = []
        self.selected_locations = []

    def _filter_nearby_locations(self, current_location: PlaceDetail,
                                 current_time: datetime) -> List[PlaceDetail]:
        """篩選附近的地點，考慮時間和類型因素"""
        if not current_location or not self.available_locations:
            return []

        nearby_locations = []

        for location in self.available_locations:
            distance = calculate_distance(
                current_location.lat,
                current_location.lon,
                location.lat,
                location.lon
            )

            adjusted_threshold = self._get_adjusted_distance_threshold(
                location.label, current_time)

            if distance <= adjusted_threshold:
                nearby_locations.append(location)

        return nearby_locations

    def _estimate_total_trip_time(self, current_location: PlaceDetail,
                                  potential_location: PlaceDetail,
                                  current_time: datetime) -> float:
        """估算加入新地點後的總行程時間（分鐘）"""
        # 計算到下一個地點的交通時間
        to_next = calculate_travel_time(
            {"lat": current_location.lat, "lon": current_location.lon, "name": current_location.name},
            {"lat": potential_location.lat, "lon": potential_location.lon, "name": potential_location.name},
            self.travel_mode)
        next_travel_time = to_next['time'].total_seconds() / 60

        # 計算在該地點的停留時間
        stay_duration = potential_location.duration_min

        return next_travel_time + stay_duration

    def _has_enough_time(self, current_location: PlaceDetail,
                         potential_location: PlaceDetail,
                         current_time: datetime) -> bool:
        """檢查是否有足夠時間訪問新地點"""
        # 計算需要的總時間
        total_needed_time = self._estimate_total_trip_time(
            current_location, potential_location, current_time)

        # 計算剩餘可用時間（分鐘）
        remaining_minutes = (self.end_datetime -
                             current_time).total_seconds() / 60

        # 預留 30 分鐘緩衝時間
        return remaining_minutes >= (total_needed_time + 30)

    def _calculate_location_score(self, location: PlaceDetail,
                                  current_location: PlaceDetail,
                                  travel_time: float,
                                  current_time: datetime) -> float:
        """計算地點的綜合評分"""
        if current_location == location:
            return float('-inf')

        # 基礎分數計算
        distance = calculate_distance(
            current_location.lat,
            current_location.lon,
            location.lat,
            location.lon
        )

        # 停留時間效率
        duration = location.duration_min
        base_efficiency = duration / (max(distance, 0.1) * max(travel_time, 1))

        # 時間調整係數
        time_factor = self._calculate_time_priority(current_time)

        # 根據地點類型調整
        type_factor = 1.0
        if location.label in ['景點', '公園']:
            if 9 <= current_time.hour <= 16:
                type_factor = 1.5
        elif location.label in ['餐廳', '小吃']:
            if self._is_meal_time(current_time):
                type_factor = 2.0
            else:
                type_factor = 0.3

        # 計算最終分數
        final_score = base_efficiency * time_factor * type_factor

        return final_score

    def _find_best_next_location(self, current_location: PlaceDetail,
                                 current_time: datetime) -> Optional[PlaceDetail]:
        """尋找下一個最佳地點"""
        best_location = None
        best_score = float('-inf')

        nearby_locations = self._filter_nearby_locations(
            current_location, current_time)

        for location in nearby_locations:
            # 檢查時間充足性
            if not self._has_enough_time(current_location, location, current_time):
                continue

            # 計算交通時間
            travel_details = calculate_travel_time(
                {"lat": current_location.lat, "lon": current_location.lon, "name": current_location.name},
                {"lat": location.lat, "lon": location.lon, "name": location.name},
                self.travel_mode)
            travel_time = travel_details['time'].total_seconds() / 60

            # 計算到達時間
            arrival_time = current_time + timedelta(minutes=int(travel_time))

            # 檢查營業時間
            if not location.is_open_at(arrival_time.weekday() + 1, 
                                     arrival_time.strftime('%H:%M')):
                continue

            # 計算地點評分
            score = self._calculate_location_score(
                location, current_location, travel_time, current_time)

            if score > best_score:
                best_score = score
                best_location = location

        return best_location

    def _is_meal_time(self, current_time: datetime) -> bool:
        """檢查是否為用餐時間"""
        hour = current_time.hour
        return (11 <= hour <= 14) or (17 <= hour <= 20)

    def _calculate_time_priority(self, current_time: datetime) -> float:
        """計算時間優先度"""
        hour = current_time.hour
        if self._is_meal_time(current_time):
            return 1.5
        return 1.0

    def _get_adjusted_distance_threshold(self, location_type: str, current_time: datetime) -> float:
        """取得根據地點類型調整後的距離閾值"""
        base_threshold = self.distance_threshold

        # 根據地點類型調整
        if location_type in ['景點', '公園']:
            return base_threshold * 1.2
        elif location_type in ['餐廳', '小吃']:
            if self._is_meal_time(current_time):
                return base_threshold * 0.8
            return base_threshold
        
        return base_threshold

    def plan(self) -> List[Dict[str, Any]]:
        """
        執行行程規劃
        
        回傳:
            List[Dict[str, Any]]: 規劃好的行程列表
        """
        itinerary = []
        current_time = self.start_datetime
        current_location = self.start_location

        # 加入起點
        itinerary.append({
            'step': 0,
            'name': current_location.name,
            'start_time': current_time.strftime('%H:%M'),
            'end_time': current_time.strftime('%H:%M'),
            'duration': 0,
            'hours': '00:00-24:00',
            'transport_details': '起點',
            'travel_time': 0
        })

        step = 1
        while current_time < self.end_datetime:
            # 尋找下一個最佳地點
            next_location = self._find_best_next_location(current_location, current_time)
            if not next_location:
                break

            # 計算交通時間
            travel_details = calculate_travel_time(
                {"lat": current_location.lat, "lon": current_location.lon, "name": current_location.name},
                {"lat": next_location.lat, "lon": next_location.lon, "name": next_location.name},
                self.travel_mode
            )
            travel_time = travel_details['time'].total_seconds() / 60

            # 更新時間
            arrival_time = current_time + timedelta(minutes=int(travel_time))
            departure_time = arrival_time + timedelta(minutes=next_location.duration_min)

            # 檢查是否超出結束時間
            if departure_time > self.end_datetime:
                break

            # 加入行程
            itinerary.append({
                'step': step,
                'name': next_location.name,
                'start_time': arrival_time.strftime('%H:%M'),
                'end_time': departure_time.strftime('%H:%M'),
                'duration': next_location.duration_min,
                'hours': str(next_location.hours),
                'transport_details': travel_details['transport_details'],
                'travel_time': travel_time,
                'is_meal': next_location.label in ['餐廳', '小吃']
            })

            # 更新當前狀態
            current_location = next_location
            current_time = departure_time
            step += 1

        # 加入終點
        if current_time < self.end_datetime:
            # 計算回到終點的交通時間
            final_travel = calculate_travel_time(
                {"lat": current_location.lat, "lon": current_location.lon, "name": current_location.name},
                {"lat": self.end_location.lat, "lon": self.end_location.lon, 
                 "name": self.end_location.name},
                self.travel_mode
            )
            final_time = current_time + timedelta(
                seconds=final_travel['time'].total_seconds())

            itinerary.append({
                'step': step,
                'name': self.end_location.name,
                'start_time': final_time.strftime('%H:%M'),
                'end_time': final_time.strftime('%H:%M'),
                'duration': 0,
                'hours': '00:00-24:00',
                'transport_details': final_travel['transport_details'],
                'travel_time': final_travel['time'].total_seconds() / 60
            })

        return itinerary