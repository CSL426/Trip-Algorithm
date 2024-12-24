from datetime import datetime, timedelta
from typing import Dict, Any
from .business_hours import BusinessHours


class LocationEvaluator:
    def __init__(self, current_time: datetime, distance_threshold: float):
        self.current_time = current_time
        self.distance_threshold = distance_threshold

    def calculate_score(self, location: Dict[str, Any],
                        current_location: Dict[str, Any],
                        travel_time: float,
                        is_meal_time: bool = False) -> float:
        """計算地點的綜合評分"""
        if current_location == location:
            return float('-inf')

        # 基礎效率計算
        distance = self._calculate_distance(current_location, location)
        score = self._calculate_base_efficiency(
            location, distance, travel_time)

        # 時間相關調整
        score = self._adjust_for_time_factors(score, travel_time)
        score = self._adjust_for_meal_time(score, location, is_meal_time)
        score = self._adjust_for_business_hours(score, location)

        return score

    def _calculate_distance(self, loc1: Dict, loc2: Dict) -> float:
        """計算兩地點間距離"""
        from src.core.utils import calculate_distance
        return calculate_distance(
            loc1['lat'], loc1['lon'],
            loc2['lat'], loc2['lon']
        )

    def _calculate_base_efficiency(self,
                                   location: Dict,
                                   distance: float,
                                   travel_time: float) -> float:
        """計算基礎效率分數"""
        stay_duration = location.get('duration', 0)
        safe_distance = max(distance, 0.1)
        safe_travel_time = max(travel_time, 0.1)
        return stay_duration / (safe_distance * safe_travel_time)

    def _adjust_for_time_factors(self, score: float, travel_time: float) -> float:
        """根據時間因素調整分數"""
        if travel_time > 45:
            score *= 0.5
        elif travel_time > 30:
            score *= 0.7
        return score

    def _adjust_for_meal_time(self,
                              score: float,
                              location: Dict,
                              is_meal_time: bool) -> float:
        """根據用餐時間調整分數"""
        if location.get('label') in ['餐廳', '小吃', '夜市']:
            if is_meal_time:
                score *= 2
            else:
                score *= 0.3
        elif is_meal_time:
            score *= 0.5
        return score

    def _adjust_for_business_hours(self, score: float, location: Dict) -> float:
        """根據營業時間調整分數"""
        hours_handler = BusinessHours(location['hours'])
        if not hours_handler.is_open_at(self.current_time):
            return float('-inf')

        # 如果接近打烊時間，降低分數
        next_period = hours_handler.get_next_open_period(self.current_time)
        if next_period:
            _, end_time = next_period
            remaining_minutes = (end_time.hour * 60 + end_time.minute) - \
                (self.current_time.hour * 60 + self.current_time.minute)
            if remaining_minutes < 60:
                score *= 0.5
        return score
