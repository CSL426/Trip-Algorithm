# src/core/planner/strategy.py

from datetime import datetime, timedelta
from typing import Any, List, Dict, Optional, Tuple
from src.core.models.place import PlaceDetail
from src.core.evaluator.scoring_system import ScoringSystem
from src.core.utils.time_core import TimeCore
from src.core.services.google_maps import GoogleMapsService


class PlanningStrategy:
    """行程規劃策略類別

    負責：
    1. 依據時段選擇適合的景點
    2. 使用評分系統評估選項
    3. 整合路線規劃
    4. 產生行程建議
    """

    def __init__(self,
                 start_time: datetime,
                 end_time: datetime,
                 travel_mode: str = 'transit',
                 distance_threshold: float = 30.0,
                 requirement: dict = None):
        """初始化規劃策略

        輸入:
            start_time: 行程開始時間
            end_time: 行程結束時間
            travel_mode: 交通方式(transit/driving/walking/bicycling)
            distance_threshold: 可接受的最大距離(公里)
            requirement: 使用者需求(包含用餐時間等)
        """
        self.start_time = start_time
        self.end_time = end_time
        self.travel_mode = travel_mode
        self.distance_threshold = distance_threshold
        self.requirement = requirement or {}

        # 初始化評分系統
        self.scoring_system = ScoringSystem(start_time, distance_threshold)

        # 初始化 Google Maps 服務
        try:
            from src.config.config import GOOGLE_MAPS_API_KEY
            self.maps_service = GoogleMapsService(GOOGLE_MAPS_API_KEY)
        except Exception as e:
            print(f"警告：Google Maps 服務初始化失敗: {str(e)}")
            self.maps_service = None

    def execute(self,
                current_location: PlaceDetail,
                available_locations: List[PlaceDetail],
                current_time: datetime) -> List[Dict[str, Any]]:
        """執行行程規劃

        輸入:
            current_location: 當前位置
            available_locations: 可選擇的地點列表
            current_time: 當前時間

        回傳:
            List[Dict]: 規劃後的行程清單
        """
        itinerary = []
        current_loc = current_location
        remaining_locations = available_locations.copy()
        visit_time = current_time

        # 追蹤用餐狀態
        had_lunch = False
        had_dinner = False

        while remaining_locations and visit_time < self.end_time:
            # 檢查用餐時間
            is_meal_time = self._check_meal_time(
                visit_time, had_lunch, had_dinner)

            # 選擇下一個地點
            next_place = self._find_best_next_location(
                current_loc,
                remaining_locations,
                visit_time,
                is_meal_time
            )

            if not next_place:
                break

            location, travel_info = next_place

            # 更新用餐狀態
            if is_meal_time and location.label in ['餐廳', '小吃']:
                if self._is_lunch_time(visit_time):
                    had_lunch = True
                else:
                    had_dinner = True

            # 更新時間和行程
            arrival_time = visit_time + timedelta(minutes=travel_info['time'])
            departure_time = arrival_time + \
                timedelta(minutes=location.duration_min)

            if departure_time > self.end_time:
                break

            # 加入行程
            itinerary.append({
                'step': len(itinerary) + 1,
                'name': location.name,
                'start_time': arrival_time.strftime('%H:%M'),
                'end_time': departure_time.strftime('%H:%M'),
                'duration': location.duration_min,
                'transport_details': travel_info['transport_details'],
                'travel_time': travel_info['time'],
                'route_info': travel_info.get('route_info')
            })

            # 更新狀態
            current_loc = location
            visit_time = departure_time
            remaining_locations.remove(location)

        return itinerary

    def _find_best_next_location(self,
                                 current_loc: PlaceDetail,
                                 available_locations: List[PlaceDetail],
                                 visit_time: datetime,
                                 is_meal_time: bool) -> Optional[Tuple[PlaceDetail, Dict]]:
        """尋找最佳的下一個地點

        輸入:
            current_loc: 當前位置
            available_locations: 可選地點列表
            visit_time: 當前時間
            is_meal_time: 是否為用餐時間

        回傳:
            Optional[Tuple[PlaceDetail, Dict]]: (選中的地點, 交通資訊)
            若所有地點都不合適則回傳 None
        """
        scored_locations = []

        for location in available_locations:
            # 使用 Google Maps 計算實際交通資訊
            travel_info = self._calculate_travel_info(
                current_loc,
                location,
                visit_time
            )

            # 使用評分系統計算分數
            score = self.scoring_system.calculate_total_score(
                location=location,
                current_location=current_loc,
                travel_time=travel_info['time'],
                is_meal_time=is_meal_time
            )

            if score > float('-inf'):
                scored_locations.append((location, score, travel_info))

        if not scored_locations:
            return None

        # 選擇分數最高的地點
        scored_locations.sort(key=lambda x: x[1], reverse=True)
        best_location, _, best_travel_info = scored_locations[0]

        return best_location, best_travel_info

    def _check_meal_time(self,
                         current_time: datetime,
                         had_lunch: bool,
                         had_dinner: bool) -> bool:
        """檢查是否為用餐時間

        輸入:
            current_time: 當前時間
            had_lunch: 是否已用午餐
            had_dinner: 是否已用晚餐

        回傳:
            bool: 是否為用餐時間
        """
        # 檢查午餐時間
        if not had_lunch and self._is_lunch_time(current_time):
            return True

        # 檢查晚餐時間
        if not had_dinner and self._is_dinner_time(current_time):
            return True

        return False

    def _calculate_travel_info(self,
                               from_location: PlaceDetail,
                               to_location: PlaceDetail,
                               departure_time: datetime = None) -> Dict:
        """計算交通資訊

        輸入:
            from_location: 起點
            to_location: 終點
            departure_time: 出發時間

        回傳:
            Dict: {
                'time': float,              # 交通時間(分鐘)
                'transport_details': str,    # 交通方式說明
                'distance_km': float,       # 距離(公里)
                'route_info': Dict          # Google Maps 路線資訊
            }
        """
        try:
            # 使用 Google Maps API
            if self.maps_service:
                route = self.maps_service.calculate_travel_time(
                    origin=(from_location.lat, from_location.lon),
                    destination=(to_location.lat, to_location.lon),
                    mode=self.travel_mode,
                    departure_time=departure_time or datetime.now()
                )

                return {
                    'time': route['duration_minutes'],
                    'distance_km': route['distance_meters'] / 1000,
                    'transport_details': self._get_transport_display(),
                    'route_info': route
                }
        except Exception as e:
            print(f"警告：Google Maps 路線查詢失敗: {str(e)}")

        # 使用直線距離估算
        distance = from_location.calculate_distance(to_location)
        speed = self._get_estimated_speed()
        est_time = (distance / speed) * 60

        return {
            'time': round(est_time),
            'distance_km': distance,
            'transport_details': self._get_transport_display(),
            'route_info': None
        }

    def _is_lunch_time(self, current_time: datetime) -> bool:
        """檢查是否為午餐時間"""
        if not self.requirement.get('lunch_time'):
            return False

        lunch_time = datetime.strptime(
            self.requirement['lunch_time'], '%H:%M').time()
        current = current_time.time()

        # 檢查是否在午餐時間前後30分鐘內
        start = TimeCore.add_minutes(lunch_time, -30)
        end = TimeCore.add_minutes(lunch_time, 30)

        return TimeCore.is_time_in_range(current, start, end)

    def _is_dinner_time(self, current_time: datetime) -> bool:
        """檢查是否為晚餐時間"""
        if not self.requirement.get('dinner_time'):
            return False

        dinner_time = datetime.strptime(
            self.requirement['dinner_time'], '%H:%M').time()
        current = current_time.time()

        # 檢查是否在晚餐時間前後30分鐘內
        start = TimeCore.add_minutes(dinner_time, -30)
        end = TimeCore.add_minutes(dinner_time, 30)

        return TimeCore.is_time_in_range(current, start, end)

    def _get_transport_display(self) -> str:
        """取得交通方式的顯示文字"""
        return {
            'transit': '大眾運輸',
            'driving': '開車',
            'walking': '步行',
            'bicycling': '騎車'
        }.get(self.travel_mode, self.travel_mode)

    def _get_estimated_speed(self) -> float:
        """取得預估的移動速度(公里/小時)"""
        return {
            'transit': 30,  # 大眾運輸 30 km/h
            'driving': 40,  # 開車 40 km/h
            'bicycling': 15,  # 騎車 15 km/h
            'walking': 5    # 步行 5 km/h
        }.get(self.travel_mode, 30)

    def _calculate_location_score(self,
                                  location: PlaceDetail,
                                  current_location: PlaceDetail,
                                  current_time: datetime,
                                  travel_time: float) -> float:
        """計算地點的綜合評分

        考慮因素：
        1. 地點評分(rating) - 30%
        2. 交通時間合理性 - 30%
        3. 時段適合度 - 20%
        4. 營業時間配合度 - 20%

        輸入參數:
            location: 要評分的地點
            current_location: 目前位置
            current_time: 當前時間
            travel_time: 預估交通時間(分鐘)

        回傳:
            float: 0~1之間的評分，或 -1 表示不合適
        """
        try:
            # 計算實際抵達時間
            arrival_time = current_time + timedelta(minutes=travel_time)
            departure_time = arrival_time + \
                timedelta(minutes=location.duration_min)

            # 1. 檢查基本條件
            # 檢查是否超過結束時間
            if departure_time > self.end_time:
                return -1

            # 檢查營業時間
            weekday = current_time.weekday() + 1  # 1-7 代表週一到週日
            time_str = arrival_time.strftime('%H:%M')
            if not location.is_open_at(weekday, time_str):
                return -1

            # 2. 計算各項分數

            # 2.1 評分分數 (0-5分轉換為0-1分)
            rating_score = min(1.0, location.rating / 5.0)

            # 2.2 交通時間分數
            # 交通時間超過2小時視為不合理
            max_travel_time = 120
            travel_score = max(0, 1 - (travel_time / max_travel_time))

            # 2.3 時段適合度分數
            period_score = 1.0 if location.is_suitable_for_current_time(
                arrival_time) else 0.3

            # 2.4 營業時間配合度分數
            time_score = 0.0
            if location.duration_min > 0:
                hours = location.hours.get(weekday, [])
                if hours and hours[0]:
                    for slot in hours:
                        if slot:
                            end_time = datetime.strptime(
                                slot['end'], '%H:%M').time()
                            end_datetime = datetime.combine(
                                arrival_time.date(), end_time)
                            if end_datetime > departure_time:
                                remaining_time = (
                                    end_datetime - departure_time).total_seconds() / 3600
                                time_score = min(
                                    1.0, remaining_time / 2)  # 至少還有2小時最理想
                                break
            else:
                time_score = 1.0

            # 3. 計算加權總分
            final_score = (
                rating_score * 0.3 +
                travel_score * 0.3 +
                period_score * 0.2 +
                time_score * 0.2
            )

            return final_score

        except Exception as e:
            print(f"評分計算錯誤 ({location.name}): {str(e)}")
            return -1  # 發生錯誤時回傳 -1

    def _calculate_distance(self,
                            from_location: PlaceDetail,
                            to_location: PlaceDetail) -> float:
        """計算兩個地點之間的直線距離

        使用 Haversine 公式計算球面上兩點間的最短距離

        輸入參數:
            from_location: 起點位置
                PlaceDetail 物件，需包含：
                - lat: 緯度
                - lon: 經度
            to_location: 終點位置
                PlaceDetail 物件，需包含：
                - lat: 緯度
                - lon: 經度

        回傳:
            float: 兩點間的直線距離(公里)
        """
        try:
            # 檢查輸入物件是否有效
            if not isinstance(from_location, PlaceDetail) or not isinstance(to_location, PlaceDetail):
                raise ValueError("輸入必須是 PlaceDetail 物件")

            # 呼叫 GeoCalculator 的 calculate_distance 方法
            distance = self.geo_calculator.calculate_distance(
                from_location,  # 起點
                to_location    # 終點
            )

            return float(distance)  # 確保回傳浮點數

        except Exception as e:
            print(
                f"距離計算錯誤 ({from_location.name} -> {to_location.name}): {str(e)}")
            return float('inf')  # 回傳無限大表示不可達

    def _filter_locations_by_period(self,
                                    locations: List[PlaceDetail],
                                    period: str) -> List[PlaceDetail]:
        """篩選特定時段的地點

        依據時段標記篩選適合的地點：
        1. 對應時段的景點
        2. 餐廳在用餐時段會被優先選擇
        3. 24小時營業的地點可以在任何時段被選擇

        輸入參數:
            locations: 所有可選地點列表
            period: 目標時段 (morning/lunch/afternoon/dinner/night)

        回傳:
            List[PlaceDetail]: 符合時段的地點列表
        """
        filtered = []
        for loc in locations:
            # 檢查是否為24小時營業
            is_24h = False
            try:
                is_24h = all(
                    isinstance(slot, list) and slot and
                    isinstance(slot[0], dict) and
                    slot[0].get('start') == '00:00' and
                    slot[0].get('end') == '23:59'
                    for day, slot in loc.hours.items()
                    if slot is not None
                )
            except Exception as e:
                print(f"檢查24小時營業時發生錯誤 ({loc.name}): {str(e)}")
                is_24h = False

            # 用餐時間優先選擇餐廳
            if period in ['lunch', 'dinner']:
                if loc.label in ['餐廳', '小吃', '夜市']:
                    filtered.append(loc)
                continue

            # 其他時段：符合時段或24小時營業
            if loc.period == period or is_24h:
                filtered.append(loc)

        return filtered

    def _get_current_period(self, current_time: datetime) -> str:
        """判斷當前時段

        依據時間判斷應該安排什麼類型的景點，考慮：
        1. 用餐時間優先安排餐廳
        2. 依時間切分成早上、下午、晚上等時段

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

        # 用餐時段的時間範圍（前後半小時）
        time_buffer = timedelta(minutes=30)

        # 檢查午餐時間
        if lunch_time and (lunch_time - time_buffer <= current_time <= lunch_time + time_buffer):
            return "lunch"

        # 檢查晚餐時間
        if dinner_time and (dinner_time - time_buffer <= current_time <= dinner_time + time_buffer):
            return "dinner"

        # 其他時段判斷
        hour = current_time.hour
        if hour < 11:
            return "morning"
        elif hour < 14:
            return "lunch"
        elif hour < 17:
            return "afternoon"
        elif hour < 19:
            return "dinner"
        else:
            return "night"

    def _calculate_travel_info(self,
                               from_location: PlaceDetail,
                               to_location: PlaceDetail,
                               departure_time: datetime = None,
                               use_api: bool = True) -> Dict[str, Any]:
        """計算交通資訊

        兩種模式：
        1. 快速模式(use_api=False)：使用直線距離和預設速度估算
        2. 精確模式(use_api=True)：使用 Google Maps API 查詢實際路線

        輸入參數:
            from_location: 起點
            to_location: 終點
            departure_time: 出發時間(預設為現在)
            use_api: 是否使用 Google Maps API

        回傳:
            Dict[str, Any]: {
                'time': float,                # 交通時間(分鐘)
                'transport_details': str,      # 交通方式說明
                'distance_km': float,         # 距離(公里)
                'route_info': Dict            # 詳細路線資訊(若使用API)
            }
        """
        # 計算直線距離
        distance = self._calculate_distance(from_location, to_location)

        # 使用 Google Maps API
        if use_api and self.maps_service:
            try:
                # 確保時間是未來時間
                current_time = datetime.now()
                query_time = departure_time if departure_time and departure_time > current_time else current_time

                route = self.maps_service.calculate_travel_time(
                    origin=(from_location.lat, from_location.lon),
                    destination=(to_location.lat, to_location.lon),
                    mode=self.travel_mode,
                    departure_time=query_time
                )

                return {
                    'time': route['duration_minutes'],
                    'distance_km': route['distance_meters'] / 1000,
                    'transport_details': self._get_transport_display(),
                    'route_info': route
                }

            except Exception as e:
                print(f"警告：Google Maps 路線查詢失敗: {str(e)}")
                # 發生錯誤時退回使用估算方式

        # 使用預設速度估算
        speeds = {
            'transit': 30,  # 大眾運輸速度約 30 km/h
            'driving': 40,  # 開車速度約 40 km/h
            'bicycling': 15,  # 自行車速度約 15 km/h
            'walking': 5   # 步行速度約 5 km/h
        }
        speed = speeds.get(self.travel_mode, 30)  # 預設使用 30 km/h
        est_time = (distance / speed) * 60  # 轉換為分鐘

        # 加入一些交通延遲的考量
        if distance > 10:  # 距離超過 10 公里
            est_time *= 1.2  # 增加 20% 的時間作為交通延遲

        return {
            'time': round(est_time),  # 四捨五入到整數分鐘
            'distance_km': distance,
            'transport_details': self._get_transport_display(),
            'route_info': None  # 不使用實際路線資訊
        }

    def _get_transport_display(self) -> str:
        """取得交通方式的顯示文字"""
        return {
            'transit': '大眾運輸',
            'driving': '開車',
            'walking': '步行',
            'bicycling': '騎車'
        }.get(self.travel_mode, self.travel_mode)

    def _get_estimated_speed(self) -> float:
        """取得預估的移動速度(公里/小時)"""
        return {
            'transit': 30,  # 大眾運輸 30 km/h
            'driving': 40,  # 開車 40 km/h
            'bicycling': 15,  # 騎車 15 km/h
            'walking': 5    # 步行 5 km/h
        }.get(self.travel_mode, 30)
