# src/core/planner/base.py

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union

from src.core.models.place import PlaceDetail
from src.core.models.trip import Transport, TripPlan
from .validator import InputValidator
from .strategy import PlanningStrategy


class TripPlanner:
    """行程規劃器基礎類別

    此類別負責：
    1. 整合驗證器和規劃策略
    2. 管理規劃過程的資源
    3. 提供統一的規劃介面
    """

    def __init__(self):
        """初始化行程規劃器"""
        self.validator = InputValidator()
        self.start_location = None
        self.end_location = None
        self.available_locations = []
        self.selected_locations = []

        # 統計資訊
        self.total_distance = 0.0
        self.total_time = 0

    def initialize_locations(self,
                             locations: List[Union[Dict, PlaceDetail]],
                             custom_start: Optional[Union[Dict,
                                                          PlaceDetail]] = None,
                             custom_end: Optional[Union[Dict, PlaceDetail]] = None) -> None:
        """初始化地點資料

        輸入參數:
            locations: 地點資料列表
            custom_start: 自訂起點(選填)
            custom_end: 自訂終點(選填)

        處理流程:
        1. 驗證所有地點資料
        2. 設定起點和終點
        3. 初始化可用地點列表
        """
        # 建立預設起點(台北車站)
        default_start = PlaceDetail(
            name='台北車站',
            lat=25.0478,
            lon=121.5170,
            duration_min=0,
            label='交通樞紐',
            period='morning',  # 加入預設時段
            hours={i: [{'start': '00:00', 'end': '23:59'}]
                   for i in range(1, 8)}
        )

        # 驗證地點資料
        validated_locations = []
        for loc in locations:
            if isinstance(loc, dict):
                if 'duration' in loc and 'duration_min' not in loc:
                    loc['duration_min'] = loc['duration']
                if 'period' not in loc:  # 確保有 period 欄位
                    loc['period'] = self._determine_default_period(loc)
                validated_locations.append(PlaceDetail(**loc))
            else:
                validated_locations.append(loc)

        self.available_locations = validated_locations

        # 處理起點
        if custom_start:
            if isinstance(custom_start, dict):
                if 'period' not in custom_start:
                    custom_start['period'] = 'morning'
                self.start_location = PlaceDetail(**custom_start)
            else:
                self.start_location = custom_start
        else:
            self.start_location = default_start

        # 處理終點
        if custom_end:
            if isinstance(custom_end, dict):
                if 'period' not in custom_end:
                    custom_end['period'] = 'night'
                self.end_location = PlaceDetail(**custom_end)
            else:
                self.end_location = custom_end
        else:
            self.end_location = self.start_location.model_copy()

    def _determine_default_period(self, location: Dict) -> str:
        """根據地點類型判斷預設的時段

        輸入參數:
            location: 地點資料

        回傳:
            str: 預設時段標記
        """
        label = location.get('label', '').lower()

        if '餐廳' in label or '小吃' in label:
            # 檢查營業時間來判斷是午餐還是晚餐地點
            hours = location.get('hours', {}).get(1, [])  # 以週一為例
            if hours and hours[0]:
                start_time = hours[0].get('start', '00:00')
                if start_time < '15:00':
                    return 'lunch'
                return 'dinner'
        elif '夜市' in label or 'night' in label.lower():
            return 'night'

        # 根據營業時間判斷
        hours = location.get('hours', {}).get(1, [])
        if hours and hours[0]:
            start_time = hours[0].get('start', '00:00')
            if start_time >= '17:00':
                return 'night'
            elif start_time >= '14:00':
                return 'afternoon'
            elif start_time >= '11:00':
                return 'lunch'
            else:
                return 'morning'

        return 'afternoon'  # 預設為下午

    def plan(self,
             start_time: str = '09:00',
             end_time: str = '18:00',
             travel_mode: str = 'transit',
             distance_threshold: float = 30.0,
             efficiency_threshold: float = 0.1,
             requirement: dict = None) -> List[Dict[str, Any]]:
        """執行行程規劃

        輸入參數:
            start_time: 開始時間 (HH:MM格式)
            end_time: 結束時間 (HH:MM格式)
            travel_mode: 交通方式
            distance_threshold: 最大可接受距離(公里)
            efficiency_threshold: 最低效率閾值
            requirement: 使用者需求(包含用餐時間等)

        回傳:
            List[Dict]: 規劃後的行程列表
        """
        # 儲存交通方式
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

        # 初始化規劃策略
        strategy = PlanningStrategy(
            start_time=self.start_datetime,
            end_time=self.end_datetime,
            travel_mode=travel_mode,
            distance_threshold=distance_threshold,
            efficiency_threshold=efficiency_threshold,
            requirement=requirement
        )

        # 執行規劃
        itinerary = strategy.execute(
            current_location=self.start_location,
            available_locations=self.available_locations,
            current_time=self.start_datetime
        )

        # 更新統計資訊
        if itinerary:
            self._update_statistics(itinerary)

        return itinerary

    def _validate_time_range(self) -> bool:
        """驗證時間範圍的合理性

        回傳:
            bool: True表示時間範圍合理，False則否
        """
        return (self.start_datetime < self.end_datetime and
                (self.end_datetime - self.start_datetime).total_seconds() <= 86400)

    def _update_statistics(self, itinerary: List[Dict]) -> None:
        """更新規劃統計資訊

        輸入參數:
            itinerary: 完整行程列表
        """
        self.total_distance = sum(item.get('travel_distance', 0)
                                  for item in itinerary)
        total_minutes = sum(item['duration'] + item['travel_time']
                            for item in itinerary)
        self.total_time = total_minutes * 60

    def get_execution_stats(self) -> Dict[str, Any]:
        """取得執行統計資訊

        回傳:
            Dict: 包含執行相關的統計資料
        """
        return {
            'total_time': self.total_time,
            'visited_count': len(self.selected_locations),
            'total_distance': self.total_distance
        }

    def get_location_by_name(self, name: str) -> Optional[PlaceDetail]:
        """根據名稱取得地點資訊

        輸入參數:
            name: str - 地點名稱

        回傳:
            Optional[PlaceDetail]: 找到的地點資訊,找不到則回傳 None
        """
        # 檢查起點
        if self.start_location and self.start_location.name == name:
            return self.start_location

        # 檢查終點
        if self.end_location and self.end_location.name == name:
            return self.end_location

        # 檢查所有可用地點
        for location in self.available_locations:
            if location.name == name:
                return location

        return None

    def get_travel_info(self,
                        from_location: PlaceDetail,
                        to_location: PlaceDetail,
                        departure_time: str) -> Dict:
        """計算兩地點間的交通資訊

        輸入參數:
            from_location: PlaceDetail - 起點資訊
            to_location: PlaceDetail - 終點資訊 
            departure_time: str - 出發時間 (HH:MM格式)

        回傳:
            Dict: {
                'time': float,              # 交通時間(分鐘)
                'transport_details': str,    # 交通方式說明
                'distance': float,          # 距離(公里)
                'route_info': Dict,         # Google Maps API 回傳的路線資訊
                'navigation_text': str      # 中文導航說明
            }
        """
        from src.core.utils.navigation_translator import NavigationTranslator

        # 將出發時間轉換為 datetime
        departure_dt = datetime.strptime(departure_time, '%H:%M')

        # 使用策略計算交通資訊
        strategy = PlanningStrategy(
            start_time=departure_dt,
            end_time=departure_dt + timedelta(hours=24),  # 設一個虛擬的結束時間
            travel_mode=self.travel_mode
        )

        # 取得基本交通資訊
        travel_info = strategy._calculate_travel_info(
            from_location=from_location,
            to_location=to_location,
            departure_time=departure_dt,
            use_api=True  # 使用 Google Maps API 獲取詳細路線
        )

        # 如果有路線資訊,添加中文導航說明
        if 'route_info' in travel_info:
            travel_info['navigation_text'] = NavigationTranslator.format_navigation(
                travel_info['route_info']
            )

        return travel_info
