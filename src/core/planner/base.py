# src/core/planner/base.py

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union

from src.core.models.place import PlaceDetail
from src.core.models.trip import Transport, TripPlan
from .validator import InputValidator
from .strategy import PlanningStrategy


class TripPlanner:
    """
    行程規劃器的基礎類別
    此類別定義了行程規劃的核心架構和基本流程

    主要職責：
    1. 管理規劃過程中的各種資源（時間、地點、交通等）
    2. 提供統一的規劃介面
    3. 確保規劃過程的正確性和完整性

    使用方式：
    planner = TripPlanner()
    planner.initialize_locations(locations, custom_start, custom_end)
    result = planner.plan(start_time='09:00', end_time='18:00')
    """

    def __init__(self):
        """
        初始化行程規劃器
        設定基本的規劃參數和資源
        """
        self.validator = InputValidator()
        self.start_location = None
        self.end_location = None
        self.available_locations = []
        self.selected_locations = []

        # 用餐狀態追蹤
        self.had_lunch = False
        self.had_dinner = False

        # 統計資訊
        self.total_distance = 0.0
        self.total_time = 0

    def initialize_locations(self,
                             locations: List[Union[Dict, PlaceDetail]],
                             custom_start: Optional[Union[Dict,
                                                          PlaceDetail]] = None,
                             custom_end: Optional[Union[Dict, PlaceDetail]] = None) -> None:
        """
        初始化所有地點資訊

        這個方法負責：
        1. 將輸入的字典資料轉換為 PlaceDetail 物件
        2. 設定起點和終點
        3. 初始化可用地點列表

        輸入參數：
            locations: 地點資料列表，每個元素可以是字典或 PlaceDetail 物件
            custom_start: 自訂起點（選填）
            custom_end: 自訂終點（選填）
        """
        # 建立預設起點（台北車站）
        default_start = PlaceDetail(
            name='台北車站',
            lat=25.0478,
            lon=121.5170,
            duration_min=0,
            label='交通樞紐',
            hours={i: [{'start': '00:00', 'end': '23:59'}]
                   for i in range(1, 8)}
        )

        # 處理所有地點
        validated_locations = []
        for loc in locations:
            if isinstance(loc, dict):
                # 確保 duration_min 欄位存在
                if 'duration' in loc and 'duration_min' not in loc:
                    loc['duration_min'] = loc['duration']
                validated_locations.append(PlaceDetail(**loc))
            else:
                validated_locations.append(loc)

        self.available_locations = validated_locations

        # 處理起點
        if custom_start:
            if isinstance(custom_start, dict):
                self.start_location = PlaceDetail(**custom_start)
            else:
                self.start_location = custom_start
        else:
            self.start_location = default_start

        # 處理終點
        if custom_end:
            if isinstance(custom_end, dict):
                self.end_location = PlaceDetail(**custom_end)
            else:
                self.end_location = custom_end
        else:
            self.end_location = self.start_location.model_copy()

    def plan(self,
             start_time: str = '09:00',
             end_time: str = '18:00',
             travel_mode: str = 'transit',
             distance_threshold: float = 30.0,
             efficiency_threshold: float = 0.1) -> List[Dict[str, Any]]:
        """
        執行行程規劃

        這個方法會：
        1. 設定規劃參數
        2. 驗證時間和交通設定
        3. 執行實際的規劃流程
        4. 產生最終的行程結果

        輸入參數：
            start_time: 開始時間（HH:MM格式）
            end_time: 結束時間（HH:MM格式）
            travel_mode: 交通方式（transit/driving/walking/bicycling）
            distance_threshold: 可接受的最大距離（公里）
            efficiency_threshold: 最低效率閾值

        回傳：
            List[Dict]: 規劃好的行程列表，每個字典包含：
                - step: 順序編號
                - name: 地點名稱
                - start_time: 到達時間
                - end_time: 離開時間
                - duration: 停留時間
                - transport_details: 交通方式
                - travel_time: 交通時間
        """
        # 初始化規劃時間
        today = datetime.now().date()
        self.start_datetime = datetime.combine(
            today, datetime.strptime(start_time, '%H:%M').time())
        self.end_datetime = datetime.combine(
            today, datetime.strptime(end_time, '%H:%M').time())

        # 驗證設定
        if not self._validate_time_range():
            raise ValueError("結束時間必須晚於開始時間")
        if not self.available_locations:
            raise ValueError("沒有可用的地點")

        # 初始化規劃參數
        self.travel_mode = travel_mode
        self.distance_threshold = distance_threshold
        self.efficiency_threshold = efficiency_threshold

        # 產生行程
        return self._generate_itinerary()

    def _validate_time_range(self) -> bool:
        """
        驗證時間範圍的合理性

        檢查：
        1. 結束時間是否晚於開始時間
        2. 時間範圍是否合理（例如不超過24小時）

        回傳：
            bool: True 表示時間範圍合理，False 則否
        """
        return (self.start_datetime < self.end_datetime and
                (self.end_datetime - self.start_datetime).total_seconds() <= 86400)

    def _generate_itinerary(self) -> List[Dict[str, Any]]:
        """
        生成完整的行程安排

        此方法整合了以下功能：
        1. 使用 PlanningStrategy 進行路線規劃
        2. 處理時間和交通資訊
        3. 產生標準格式的行程輸出

        回傳：
            List[Dict]: 行程列表，每個字典包含：
                - step: 順序編號
                - name: 地點名稱
                - start_time: 到達時間
                - end_time: 離開時間
                - duration: 停留時間（分鐘）
                - transport_details: 交通方式說明
                - travel_time: 交通所需時間
        """
        # 建立規劃策略
        strategy = PlanningStrategy(
            start_time=self.start_datetime,
            end_time=self.end_datetime,
            travel_mode=self.travel_mode,
            distance_threshold=self.distance_threshold,
            efficiency_threshold=self.efficiency_threshold
        )

        # 執行行程規劃
        itinerary = strategy.execute(
            current_location=self.start_location,
            available_locations=self.available_locations,
            current_time=self.start_datetime
        )

        # 更新總距離和時間（用於統計資訊）
        if itinerary:
            self.total_distance = sum(
                item.get('travel_distance', 0) for item in itinerary)
            total_minutes = sum(item['duration'] +
                                item['travel_time'] for item in itinerary)
            self.total_time = total_minutes * 60  # 轉換為秒

        return itinerary

    def get_execution_stats(self) -> Dict[str, Any]:
        """
        取得執行統計資訊

        回傳：
            Dict: 包含執行相關的統計資料
                - total_time: 總執行時間（秒）
                - visited_count: 造訪地點數量
                - total_distance: 總距離（公里）
        """
        return {
            'total_time': self.total_time,
            'visited_count': len(self.selected_locations),
            'total_distance': self.total_distance
        }
