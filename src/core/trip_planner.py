# src\core\trip_planner.py

from typing import List, Dict, Optional
from src.core.models import PlaceDetail
from src.core.test_data import TEST_LOCATIONS, TEST_CUSTOM_START
from src.core.planners.advanced_planner import AdvancedTripPlanner


class TripPlanner:
    """
    行程規劃器主類別
    負責管理行程規劃的流程和實作
    """

    def __init__(self):
        """
        初始化 TripPlanner
        設定基本屬性並建立規劃器實例
        """
        self.planner = None
        self.locations = None

    def initialize_locations(self, locations: List[Dict], custom_start: Optional[Dict] = None,
                             custom_end: Optional[Dict] = None) -> None:
        """
        初始化地點資料

        輸入參數:
            locations (List[Dict]): 景點清單
                格式：[{
                    'name': str,          # 景點名稱
                    'lat': float,         # 緯度
                    'lon': float,         # 經度
                    'duration': int,      # 建議停留時間（分鐘）
                    'label': str,         # 景點類型
                    'hours': Dict         # 營業時間
                }]
            custom_start (Optional[Dict]): 自訂起點，預設None
            custom_end (Optional[Dict]): 自訂終點，預設None
        """
        # 將字典格式轉換為 PlaceDetail 物件
        place_details = []
        for loc in locations:
            # 將 duration 轉換為 duration_min（如果需要的話）
            if 'duration' in loc and 'duration_min' not in loc:
                loc['duration_min'] = loc['duration']
            place_details.append(PlaceDetail(**loc))

        # 處理自訂起點
        custom_start_place = None
        if custom_start:
            if 'duration' in custom_start:
                custom_start['duration_min'] = custom_start['duration']
            custom_start_place = PlaceDetail(
                name=custom_start.get('name', '自訂起點'),
                lat=custom_start['lat'],
                lon=custom_start['lon'],
                duration_min=0,
                label='起點',
                hours={i: [{'start': '00:00', 'end': '23:59'}]
                       for i in range(1, 8)}
            )

        # 處理自訂終點
        custom_end_place = None
        if custom_end:
            if 'duration' in custom_end:
                custom_end['duration_min'] = custom_end['duration']
            custom_end_place = PlaceDetail(
                name=custom_end.get('name', '自訂終點'),
                lat=custom_end['lat'],
                lon=custom_end['lon'],
                duration_min=0,
                label='終點',
                hours={i: [{'start': '00:00', 'end': '23:59'}]
                       for i in range(1, 8)}
            )

        self.locations = place_details
        if self.planner:
            self.planner.initialize_locations(
                self.locations,
                custom_start_place,
                custom_end_place
            )

    def plan(self, start_time: str = '09:00', end_time: str = '20:00',
             travel_mode: str = 'transit', custom_start: Optional[Dict] = None,
             custom_end: Optional[Dict] = None) -> List[Dict]:
        """
        執行行程規劃

        輸入參數:
            start_time (str): 開始時間，格式為 'HH:MM'
            end_time (str): 結束時間，格式為 'HH:MM'
            travel_mode (str): 交通方式，可選 "transit", "driving", "bicycling", "walking"
            custom_start (Optional[Dict]): 自訂起點資訊
            custom_end (Optional[Dict]): 自訂終點資訊

        回傳:
            List[Dict]: 規劃好的行程清單
                格式：[{
                    'step': int,              # 行程順序
                    'name': str,              # 地點名稱
                    'start_time': str,        # 開始時間 (HH:MM)
                    'end_time': str,          # 結束時間 (HH:MM)
                    'duration': int,          # 停留時間（分鐘）
                    'hours': str,             # 營業時間
                    'transport_details': str,  # 交通方式描述
                    'travel_time': float,     # 交通時間（分鐘）
                    'is_meal': bool           # 是否為餐廳
                }]
        """
        # 建立進階規劃器實例
        self.planner = AdvancedTripPlanner(
            start_time=start_time,
            end_time=end_time,
            travel_mode=travel_mode
        )

        # 初始化地點資訊
        self.planner.initialize_locations(
            self.locations,
            custom_start,
            custom_end
        )

        # 執行規劃並回傳結果
        return self.planner.plan()


def test_planner():
    """
    測試行程規劃功能
    """
    # 建立規劃器實例
    planner = TripPlanner()

    # 測試案例 1：基本行程規劃
    print("\n=== 測試 1：基本行程規劃 ===")
    planner.initialize_locations(TEST_LOCATIONS)
    result = planner.plan(
        start_time="09:00",
        end_time="18:00",
        travel_mode="transit"
    )

    # 輸出結果
    for i, item in enumerate(result):
        print(f"\n[地點 {item['step']}]")
        print(f"名稱: {item['name']}")
        print(f"時間: {item['start_time']} - {item['end_time']}")
        print(f"交通: {item['transport_details']} ({item['travel_time']:.1f}分鐘)")

    # 測試案例 2：自訂起點
    print("\n=== 測試 2：自訂起點 ===")
    planner.initialize_locations(
        TEST_LOCATIONS,
        custom_start=TEST_CUSTOM_START
    )
    result = planner.plan(
        start_time="10:00",
        end_time="19:00",
        travel_mode="driving"
    )

    # 輸出結果
    for i, item in enumerate(result):
        print(f"\n[地點 {item['step']}]")
        print(f"名稱: {item['name']}")
        print(f"時間: {item['start_time']} - {item['end_time']}")
        print(f"交通: {item['transport_details']} ({item['travel_time']:.1f}分鐘)")


if __name__ == "__main__":
    test_planner()
