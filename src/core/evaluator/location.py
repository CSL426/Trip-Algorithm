# src/core/evaluator/location.py

from datetime import datetime, timedelta
from typing import Dict, Any
from src.core.models.place import PlaceDetail
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

    def calculate_score(self,
                        location: PlaceDetail,
                        current_location: PlaceDetail,
                        travel_time: float,
                        is_meal_time: bool = False) -> float:
        """計算地點的綜合評分

        計算公式：
        總分 = 效率分數(50%) + 時段適合度(30%) + 營業時間配合度(20%)

        輸入參數:
            location: 要評分的地點
            current_location: 目前位置
            travel_time: 預估交通時間(分鐘)
            is_meal_time: 是否為用餐時間

        回傳:
            float: 0-1之間的評分，或 float('-inf') 表示不適合
        """
        # 檢查營業時間
        if not self._check_business_hours(location):
            return float('-inf')

        # 計算各項評分
        efficiency_score = self._calculate_efficiency_score(
            location, current_location, travel_time)

        period_score = self._calculate_period_score(
            location, self.current_time, is_meal_time)

        time_score = self._calculate_time_score(location)

        # 計算加權總分
        score = (efficiency_score * 0.5 +
                 period_score * 0.3 +
                 time_score * 0.2)

        return score

    def _calculate_efficiency_score(self,
                                    location: PlaceDetail,
                                    current_location: PlaceDetail,
                                    travel_time: float) -> float:
        """計算效率評分

        計算公式：k / (距離 × 交通時間)
        k值根據停留時間調整：
        - 停留>=120分鐘：k=2.0
        - 停留>=60分鐘：k=1.5
        - 停留<60分鐘：k=1.0

        輸入參數:
            location: 地點資訊
            current_location: 當前位置
            travel_time: 交通時間

        回傳:
            float: 0-1之間的效率評分
        """
        # 計算距離
        distance = self.distance_calculator.calculate_distance(
            current_location, location)

        if distance > self.distance_threshold:
            return 0.0

        # 根據停留時間決定k值
        if location.duration_min >= 120:
            k = 2.0
        elif location.duration_min >= 60:
            k = 1.5
        else:
            k = 1.0

        # 避免除以零
        if distance == 0 or travel_time == 0:
            return 1.0

        # 計算效率值
        efficiency = k / (distance * travel_time)

        # 標準化到0-1之間
        return min(1.0, efficiency / 0.1)  # 0.1為基準效率值

    def _calculate_period_score(self,
                                location: PlaceDetail,
                                current_time: datetime,
                                is_meal_time: bool) -> float:
        """計算時段適合度評分

        評分標準：
        - 完全符合目前時段：1.0
        - 接近目標時段：0.7
        - 不適合的時段：0.3
        - 用餐時間的餐廳：1.0
        - 用餐時間的非餐廳：0.3

        輸入參數:
            location: 地點資訊
            current_time: 當前時間
            is_meal_time: 是否為用餐時間

        回傳:
            float: 0-1之間的時段評分
        """
        # 用餐時間特殊處理
        if is_meal_time:
            if location.label in ['餐廳', '小吃', '夜市']:
                return 1.0
            return 0.3

        # 檢查時段適合度
        hour = current_time.hour
        period = location.period

        # 時段適合度判斷
        if period == 'morning' and 9 <= hour < 11:
            return 1.0
        elif period == 'lunch' and 11 <= hour < 14:
            return 1.0
        elif period == 'afternoon' and 14 <= hour < 17:
            return 1.0
        elif period == 'dinner' and 17 <= hour < 19:
            return 1.0
        elif period == 'night' and hour >= 19:
            return 1.0

        # 接近時段的給予部分分數
        if (period == 'morning' and 8 <= hour < 9) or \
           (period == 'lunch' and 10 <= hour < 11) or \
           (period == 'afternoon' and 13 <= hour < 14) or \
           (period == 'dinner' and 16 <= hour < 17) or \
           (period == 'night' and 18 <= hour < 19):
            return 0.7

        return 0.3

    def _calculate_time_score(self, location: PlaceDetail) -> float:
        """計算營業時間配合度評分

        評分標準：
        - 營業中且離結束還有充足時間：1.0
        - 營業中但接近結束：0.7
        - 非營業時間：0.0

        輸入參數:
            location: 地點資訊

        回傳:
            float: 0-1之間的評分
        """
        weekday = self.current_time.weekday() + 1
        time_str = self.current_time.strftime('%H:%M')

        if not location.is_open_at(weekday, time_str):
            return 0.0

        # 檢查是否接近打烊時間
        close_time = None
        if weekday in location.hours and location.hours[weekday]:
            for slot in location.hours[weekday]:
                if slot and 'end' in slot:
                    close_time = datetime.strptime(slot['end'], '%H:%M').replace(
                        year=self.current_time.year,
                        month=self.current_time.month,
                        day=self.current_time.day
                    )
                    # 找到當前時段的結束時間後跳出
                    if close_time > self.current_time:
                        break

        if close_time:
            remaining_time = (
                close_time - self.current_time).total_seconds() / 3600
            if remaining_time < 1:
                return 0.7
            elif remaining_time < location.duration_min / 60:
                return 0.8

        return 1.0

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
