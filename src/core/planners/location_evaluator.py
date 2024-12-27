# src\core\planners\location_evaluator.py

from datetime import datetime, timedelta
from typing import Dict, Any


class LocationEvaluator:
    """
    地點評分器類別
    負責計算每個地點的綜合評分，用於行程規劃時的地點選擇

    主要功能:
    1. 計算基礎效率分數
    2. 根據時間進行分數調整
    3. 根據用餐時間調整分數
    4. 考慮營業時間的影響
    """

    def __init__(self, current_time: datetime, distance_threshold: float):
        """
        初始化地點評分器

        輸入參數:
            current_time (datetime): 當前時間點
            distance_threshold (float): 可接受的最大距離（公里）
        """
        self.current_time = current_time
        self.distance_threshold = distance_threshold

    def calculate_score(self,
                        location: Dict[str, Any],
                        current_location: Dict[str, Any],
                        travel_time: float,
                        is_meal_time: bool = False) -> float:
        """
        計算地點的綜合評分

        輸入參數:
            location (Dict): 目標地點資訊，需包含:
                - lat: 緯度
                - lon: 經度
                - duration: 建議停留時間(分鐘)
                - label: 地點類型標籤
            current_location (Dict): 目前位置資訊
            travel_time (float): 交通所需時間(分鐘)
            is_meal_time (bool): 是否為用餐時段

        回傳:
            float: 綜合評分，分數越高代表越適合造訪
            若回傳 float('-inf') 代表該地點不適合在此時造訪

        評分考慮因素:
        1. 距離與交通時間的效率
        2. 時間相關的調整（尖峰、用餐）
        3. 營業時間的限制
        4. 地點類型的權重
        """
        # 檢查是否為同一地點
        if current_location == location:
            return float('-inf')

        # 計算基礎分數
        distance = self._calculate_distance(current_location, location)
        score = self._calculate_base_efficiency(
            location, distance, travel_time)

        # 進行各種調整
        score = self._adjust_for_time_factors(score, travel_time)
        score = self._adjust_for_meal_time(score, location, is_meal_time)
        score = self._adjust_for_business_hours(score, location)

        return score

    def _calculate_distance(self, loc1: Dict, loc2: Dict) -> float:
        """
        計算兩地點間的直線距離

        輸入參數:
            loc1 (Dict): 起點資訊，需包含 lat(緯度)、lon(經度)
            loc2 (Dict): 終點資訊，需包含 lat(緯度)、lon(經度)

        回傳:
            float: 兩地點間的直線距離（公里）
        """
        from src.core.utils import calculate_distance
        return calculate_distance(
            loc1['lat'], loc1['lon'],
            loc2['lat'], loc2['lon']
        )

    def _calculate_base_efficiency(self,
                                   location: Dict,
                                   distance: float,
                                   travel_time: float) -> float:
        """
        計算基礎效率分數

        計算公式: 停留時間 / (距離 * 交通時間)

        輸入參數:
            location (Dict): 地點資訊，需包含 duration(建議停留時間)
            distance (float): 距離（公里）
            travel_time (float): 交通時間（分鐘）

        回傳:
            float: 基礎效率分數，分數越高代表效率越好
        """
        stay_duration = location.get('duration', 0)
        safe_distance = max(distance, 0.1)  # 避免除以零
        safe_travel_time = max(travel_time, 0.1)  # 避免除以零
        return stay_duration / (safe_distance * safe_travel_time)

    def _adjust_for_time_factors(self, score: float, travel_time: float) -> float:
        """
        根據時間因素調整分數

        輸入參數:
            score (float): 原始分數
            travel_time (float): 交通時間（分鐘）

        回傳:
            float: 調整後的分數

        調整規則:
        - 交通時間 > 45分鐘: 分數減半
        - 交通時間 > 30分鐘: 分數 * 0.7
        """
        if travel_time > 45:
            score *= 0.5
        elif travel_time > 30:
            score *= 0.7
        return score

    def _adjust_for_meal_time(self,
                              score: float,
                              location: Dict,
                              is_meal_time: bool) -> float:
        """
        根據用餐時間調整分數

        輸入參數:
            score (float): 原始分數
            location (Dict): 地點資訊，需包含 label(地點類型)
            is_meal_time (bool): 是否為用餐時段

        回傳:
            float: 調整後的分數

        調整規則:
        - 用餐時段的餐廳分數 * 2
        - 非用餐時段的餐廳分數 * 0.3
        - 用餐時段的非餐廳分數 * 0.5
        """
        if location.get('label') in ['餐廳', '小吃', '夜市']:
            if is_meal_time:
                score *= 2
            else:
                score *= 0.3
        elif is_meal_time:
            score *= 0.5
        return score

    def _adjust_for_business_hours(self, score: float, location: Dict) -> float:
        """
        根據營業時間調整分數

        輸入參數:
            score (float): 原始分數
            location (Dict): 地點資訊，需包含:
                - hours: 營業時間資訊
                - is_open_at: 檢查營業狀態的方法

        回傳:
            float: 調整後的分數
            若地點在當前時間未營業，回傳 float('-inf')

        調整規則:
        - 非營業時間回傳 -inf
        - 接近打烊時間（剩餘<60分鐘）分數 * 0.5
        """
        # 檢查是否營業中
        if not location.is_open_at(self.current_time.weekday() + 1,
                                   self.current_time.strftime('%H:%M')):
            return float('-inf')

        # 檢查是否接近打烊
        # 使用原本的營業時間資料來計算剩餘時間
        weekday = self.current_time.weekday() + 1
        hours = location.hours.get(weekday, [])

        for period in hours:
            if period is None:
                continue

            end_time = datetime.strptime(period['end'], '%H:%M').time()
            current_minutes = self.current_time.hour * 60 + self.current_time.minute
            end_minutes = end_time.hour * 60 + end_time.minute

            if end_minutes > current_minutes:  # 如果還在當前營業時段
                remaining_minutes = end_minutes - current_minutes
                if remaining_minutes < 60:
                    score *= 0.5
                break

        return score
