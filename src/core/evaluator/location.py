# src/core/evaluator/location.py

from datetime import datetime, timedelta
from typing import Dict, Any
from src.core.models.place import PlaceDetail
from src.core.utils.time_core import TimeCore
from .distance import DistanceCalculator


class LocationEvaluator:
    """地點評分器類別

    負責計算地點的綜合評分，考慮因素：
    1. 距離與交通時間
    2. 時段適合度
    3. 營業時間配合度
    4. 停留時間價值
    """

    def __init__(self, current_time: datetime, distance_threshold: float):
        """初始化評分器

        輸入參數:
            current_time: 當前時間
            distance_threshold: 可接受的最大距離(公里)
        """
        self.current_time = current_time
        self.distance_threshold = distance_threshold
        self.distance_calculator = DistanceCalculator()

    def calculate_score(self, location: PlaceDetail,
                        current_location: PlaceDetail,
                        travel_time: float,
                        is_meal_time: bool = False) -> float:
        """計算地點的綜合評分

        輸入:
            location: 要評分的地點
            current_location: 當前位置
            travel_time: 預估交通時間(分鐘)
            is_meal_time: 是否為用餐時間

        回傳:
            float: 0-1之間的評分，或 float('-inf') 表示不適合
        """
        # 檢查營業狀態
        time_str = self.current_time.strftime(TimeCore.TIME_FORMAT)
        weekday = self.current_time.weekday() + 1

        if not location.is_open_at(weekday, time_str):
            return float('-inf')

        # 計算各項分數
        efficiency_score = self._calculate_efficiency_score(
            location, current_location, travel_time)
        period_score = self._calculate_period_score(
            location, self.current_time, is_meal_time)
        time_score = self._calculate_time_score(location)

        # 加權計算
        return (efficiency_score * 0.5 +
                period_score * 0.3 +
                time_score * 0.2)

    def _calculate_efficiency_score(self,
                                    location: PlaceDetail,
                                    current_location: PlaceDetail,
                                    travel_time: float) -> float:
        """計算效率評分

        輸入:
            location: 目標地點
            current_location: 當前位置
            travel_time: 交通時間(分鐘)

        回傳:
            float: 0-1之間的效率評分
        """
        distance = self.distance_calculator.calculate_distance(
            current_location, location)

        if distance > self.distance_threshold:
            return 0.0

        # 根據停留時間調整 k 值
        k = 2.0 if location.duration_min >= 120 else \
            1.5 if location.duration_min >= 60 else 1.0

        # 避免除以零
        if distance == 0 or travel_time == 0:
            return 1.0

        # 計算效率值並標準化
        efficiency = k / (distance * travel_time)
        return min(1.0, efficiency / 0.1)

    def _calculate_period_score(self,
                                location: PlaceDetail,
                                current_time: datetime,
                                is_meal_time: bool) -> float:
        """計算時段適合度評分

        輸入:
            location: 地點資訊
            current_time: 當前時間 
            is_meal_time: 是否為用餐時間

        回傳:
            float: 0-1之間的時段評分
            - 1.0: 完全符合目標時段
            - 0.7: 接近目標時段 
            - 0.3: 不適合的時段
        """
        # 用餐時間特殊處理
        if is_meal_time:
            if location.label in ['餐廳', '小吃', '夜市']:
                return 1.0
            return 0.3

        # 使用 TimeCore 檢查時段適合度
        time_str = current_time.strftime(TimeCore.TIME_FORMAT)
        start, end = TimeCore.parse_time_range('00:00', '23:59')
        current = current_time.time()

        # 依照不同時段定義評分
        period_times = {
            # (接近時段, 最佳時段)
            'morning': (('08:00', '09:00'), ('09:00', '11:00')),
            'lunch': (('10:00', '11:00'), ('11:00', '14:00')),
            'afternoon': (('13:00', '14:00'), ('14:00', '17:00')),
            'dinner': (('16:00', '17:00'), ('17:00', '19:00')),
            'night': (('18:00', '19:00'), ('19:00', '23:59'))
        }

        if location.period not in period_times:
            return 0.3

        near_time, best_time = period_times[location.period]

        # 檢查是否在最佳時段
        best_start, best_end = TimeCore.parse_time_range(*best_time)
        if TimeCore.is_time_in_range(current, best_start, best_end):
            return 1.0

        # 檢查是否在接近時段
        near_start, near_end = TimeCore.parse_time_range(*near_time)
        if TimeCore.is_time_in_range(current, near_start, near_end):
            return 0.7

        return 0.3

    def _calculate_time_score(self, location: PlaceDetail) -> float:
        """計算營業時間配合度評分

        輸入:
            location: 地點資訊

        回傳:
            float: 0-1之間的評分
            - 1.0: 營業中且有充足時間
            - 0.8: 營業中但時間較緊
            - 0.0: 未營業
        """
        weekday = self.current_time.weekday() + 1
        time_str = self.current_time.strftime(TimeCore.TIME_FORMAT)

        if not location.is_open_at(weekday, time_str):
            return 0.0

        if location.duration_min == 0:
            return 1.0

        # 檢查是否接近打烊時間
        for slot in location.hours.get(weekday, []):
            if slot is None:
                continue

            # 使用 TimeCore 解析時間
            close_time = datetime.strptime(
                slot['end'], TimeCore.TIME_FORMAT).time()
            current = self.current_time.time()

            # 如果這是當前的營業時段
            if TimeCore.is_time_in_range(current,
                                         datetime.strptime(
                                             slot['start'], TimeCore.TIME_FORMAT).time(),
                                         close_time):

                remaining_minutes = TimeCore.calculate_duration(
                    current,
                    close_time,
                    allow_overnight=True
                )

                if remaining_minutes < 60:  # 剩不到1小時
                    return 0.7
                if remaining_minutes < location.duration_min:  # 剩餘時間不足建議停留時間
                    return 0.8
                return 1.0

        return 0.0

    def _check_business_hours(self, location: PlaceDetail) -> bool:
        """檢查地點是否在營業時間內

        輸入參數:
            location: 地點資訊

        回傳:
            bool: True表示營業中，False表示未營業
        """
        weekday = self.current_time.weekday() + 1
        time_str = self.current_time.strftime('%H:%M')

        return location.is_open_at(weekday, time_str)

    def is_meal_time(self, current_time: datetime) -> bool:
        """判斷是否為用餐時間

        輸入:
            current_time: 當前時間

        回傳:
            bool: 是否為用餐時間
        """
        lunch_time = ('11:30', '13:30')
        dinner_time = ('17:30', '19:30')

        current = current_time.time()

        # 檢查午餐時間
        lunch_start, lunch_end = TimeCore.parse_time_range(*lunch_time)
        if TimeCore.is_time_in_range(current, lunch_start, lunch_end):
            return True

        # 檢查晚餐時間
        dinner_start, dinner_end = TimeCore.parse_time_range(*dinner_time)
        return TimeCore.is_time_in_range(current, dinner_start, dinner_end)
