# src/core/planner/base.py

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from ..models.place import PlaceDetail
from ..models.trip import Transport, TripPlan
from ..utils.validator import TripValidator


class TripPlanner:
    """行程規劃器基礎類別"""

    def __init__(self):
        """初始化行程規劃器"""
        self.validator = TripValidator()  # 改用新的驗證器
        self.start_location = None
        self.end_location = None
        self.available_locations = []
        self.selected_locations = []
        self.travel_mode = 'transit'

        # 統計資訊
        self.total_distance = 0.0
        self.total_time = 0

    def initialize_locations(self,
                             locations: List[Union[Dict, PlaceDetail]],
                             custom_start: Optional[Union[Dict,
                                                          PlaceDetail]] = None,
                             custom_end: Optional[Union[Dict, PlaceDetail]] = None) -> None:
        """初始化地點資料

        輸入:
            locations: 地點資料列表
            custom_start: 自訂起點(選填)
            custom_end: 自訂終點(選填)
        """
        try:
            # 轉換所有地點為 PlaceDetail 物件
            self.available_locations = []
            for loc in locations:
                if isinstance(loc, dict):
                    self.validator.validate_place(loc)
                    self.available_locations.append(PlaceDetail(**loc))
                else:
                    self.available_locations.append(loc)

            # 設定起點
            if custom_start:
                if isinstance(custom_start, dict):
                    self.validator.validate_place(custom_start)
                    self.start_location = PlaceDetail(**custom_start)
                else:
                    self.start_location = custom_start
            else:
                # 使用預設起點（台北車站）
                self.start_location = PlaceDetail(
                    name='台北車站',
                    lat=25.0478,
                    lon=121.5170,
                    duration_min=0,
                    label='交通樞紐',
                    period='morning',
                    hours={i: [{'start': '00:00', 'end': '23:59'}]
                           for i in range(1, 8)}
                )

            # 設定終點
            if custom_end:
                if isinstance(custom_end, dict):
                    self.validator.validate_place(custom_end)
                    self.end_location = PlaceDetail(**custom_end)
                else:
                    self.end_location = custom_end
            else:
                self.end_location = self.start_location.model_copy()

        except TripValidator as e:
            raise ValueError(f"地點資料驗證失敗: {str(e)}")

    def plan(self,
             start_time: str = '09:00',
             end_time: str = '18:00',
             travel_mode: str = 'transit',
             distance_threshold: float = 30.0,
             requirement: dict = None) -> List[Dict[str, Any]]:
        """執行行程規劃

        這個方法使用策略模式來處理行程規劃。它會：
        1. 建立規劃的上下文（包含所有必要的參數和狀態）
        2. 使用策略工廠創建合適的策略
        3. 通過策略管理器來執行和監控規劃過程

        參數:
            start_time: 開始時間 (HH:MM格式)
            end_time: 結束時間 (HH:MM格式)
            travel_mode: 交通方式
            distance_threshold: 最大可接受距離(公里)
            requirement: 使用者需求

        回傳:
            List[Dict]: 規劃後的行程列表
        """
        requirement = requirement or {}
        try:
            self.validator.validate_trip_requirement({
                'start_time': start_time,
                'end_time': end_time,
                'transport_mode': travel_mode,
                'distance_threshold': distance_threshold,
                **requirement
            })

            self.travel_mode = travel_mode

            # 初始化時間
            today = datetime.now().date()
            self.start_datetime = datetime.combine(
                today, datetime.strptime(start_time, '%H:%M').time())
            self.end_datetime = datetime.combine(
                today, datetime.strptime(end_time, '%H:%M').time())

            # 驗證基本設定
            if not self._validate_time_range():
                raise ValueError("結束時間必須晚於開始時間")
            if not self.available_locations:
                raise ValueError("沒有可用的地點")

            # 建立策略工廠和管理器
            from src.core.planner.strategy import PlanningStrategyFactory, StrategyManager

            # 創建策略工廠
            strategy_factory = PlanningStrategyFactory(
                time_service=self.time_service,
                geo_service=self.geo_service,
                place_scoring=self.place_scoring
            )

            # 創建策略管理器
            strategy_manager = StrategyManager(strategy_factory)

            # 準備規劃上下文
            context = {
                'start_time': self.start_datetime,
                'end_time': self.end_datetime,
                'travel_mode': travel_mode,
                'distance_threshold': distance_threshold,
                'start_location': self.start_location,
                'available_places': self.available_locations,
                **requirement
            }

            # 初始化並執行策略
            strategy = strategy_manager.initialize_strategy(context)
            itinerary = strategy.execute(
                current_location=self.start_location,
                available_places=self.available_locations,
                current_time=self.start_datetime
            )

            return itinerary

        except TripValidator as e:
            raise ValueError(f"行程需求驗證失敗: {str(e)}")

    def _validate_time_range(self) -> bool:
        """驗證時間範圍的合理性"""
        return (self.start_datetime < self.end_datetime and
                (self.end_datetime - self.start_datetime).total_seconds() <= 86400)

    def _update_statistics(self, itinerary: List[Dict]) -> None:
        """更新規劃統計資訊"""
        self.total_distance = sum(item.get('travel_distance', 0)
                                  for item in itinerary)
        total_minutes = sum(item['duration'] + item['travel_time']
                            for item in itinerary)
        self.total_time = total_minutes * 60

    def get_execution_stats(self) -> Dict[str, Any]:
        """取得執行統計資訊"""
        return {
            'total_time': self.total_time,
            'visited_count': len(self.selected_locations),
            'total_distance': self.total_distance
        }

    def get_location_by_name(self, name: str) -> Optional[PlaceDetail]:
        """根據名稱取得地點資訊"""
        if not name:
            raise ValueError("地點名稱不能為空")

        if self.start_location and self.start_location.name == name:
            return self.start_location

        if self.end_location and self.end_location.name == name:
            return self.end_location

        for location in self.available_locations:
            if location.name == name:
                return location

        return None
