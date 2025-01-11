# src/core/planner/strategy.py

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import random
from typing import List, Dict, Optional, Tuple
from ..models.place import PlaceDetail
from ..services.time_service import TimeService
from ..services.geo_service import GeoService
from ..evaluator.place_scoring import PlaceScoring


class BasePlanningStrategy:
    """行程規劃策略基礎類別

    此類別負責：
    1. 管理時段狀態與轉換
    2. 選擇適合的下一個地點
    3. 建立完整行程規劃
    4. 追蹤規劃進度
    """

    def __init__(self,
                 time_service: TimeService,
                 geo_service: GeoService,
                 place_scoring: PlaceScoring,
                 config: Dict):
        """初始化規劃策略

        輸入參數:
            time_service: 時間服務，處理時間計算與時段判斷
            geo_service: 地理服務，處理距離計算與路線規劃
            place_scoring: 地點評分服務，計算地點分數
            config: 規劃設定，必須包含:
                - start_time: datetime 開始時間
                - end_time: datetime 結束時間
                - travel_mode: str 交通方式
                - distance_threshold: float 最大可接受距離(公里)
        """
        # 基礎服務元件
        self.time_service = time_service
        self.geo_service = geo_service
        self.place_scoring = place_scoring

        # 基本設定
        self.start_time = config['start_time']
        self.end_time = config['end_time']
        self.travel_mode = config['travel_mode']
        self.distance_threshold = config.get('distance_threshold', 30)
        self.end_location = config.get('end_location')

        # 時段管理
        self.period_sequence = ['morning', 'lunch',
                                'afternoon', 'dinner', 'night']
        self.period_status = {period: False for period in self.period_sequence}
        self.current_period = 'morning'

        # 狀態追蹤
        self.visited_places = set()  # 使用set避免重複選擇地點
        self._itinerary = []  # 儲存規劃的行程
        self.total_distance = 0.0  # 總行程距離

        # 用餐狀態
        self.lunch_completed = False
        self.dinner_completed = False

    def select_next_place(self,
                          current_location: PlaceDetail,
                          available_places: List[PlaceDetail],
                          current_time: datetime) -> Optional[Tuple[PlaceDetail, Dict]]:
        """選擇下一個地點"""
        # 1. 取得當前時段
        current_period = self.time_service.get_current_period(current_time)

        # 2. 篩選符合時段的地點
        suitable_places = [
            place for place in available_places
            if place.period == current_period and place.name not in self.visited_places
        ]

        if not suitable_places:
            print(f"沒有符合{current_period}時段的地點")
            return None

        # 3. 計算直線距離並評分
        scored_places = []
        for place in suitable_places:
            distance = self.geo_service.calculate_distance(
                {'lat': current_location.lat, 'lon': current_location.lon},
                {'lat': place.lat, 'lon': place.lon}
            )

            if distance <= self.distance_threshold:
                # 使用預估交通時間計算評分
                estimated_time = distance * 2  # 粗略估計，1公里約2分鐘
                score = self.place_scoring.calculate_score(
                    place=place,
                    current_location=current_location,
                    current_time=current_time,
                    travel_time=estimated_time
                )
                if score > float('-inf'):
                    scored_places.append((place, score))

        if not scored_places:
            print("沒有在可接受距離內的地點")
            return None

        # 4. 取評分最高的前3-5個地點
        top_places = sorted(
            scored_places, key=lambda x: x[1], reverse=True)[:5]

        # 5. 隨機選擇一個
        selected_place, _ = random.choice(top_places[:max(3, len(top_places))])

        # 6. 只對選中的地點取得路線資訊
        travel_info = self.geo_service.get_route(
            origin={"lat": current_location.lat, "lon": current_location.lon},
            destination={"lat": selected_place.lat, "lon": selected_place.lon},
            mode=self.travel_mode,
            departure_time=current_time
        )

        # print(f"\n選中地點: {selected_place.name}")
        # print(f"預計交通時間: {travel_info['duration_minutes']}分鐘")

        # 7. 更新用餐狀態
        self.time_service.update_meal_status(selected_place.period)

        return selected_place, travel_info

    def execute(self,
                current_location: PlaceDetail,
                available_places: List[PlaceDetail],
                current_time: datetime) -> List[Dict]:
        """執行行程規劃

        這是策略的主要執行方法，負責:
        1. 初始化行程狀態
        2. 依照時段選擇適合的地點
        3. 建立完整行程資訊
        4. 追蹤時段和用餐狀態

        輸入參數:
            current_location: PlaceDetail - 起點位置
            available_places: List[PlaceDetail] - 所有可選擇的地點
            current_time: datetime - 開始時間

        回傳:
            List[Dict] - 完整的行程列表，每個行程項目包含:
                - name: str - 地點名稱
                - step: int - 順序編號
                - start_time: str - 到達時間(HH:MM格式)
                - end_time: str - 離開時間(HH:MM格式)
                - duration: int - 停留時間(分鐘)
                - travel_time: int - 交通時間(分鐘)
                - travel_distance: float - 交通距離(公里)
                - transport: str - 交通方式
                - route_info: Dict - 路線資訊(如果有)
        """
        # 初始化行程
        if not hasattr(self, '_itinerary'):
            self._itinerary = []
        else:
            self._itinerary.clear()

        # 重置時間服務狀態
        self.time_service.reset()

        # 加入起點
        start_item = self._create_itinerary_item(
            place=current_location,
            arrival_time=current_time,
            departure_time=current_time,  # 起點不需要停留時間
            travel_info={
                'duration_minutes': 0,
                'distance_km': 0,
                'transport_mode': self.travel_mode
            }
        )
        self.visited_places.add(current_location.name)
        self._itinerary.append(start_item)

        print(f"\n=== 開始規劃行程 ===")

        # 初始化規劃狀態
        remaining_places = available_places.copy()
        current_loc = current_location
        visit_time = current_time
        iteration = 1

        # 主要規劃迴圈
        while remaining_places and visit_time < self.end_time:
            # print(f"\n==== 選擇第 {iteration} 個地點 ====")

            # 選擇下一個地點
            next_place = self.select_next_place(
                current_loc,
                remaining_places,
                visit_time
            )

            if not next_place:
                print("找不到合適的下一個地點，結束規劃")
                break

            place, travel_info = next_place

            # 計算到達和離開時間
            arrival_time = self._calculate_arrival_time(
                visit_time,
                travel_info['duration_minutes']
            )
            departure_time = self._calculate_departure_time(
                arrival_time,
                place.duration_min
            )

            # 檢查是否超過結束時間
            if departure_time > self.end_time:
                print("已達每日結束時間，停止規劃")
                break

            # 建立行程項目
            itinerary_item = self._create_itinerary_item(
                place,
                arrival_time,
                departure_time,
                travel_info
            )
            self._itinerary.append(itinerary_item)

            # 更新規劃狀態
            current_loc = place
            visit_time = departure_time
            remaining_places.remove(place)
            self.visited_places.add(place.name)
            self.total_distance += travel_info['distance_km']

            iteration += 1

        # 加入返回終點
        if self._itinerary[-1]['name'] != self.end_location.name:  # 使用設定的終點
            # 計算返回終點的路線
            final_travel_info = self.geo_service.get_route(
                origin={
                    "lat": float(self._itinerary[-1]['lat']),
                    "lon": float(self._itinerary[-1]['lon'])
                },
                destination={
                    "lat": self.end_location.lat,  # 使用設定的終點
                    "lon": self.end_location.lon
                },
                mode=self.travel_mode
            )

            final_arrival_time = self._calculate_arrival_time(
                visit_time,
                final_travel_info['duration_minutes']
            )

            # 加入終點到行程
            end_item = self._create_itinerary_item(
                place=self.end_location,  # 使用設定的終點
                arrival_time=final_arrival_time,
                departure_time=final_arrival_time,
                travel_info=final_travel_info
            )
            self._itinerary.append(end_item)
            self.total_distance += final_travel_info['distance_km']

        print(f"\n=== 行程規劃完成 ===")
        print(f"規劃地點數: {len(self._itinerary)}")
        print(f"總行程距離: {self.total_distance:.1f} 公里")

        return self._itinerary

    def _calculate_arrival_time(self,
                                start_time: datetime,
                                travel_minutes: float) -> datetime:
        """計算到達時間

        根據出發時間和交通時間計算預計到達時間

        輸入參數:
            start_time: datetime 出發時間
            travel_minutes: float 交通時間(分鐘)

        回傳:
            datetime 預計到達時間
        """
        return start_time + timedelta(minutes=int(travel_minutes))

    def _calculate_departure_time(self,
                                  arrival_time: datetime,
                                  duration_minutes: int) -> datetime:
        """計算離開時間

        根據到達時間和停留時間計算預計離開時間

        輸入參數:
            arrival_time: datetime 到達時間
            duration_minutes: int 停留時間(分鐘)

        回傳:
            datetime 預計離開時間
        """
        return arrival_time + timedelta(minutes=duration_minutes)

    def _create_itinerary_item(self,
                               place: PlaceDetail,
                               arrival_time: datetime,
                               departure_time: datetime,
                               travel_info: Dict) -> Dict:
        """建立行程項目

        整合所有資訊，建立完整的行程項目資料

        輸入參數:
            place: PlaceDetail 地點資訊
            arrival_time: datetime 到達時間
            departure_time: datetime 離開時間
            travel_info: Dict 交通資訊，必須包含:
                - duration_minutes: 交通時間(分鐘)
                - distance_km: 距離(公里)
                - transport_mode: 交通方式
                - route_info: 路線資訊(選填)

        回傳:
            Dict 完整的行程項目資訊，包含:
                name: str - 地點名稱
                step: int - 在整個行程中的順序編號，從1開始計數
                start_time: str - 到達時間，採用 "HH:MM" 格式 (例如 "09:30")
                end_time: str - 離開時間，採用 "HH:MM" 格式
                duration: int - 在該地點的停留時間，以分鐘為單位
                travel_time: int - 到達該地點所需的交通時間，以分鐘為單位
                travel_distance: float - 到達該地點的交通距離，以公里為單位
                transport: str - 使用的交通方式（例如：driving、transit、walking）
                route_info: Dict - 詳細的路線資訊（若有），包含路徑指引等
        """

        # 取得當天的營業時間
        weekday = arrival_time.isoweekday()  # 1-7
        day_hours = place.hours.get(weekday, [])

        # 找出符合抵達時間的營業時段
        matching_hours = None
        for slot in day_hours:
            if slot:
                start = datetime.strptime(slot['start'], '%H:%M').time()
                end = datetime.strptime(slot['end'], '%H:%M').time()
                if start <= arrival_time.time() <= end:
                    matching_hours = slot
                    break

        # 計算交通時段
        travel_end = arrival_time
        travel_start = travel_end - \
            timedelta(minutes=travel_info.get('duration_minutes', 0))
        travel_period = f"{travel_start.strftime('%H:%M')}-{travel_end.strftime('%H:%M')}"
        
        # 把起點終點的label替換
        if len(self.visited_places) == 0:
            display_label = '起點'
        elif self.end_location and place.name == self.end_location.name:
            display_label = '終點'
        else:
            display_label = place.label
        
        # 交通方式中英對照
        transport_display = {
            'transit': '大眾運輸',
            'driving': '開車',
            'walking': '步行',
            'bicycling': '騎車'
        }
        transport_mode = travel_info.get('transport_mode', self.travel_mode)
        transport_chinese = transport_display.get(transport_mode, transport_mode)
    
        return {
            'step': len(self.visited_places),
            'name': place.name,
            'label': display_label,
            'hours': matching_hours,
            'lat': place.lat,
            'lon': place.lon,
            'start_time': arrival_time.strftime('%H:%M'),
            'end_time': departure_time.strftime('%H:%M'),
            'duration': place.duration_min,
            'transport': {
                'mode': transport_chinese,
                'travel_distance': travel_info.get('distance_km', 0),
                'time': travel_info.get('duration_minutes', 20),
                'period': travel_period,
            },
            'route_info': travel_info.get('route_info'),
            'route_url': 'example@url',
        }

    def is_feasible(self,
                    place: PlaceDetail,
                    current_location: PlaceDetail,
                    current_time: datetime,
                    travel_info: Dict) -> bool:
        """檢查地點是否可以加入行程

        檢查項目：
        1. 是否有足夠的剩餘時間(含交通和停留)
        2. 是否在營業時間內
        3. 是否符合當前時段

        輸入參數:
            place: PlaceDetail 要檢查的地點
            current_location: PlaceDetail 當前位置
            current_time: datetime 當前時間
            travel_info: Dict 交通資訊

        回傳:
            bool True=可行 False=不可行
        """
        # 計算預計到達時間
        arrival_time = self._calculate_arrival_time(
            current_time,
            travel_info['duration_minutes']
        )

        # 計算預計離開時間
        departure_time = self._calculate_departure_time(
            arrival_time,
            place.duration_min
        )

        # 檢查是否超過每日結束時間
        if departure_time > self.end_time:
            print("超過每日結束時間限制")
            return False

        # 檢查是否營業
        weekday = arrival_time.isoweekday()
        if not place.is_open_at(weekday, arrival_time.strftime('%H:%M')):
            print("該時段未營業")
            return False

        # 檢查是否符合當前時段
        if place.period != self.current_period:
            print(f"不符合當前時段: {self.current_period}")
            return False

        return True
