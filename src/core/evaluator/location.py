# src/core/evaluator/location.py

from datetime import datetime, timedelta
from typing import Dict, Any
from .distance import DistanceCalculator


class LocationEvaluator:
    """
    地點評分器類別
    負責計算每個地點的綜合評分，用於規劃最佳行程時的地點選擇

    這個評分器綜合考慮了多個面向：
    1. 距離和交通時間的效率性
    2. 營業時間的適合度
    3. 用餐時間的配合度
    4. 停留時間的合理性

    主要使用場景：
    - 在行程規劃時，為每個候選地點計算適合度分數
    - 根據當前時間和位置，找出最佳的下一個造訪地點
    - 優化整體行程的時間利用效率
    """

    def __init__(self, current_time: datetime, distance_threshold: float):
        """
        初始化地點評分器

        輸入參數:
            current_time (datetime): 當前時間點
                這個時間點會影響營業時間的判斷和用餐時間的考量
            distance_threshold (float): 可接受的最大距離（公里）
                用於過濾距離過遠的地點，並調整距離分數

        使用範例:
            evaluator = LocationEvaluator(
                current_time=datetime.now(),
                distance_threshold=30.0
            )
        """
        self.current_time = current_time
        self.distance_threshold = distance_threshold
        self.distance_calculator = DistanceCalculator()

    def calculate_score(self,
                        location: Dict[str, Any],
                        current_location: Dict[str, Any],
                        travel_time: float,
                        is_meal_time: bool = False) -> float:
        """
        計算地點的綜合評分

        這個方法整合了多個評分面向，每個面向都有其權重和調整因子。
        最終分數越高，表示該地點越適合在當前情況下造訪。

        輸入參數:
            location (Dict): 目標地點資訊，需包含:
                - lat: 緯度
                - lon: 經度
                - duration: 建議停留時間(分鐘)
                - label: 地點類型標籤
                - hours: 營業時間資訊
            current_location (Dict): 目前位置資訊，格式同上
            travel_time (float): 預估交通時間（分鐘）
            is_meal_time (bool): 是否為用餐時段

        回傳:
            float: 綜合評分，分數越高代表越適合造訪
                  若回傳 float('-inf') 代表該地點不適合在此時造訪
        """
        # 檢查是否為同一地點
        if current_location == location:
            return float('-inf')

        # 計算基礎分數
        base_score = self._calculate_base_efficiency(
            location, current_location, travel_time)

        # 進行各種調整
        score = base_score
        score = self._adjust_for_time_factors(score, travel_time)
        score = self._adjust_for_meal_time(score, location, is_meal_time)
        score = self._adjust_for_business_hours(score, location)

        return score

    def _calculate_base_efficiency(self,
                                   location: Dict,
                                   current_location: Dict,
                                   travel_time: float) -> float:
        """
        計算基礎效率分數

        考慮因素：
        1. 停留時間與交通時間的比例
        2. 實際距離與閾值的關係
        3. 地點本身的重要性（由停留時間反映）

        輸入參數:
            location (Dict): 目標地點資訊
            current_location (Dict): 目前位置
            travel_time (float): 交通時間（分鐘）

        回傳:
            float: 基礎效率分數
        """
        # 計算實際距離
        distance = self.distance_calculator.calculate_distance(
            current_location, location)

        # 取得距離評分因子
        distance_factor = self.distance_calculator.get_distance_factor(
            distance, self.distance_threshold)

        # 計算時間效率
        stay_duration = location.get('duration', 0)
        safe_travel_time = max(travel_time, 0.1)  # 避免除以零
        time_efficiency = stay_duration / safe_travel_time

        return time_efficiency * distance_factor

    def _adjust_for_time_factors(self,
                                 score: float,
                                 travel_time: float) -> float:
        """
        根據時間因素調整分數

        主要考慮：
        1. 交通時間過長會降低評分
        2. 不同時段的交通狀況影響
        3. 時間利用的效率性

        輸入參數:
            score (float): 原始分數
            travel_time (float): 交通時間（分鐘）

        回傳:
            float: 調整後的分數
        """
        if travel_time > 45:
            score *= 0.5  # 交通時間過長，大幅降低分數
        elif travel_time > 30:
            score *= 0.7  # 交通時間較長，適度降低分數
        return score

    def _adjust_for_meal_time(self,
                              score: float,
                              location: Dict,
                              is_meal_time: bool) -> float:
        """
        根據用餐時間調整分數

        考慮因素：
        1. 是否為餐飲類地點
        2. 當前是否為用餐時段
        3. 不同類型餐廳的適用時段

        輸入參數:
            score (float): 原始分數
            location (Dict): 地點資訊
            is_meal_time (bool): 是否為用餐時段

        回傳:
            float: 調整後的分數
        """
        if location.get('label') in ['餐廳', '小吃', '夜市']:
            if is_meal_time:
                score *= 2.0  # 用餐時段的餐廳提高權重
            else:
                score *= 0.3  # 非用餐時段的餐廳降低權重
        elif is_meal_time:
            score *= 0.5  # 用餐時段的非餐廳降低權重

        return score

    def _adjust_for_business_hours(self,
                                   score: float,
                                   location: Dict) -> float:
        """
        根據營業時間調整分數

        考慮因素：
        1. 當前是否在營業時間內
        2. 距離打烊時間的剩餘時間
        3. 特殊營業時段的影響

        輸入參數:
            score (float): 原始分數
            location (Dict): 地點資訊

        回傳:
            float: 調整後的分數
            若地點未營業，回傳 float('-inf')
        """
        # 檢查是否營業中
        weekday = self.current_time.weekday() + 1  # 轉換到 1-7 的星期格式
        if not location.is_open_at(weekday,
                                   self.current_time.strftime('%H:%M')):
            return float('-inf')

        # 檢查距離打烊時間
        # 使用地點的營業時間資訊來計算剩餘時間
        hours = location.hours.get(weekday, [])
        for period in hours:
            if period is None:
                continue

            end_time = datetime.strptime(period['end'], '%H:%M').time()
            current_minutes = self.current_time.hour * 60 + self.current_time.minute
            end_minutes = end_time.hour * 60 + end_time.minute

            # 如果在當前營業時段
            if end_minutes > current_minutes:
                remaining_minutes = end_minutes - current_minutes
                if remaining_minutes < 60:
                    score *= 0.5  # 接近打烊時間，降低評分

                break

        return score
