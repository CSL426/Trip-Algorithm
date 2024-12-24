from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from .base_planner import BaseTripPlanner
from .location_evaluator import LocationEvaluator
from .business_hours import BusinessHours
from src.core.utils import calculate_travel_time, calculate_distance


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

    def _calculate_time_priority(self, current_time: datetime) -> float:
        """計算時間優先度，用於調整景點選擇策略

        根據當前時間返回優先度係數：
        - 早上時段（8-11點）：偏好主要景點
        - 用餐時段：偏好餐廳
        - 下午時段：平衡選擇
        - 傍晚時段：偏好較近的景點
        """
        hour = current_time.hour

        if 8 <= hour < 11:
            return 1.5  # 早上偏好主要景點
        elif (11 <= hour < 14) or (17 <= hour < 19):
            # 用餐時段
            return 2.0 if not (self.had_lunch and self.had_dinner) else 0.5
        elif 14 <= hour < 17:
            return 1.0  # 下午平衡選擇
        else:
            return 0.7  # 傍晚偏好近距離

    def _get_adjusted_distance_threshold(self, location_type: str,
                                         current_time: datetime) -> float:
        """根據地點類型和時間調整可接受的距離閾值"""
        base_threshold = self.distance_threshold
        time_factor = self._calculate_time_priority(current_time)

        if location_type in ['景點', '公園']:
            return base_threshold * 1.5 * time_factor
        elif location_type in ['小吃', '餐廳']:
            return base_threshold * 0.8 * time_factor
        else:
            return base_threshold * time_factor

    def _filter_nearby_locations(self, current_location: Dict,
                                 current_time: datetime) -> List[Dict]:
        """篩選附近的地點，考慮時間和類型因素"""
        if not current_location or not self.available_locations:
            return []

        nearby_locations = []

        for location in self.available_locations:
            distance = calculate_distance(
                current_location['lat'],
                current_location['lon'],
                location['lat'],
                location['lon']
            )

            adjusted_threshold = self._get_adjusted_distance_threshold(
                location.get('label', ''), current_time)

            if distance <= adjusted_threshold:
                nearby_locations.append(location)

        return nearby_locations

    def _estimate_total_trip_time(self, current_location: Dict,
                                  potential_location: Dict,
                                  current_time: datetime) -> float:
        """估算加入新地點後的總行程時間（分鐘）"""
        # 計算到下一個地點的交通時間
        to_next = calculate_travel_time(
            current_location, potential_location, self.travel_mode)
        next_travel_time = to_next['time'].total_seconds() / 60

        # 計算在該地點的停留時間
        stay_duration = potential_location.get('duration', 0)

        return next_travel_time + stay_duration

    def _has_enough_time(self, current_location: Dict,
                         potential_location: Dict,
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

    def _calculate_location_score(self, location: Dict,
                                  current_location: Dict,
                                  travel_time: float,
                                  current_time: datetime) -> float:
        """計算地點的綜合評分"""
        if current_location == location:
            return float('-inf')

        # 基礎分數計算
        distance = calculate_distance(
            current_location['lat'],
            current_location['lon'],
            location['lat'],
            location['lon']
        )

        # 停留時間效率
        duration = location.get('duration', 0)
        base_efficiency = duration / (max(distance, 0.1) * max(travel_time, 1))

        # 時間調整係數
        time_factor = self._calculate_time_priority(current_time)

        # 根據地點類型調整
        type_factor = 1.0
        if location.get('label') in ['景點', '公園']:
            if 9 <= current_time.hour <= 16:
                type_factor = 1.5
        elif location.get('label') in ['餐廳', '小吃']:
            if self._is_meal_time(current_time):
                type_factor = 2.0
            else:
                type_factor = 0.3

        # 計算最終分數
        final_score = base_efficiency * time_factor * type_factor

        return final_score

    def _find_best_next_location(self, current_location: Dict,
                                 current_time: datetime) -> Optional[Dict]:
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
                current_location, location, self.travel_mode)
            travel_time = travel_details['time'].total_seconds() / 60

            # 計算到達時間
            arrival_time = current_time + timedelta(minutes=int(travel_time))

            # 檢查營業時間
            hours_handler = BusinessHours(location['hours'])
            if not hours_handler.is_open_at(arrival_time):
                continue

            # 計算地點評分
            score = self._calculate_location_score(
                location, current_location, travel_time, current_time)

            if score > best_score:
                best_score = score
                best_location = location

        return best_location

    def _is_meal_time(self, current_time: datetime) -> bool:
        """判斷是否為用餐時間"""
        hour = current_time.hour

        if not self.had_lunch and 11 <= hour <= 13:
            return True

        if not self.had_dinner and 17 <= hour <= 19:
            return True

        return False

    def _update_meal_status(self, location: Dict, time: datetime):
        """更新用餐狀態"""
        if location.get('label') in ['餐廳', '小吃', '夜市']:
            hour = time.hour
            if 11 <= hour <= 13:
                self.had_lunch = True
            elif 17 <= hour <= 19:
                self.had_dinner = True

    def plan(self) -> List[Dict[str, Any]]:
        """執行行程規劃"""
        current_time = self.start_datetime
        current_location = self.start_location

        # 初始化行程清單
        itinerary = []

        # 加入起點
        itinerary.append({
            'step': 0,
            'name': current_location['name'],
            'start_time': current_time.strftime('%H:%M'),
            'end_time': current_time.strftime('%H:%M'),
            'duration': 0,
            'travel_time': 0,
            'transport_details': '起點',
            'hours': current_location.get('hours', '24小時開放')
        })

        # 主要規劃循環
        while self.available_locations and current_time < self.end_datetime:
            best_location = self._find_best_next_location(
                current_location, current_time)

            if not best_location:
                break

            # 計算交通資訊
            travel_details = calculate_travel_time(
                current_location, best_location, self.travel_mode)
            travel_time = travel_details['time'].total_seconds() / 60

            # 更新時間
            arrival_time = current_time + timedelta(minutes=int(travel_time))
            end_time = arrival_time + \
                timedelta(minutes=best_location['duration'])

            # 檢查是否超過結束時間
            if end_time > self.end_datetime:
                break

            # 更新用餐狀態
            self._update_meal_status(best_location, arrival_time)

            # 加入行程
            itinerary.append({
                'step': len(itinerary),
                'name': best_location['name'],
                'start_time': arrival_time.strftime('%H:%M'),
                'end_time': end_time.strftime('%H:%M'),
                'duration': best_location['duration'],
                'travel_time': travel_time,
                'transport_details': travel_details['transport_details'],
                'hours': best_location.get('hours', '24小時開放')
            })

            # 更新狀態
            self.selected_locations.append(best_location)
            self.available_locations.remove(best_location)
            current_location = best_location
            current_time = end_time

        # 加入終點
        if current_location != self.end_location:
            travel_details = calculate_travel_time(
                current_location, self.end_location, self.travel_mode)
            travel_time = travel_details['time'].total_seconds() / 60
            arrival_time = current_time + timedelta(minutes=int(travel_time))

            if arrival_time > self.end_datetime:
                arrival_time = self.end_datetime

            itinerary.append({
                'step': len(itinerary),
                'name': self.end_location['name'],
                'start_time': arrival_time.strftime('%H:%M'),
                'end_time': arrival_time.strftime('%H:%M'),
                'duration': 0,
                'travel_time': travel_time,
                'transport_details': travel_details['transport_details'],
                'hours': self.end_location.get('hours', '24小時開放')
            })

        return itinerary
