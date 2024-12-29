# main.py

"""行程規劃系統主程式

此模組負責：
1. 資料驗證和轉換
2. 規劃流程控制
3. 結果輸出與格式化
"""

import time
from typing import Dict, List, Optional
from datetime import datetime

from src.core.planner.base import TripPlanner
from src.core.models import TripRequirement, PlaceDetail
from data import TEST_LOCATIONS, TEST_REQUIREMENT, TEST_CUSTOM_START


class TripPlanningSystem:
    """行程規劃系統

    整合各個元件並執行完整的行程規劃流程：
    1. 驗證輸入資料
    2. 執行規劃
    3. 格式化輸出
    """

    def __init__(self):
        """初始化規劃系統"""
        self.execution_time = 0
        from src.core.planner.base import TripPlanner
        self.planner = TripPlanner()

    def validate_locations(self, locations: List[Dict]) -> List[PlaceDetail]:
        """驗證並轉換地點資料

        輸入參數:
            locations: 地點資料列表，每個地點必須包含：
                - name: str          # 地點名稱
                - lat: float         # 緯度
                - lon: float         # 經度
                - duration: int      # 建議停留時間(分鐘)
                - label: str         # 地點類型
                - period: str        # 時段標記(morning/lunch/afternoon/dinner/night)
                - hours: Dict        # 營業時間
                - rating: float      # 評分(選填)

        回傳：
            List[PlaceDetail]: 驗證後的地點物件列表

        異常：
            ValueError: 當資料格式不正確時
        """
        try:
            validated = []
            for loc in locations:
                # 確保所需欄位都存在
                required_fields = ['name', 'lat', 'lon',
                                   'duration', 'label', 'period', 'hours']
                missing = [
                    field for field in required_fields if field not in loc]
                if missing:
                    raise ValueError(
                        f"地點 {loc.get('name', 'Unknown')} 缺少必要欄位: {missing}")

                # duration_min 相容性處理
                if 'duration' in loc and 'duration_min' not in loc:
                    loc['duration_min'] = loc['duration']

                # 驗證 period 值
                valid_periods = {'morning', 'lunch',
                                 'afternoon', 'dinner', 'night'}
                if loc['period'] not in valid_periods:
                    raise ValueError(
                        f"地點 {loc['name']} 的 period 值無效: {loc['period']}")

                validated.append(PlaceDetail(**loc))
            return validated

        except Exception as e:
            raise ValueError(f"地點資料驗證錯誤: {str(e)}")

    def validate_requirement(self, requirement: Dict) -> TripRequirement:
        """驗證並轉換行程需求

        輸入參數:
            requirement: 需求資料，必須包含：
                - start_time: str        # 開始時間 (HH:MM)
                - end_time: str          # 結束時間 (HH:MM)
                - start_point: str       # 起點名稱
                - end_point: str         # 終點名稱
                - transport_mode: str    # 交通方式
                - distance_threshold: int # 距離限制(公里)
                - lunch_time: str        # 午餐時間 (HH:MM 或 none)
                - dinner_time: str       # 晚餐時間 (HH:MM 或 none)

        回傳：
            TripRequirement: 驗證後的需求物件

        異常：
            ValueError: 當資料格式不正確時
        """
        try:
            # 驗證時間格式
            time_fields = ['start_time', 'end_time']
            meal_fields = ['lunch_time', 'dinner_time']

            for field in time_fields:
                if not self._is_valid_time_format(requirement[field]):
                    raise ValueError(f"時間格式錯誤: {field}={requirement[field]}")

            for field in meal_fields:
                if requirement[field] != 'none' and not self._is_valid_time_format(requirement[field]):
                    raise ValueError(f"用餐時間格式錯誤: {field}={requirement[field]}")

            return TripRequirement(**requirement)

        except Exception as e:
            raise ValueError(f"需求資料驗證錯誤: {str(e)}")

    def _is_valid_time_format(self, time_str: str) -> bool:
        """檢查時間格式是否正確 (HH:MM)"""
        if time_str == 'none':
            return True

        try:
            datetime.strptime(time_str, '%H:%M')
            return True
        except ValueError:
            return False

    def plan_trip(self,
                  locations: List[Dict],
                  requirement: Dict,
                  custom_start: Optional[Dict] = None) -> List[Dict]:
        """執行行程規劃

        輸入參數:
            locations: 地點資料列表
            requirement: 行程需求
            custom_start: 自訂起點(選填)

        回傳：
            List[Dict]: 規劃後的行程列表，每個景點包含：
                - step: int          # 順序編號
                - name: str          # 地點名稱
                - start_time: str    # 到達時間 (HH:MM)
                - end_time: str      # 離開時間 (HH:MM)
                - duration: int      # 停留時間(分鐘)
                - transport_details: str  # 交通方式
                - travel_time: float     # 交通時間(分鐘)
        """
        start_time = time.time()

        try:
            # 1. 資料驗證
            validated_locations = self.validate_locations(locations)
            validated_requirement = self.validate_requirement(requirement)

            # 2. 初始化地點資料
            self.planner.initialize_locations(validated_locations,
                                              custom_start=custom_start)

            # 3. 執行規劃
            itinerary = self.planner.plan(
                start_time=validated_requirement.start_time,
                end_time=validated_requirement.end_time,
                travel_mode=validated_requirement.transport_mode,
                requirement=requirement
            )

            self.execution_time = time.time() - start_time
            return itinerary

        except Exception as e:
            print(f"行程規劃錯誤: {str(e)}")
            raise

    def get_execution_time(self) -> float:
        """取得執行時間（秒）"""
        return self.execution_time

    def print_itinerary(self, itinerary: List[Dict]) -> None:
        """列印行程結果

        輸入參數:
            itinerary: 行程列表
        """
        print("\n=== 行程規劃結果 ===")

        total_travel_time = 0
        total_duration = 0

        for plan in itinerary:
            print(f"\n[地點 {plan['step']}]")
            print(f"名稱: {plan['name']}")
            print(f"時間: {plan['start_time']} - {plan['end_time']}")
            print(f"停留: {plan['duration']}分鐘")
            print(
                f"交通: {plan['transport_details']} ({int(plan['travel_time'])}分鐘)")

            total_travel_time += plan['travel_time']
            total_duration += plan['duration']

        # 輸出統計資訊
        print("\n=== 統計資訊 ===")
        print(f"總景點數: {len(itinerary)}個")
        print(f"總停留時間: {total_duration}分鐘 ({total_duration/60:.1f}小時)")
        print(
            f"總交通時間: {total_travel_time:.0f}分鐘 ({total_travel_time/60:.1f}小時)")
        print(f"規劃耗時: {self.execution_time:.2f}秒")


def main():
    """主程式進入點"""
    try:
        # 建立規劃系統
        system = TripPlanningSystem()

        # 顯示規劃參數
        print("=== 行程規劃系統 ===")
        print(f"起點：{TEST_CUSTOM_START['name']}")
        print(
            f"時間：{TEST_REQUIREMENT['start_time']} - {TEST_REQUIREMENT['end_time']}")
        print(f"午餐：{TEST_REQUIREMENT['lunch_time']}")
        print(f"晚餐：{TEST_REQUIREMENT['dinner_time']}")
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

    except Exception as e:
        print(f"\n發生錯誤: {str(e)}")
        raise


if __name__ == "__main__":
    main()
