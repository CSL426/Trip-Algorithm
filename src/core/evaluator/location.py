# src/core/evaluator/location.py

from datetime import datetime, timedelta
from typing import Dict, Any
from src.core.models.place import PlaceDetail
from .distance import DistanceCalculator


class LocationEvaluator:
    """
    地點評分器類別
    負責計算每個地點的綜合評分，用於規劃最佳行程時的地點選擇

    主要考慮因素：
    1. 距離和交通時間
    2. 地點類型（特別是用餐時間的餐廳優先）
    3. 營業時間
    4. 停留時間的合理性
    """

    def __init__(self, current_time: datetime, distance_threshold: float):
        """
        初始化評分器

        輸入參數：
            current_time: 當前時間，用於判斷營業時間和用餐時段
            distance_threshold: 可接受的最大距離（公里）
        """
        self.current_time = current_time
        self.distance_threshold = distance_threshold
        self.distance_calculator = DistanceCalculator()

    def calculate_score(self,
                        location: PlaceDetail,
                        current_location: PlaceDetail,
                        travel_time: float,
                        is_meal_time: bool) -> float:
        """
        計算地點的綜合評分

        評分過程：
        1. 先計算基本分數（考慮距離和效率）
        2. 根據各種情況調整分數
        3. 最後檢查營業時間

        輸入參數：
            location: 要評分的地點
            current_location: 目前位置
            travel_time: 預估交通時間（分鐘）
            is_meal_time: 是否為用餐時段

        回傳：
            float: 綜合評分，分數越高代表越適合造訪
                  若回傳 float('-inf') 表示該地點不適合在此時造訪
        """
        # 先檢查是否營業中
        if not self._check_business_hours(location):
            return float('-inf')

        # 計算基礎效率分數
        base_score = self._calculate_base_efficiency(location,
                                                     current_location,
                                                     travel_time)

        # 調整各種因素
        score = base_score
        score = self._adjust_for_travel_time(score, travel_time)
        score = self._adjust_for_meal_time_priority(
            score, location, is_meal_time)

        return score

    def _calculate_base_efficiency(self,
                                   location: PlaceDetail,
                                   current_location: PlaceDetail,
                                   travel_time: float) -> float:
        """
        計算基礎效率分數

        考慮因素：
        1. 停留時間與交通時間的比例
        2. 距離是否在可接受範圍內
        """
        # 計算實際距離
        distance = self.distance_calculator.calculate_distance(
            current_location, location)

        # 如果超過距離閾值，大幅降低分數
        if distance > self.distance_threshold:
            return 0.1

        # 計算時間效率（停留時間/交通時間）
        safe_travel_time = max(travel_time, 1)  # 避免除以零
        time_efficiency = location.duration_min / safe_travel_time

        # 距離越近分數越高
        distance_factor = 1 - (distance / self.distance_threshold)

        return time_efficiency * distance_factor

    def _adjust_for_travel_time(self, score: float, travel_time: float) -> float:
        """
        根據交通時間調整分數

        調整邏輯：
        - 交通時間 < 15分鐘：維持原分數
        - 15-30分鐘：稍微降低
        - 30-45分鐘：明顯降低
        - > 45分鐘：大幅降低
        """
        if travel_time <= 15:
            return score
        elif travel_time <= 30:
            return score * 0.9
        elif travel_time <= 45:
            return score * 0.7
        else:
            return score * 0.5

    def _adjust_for_meal_time_priority(self,
                                       score: float,
                                       location: PlaceDetail,
                                       is_meal_time: bool) -> float:
        """
        根據用餐時間調整分數

        調整邏輯：
        1. 用餐時間的餐廳類型：大幅提升分數
        2. 用餐時間的非餐廳：大幅降低分數
        3. 非用餐時間維持原分數
        """
        if is_meal_time:
            if location.label in ['餐廳', '小吃', '夜市']:
                return score * 100.0  # 用餐時間的餐廳獲得極高優先級
            else:
                return score * 0.1    # 用餐時間非餐廳大幅降低優先級
        return score

    def _check_business_hours(self, location: PlaceDetail) -> bool:
        """
        檢查地點是否在營業時間內

        回傳：
            bool: True 表示營業中，False 表示未營業
        """
        weekday = self.current_time.weekday() + 1  # 1-7代表週一到週日
        time_str = self.current_time.strftime('%H:%M')
        return location.is_open_at(weekday, time_str)
