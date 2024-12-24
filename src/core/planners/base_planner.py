from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional


class BaseTripPlanner:
    """
    行程規劃器的基礎類別，定義了規劃行程所需的基本方法和屬性
    """

    def __init__(self, start_time='09:00', end_time='20:00', travel_mode='transit',
                 distance_threshold=30, efficiency_threshold=0.1,
                 custom_start=None, custom_end=None):  # 加入自訂起終點
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
        self.start_location: Optional[Dict] = None
        self.end_location: Optional[Dict] = None
        self.available_locations: List[Dict] = []
        self.selected_locations: List[Dict] = []

    def initialize_locations(self,
                             locations: List[Dict[str, Any]],
                             custom_start: Optional[Dict] = None,
                             custom_end: Optional[Dict] = None) -> None:
        """
        初始化所有地點資訊，包括起點和終點

        參數:
            locations: 所有可能的景點列表
            custom_start: 自定義起點
            custom_end: 自定義終點
        """
        # 預設起點/終點（台北車站）
        default_point = {
            'name': '台北車站',
            'lat': 25.0426731,
            'lon': 121.5170756,
            'duration': 0,
            'label': '交通樞紐',
            'hours': '24小時開放'
        }

        # 設定起點
        self.start_location = custom_start if custom_start else default_point.copy()
        if 'duration' not in self.start_location:
            self.start_location['duration'] = 0
        if 'hours' not in self.start_location:
            self.start_location['hours'] = '24小時開放'
        if 'label' not in self.start_location:
            self.start_location['label'] = '起點'

        # 設定終點
        self.end_location = custom_end if custom_end else self.start_location.copy()

        # 儲存所有可用地點
        self.available_locations = locations.copy()

    def plan(self) -> List[Dict[str, Any]]:
        """
        執行行程規劃（抽象方法）

        返回:
            規劃好的行程列表
        """
        raise NotImplementedError("Subclasses must implement plan()")
