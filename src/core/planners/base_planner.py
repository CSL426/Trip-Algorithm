# src\core\planners\base_planner.py

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from src.core.models import PlaceDetail


class BaseTripPlanner:
    """
    行程規劃器的基礎類別
    定義了規劃行程所需的基本方法和屬性

    這個類別提供了行程規劃的基本框架，包含：
    1. 時間管理（開始和結束時間）
    2. 地點管理（起點、終點和可用地點）
    3. 交通方式設定
    4. 距離和效率的限制條件
    """

    def __init__(self, start_time='09:00', end_time='20:00', travel_mode='transit',
                 distance_threshold=30, efficiency_threshold=0.1):
        """
        初始化行程規劃器

        參數說明:
            start_time (str): 行程開始時間，格式為 'HH:MM'
            end_time (str): 行程結束時間，格式為 'HH:MM'
            travel_mode (str): 交通方式，可選值：
                - 'transit': 大眾運輸
                - 'driving': 開車
                - 'walking': 步行
                - 'bicycling': 騎自行車
            distance_threshold (float): 可接受的最大距離（公里）
            efficiency_threshold (float): 最低效率閾值，用於評估行程效率
        """
        # 將時間字串轉換為 datetime 物件，設定今天的日期
        today = datetime.now().date()
        self.start_datetime = datetime.combine(
            today,
            datetime.strptime(start_time, '%H:%M').time()
        )
        self.end_datetime = datetime.combine(
            today,
            datetime.strptime(end_time, '%H:%M').time()
        )

        # 基本設定
        self.travel_mode = travel_mode
        self.distance_threshold = distance_threshold
        self.efficiency_threshold = efficiency_threshold

        # 用餐狀態追蹤
        self.had_lunch = False
        self.had_dinner = False

        # 地點資訊初始化
        self.start_location: Optional[PlaceDetail] = None
        self.end_location: Optional[PlaceDetail] = None
        self.available_locations: List[PlaceDetail] = []
        self.selected_locations: List[PlaceDetail] = []

    def initialize_locations(self,
                             locations: List[Union[Dict, PlaceDetail]],
                             custom_start: Optional[Union[Dict,
                                                          PlaceDetail]] = None,
                             custom_end: Optional[Union[Dict, PlaceDetail]] = None) -> None:
        """
        初始化所有地點資訊，包括起點和終點

        參數說明:
            locations: 所有可能的景點列表，可接受以下兩種格式：
                1. PlaceDetail 物件列表
                2. 字典列表，每個字典包含：
                    - name (str): 地點名稱
                    - lat (float): 緯度
                    - lon (float): 經度
                    - duration_min (int): 建議停留時間（分鐘）
                    - label (str): 地點類型
                    - hours (Dict): 營業時間資訊

            custom_start: 自定義起點，可接受 PlaceDetail 物件或字典
            custom_end: 自定義終點，可接受 PlaceDetail 物件或字典
        """
        # 預設起點（台北車站）設定
        default_point = PlaceDetail(
            name='台北車站',
            lat=25.0426731,
            lon=121.5170756,
            duration_min=0,
            label='交通樞紐',
            hours={
                i: [{'start': '00:00', 'end': '23:59'}]
                for i in range(1, 8)
            }
        )

        # 處理輸入的地點列表
        self.available_locations = []
        for loc in locations:
            if isinstance(loc, PlaceDetail):
                self.available_locations.append(loc)
            else:
                # 如果是字典格式，需要轉換為 PlaceDetail
                if 'duration' in loc and 'duration_min' not in loc:
                    loc['duration_min'] = loc['duration']
                self.available_locations.append(PlaceDetail(**loc))

        # 處理起點設定
        if custom_start:
            if isinstance(custom_start, PlaceDetail):
                self.start_location = custom_start
            else:
                if 'duration' in custom_start:
                    custom_start['duration_min'] = custom_start['duration']
                self.start_location = PlaceDetail(**custom_start)
        else:
            self.start_location = default_point

        # 處理終點設定
        if custom_end:
            if isinstance(custom_end, PlaceDetail):
                self.end_location = custom_end
            else:
                if 'duration' in custom_end:
                    custom_end['duration_min'] = custom_end['duration']
                self.end_location = PlaceDetail(**custom_end)
        else:
            self.end_location = self.start_location

    def plan(self) -> List[Dict[str, Any]]:
        """
        執行行程規劃（抽象方法）

        子類別必須實作此方法來提供具體的規劃邏輯

        回傳:
            List[Dict[str, Any]]: 規劃好的行程列表，每個字典包含：
                - step (int): 順序編號
                - name (str): 地點名稱
                - start_time (str): 開始時間（HH:MM 格式）
                - end_time (str): 結束時間（HH:MM 格式）
                - duration (int): 停留時間（分鐘）
                - hours (str): 營業時間描述
                - transport_details (str): 交通方式描述
                - travel_time (float): 交通時間（分鐘）
        """
        raise NotImplementedError("子類別必須實作 plan() 方法")

    def _validate_time_range(self) -> bool:
        """
        驗證時間範圍是否合理

        回傳:
            bool: True 表示時間範圍合理，False 表示不合理
        """
        return self.start_datetime < self.end_datetime
