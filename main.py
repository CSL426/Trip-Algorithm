# main.py

from time import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from src.core.planner.base import TripPlanner
from src.core.planner.validator import InputValidator
from src.core.utils.navigation_translator import NavigationTranslator
from sample_data import DEFAULT_LOCATIONS, DEFAULT_REQUIREMENT


class TripPlanningSystem:
    """行程規劃系統

    負責：
    1. 整合各個元件
    2. 處理使用者輸入
    3. 格式化輸出
    4. 系統流程控制
    """

    def __init__(self):
        """初始化規劃系統"""
        self.planner = TripPlanner()
        self.validator = InputValidator()
        self.execution_time = 0

    def plan_trip(self, locations: List[Dict], requirement: Dict) -> List[Dict]:
        """執行行程規劃

        輸入:
            locations: 所有可用地點列表
            requirement: 行程需求

        回傳:
            List[Dict]: 規劃後的行程列表
        """
        start_time = time.time()

        try:
            # 設定預設值
            requirement = self.validator.set_default_requirement(requirement)

            # 初始化地點資料
            self.planner.initialize_locations(
                locations=locations,
                custom_start=self._get_start_location(requirement),
                custom_end=self._get_end_location(requirement)
            )

            # 執行規劃
            result = self.planner.plan(
                start_time=requirement['start_time'],
                end_time=requirement['end_time'],
                travel_mode=requirement['transport_mode'],
                requirement=requirement
            )

            self.execution_time = time.time() - start_time
            return result

        except Exception as e:
            print(f"行程規劃錯誤: {str(e)}")
            raise

    def print_itinerary(self, itinerary: List[Dict], show_navigation: bool = False) -> None:
        """列印行程結果

        輸入:
            itinerary: 行程列表
            show_navigation: 是否顯示導航說明
        """
        print("\n=== 行程規劃結果 ===")

        total_travel_time = 0
        total_duration = 0

        for plan in itinerary:
            print(f"\n[地點 {plan['step']}]", end=' ')
            print(f"名稱: {plan['name']}")
            print(f"時間: {plan['start_time']} - {plan['end_time']}")
            print(f"停留: {plan['duration']}分鐘", end=' ')
            print(f"交通: {plan['transport_details']}"
                  f"({int(plan['travel_time'])}分鐘)")

            if show_navigation and 'route_info' in plan:
                print("\n前往下一站的導航:")
                print(NavigationTranslator.format_navigation(
                    plan['route_info']))

            total_travel_time += plan['travel_time']
            total_duration += plan['duration']

        print("\n=== 統計資訊 ===")
        print(f"總景點數: {len(itinerary)}個")
        print(f"總停留時間: {total_duration}分鐘 ({total_duration/60:.1f}小時)")
        print(
            f"總交通時間: {total_travel_time:.0f}分鐘 ({total_travel_time/60:.1f}小時)")
        print(f"規劃耗時: {self.execution_time:.2f}秒")

    def _get_start_location(self, requirement: Dict) -> Optional[Dict]:
        """處理起點設定"""
        start_point = requirement.get('start_point')
        if not start_point or start_point == "台北車站":
            return None
        return self._get_location_info(start_point)

    def _get_end_location(self, requirement: Dict) -> Optional[Dict]:
        """處理終點設定"""
        end_point = requirement.get('end_point')
        if not end_point:
            return None
        return self._get_location_info(end_point)

    def _get_location_info(self, place_name: str) -> Dict:
        """取得地點資訊"""
        try:
            from src.core.services.google_maps import GoogleMapsService
            from src.config.config import GOOGLE_MAPS_API_KEY
            service = GoogleMapsService(GOOGLE_MAPS_API_KEY)
            location = service.geocode(place_name)
            return {
                'name': place_name,
                'lat': location['lat'],
                'lon': location['lng'],
                'duration_min': 0,
                'label': '交通',
                'period': 'morning',
                'hours': {i: [{'start': '00:00', 'end': '23:59'}]
                          for i in range(1, 8)}
            }
        except Exception as e:
            raise ValueError(f"無法取得地點資訊: {str(e)}")


def main():
    """主程式進入點"""
    try:
        system = TripPlanningSystem()

        # 處理預設值
        processed_requirement = system.validator.set_default_requirement(
            DEFAULT_REQUIREMENT)

        # 顯示規劃參數
        print("=== 行程規劃系統 ===")
        print(f"起點：{processed_requirement['start_point']}")
        print(f"時間：{processed_requirement['start_time']} - "
              f"{processed_requirement['end_time']}")
        print(f"午餐：{processed_requirement['lunch_time']}")
        print(f"晚餐：{processed_requirement['dinner_time']}")
        print(f"景點數量：{len(DEFAULT_LOCATIONS)}個")
        print(f"交通方式：{processed_requirement['transport_mode_display']}")

        print("\n開始規劃行程...")

        # 執行規劃
        result = system.plan_trip(
            locations=DEFAULT_LOCATIONS,
            requirement=processed_requirement
        )

        # 輸出結果
        system.print_itinerary(result, show_navigation=False)

    except Exception as e:
        print(f"\n發生錯誤: {str(e)}")
        raise


if __name__ == "__main__":
    main()
