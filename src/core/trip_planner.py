# src/core/trip_planner.py

from typing import List, Dict, Union, Optional
from datetime import datetime
from src.core.models import PlaceDetail
from tests.data.test_data import TEST_LOCATIONS, TEST_CUSTOM_START
from src.core.planners.advanced_planner import AdvancedTripPlanner
from src.core.utils import calculate_travel_time


class TripPlanner:
    """
    行程規劃器主類別，負責管理整個行程規劃流程。
    提供地點資料初始化、行程規劃執行和結果輸出等功能。
    """

    def __init__(self):
        """
        初始化行程規劃器，建立必要的資料結構和狀態追蹤
        """
        self.planner = None          # 儲存進階規劃器實例
        self.locations = None        # 儲存已驗證的地點資料
        self.start_location = None   # 儲存起點資訊
        self.end_location = None     # 儲存終點資訊

    def initialize_locations(self,
                             locations: List[Union[Dict, PlaceDetail]],
                             custom_start: Optional[Union[Dict,
                                                          PlaceDetail]] = None,
                             custom_end: Optional[Union[Dict, PlaceDetail]] = None) -> None:
        """
        初始化地點資料，包含地點清單和自訂起終點

        參數:
            locations: 地點列表，可以是字典或 PlaceDetail 物件
            custom_start: 自訂起點（可選）
            custom_end: 自訂終點（可選）
        """
        # 預設起點（台北車站）
        default_point = PlaceDetail(
            name='台北車站',
            lat=25.0426731,
            lon=121.5170756,
            duration_min=0,
            label='交通樞紐',
            hours={
                i: [{'start': '00:00', 'end': '23:59'}]
                for i in range(1, 8)
            }
        )

        # 處理地點列表
        self.locations = []
        for loc in locations:
            if isinstance(loc, PlaceDetail):
                self.locations.append(loc)
            else:
                # 處理 duration 欄位
                if 'duration' in loc and 'duration_min' not in loc:
                    loc['duration_min'] = loc['duration']
                self.locations.append(PlaceDetail(**loc))

        # 設定起點
        if custom_start:
            if isinstance(custom_start, PlaceDetail):
                self.start_location = custom_start
            else:
                if 'duration' in custom_start:
                    custom_start['duration_min'] = custom_start['duration']
                self.start_location = PlaceDetail(**custom_start)
        else:
            self.start_location = default_point

        # 設定終點
        if custom_end:
            if isinstance(custom_end, PlaceDetail):
                self.end_location = custom_end
            else:
                if 'duration' in custom_end:
                    custom_end['duration_min'] = custom_end['duration']
                self.end_location = PlaceDetail(**custom_end)
        else:
            self.end_location = self.start_location

    def plan(self,
             start_time: str = '09:00',
             end_time: str = '20:00',
             travel_mode: str = 'transit',
             custom_start: Optional[Dict] = None,
             custom_end: Optional[Dict] = None) -> List[Dict]:
        """
        執行行程規劃

        參數:
            start_time: 開始時間，格式 'HH:MM'
            end_time: 結束時間，格式 'HH:MM'
            travel_mode: 交通方式
            custom_start: 自訂起點
            custom_end: 自訂終點

        回傳:
            規劃好的行程列表
        """
        # 確保有地點資料
        if not self.locations:
            raise ValueError("請先使用 initialize_locations 初始化地點資料")

        # 建立進階規劃器
        self.planner = AdvancedTripPlanner(
            start_time=start_time,
            end_time=end_time,
            travel_mode=travel_mode
        )

        # 初始化規劃器的地點資料
        self.planner.initialize_locations(
            locations=self.locations,
            custom_start=self.start_location,
            custom_end=self.end_location
        )

        # 執行規劃
        return self.planner.plan()

    def get_execution_stats(self) -> Dict:
        """
        取得執行統計資訊

        回傳:
            包含總執行時間、造訪地點數和總距離的統計資料
        """
        if not self.planner:
            return {
                'total_time': 0,
                'visited_count': 0,
                'total_distance': 0
            }

        return {
            'total_time': getattr(self.planner, 'execution_time', 0),
            'visited_count': len(getattr(self.planner, 'selected_locations', [])),
            'total_distance': getattr(self.planner, 'total_distance', 0)
        }


def test_planner():
    """
    測試行程規劃功能。
    執行基本行程規劃和自訂起點的測試案例。
    """
    # 建立規劃器實例
    planner = TripPlanner()

    # 測試案例 1：基本行程規劃
    print("\n=== 測試 1：基本行程規劃 ===")

    # 初始化地點資料
    planner.initialize_locations(TEST_LOCATIONS)

    # 執行規劃
    result = planner.plan(
        start_time="09:00",
        end_time="18:00",
        travel_mode="transit"
    )

    # 輸出結果
    if result:
        for item in result:
            print(f"\n[地點 {item['step']}]")
            print(f"名稱: {item['name']}")
            print(f"時間: {item['start_time']} - {item['end_time']}")
            print(f"停留: {item['duration']}分鐘")
            print(f"交通: {item['transport_details']}"
                  f"({item['travel_time']:.1f}分鐘)")

    # 測試案例 2：自訂起點
    print("\n=== 測試 2：自訂起點 ===")

    # 初始化地點資料（包含自訂起點）
    planner.initialize_locations(
        TEST_LOCATIONS,
        custom_start=TEST_CUSTOM_START
    )

    # 執行規劃
    result = planner.plan(
        start_time="10:00",
        end_time="19:00",
        travel_mode="driving"
    )

    # 輸出結果
    if result:
        for item in result:
            print(f"\n[地點 {item['step']}]")
            print(f"名稱: {item['name']}")
            print(f"時間: {item['start_time']} - {item['end_time']}")
            print(f"停留: {item['duration']}分鐘")
            print(f"交通: {item['transport_details']}"
                  f"({item['travel_time']:.1f}分鐘)")


if __name__ == "__main__":
    test_planner()
