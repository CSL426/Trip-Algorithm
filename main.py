# main.py

"""行程規劃系統主程式

此模組提供行程規劃系統的主要功能介面，包含：
1. 系統初始化
2. 資料驗證
3. 行程規劃
4. 結果輸出

使用方式：
1. 直接執行此檔案進行測試：python main.py
2. 作為模組匯入使用系統功能
"""

import time
from typing import Dict, List, Optional
from datetime import datetime

from data import TEST_LOCATIONS, TEST_REQUIREMENT, TEST_CUSTOM_START
from src.core.models import TripRequirement, PlaceDetail


class TripPlanningSystem:
    """行程規劃系統

    整合各個元件並執行完整的行程規劃流程：
    1. 資料驗證
    2. 行程規劃
    3. 結果輸出
    """

    def __init__(self):
        """初始化規劃系統"""
        self.execution_time = 0
        from src.core.planner.base import TripPlanner
        self.planner = TripPlanner()
        self.execution_time = 0

    def validate_locations(self, locations: List[Dict]) -> List[PlaceDetail]:
        """驗證並轉換地點資料

        輸入參數:
            locations (List[Dict]): 地點資料列表，每個地點必須包含:
                - name: str,             # 地點名稱
                - lat: float,            # 緯度
                - lon: float,            # 經度
                - duration: int,         # 建議停留時間(分鐘)
                - label: str,            # 地點類型
                - hours: Dict,           # 營業時間，格式見 data.py
                - rating: float = 0.0    # 評分(選填)

        回傳:
            List[PlaceDetail]: 驗證後的地點物件列表

        異常:
            ValueError: 當資料格式不正確時
        """
        try:
            validated = []
            for loc in locations:
                if 'duration' in loc and 'duration_min' not in loc:
                    loc['duration_min'] = loc['duration']
                validated.append(PlaceDetail(**loc))
            return validated
        except Exception as e:
            raise ValueError(f"地點資料驗證錯誤: {str(e)}")

    def validate_requirement(self, requirement: Dict) -> TripRequirement:
        """驗證並轉換行程需求

        輸入參數:
            requirement (Dict): 需求資料，必須包含:
                - start_time: str        # 開始時間 (HH:MM)
                - end_time: str          # 結束時間 (HH:MM)
                - start_point: str       # 起點名稱
                - end_point: str         # 終點名稱
                - transport_mode: str    # 交通方式
                - distance_threshold: int # 距離限制(km)
                - breakfast_time: str    # 早餐時間
                - lunch_time: str        # 午餐時間
                - dinner_time: str       # 晚餐時間
                - budget: Union[int,str] # 預算
                - date: str             # 日期 (MM-DD)

        回傳:
            TripRequirement: 驗證後的需求物件

        異常:
            ValueError: 當資料格式不正確時
        """
        try:
            return TripRequirement(**requirement)
        except Exception as e:
            raise ValueError(f"需求資料驗證錯誤: {str(e)}")

    def plan_trip(self,
                  locations: List[Dict],
                  requirement: Dict,
                  custom_start: Optional[Dict] = None) -> List[Dict]:
        """執行行程規劃

        輸入參數:
            locations (List[Dict]): 地點資料列表
            requirement (Dict): 行程需求
            custom_start (Optional[Dict]): 自訂起點(選填)

        回傳:
            List[Dict]: 規劃後的行程列表，每個行程包含:
                - step: int          # 順序編號
                - name: str          # 地點名稱
                - start_time: str    # 開始時間 (HH:MM)
                - end_time: str      # 結束時間 (HH:MM)
                - duration: int      # 停留時間(分鐘)
                - transport_details: str  # 交通方式說明
                - travel_time: float     # 交通時間(分鐘)
        """
        start_time = time.time()

        try:
            # 1. 資料驗證
            validated_locations = self.validate_locations(locations)
            validated_requirement = self.validate_requirement(requirement)

            # 2. 初始化地點資料
            self.planner.initialize_locations(validated_locations)

            # 步驟3: 執行規劃
            itinerary = self.planner.plan(
                start_time=validated_requirement.start_time,
                end_time=validated_requirement.end_time,
                travel_mode=validated_requirement.transport_mode,
                requirement=requirement  # 加入requirement參數
            )

            self.execution_time = time.time() - start_time
            return itinerary

        except Exception as e:
            print(f"行程規劃錯誤: {str(e)}")
            raise

    def get_execution_time(self) -> float:
        """取得執行時間

        回傳:
            float: 執行時間(秒)
        """
        return self.execution_time

    def print_itinerary(self, itinerary: List[Dict]) -> None:
        """列印行程結果

        輸入參數:
            itinerary (List[Dict]): 行程列表
        """
        print("\n=== 行程規劃結果 ===")
        for plan in itinerary:
            print(f"\n[地點 {plan['step']}]")
            print(f"名稱: {plan['name']}")
            print(f"時間: {plan['start_time']} - {plan['end_time']}")
            print(f"停留: {plan['duration']}分鐘")
            print(f"交通: {plan['transport_details']}"
                  f"({plan['travel_time']:.1f}分鐘)")


def main():
    """主程式進入點

    展示系統功能的範例流程：
    1. 讀取測試資料
    2. 執行行程規劃
    3. 輸出結果
    """
    try:
        # 顯示歡迎訊息
        print("=== 歡迎使用行程規劃系統 ===")
        print("載入測試資料...")

        # 建立行程規劃系統
        system = TripPlanningSystem()

        # 顯示規劃參數
        print("\n規劃參數：")
        print(f"起點：{TEST_CUSTOM_START['name']}")
        print(f"時間：{TEST_REQUIREMENT['start_time']}"
              f" - {TEST_REQUIREMENT['end_time']}")
        print(f"景點數量：{len(TEST_LOCATIONS)}個")
        print(f"交通方式：{TEST_REQUIREMENT['transport_mode']}")

        print("\n開始規劃行程...")

        # 執行規劃
        result = system.plan_trip(
            locations=TEST_LOCATIONS,
            requirement=TEST_REQUIREMENT,
            custom_start=TEST_CUSTOM_START
        )

        # 輸出結果
        system.print_itinerary(result)

        # 顯示統計資訊
        print(f"\n統計資訊:")
        print(f"規劃耗時: {system.get_execution_time():.2f}秒")
        print(f"景點數量: {len(result)}個")
        total_duration = sum(x['duration'] for x in result)
        total_travel = sum(x['travel_time'] for x in result)
        print(f"總停留時間: {total_duration}分鐘")
        print(f"總交通時間: {total_travel:.0f}分鐘")

        print("\n規劃完成！")

    except ValueError as e:
        print(f"\n資料錯誤: {str(e)}")
        raise
    except Exception as e:
        print(f"\n發生未預期的錯誤: {str(e)}")
        raise


if __name__ == "__main__":
    main()
