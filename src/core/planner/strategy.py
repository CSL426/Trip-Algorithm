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
                 efficiency_threshold: float = 0.1,
                 requirement: dict = None):
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
        self.requirement = requirement or {}

        # 初始化評分器
        self.evaluator = LocationEvaluator(start_time, distance_threshold)

    def execute(self, current_location: PlaceDetail,
                available_locations: List[PlaceDetail],
                current_time: datetime) -> List[Dict[str, Any]]:
        """
        執行行程規劃策略

        輸入參數：
            current_location: 目前位置（PlaceDetail物件）
            available_locations: 可選擇的地點列表（PlaceDetail物件的列表）
            current_time: 當前時間
        """
        itinerary = []
        current_loc = current_location
        remaining_locations = available_locations.copy()
        visit_time = current_time

        while remaining_locations and visit_time < self.end_time:
            # 尋找下一個最佳地點
            next_location = self._find_best_next_location(
                current_loc,
                remaining_locations,
                visit_time
            )

            if not next_location:
                break

            # 計算交通時間（注意這裡使用點號存取）
            travel_info = self._calculate_travel_info(
                current_loc,
                next_location
            )

            # 計算時間安排
            arrival_time = visit_time + timedelta(minutes=travel_info['time'])
            departure_time = arrival_time + \
                timedelta(minutes=next_location.duration_min)

            # 加入行程
            itinerary.append({
                'step': len(itinerary) + 1,
                'name': next_location.name,  # 使用點號存取
                'start_time': arrival_time.strftime('%H:%M'),
                'end_time': departure_time.strftime('%H:%M'),
                'duration': next_location.duration_min,  # 使用點號存取
                'transport_details': travel_info['transport_details'],
                'travel_time': travel_info['time']
            })

            current_loc = next_location
            visit_time = departure_time
            remaining_locations.remove(next_location)

        return itinerary

    def get_restaurant_type(self, restaurant: PlaceDetail) -> str:
        """
        根據評分判斷餐廳類型

        輸入參數:
            restaurant: PlaceDetail, 餐廳資訊，包含:
                - rating: float, 評分(0-5分)
                - label: str, 類型標籤(餐廳/小吃/夜市等)

        回傳:
            str: 餐廳類型(popular/normal/snack)
        """
        rating = restaurant.rating
        label = restaurant.label

        if rating >= 4.5:
            return 'popular'
        elif label in ['小吃', '夜市']:
            return 'snack'
        else:
            return 'normal'

    def get_general_time_range(self, target_time: datetime) -> tuple:
        """
        取得一般用餐時間範圍（不考慮特定餐廳）

        輸入參數:
            target_time: datetime, 目標用餐時間

        回傳:
            tuple: (最早可接受時間, 最晚可接受時間)
        """
        # 一般用餐時間前後45分鐘
        early_buffer, late_buffer = -45, 45

        earliest = target_time + timedelta(minutes=early_buffer)
        latest = target_time + timedelta(minutes=late_buffer)

        return earliest, latest

    def get_dining_time_range(self, restaurant: PlaceDetail, target_time: datetime) -> tuple:
        """
        根據餐廳類型取得建議的用餐時間範圍

        輸入參數:
            restaurant: PlaceDetail, 餐廳資訊
            target_time: datetime, 目標用餐時間

        回傳:
            tuple: (最早可接受時間, 最晚可接受時間)
        """
        restaurant_type = self.get_restaurant_type(restaurant)

        # 根據餐廳類型設定不同的緩衝時間(分鐘)
        time_buffers = {
            'popular': (-60, 30),   # 熱門餐廳：提前1小時到 最晚延後30分
            'normal': (-45, 45),    # 一般餐廳：前後45分鐘
            'snack': (-90, 90)      # 小吃：前後都很彈性
        }

        early_buffer, late_buffer = time_buffers[restaurant_type]
        earliest = target_time + timedelta(minutes=early_buffer)
        latest = target_time + timedelta(minutes=late_buffer)

        return earliest, latest

    def _find_best_next_location(self, current_location: PlaceDetail,
                                 available_locations: List[PlaceDetail],
                                 current_time: datetime) -> Optional[PlaceDetail]:
        """修改原本的函式，加入用餐時間的考量"""
        best_location = None
        best_score = float('-inf')

        # 判斷是否為用餐時間
        is_lunch_time = False
        is_dinner_time = False

        # 從需求中取得用餐時間
        lunch_time_str = self.requirement.get('lunch_time')
        dinner_time_str = self.requirement.get('dinner_time')

        if lunch_time_str and lunch_time_str != 'none':
            lunch_time = datetime.strptime(lunch_time_str, '%H:%M').replace(
                year=current_time.year,
                month=current_time.month,
                day=current_time.day
            )
            # 使用一般時間範圍來判斷是否在用餐時段
            earliest_lunch, latest_lunch = self.get_general_time_range(
                lunch_time)
            is_lunch_time = earliest_lunch <= current_time <= latest_lunch

        if dinner_time_str and dinner_time_str != 'none':
            dinner_time = datetime.strptime(dinner_time_str, '%H:%M').replace(
                year=current_time.year,
                month=current_time.month,
                day=current_time.day
            )
            earliest_dinner, latest_dinner = self.get_general_time_range(
                dinner_time)
            is_dinner_time = earliest_dinner <= current_time <= latest_dinner

        # 如果是用餐時間，只考慮餐廳
        if is_lunch_time or is_dinner_time:
            available_locations = [loc for loc in available_locations
                                   if loc.label in ['餐廳', '小吃', '夜市']]
            if not available_locations:
                return None

        # 更新評分器的當前時間
        self.evaluator.current_time = current_time

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

            # 如果是用餐時間且是餐廳，檢查是否在合適的時間範圍
            if (is_lunch_time or is_dinner_time) and \
                    location.label in ['餐廳', '小吃', '夜市']:
                target_time = lunch_time if is_lunch_time else dinner_time
                # 這裡傳入具體的餐廳資訊
                earliest, latest = self.get_dining_time_range(
                    location, target_time)
                if not (earliest <= arrival_time <= latest):
                    continue

            # 計算評分
            score = self.evaluator.calculate_score(
                location,
                current_location,
                travel_time,
                is_meal_time=(is_lunch_time or is_dinner_time)
            )

            if score > best_score:
                best_score = score
                best_location = location

        return best_location

    def _calculate_travel_info(self,
                               from_location: PlaceDetail,
                               to_location: PlaceDetail) -> Dict[str, Any]:
        """
        計算兩地點間的交通資訊

        輸入參數：
            from_location: 起點（PlaceDetail物件）
            to_location: 終點（PlaceDetail物件）
        """
        return {
            'time': 30,  # 先使用固定的交通時間
            'transport_details': f'使用 {self.travel_mode} 方式前往',
            'coordinates': {
                'from': {
                    'lat': from_location.lat,  # 使用點號存取
                    'lon': from_location.lon
                },
                'to': {
                    'lat': to_location.lat,  # 使用點號存取
                    'lon': to_location.lon
                }
            }
        }

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
