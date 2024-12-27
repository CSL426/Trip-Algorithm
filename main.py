# main.py

import time
from typing import Dict, List, Optional

from src.core.trip_planner import TripPlanner
from src.core.models import TripRequirement, PlaceDetail
from tests.data.test_data import TEST_LOCATIONS


class TripPlanningSystem:
    """
    行程規劃系統主類別

    負責整合各個元件並執行完整的行程規劃流程
    包含：資料驗證、行程規劃、結果輸出
    """

    def __init__(self):
        """初始化行程規劃器"""
        self.planner = TripPlanner()
        self.execution_time = 0

    def validate_locations(self, locations: List[Dict]) -> List[PlaceDetail]:
        """
        驗證並轉換地點資料格式

        參數:
            locations: 原始地點資料列表

        回傳:
            List[PlaceDetail]: 驗證後的地點資料列表
        """
        validated_locations = []
        for loc in locations:
            try:
                if isinstance(loc, PlaceDetail):
                    validated_locations.append(loc)
                else:
                    validated_locations.append(PlaceDetail(**loc))
            except Exception as e:
                print(f"地點資料驗證錯誤 ({loc.get('name', 'Unknown')}): {str(e)}")
                raise
        return validated_locations

    def validate_requirement(self, requirement: Dict) -> TripRequirement:
        """
        驗證並轉換使用者需求資料

        輸入參數:
            requirement (Dict): 使用者需求資料
                格式: {
                    "start_time": str,        # 開始時間 (HH:MM)
                    "end_time": str,          # 結束時間 (HH:MM)
                    "start_point": str,       # 起點
                    "end_point": str,         # 終點
                    "transport_mode": str,    # 交通方式
                    "distance_threshold": int, # 距離限制(km)
                    "breakfast_time": str,    # 早餐時間
                    "lunch_time": str,        # 午餐時間
                    "dinner_time": str,       # 晚餐時間
                    "budget": Union[int,str], # 預算
                    "date": str               # 日期 (MM-DD)
                }

        回傳:
            TripRequirement: 驗證後的需求物件
        """
        try:
            return TripRequirement(**requirement)
        except Exception as e:
            print(f"需求資料驗證錯誤: {str(e)}")
            raise

    def plan_trip(self, locations: List[Dict], requirement: Dict) -> List[Dict]:
        """
        執行行程規劃流程

        輸入參數:
            locations (List[Dict]): 地點資料列表
            requirement (Dict): 使用者需求資料

        回傳:
            List[Dict]: 規劃後的行程列表
        """
        start_time = time.time()

        try:
            # 步驟1: 資料驗證
            validated_locations = self.validate_locations(locations)
            validated_requirement = self.validate_requirement(requirement)

            # 步驟2: 初始化地點資料
            self.planner.initialize_locations(validated_locations)

            # 步驟3: 執行規劃
            itinerary = self.planner.plan(
                start_time=validated_requirement.start_time,
                end_time=validated_requirement.end_time,
                travel_mode=validated_requirement.transport_mode
            )

            self.execution_time = time.time() - start_time
            return itinerary

        except Exception as e:
            print(f"行程規劃錯誤: {str(e)}")
            raise

    def get_execution_time(self) -> float:
        """取得執行時間(秒)"""
        return self.execution_time


def main():
    """
    主程式進入點
    用於測試行程規劃系統
    """
    # 測試資料
    test_requirement = {
        "start_time": "09:00",
        "end_time": "18:00",
        "start_point": "台北車站",
        "end_point": "台北車站",
        "transport_mode": "transit",
        "distance_threshold": 30,
        "breakfast_time": "none",
        "lunch_time": "12:00",
        "dinner_time": "18:00",
        "budget": "none",
        "date": "12-25"
    }

    try:
        # 建立行程規劃系統
        system = TripPlanningSystem()

        # 執行規劃
        result = system.plan_trip(
            locations=TEST_LOCATIONS,
            requirement=test_requirement
        )

        # 輸出結果
        print("\n=== 行程規劃結果 ===")
        for i, plan in enumerate(result, 1):
            print(f"\n[地點 {plan['step']}]")
            print(f"名稱: {plan['name']}")
            print(f"時間: {plan['start_time']} - {plan['end_time']}")
            print(f"停留: {plan['duration']}分鐘")
            print(f"交通: {plan['transport_details']}"
                  f"({plan['travel_time']:.1f}分鐘)")

        print(f"\n規劃耗時: {system.get_execution_time():.2f}秒")

    except Exception as e:
        print(f"\n發生錯誤: {str(e)}")
        raise


if __name__ == "__main__":
    main()
