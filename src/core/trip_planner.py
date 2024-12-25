# src\core\trip_planner.py

# fmt: off
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any

# 將專案根目錄加入到 Python 路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

# 使用絕對導入
from src.core.test_data import TEST_LOCATIONS, TEST_CUSTOM_START
from src.core.planners.base_planner import BaseTripPlanner
from src.core.planners.advanced_planner import AdvancedTripPlanner
from src.core.trip_node import convert_itinerary_to_trip_plan
# fmt: on


class TripPlanner(BaseTripPlanner):
    """
    行程規劃器主類別
    繼承自 BaseTripPlanner，提供完整的行程規劃功能
    """

    def __init__(self):
        """
        初始化 TripPlanner
        設定基本屬性並建立規劃器實例
        """
        super().__init__()
        self.planner = None
        self.locations = None

    def initialize_locations(self, locations, custom_start=None, custom_end=None):
        """
        初始化地點資料

        參數：
            locations (List[Dict]): 景點清單，每個景點包含：
                - name: 景點名稱
                - lat: 緯度
                - lon: 經度
                - duration: 建議停留時間（分鐘）
                - label: 景點類型
                - hours: 營業時間資訊
            custom_start (Dict): 自訂起點資訊，預設為 None
            custom_end (Dict): 自訂終點資訊，預設為 None
        """
        self.locations = locations
        super().initialize_locations(locations, custom_start, custom_end)

    def plan(self, start_time='09:00', end_time='20:00',
             travel_mode='transit', custom_start=None, custom_end=None):
        """
        執行行程規劃

        參數：
            start_time (str): 開始時間，格式為 'HH:MM'
            end_time (str): 結束時間，格式為 'HH:MM'
            travel_mode (str): 交通方式，可選 "大眾運輸", "開車", "騎自行車", "步行"
            custom_start (Dict): 自訂起點資訊
            custom_end (Dict): 自訂終點資訊

        回傳：
            List[Dict]: 規劃好的行程清單
        """
        # 建立進階規劃器實例
        self.planner = AdvancedTripPlanner(
            start_time=start_time,
            end_time=end_time,
            travel_mode=travel_mode,
            custom_start=custom_start,
            custom_end=custom_end
        )

        # 初始化地點資訊
        self.planner.initialize_locations(
            self.available_locations,
            custom_start,
            custom_end
        )

        # 執行規劃並回傳結果
        return self.planner.plan()


def main():
    """測試主函式"""
    import time

    total_start_time = time.time()

    # 建立規劃器實例
    planner = TripPlanner()

    # 步驟1：初始化地點資料
    planner.initialize_locations(
        locations=TEST_LOCATIONS,
        custom_start=TEST_CUSTOM_START,
        custom_end=TEST_CUSTOM_START
    )

    # 步驟2：執行行程規劃
    itinerary = planner.plan(
        start_time='08:00',
        end_time='18:00',
        travel_mode='開車'
    )

    # 輸出行程結果
    trip_plan = convert_itinerary_to_trip_plan(itinerary)
    trip_plan.print_itinerary()

    # 顯示執行時間
    total_execution_time = time.time() - total_start_time
    print(f"\n總執行時間：{total_execution_time:.2f}秒")


if __name__ == "__main__":
    main()
