# src\core\planners\base_planner.py

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from src.core.models import PlaceDetail


class BaseTripPlanner:
    """
    行程規劃器的基礎類別
    定義了規劃行程所需的基本方法和屬性
    """

    def __init__(self, start_time='09:00', end_time='20:00', travel_mode='transit',
                 distance_threshold=30, efficiency_threshold=0.1):
        """
        初始化行程規劃器

        參數:
            start_time: 行程開始時間，格式為 'HH:MM'
            end_time: 行程結束時間，格式為 'HH:MM'
            travel_mode: 交通方式，可選 'transit', 'driving', 'walking', 'bicycling'
            distance_threshold: 可接受的最大距離（公里）
            efficiency_threshold: 最低效率閾值
        """
        self.start_datetime = datetime.strptime(start_time, '%H:%M')
        self.end_datetime = datetime.strptime(end_time, '%H:%M')
        self.travel_mode = travel_mode
        self.distance_threshold = distance_threshold
        self.efficiency_threshold = efficiency_threshold

        # 用餐狀態追蹤
        self.had_lunch = False
        self.had_dinner = False

        # 儲存地點資訊
        self.start_location: Optional[PlaceDetail] = None
        self.end_location: Optional[PlaceDetail] = None
        self.available_locations: List[PlaceDetail] = []
        self.selected_locations: List[PlaceDetail] = []

    def initialize_locations(self,
                             locations: List[PlaceDetail],
                             custom_start: Optional[PlaceDetail] = None,
                             custom_end: Optional[PlaceDetail] = None) -> None:
        """
        初始化所有地點資訊，包括起點和終點

        參數:
            locations: 所有可能的景點列表（PlaceDetail 物件）
            custom_start: 自定義起點（PlaceDetail 物件）
            custom_end: 自定義終點（PlaceDetail 物件）
        """
        # 預設起點（台北車站）
        default_point = PlaceDetail(
            name='台北車站',
            lat=25.0426731,
            lon=121.5170756,
            duration_min=0,
            label='交通樞紐',
            hours={
                1: [{'start': '00:00', 'end': '23:59'}],
                2: [{'start': '00:00', 'end': '23:59'}],
                3: [{'start': '00:00', 'end': '23:59'}],
                4: [{'start': '00:00', 'end': '23:59'}],
                5: [{'start': '00:00', 'end': '23:59'}],
                6: [{'start': '00:00', 'end': '23:59'}],
                7: [{'start': '00:00', 'end': '23:59'}]
            }
        )

        # 設定起點
        self.start_location = custom_start if custom_start else default_point

        # 設定終點
        self.end_location = custom_end if custom_end else self.start_location

        # 儲存所有可用地點
        self.available_locations = locations

    def plan(self) -> List[Dict[str, Any]]:
        """
        執行行程規劃（抽象方法）

        返回:
            規劃好的行程列表，每個項目包含:
                - step: 順序編號
                - name: 地點名稱
                - start_time: 開始時間
                - end_time: 結束時間
                - duration: 停留時間
                - hours: 營業時間
                - transport_details: 交通方式
                - travel_time: 交通時間
        """
        raise NotImplementedError("子類別必須實作 plan() 方法")
