# src/core/planner/strategy.py

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from src.core.models.place import PlaceDetail
from src.core.evaluator import LocationEvaluator
from src.core.utils import calculate_travel_time


class PlanningStrategy:
    """
    行程規劃策略的實現類別
    負責執行具體的行程規劃邏輯，使用改良的貪婪演算法

    工作原理：
    1. 根據當前位置和時間，評估所有可能的下一個地點
    2. 綜合考慮距離、時間效率、營業時間等因素
    3. 選擇最佳的下一個地點加入行程
    4. 重複此過程直到無法加入更多地點或達到結束時間

    主要特點：
    - 動態評分：根據不同時段調整評分權重
    - 智能篩選：自動過濾不合適的地點
    - 彈性調整：支援不同的規劃參數
    """

    def __init__(self, start_time: datetime, end_time: datetime,
                 travel_mode: str = 'transit',
                 distance_threshold: float = 30.0,
                 efficiency_threshold: float = 0.1):
        """
        初始化規劃策略

        輸入參數：
            start_time (datetime): 行程開始時間
            end_time (datetime): 行程結束時間
            travel_mode (str): 交通方式（transit/driving/walking/bicycling）
            distance_threshold (float): 可接受的最大距離（公里）
            efficiency_threshold (float): 最低效率閾值
        """
        self.start_time = start_time
        self.end_time = end_time
        self.travel_mode = travel_mode
        self.distance_threshold = distance_threshold
        self.efficiency_threshold = efficiency_threshold

        # 初始化評分器
        self.evaluator = LocationEvaluator(start_time, distance_threshold)

    def execute(self, current_location: PlaceDetail,
                available_locations: List[PlaceDetail],
                current_time: datetime) -> List[Dict[str, Any]]:
        """
        執行行程規劃策略

        輸入參數：
            current_location (PlaceDetail): 目前位置
            available_locations (List[PlaceDetail]): 可選擇的地點列表
            current_time (datetime): 當前時間

        回傳：
            List[Dict]: 規劃好的行程列表
        """
        itinerary = []
        current_loc = current_location
        remaining_locations = available_locations.copy()
        visit_time = current_time

        while remaining_locations and visit_time < self.end_time:
            # 尋找下一個最佳地點
            next_location = self._find_best_next_location(
                current_loc, remaining_locations, visit_time)

            if not next_location:
                break

            # 計算交通時間
            travel_info = self._calculate_travel_info(
                current_loc, next_location)

            # 計算時間安排
            arrival_time = visit_time + timedelta(minutes=travel_info['time'])
            departure_time = arrival_time + \
                timedelta(minutes=next_location.duration_min)

            # 檢查是否超過結束時間
            if departure_time > self.end_time:
                break

            # 加入行程
            itinerary.append({
                'step': len(itinerary) + 1,
                'name': next_location.name,
                'start_time': arrival_time.strftime('%H:%M'),
                'end_time': departure_time.strftime('%H:%M'),
                'duration': next_location.duration_min,
                'transport_details': travel_info['transport_details'],
                'travel_time': travel_info['time']
            })

            # 更新狀態
            current_loc = next_location
            visit_time = departure_time
            remaining_locations.remove(next_location)

        return itinerary

    def _find_best_next_location(self, current_location: PlaceDetail,
                                 available_locations: List[PlaceDetail],
                                 current_time: datetime) -> Optional[PlaceDetail]:
        """
        尋找下一個最佳造訪地點

        評分考慮因素：
        1. 距離和交通時間的效率
        2. 營業時間的配合度
        3. 用餐時間的協調性
        4. 停留時間的合理性

        輸入參數：
            current_location: 目前位置
            available_locations: 可選擇的地點列表
            current_time: 當前時間

        回傳：
            Optional[PlaceDetail]: 最佳的下一個地點，如果沒有合適的地點則回傳 None
        """
        best_location = None
        best_score = float('-inf')

        # 判斷是否為用餐時間
        is_meal_time = self._is_meal_time(current_time)

        for location in available_locations:
            # 計算交通時間
            travel_info = self._calculate_travel_info(
                current_location, location)
            travel_time = travel_info['time']

            # 計算到達時間
            arrival_time = current_time + timedelta(minutes=travel_time)

            # 檢查時間限制
            if not self._has_enough_time(location, arrival_time):
                continue

            # 計算地點評分
            score = self.evaluator.calculate_score(
                location,
                current_location,
                travel_time,
                is_meal_time
            )

            if score > best_score:
                best_score = score
                best_location = location

        return best_location

    def _calculate_travel_info(self, from_location: PlaceDetail,
                               to_location: PlaceDetail) -> Dict[str, Any]:
        """
        計算兩地點間的交通資訊

        輸入參數：
            from_location: 起點
            to_location: 終點

        回傳：
            Dict: 包含交通時間和交通方式的資訊
        """
        return calculate_travel_time(
            {"lat": from_location.lat, "lon": from_location.lon,
             "name": from_location.name},
            {"lat": to_location.lat, "lon": to_location.lon,
             "name": to_location.name},
            self.travel_mode
        )

    def _has_enough_time(self, location: PlaceDetail,
                         arrival_time: datetime) -> bool:
        """
        檢查是否有足夠時間造訪該地點

        輸入參數：
            location: 要檢查的地點
            arrival_time: 預計到達時間

        回傳：
            bool: True 表示有足夠時間，False 則否
        """
        departure_time = arrival_time + \
            timedelta(minutes=location.duration_min)
        return (departure_time <= self.end_time and
                location.is_open_at(arrival_time.weekday() + 1,
                                    arrival_time.strftime('%H:%M')))

    def _is_meal_time(self, current_time: datetime) -> bool:
        """
        判斷是否為用餐時間

        輸入參數：
            current_time: 當前時間

        回傳：
            bool: True 表示是用餐時間，False 則否
        """
        hour = current_time.hour
        return (11 <= hour <= 14) or (17 <= hour <= 20)
