# src/core/evaluator/place_scoring.py

from datetime import datetime, timedelta
from typing import Dict, Optional
from src.core.models.place import PlaceDetail
from src.core.services.time_service import TimeService


class PlaceScoring:
    """
    地點評分系統

    負責計算每個地點的綜合評分，主要考慮：
    1. 基礎評分(rating)：地點本身的評價
    2. 效率評分：考慮停留時間與交通時間的比值
    """

    def __init__(self, time_service: TimeService):
        """
        初始化評分系統

        參數:
            time_service: 時間服務，用於判斷時段
        """
        self.time_service = time_service
        self.efficiency_base = 1.5  # 效率基準值

    def calculate_score(self,
                        place: PlaceDetail,
                        current_location: PlaceDetail,
                        current_time: datetime,
                        travel_time: float) -> float:
        """
        計算地點的綜合評分

        參數:
            place: 要評分的地點
            current_location: 當前位置
            current_time: 當前時間
            travel_time: 預估交通時間(分鐘)

        回傳:
            float: 0-1之間的評分，或 float('-inf') 表示不適合
        """
        # 檢查營業時間
        if not self._check_business_hours(place, current_time):
            return float('-inf')

        # 計算效率評分
        efficiency_score = self._calculate_efficiency_score(
            place=place,
            travel_time=travel_time,
            is_meal_time=self.time_service.is_meal_time(current_time)
        )

        # 計算基礎評分
        base_score = self._calculate_base_score(place)

        # 加權計算最終分數
        return efficiency_score * 0.6 + base_score * 0.4

    def _calculate_efficiency_score(self,
                                    place: PlaceDetail,
                                    travel_time: float,
                                    is_meal_time: bool) -> float:
        """
        計算效率評分

        參數:
            place: 要評分的地點
            travel_time: 交通時間(分鐘)
            is_meal_time: 是否為用餐時段

        回傳:
            float: 0-1之間的效率評分
        """
        # 避免除以零
        if travel_time <= 0:
            return 1.0

        # 計算基本效率係數
        efficiency = place.duration_min / travel_time

        # 在非用餐時段，餐飲類地點獲得額外加權
        if not is_meal_time and place.label in ['餐廳', '小吃']:
            efficiency *= 1.5

        # 標準化到0-1區間
        normalized_score = min(1.0, efficiency / self.efficiency_base)

        return normalized_score

    def _calculate_base_score(self, place: PlaceDetail) -> float:
        """
        計算基礎評分

        參數:
            place: 要評分的地點

        回傳:
            float: 0-1之間的基礎評分
        """
        # 將評分從0-5標準化到0-1區間
        return min(1.0, place.rating / 5.0)

    def _check_business_hours(self,
                              place: PlaceDetail,
                              current_time: datetime) -> bool:
        """
        檢查是否在營業時間內

        參數:
            place: 要檢查的地點
            current_time: 當前時間

        回傳:
            bool: True表示營業中，False表示未營業
        """
        weekday = current_time.weekday() + 1  # 1-7代表週一到週日
        time_str = current_time.strftime('%H:%M')
        return place.is_open_at(weekday, time_str)
