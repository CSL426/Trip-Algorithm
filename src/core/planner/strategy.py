# src/core/planner/strategy.py

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import random
from src.core.models.place import PlaceDetail
from src.core.evaluator import LocationEvaluator
from src.core.utils.geo import GeoCalculator


class PlanningStrategy:
    """行程規劃策略類別

    此類別負責行程規劃的核心邏輯，包含：
    1. 依據時段選擇適合的景點
    2. 計算並評分可行的選項
    3. 產生最終的行程建議
    """

    def __init__(self,
                 start_time: datetime,
                 end_time: datetime,
                 travel_mode: str = 'transit',
                 distance_threshold: float = 30.0,
                 efficiency_threshold: float = 0.1,
                 requirement: dict = None):
        """初始化規劃策略

        輸入參數:
            start_time: 行程開始時間
            end_time: 行程結束時間
            travel_mode: 交通方式(transit/driving/walking/bicycling)
            distance_threshold: 可接受的最大距離(公里)
            efficiency_threshold: 最低效率閾值
            requirement: 使用者需求(包含用餐時間等)
        """
        self.start_time = start_time
        self.end_time = end_time
        self.travel_mode = travel_mode
        self.distance_threshold = distance_threshold
        self.efficiency_threshold = efficiency_threshold
        self.requirement = requirement or {}
        self.geo_calculator = GeoCalculator()

    def _get_current_period(self, current_time: datetime) -> str:
        """判斷當前應該選擇哪個時段的景點

        輸入參數:
            current_time: 當前時間

        回傳:
            str: 時段標記(morning/lunch/afternoon/dinner/night)
        """
        # 檢查是否接近用餐時間
        lunch_time = None
        dinner_time = None

        if self.requirement.get('lunch_time') and self.requirement['lunch_time'] != 'none':
            lunch_time = datetime.strptime(self.requirement['lunch_time'], '%H:%M').replace(
                year=current_time.year,
                month=current_time.month,
                day=current_time.day
            )

        if self.requirement.get('dinner_time') and self.requirement['dinner_time'] != 'none':
            dinner_time = datetime.strptime(self.requirement['dinner_time'], '%H:%M').replace(
                year=current_time.year,
                month=current_time.month,
                day=current_time.day
            )

        # 提前一小時開始尋找用餐地點
        if lunch_time:
            lunch_buffer = timedelta(hours=1)
            if current_time >= lunch_time - lunch_buffer and current_time <= lunch_time:
                return "lunch"

        if dinner_time:
            dinner_buffer = timedelta(hours=1)
            if current_time >= dinner_time - dinner_buffer and current_time <= dinner_time:
                return "dinner"

        # 其他時段判斷
        hour = current_time.hour
        if hour < 11:
            return "morning"
        elif hour < 14:
            return "afternoon"
        elif hour < 17:
            return "afternoon"
        else:
            return "night"

    def _filter_locations_by_period(self,
                                    locations: List[PlaceDetail],
                                    period: str) -> List[PlaceDetail]:
        """篩選特定時段的地點

        輸入參數:
            locations: 所有可選地點列表
            period: 目標時段

        回傳:
            List[PlaceDetail]: 符合時段的地點列表
        """
        return [loc for loc in locations if loc.period == period]

    def _calculate_distance(self,
                            loc1: PlaceDetail,
                            loc2: PlaceDetail) -> float:
        """計算兩地點間的直線距離

        輸入參數:
            loc1: 起點
            loc2: 終點

        回傳:
            float: 距離(公里)
        """
        return self.geo_calculator.calculate_distance(loc1, loc2)

    def _calculate_efficiency_score(self,
                                    location: PlaceDetail,
                                    distance: float) -> float:
        """計算效率評分

        計算公式：效率 = k / (距離 × 交通時間)
        k值根據停留時間調整：
        - 停留>=120分鐘：k=2.0
        - 停留>=60分鐘：k=1.5
        - 停留<60分鐘：k=1.0

        輸入參數:
            location: 地點資訊
            distance: 與當前位置的距離(公里)

        回傳:
            float: 0.0-1.0 之間的評分
        """
        # 計算k值
        if location.duration_min >= 120:
            k = 2.0
        elif location.duration_min >= 60:
            k = 1.5
        else:
            k = 1.0

        # 預估交通時間(分鐘)：假設平均速度 30km/h
        est_travel_time = (distance / 30) * 60

        # 避免除以零
        if distance == 0 or est_travel_time == 0:
            return 1.0

        # 計算效率值
        efficiency = k / (distance * est_travel_time)

        # 標準化到 0-1 之間
        return min(1.0, efficiency)

    def _calculate_time_fitness_score(self,
                                      location: PlaceDetail,
                                      arrival_time: datetime) -> float:
        """計算時間配合度評分

        評分標準：
        - 完全在營業時間內：1.0
        - 接近打烊(少於1小時)：0.7
        - 非營業時間：0.0

        輸入參數:
            location: 地點資訊
            arrival_time: 預計到達時間

        回傳:
            float: 0.0-1.0 之間的評分
        """
        # 檢查是否營業中
        weekday = arrival_time.weekday() + 1
        time_str = arrival_time.strftime('%H:%M')

        if not location.is_open_at(weekday, time_str):
            return 0.0

        # 檢查是否接近打烊時間
        close_time = None
        if weekday in location.hours and location.hours[weekday]:
            for slot in location.hours[weekday]:
                if slot and 'end' in slot:
                    close_time = datetime.strptime(slot['end'], '%H:%M').replace(
                        year=arrival_time.year,
                        month=arrival_time.month,
                        day=arrival_time.day
                    )

        if close_time:
            remaining_time = (close_time - arrival_time).total_seconds() / 3600
            if remaining_time < 1:
                return 0.7

        return 1.0

    def _calculate_location_score(self,
                                  location: PlaceDetail,
                                  current_location: PlaceDetail,
                                  current_time: datetime) -> float:
        """計算地點的綜合評分

        評分權重：
        - 效率評分：70%
        - 時間配合度：30%

        輸入參數:
            location: 待評分的地點
            current_location: 當前位置
            current_time: 當前時間

        回傳:
            float: 0.0-1.0 之間的綜合評分
        """
        # 計算距離
        distance = self._calculate_distance(current_location, location)

        # 如果超過最大距離，直接回傳0分
        if distance > self.distance_threshold:
            return 0.0

        # 計算效率評分
        efficiency_score = self._calculate_efficiency_score(location, distance)

        # 計算預計到達時間
        est_travel_time = (distance / 30) * 60  # 預估交通時間(分鐘)
        arrival_time = current_time + timedelta(minutes=est_travel_time)

        # 計算時間配合度評分
        time_score = self._calculate_time_fitness_score(location, arrival_time)

        # 計算加權總分
        total_score = (efficiency_score * 0.7) + (time_score * 0.3)

        return total_score

    def _find_best_next_location(self,
                                 current_location: PlaceDetail,
                                 available_locations: List[PlaceDetail],
                                 current_time: datetime) -> Optional[PlaceDetail]:
        """尋找下一個最佳景點

        主要流程：
        1. 判斷當前時段
        2. 篩選符合時段的地點
        3. 計算每個地點的綜合評分
        4. 選出前三名
        5. 隨機選擇一個

        輸入參數:
            current_location: 當前位置
            available_locations: 可選擇的地點列表
            current_time: 當前時間

        回傳:
            Optional[PlaceDetail]: 選中的下一個地點，如果沒有合適的地點則回傳None
        """
        # 判斷當前時段
        current_period = self._get_current_period(current_time)

        # 篩選符合時段的地點
        period_locations = self._filter_locations_by_period(
            available_locations,
            current_period
        )

        if not period_locations:
            return None

        # 計算每個地點的評分
        scored_locations = []
        for location in period_locations:
            score = self._calculate_location_score(
                location,
                current_location,
                current_time
            )
            if score > 0:  # 只保留有效的選項
                scored_locations.append((location, score))

        if not scored_locations:
            return None

        # 依評分排序並選出前三名
        scored_locations.sort(key=lambda x: x[1], reverse=True)
        top3 = scored_locations[:3]

        if not top3:
            return None

        # 隨機選擇一個
        selected_location = random.choice(top3)[0]

        return selected_location

    def execute(self,
                current_location: PlaceDetail,
                available_locations: List[PlaceDetail],
                current_time: datetime) -> List[Dict[str, Any]]:
        """執行行程規劃

        主要流程：
        1. 從起點開始，逐步找尋下一個最佳地點
        2. 計算實際交通時間和路線
        3. 產生完整的行程清單

        輸入參數:
            current_location: 起點位置
            available_locations: 可選擇的地點列表
            current_time: 開始時間

        回傳:
            List[Dict[str, Any]]: 完整的行程清單，每個景點包含：
            - step: 順序編號
            - name: 地點名稱
            - start_time: 到達時間
            - end_time: 離開時間
            - duration: 停留時間
            - transport_details: 交通方式
            - travel_time: 交通時間
        """
        itinerary = []
        current_loc = current_location
        remaining_locations = available_locations.copy()
        visit_time = current_time

        while remaining_locations and visit_time < self.end_time:
            # 尋找下一個最佳地點
            next_location = self._find_best_next_location(
                current_loc,
                remaining_locations,
                visit_time
            )

            if not next_location:
                break

            # 計算交通資訊
            travel_info = self._calculate_travel_info(
                current_loc, next_location)

            # 計算時間
            arrival_time = visit_time + timedelta(minutes=travel_info['time'])
            departure_time = arrival_time + \
                timedelta(minutes=next_location.duration_min)

            # 檢查是否超過結束時間
            if departure_time > self.end_time:
                break

            # 加入行程
            itinerary.append({
                'step': len(itinerary) + 1,
                'name': next_location.name,
                'start_time': arrival_time.strftime('%H:%M'),
                'end_time': departure_time.strftime('%H:%M'),
                'duration': next_location.duration_min,
                'transport_details': travel_info['transport_details'],
                'travel_time': travel_info['time']
            })

            # 更新狀態
            current_loc = next_location
            visit_time = departure_time
            remaining_locations.remove(next_location)

        return itinerary

    def _calculate_travel_info(self,
                               from_location: PlaceDetail,
                               to_location: PlaceDetail) -> Dict[str, Any]:
        """計算交通資訊

        此方法先使用直線距離和預估速度計算大概的交通時間
        之後在最終確定行程時才會使用 Google Maps API 取得實際路線

        輸入參數:
            from_location: 起點
            to_location: 終點

        回傳:
            Dict[str, Any]: 包含以下資訊的字典：
            - time: 預估交通時間(分鐘)
            - transport_details: 交通方式說明
            - coordinates: 起訖點座標
        """
        # 計算直線距離
        distance = self._calculate_distance(from_location, to_location)

        # 根據交通方式預估平均速度(公里/小時)
        speeds = {
            'transit': 30,
            'driving': 40,
            'bicycling': 15,
            'walking': 5
        }
        speed = speeds.get(self.travel_mode, 30)

        # 計算預估時間(分鐘)
        est_time = (distance / speed) * 60

        # 回傳交通資訊
        return {
            'time': est_time,
            'transport_details': f'使用 {self.travel_mode} 方式前往',
            'coordinates': {
                'from': {
                    'lat': from_location.lat,
                    'lon': from_location.lon
                },
                'to': {
                    'lat': to_location.lat,
                    'lon': to_location.lon
                }
            }
        }
