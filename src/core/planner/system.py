# src/core/planner/system.py


from datetime import datetime
from typing import Dict, List
from ..evaluator.place_scoring import PlaceScoring
from ..models.place import PlaceDetail
from .strategy import BasePlanningStrategy
from ..services.geo_service import GeoService
from ..services.time_service import TimeService
from ..utils.navigation_translator import NavigationTranslator


class TripPlanningSystem:
    """行程規劃系統

    整合各種服務來規劃最佳行程:
    1. 時間管理：使用 TimeService 處理時段和時間
    2. 地理服務：計算距離和規劃路線
    3. 評分服務：評估地點適合度
    4. 策略系統：執行實際的規劃邏輯
    """

    def __init__(self):
        """初始化規劃系統並連結所有需要的服務"""
        # 初始化時間服務，設定預設用餐時間
        self.time_service = TimeService(
            lunch_time="12:00",   # 預設中午12點用餐
            dinner_time="18:00"   # 預設晚上6點用餐
        )

        # 初始化其他服務
        self.geo_service = GeoService()
        self.place_scoring = PlaceScoring(
            time_service=self.time_service,
            geo_service=self.geo_service
        )

        # 初始化策略系統
        self.strategy = None

        # 執行狀態追蹤
        self.execution_time = 0.0

    def plan_trip(self, locations: List[Dict], requirement: Dict) -> List[Dict]:
        """執行行程規劃

        輸入參數:
            locations: List[Dict] - 所有可用地點的資料，每個地點包含:
                - name: str - 地點名稱
                - lat: float - 緯度
                - lon: float - 經度
                - duration: int - 建議停留時間(分鐘)
                - label: str - 地點類型
                - period: str - 適合的時段
                - hours: Dict - 營業時間

            requirement: Dict - 使用者的規劃需求，包含:
                - start_time: str - 開始時間(HH:MM)
                - end_time: str - 結束時間(HH:MM)
                - lunch_time: str - 午餐時間(HH:MM)
                - dinner_time: str - 晚餐時間(HH:MM)
                - transport_mode: str - 交通方式
                - distance_threshold: float - 最大可接受距離(公里)

        回傳:
            List[Dict]: 規劃好的行程列表
        """
        start_time = datetime.now()

        try:
            # 先設定預設值
            default_requirement = {
                "start_time": "09:00",        # 預設早上9點開始
                "end_time": "21:00",          # 預設晚上9點結束
                "start_point": "台北車站",     # 預設起點
                "end_point": None,            # 預設終點（會使用起點）
                "transport_mode": "driving",   # 預設開車
                "distance_threshold": 30,      # 預設最大30公里
                "lunch_time": "12:00",        # 預設中午12點午餐
                "dinner_time": "18:00"        # 預設晚上6點晚餐
            }
            # 更新預設值，只使用非 None 的使用者設定
            for key, value in requirement.items():
                if value is not None:
                    default_requirement[key] = value

            # 使用更新後的設定值
            requirement = default_requirement

            # 設定起點和終點
            self.start_location = self._get_start_location(
                requirement.get('start_point')
            )
            self.end_location = self._get_end_location(
                requirement.get('end_point')
            )

            # 更新時間服務的用餐時間設定
            if requirement.get('lunch_time'):
                self.time_service = TimeService(
                    lunch_time=requirement['lunch_time'],
                    dinner_time=requirement.get('dinner_time', "18:00")
                )

            # 轉換地點資料為 PlaceDetail 物件
            available_places = [
                PlaceDetail(**location) if isinstance(location, dict)
                else location for location in locations
            ]

            # 準備規劃上下文
            context = {
                'start_time': datetime.strptime(requirement['start_time'], '%H:%M'),
                'end_time': datetime.strptime(requirement['end_time'], '%H:%M'),
                'travel_mode': requirement.get('transport_mode', 'driving'),
                'distance_threshold': requirement.get('distance_threshold', 30),
                'start_location': self.start_location,
                'end_location': self.end_location,
            }

            # 初始化並執行規劃策略
            self.strategy = BasePlanningStrategy(
                time_service=self.time_service,
                geo_service=self.geo_service,
                place_scoring=self.place_scoring,
                config=context
            )

            # 執行規劃
            itinerary = self.strategy.execute(
                current_location=self.start_location,
                available_places=available_places,
                current_time=context['start_time']
            )

            # 記錄執行時間
            self.execution_time = (datetime.now() - start_time).total_seconds()

            return itinerary

        except Exception as e:
            print(f"行程規劃失敗: {str(e)}")
            raise

    def _prepare_planning_context(self, locations: List[PlaceDetail], requirement: Dict) -> Dict:
        """準備規劃上下文

        將所有規劃所需的資訊整理成統一的格式。主要處理：
        1. 起點位置的設定
        2. 時間格式的轉換
        3. 其他相關參數的整理

        參數:
            locations: 已轉換為 PlaceDetail 的地點列表
            requirement: 包含規劃需求的字典

        回傳:
            Dict: 完整的規劃上下文
        """
        # 從 requirement 中取得起點，如果沒有則使用預設值
        start_point = requirement.get('start_point', "台北車站")

        # 取得並轉換起點資訊
        start_location = self._get_start_location(start_point)
        if isinstance(start_location, dict):
            start_location = PlaceDetail(**start_location)

        # 準備完整的規劃上下文
        context = {
            'start_location': start_location,
            'available_places': locations,
            'start_time': datetime.strptime(
                requirement['start_time'], '%H:%M'
            ),
            'end_time': datetime.strptime(
                requirement['end_time'], '%H:%M'
            ),
            'travel_mode': requirement.get('transport_mode', 'driving'),
            'theme': requirement.get('theme'),
            'meal_times': {
                'lunch': requirement.get('lunch_time'),
                'dinner': requirement.get('dinner_time')
            }
        }

        return context

    def print_itinerary(self, itinerary: List[Dict], show_navigation: bool = False) -> None:
        """輸出行程規劃結果

        輸入參數:
            itinerary: List[Dict] - 規劃好的行程列表
            show_navigation: bool - 是否顯示詳細導航資訊
        """
        print("\n=== 行程規劃結果 ===")

        total_travel_time = 0
        total_duration = 0

        for plan in itinerary:
            # 顯示地點資訊
            print(f"\n[地點 {plan['step']}]")
            print(f"名稱: {plan['name']}")
            print(f"時間: {plan['start_time']} - {plan['end_time']}")
            print(f"停留: {plan['duration']}分鐘", end=' ')
            print(
                f"交通: {plan['transport']['mode']}({plan['transport']['time']}分鐘)")

            # 如果需要，顯示詳細導航
            if show_navigation and 'route_info' in plan:
                print("\n前往下一站的導航:")
                print(NavigationTranslator.format_navigation(
                    plan['route_info']))

            total_travel_time += plan['transport']['time']
            total_duration += plan['duration']

        # 顯示統計資訊
        print("\n=== 統計資訊 ===")
        print(f"總景點數: {len(itinerary)}個")
        print(f"總時間: {(total_duration + total_travel_time)/60:.1f}小時")
        print(f"- 遊玩時間: {total_duration/60:.1f}小時")
        print(f"- 交通時間: {total_travel_time/60:.1f}小時")

        print(f"規劃耗時: {self.execution_time:.2f}秒")

    def _get_start_location(self, start_point: str) -> PlaceDetail:
        """處理起點設定

        將起點資訊轉換為 PlaceDetail 物件

        輸入參數:
            start_point: str - 起點的名稱

        回傳:
            PlaceDetail - 起點的完整資訊物件
        """
        # 準備預設的起點資料
        default_location = {
            'name': '台北車站',
            'lat': 25.0478,
            'lon': 121.5170,
            'duration_min': 0,
            'label': '交通樞紐',
            'period': 'morning',
            'hours': {i: [{'start': '00:00', 'end': '23:59'}]
                      for i in range(1, 8)}
        }

        if not start_point or start_point == "台北車站":
            # 使用預設起點
            return PlaceDetail(**default_location)

        try:
            # 如果有指定其他起點，取得該地點資訊
            location = self._get_location_info(start_point)
            return PlaceDetail(**location)
        except Exception as e:
            print(f"無法取得起點資訊，使用預設起點: {str(e)}")
            return PlaceDetail(**default_location)

    def _get_end_location(self, end_point: str) -> PlaceDetail:
        """取得終點位置資訊

        如果沒有指定終點，會使用起點作為終點
        如果指定了終點，會取得該地點的詳細資訊

        輸入參數:
            end_point: Optional[str] - 終點名稱，可以是 None

        回傳:
            PlaceDetail - 終點的完整資訊物件
        """
        if not end_point or end_point == "none":
            # 如果沒有指定終點，使用起點作為終點
            return self.start_location

        try:
            # 如果有指定終點，取得該地點資訊
            location = self._get_location_info(end_point)
            return PlaceDetail(**location)
        except Exception as e:
            print(f"無法取得終點資訊，使用起點作為終點: {str(e)}")
            return self.start_location

    def _get_location_info(self, place_name: str) -> Dict:
        """取得地點詳細資訊

        使用地理服務來取得指定地點的完整資訊，包括：
        1. 座標位置
        2. 基本資訊
        3. 營業時間等
        """
        try:
            location = self.geo_service.geocode(place_name)
            return {
                'name': place_name,
                'lat': location['lat'],
                'lon': location['lon'],
                'duration_min': 0,  # 起點/終點不需要停留時間
                'label': '交通樞紐',
                'period': 'morning',  # 起點預設為早上時段
                'hours': {i: [{'start': '00:00', 'end': '23:59'}] for i in range(1, 8)}
            }
        except Exception as e:
            raise ValueError(f"無法取得地點資訊: {str(e)}")
