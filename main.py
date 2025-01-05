# main.py

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.core.models.place import PlaceDetail
from src.core.services.time_service import TimeService
from src.core.services.geo_service import GeoService
from src.core.evaluator.place_scoring import PlaceScoring
from src.core.planner import (
    TripPlanner,
    PlanningStrategyFactory,
    StrategyManager
)
from src.core.utils.navigation_translator import NavigationTranslator


class TripPlanningSystem:
    """行程規劃系統

    這個系統就像是一個專業的旅遊顧問，整合了各種服務來為用戶規劃最佳行程。
    它會考慮用戶的需求、時間限制、交通方式等多個因素，並且能夠靈活地調整規劃策略。
    """

    def __init__(self):
        """初始化規劃系統

        建立並連結各項服務：
        - 時間服務：處理時段判斷和用餐時間
        - 地理服務：處理距離和路線計算
        - 評分服務：計算地點分數
        """
        # 初始化時間服務(需要用餐時間設定)
        self.time_service = TimeService(
            lunch_time="12:00",  # 預設中午12點
            dinner_time="18:00"  # 預設晚上6點
        )

        self.geo_service = GeoService()
        self.place_scoring = PlaceScoring(
            time_service=self.time_service,
            geo_service=self.geo_service
        )

        # 初始化策略系統
        self.strategy_factory = PlanningStrategyFactory(
            time_service=self.time_service,
            geo_service=self.geo_service,
            place_scoring=self.place_scoring
        )
        self.strategy_manager = StrategyManager(self.strategy_factory)

        # 執行狀態追蹤
        self.execution_time = 0
        self.period_statistics = {
            'morning': {'count': 0, 'time': 0},
            'lunch': {'count': 0, 'time': 0},
            'afternoon': {'count': 0, 'time': 0},
            'dinner': {'count': 0, 'time': 0},
            'night': {'count': 0, 'time': 0}
        }

    def plan_trip(self, locations: List[Dict], requirement: Dict) -> List[Dict]:
        """執行行程規劃

        輸入參數:
            locations: List[Dict], 所有可用地點的資料
            requirement: Dict, 使用者的規劃需求，包含：
                - start_time: 開始時間
                - end_time: 結束時間
                - lunch_time: 午餐時間
                - dinner_time: 晚餐時間

        回傳:
            List[Dict]: 規劃好的行程列表
        """
        start_time = datetime.now()

        try:
            # 重設時間服務狀態
            self.time_service.reset()
            start_location = self._get_start_location(
                requirement['start_point'])
            self.geo_service.preload_routes(
                locations=[PlaceDetail(**loc) for loc in locations],
                center=PlaceDetail(**start_location),
                mode=requirement['transport_mode']
            )
            # 更新用餐時間設定
            if requirement.get('lunch_time'):
                self.time_service.lunch_time = datetime.strptime(
                    requirement['lunch_time'], '%H:%M').time()
            if requirement.get('dinner_time'):
                self.time_service.dinner_time = datetime.strptime(
                    requirement['dinner_time'], '%H:%M').time()

            # 轉換地點資料
            available_places = [
                PlaceDetail(**location) if isinstance(location, dict)
                else location for location in locations
            ]

            # 準備規劃上下文
            context = self._prepare_planning_context(
                available_places, requirement)

            print("\n=== 開始行程規劃 ===")
            print(f"規劃起始時間: {context['start_time'].strftime('%H:%M')}")
            print(f"預計結束時間: {context['end_time'].strftime('%H:%M')}")
            print(f"午餐時間設定: {self.time_service.lunch_time.strftime('%H:%M')}")
            print(f"晚餐時間設定: {self.time_service.dinner_time.strftime('%H:%M')}")

            # 初始化策略
            strategy = self.strategy_manager.initialize_strategy(context)

            # 執行規劃
            itinerary = strategy.execute(
                current_location=context['start_location'],
                available_places=context['available_places'],
                current_time=context['start_time']
            )

            # 記錄執行時間
            self.execution_time = (datetime.now() - start_time).total_seconds()

            # 統計各時段的規劃結果
            self._update_period_statistics(itinerary)

            return itinerary

        except Exception as e:
            print(f"行程規劃失敗: {str(e)}")
            raise

    def _update_period_statistics(self, itinerary: List[Dict]) -> None:
        """更新各時段的統計資訊"""
        for item in itinerary:
            period = self.time_service.get_current_period(
                datetime.strptime(item['start_time'], '%H:%M')
            )
            self.period_statistics[period]['count'] += 1
            self.period_statistics[period]['time'] += item['duration']

    def print_planning_summary(self) -> None:
        """輸出規劃統計摘要"""
        print("\n=== 規劃統計 ===")
        for period, stats in self.period_statistics.items():
            if stats['count'] > 0:
                print(f"{period}: {stats['count']}個地點，"
                      f"共{stats['time']}分鐘")

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

        這個方法就像是將我們規劃好的行程整理成一份清晰的旅遊指南。它會：
        1. 顯示每個景點的詳細資訊
        2. 提供交通指引
        3. 顯示時間安排
        4. 提供整體行程的統計資訊
        """
        print("\n=== 行程規劃結果 ===")

        total_travel_time = 0
        total_duration = 0

        for plan in itinerary:
            # 顯示景點資訊
            print(f"\n[地點 {plan['step']}]")
            print(f"名稱: {plan['name']}")
            print(f"時間: {plan['start_time']} - {plan['end_time']}")
            print(f"停留: {plan['duration']}分鐘", end=' ')

            # 顯示交通資訊
            print(f"交通: {plan['transport_details']}"
                  f"({int(plan['travel_time'])}分鐘)")

            # 如果需要，顯示詳細的導航資訊
            if show_navigation and 'route_info' in plan:
                print("\n前往下一站的導航:")
                print(NavigationTranslator.format_navigation(
                    plan['route_info']))

            # 累計時間統計
            total_travel_time += plan['travel_time']
            total_duration += plan['duration']

        # 顯示整體統計資訊
        print("\n=== 統計資訊 ===")
        print(f"總景點數: {len(itinerary)}個")
        print(f"總停留時間: {total_duration}分鐘 "
              f"({total_duration/60:.1f}小時)")
        print(f"總交通時間: {total_travel_time:.0f}分鐘 "
              f"({total_travel_time/60:.1f}小時)")
        print(f"規劃耗時: {self.execution_time:.2f}秒")

    def _get_start_location(self, start_point: str) -> Dict:
        """處理起點設定

        這個方法負責將起點的字串名稱轉換為完整的地點資訊。
        它會：
        1. 檢查是否使用預設起點（台北車站）
        2. 如果不是預設起點，則取得該地點的詳細資訊
        3. 確保回傳的資料包含所有必要的欄位

        參數:
            start_point: 起點的名稱（字串）

        回傳:
            Dict: 包含完整地點資訊的字典
        """
        if not start_point or start_point == "台北車站":
            # 使用預設起點
            return {
                'name': '台北車站',
                'lat': 25.0478,
                'lon': 121.5170,
                'duration_min': 0,
                'label': '交通樞紐',
                'period': 'morning',
                'hours': {i: [{'start': '00:00', 'end': '23:59'}]
                          for i in range(1, 8)}
            }

        return self._get_location_info(start_point)

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
                'duration_min': 0,
                'label': '交通',
                'period': 'morning',
                'hours': {i: [{'start': '00:00', 'end': '23:59'}]
                          for i in range(1, 8)}
            }
        except Exception as e:
            raise ValueError(f"無法取得地點資訊: {str(e)}")


def main():
    """主程式入口

    這是系統的啟動點，負責：
    1. 初始化系統
    2. 讀取必要的資料
    3. 執行規劃流程
    4. 處理可能的錯誤
    """
    try:
        from sample_data import DEFAULT_LOCATIONS, DEFAULT_REQUIREMENT

        # 初始化規劃系統
        system = TripPlanningSystem()

        # 顯示規劃參數
        print("=== 行程規劃系統 ===")
        print(f"起點：{DEFAULT_REQUIREMENT['start_point']}")
        print(f"時間：{DEFAULT_REQUIREMENT['start_time']} - "
              f"{DEFAULT_REQUIREMENT['end_time']}")
        print(f"午餐：{DEFAULT_REQUIREMENT['lunch_time']}")
        print(f"晚餐：{DEFAULT_REQUIREMENT['dinner_time']}")
        print(f"景點數量：{len(DEFAULT_LOCATIONS)}個")
        print(f"交通方式：{DEFAULT_REQUIREMENT['transport_mode']}")

        print("\n開始規劃行程...")

        # 執行行程規劃
        result = system.plan_trip(
            locations=DEFAULT_LOCATIONS,
            requirement=DEFAULT_REQUIREMENT
        )

        # 輸出結果
        system.print_itinerary(result, show_navigation=False)

    except Exception as e:
        print(f"\n發生錯誤: {str(e)}")
        raise


if __name__ == "__main__":
    main()
