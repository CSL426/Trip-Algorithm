# src/core/evaluator/scoring_system.py

from datetime import datetime
from typing import Dict
from src.core.models.place import PlaceDetail
from src.core.utils.time_core import TimeCore


class ScoringSystem:
    """地點評分系統

    負責:
    1. 計算地點的綜合評分
    2. 時段適合度評估
    3. 效率分數計算
    4. 各種評分規則的管理
    """

    def __init__(self, current_time: datetime, distance_threshold: float):
        """初始化評分系統

        輸入:
            current_time: 當前時間
            distance_threshold: 可接受的最大距離(公里)
        """
        self.current_time = current_time
        self.distance_threshold = distance_threshold

        # 時段定義
        self.period_times = {
            # (接近時段, 最佳時段)
            'morning': (('08:00', '09:00'), ('09:00', '11:00')),
            'lunch': (('10:00', '11:00'), ('11:00', '14:00')),
            'afternoon': (('13:00', '14:00'), ('14:00', '17:00')),
            'dinner': (('16:00', '17:00'), ('17:00', '19:00')),
            'night': (('18:00', '19:00'), ('19:00', '23:59'))
        }

    def calculate_total_score(self,
                              location: PlaceDetail,
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
        efficiency = self._calculate_efficiency_score(
            location, current_location, travel_time)
        period = self._calculate_period_score(location, is_meal_time)
        time = self._calculate_time_score(location)

        # 加權計算
        return (efficiency * 0.5 + period * 0.3 + time * 0.2)

    def _calculate_efficiency_score(self,
                                    location: PlaceDetail,
                                    current_location: PlaceDetail,
                                    travel_time: float) -> float:
        """計算效率評分

        考慮:
        1. 距離 - 距離越遠分數越低
        2. 交通時間 - 交通時間越長分數越低
        3. 停留時間價值 - 停留時間越長權重越高

        輸入:
            location: 目標地點
            current_location: 當前位置
            travel_time: 交通時間(分鐘)

        回傳:
            float: 0-1之間的效率評分
        """
        # 計算距離
        distance = location.calculate_distance(current_location)

        # 如果超過最大距離限制，直接回傳 0
        if distance > self.distance_threshold:
            return 0.0

        # 避免除以零
        if distance == 0 or travel_time == 0:
            return 1.0

        # 根據停留時間調整權重 k
        # - 停留超過2小時的景點 k=2.0，表示值得遠行
        # - 停留1-2小時的景點 k=1.5
        # - 停留不到1小時的景點 k=1.0，表示不值得遠行
        k = 2.0 if location.duration_min >= 120 else \
            1.5 if location.duration_min >= 60 else 1.0

        # 計算距離權重 (距離越遠權重越低)
        distance_weight = max(0, 1 - (distance / self.distance_threshold))

        # 計算效率值
        # 效率 = k * 停留時間 * 距離權重 / 交通時間
        efficiency = k * location.duration_min * distance_weight / travel_time

        # 標準化到 0-1 之間
        return min(1.0, efficiency / 0.1)

    def _calculate_period_score(self,
                                location: PlaceDetail,
                                is_meal_time: bool) -> float:
        """計算時段適合度評分"""
        # 用餐時間特殊處理
        if is_meal_time:
            if location.label in ['餐廳', '小吃', '夜市']:
                return 1.0
            return 0.3

        current = self.current_time.time()

        if location.period not in self.period_times:
            return 0.3

        near_time, best_time = self.period_times[location.period]

        # 檢查最佳時段
        best_start, best_end = TimeCore.parse_time_range(*best_time)
        if TimeCore.is_time_in_range(current, best_start, best_end):
            return 1.0

        # 檢查接近時段
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
