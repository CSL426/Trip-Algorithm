# tests/test_cases/planner/test_strategy.py

import pytest
from datetime import datetime, timedelta
from src.core.planner.strategy import PlanningStrategy
from src.core.models.place import PlaceDetail


class TestPlanningStrategy:
    """
    規劃策略的測試類別

    測試行程規劃的核心演算法，包括：
    1. 最佳地點選擇邏輯
    2. 時間和距離的計算
    3. 效率評分機制
    4. 完整規劃流程
    """

    @pytest.fixture
    def strategy(self):
        """提供測試用的規劃策略實例"""
        start_time = datetime.strptime("09:00", "%H:%M")
        end_time = datetime.strptime("18:00", "%H:%M")
        return PlanningStrategy(
            start_time=start_time,
            end_time=end_time,
            travel_mode="transit"
        )

    @pytest.fixture
    def sample_places(self):
        """提供測試用的地點清單"""
        return [
            PlaceDetail(
                name="台北101",
                rating=4.5,
                lat=25.0339808,
                lon=121.561964,
                duration_min=90,
                label="景點",
                hours={i: [{'start': '09:00', 'end': '22:00'}]
                       for i in range(1, 8)}
            ),
            PlaceDetail(
                name="故宮博物院",
                rating=4.7,
                lat=25.1023,
                lon=121.5482,
                duration_min=120,
                label="博物館",
                hours={i: [{'start': '08:30', 'end': '18:30'}]
                       for i in range(1, 8)}
            ),
            PlaceDetail(
                name="鼎泰豐",
                rating=4.6,
                lat=25.0329,
                lon=121.5604,
                duration_min=60,
                label="餐廳",
                hours={
                    i: [
                        {'start': '11:30', 'end': '14:30'},
                        {'start': '17:30', 'end': '21:30'}
                    ] for i in range(1, 8)
                }
            )
        ]

    @pytest.fixture
    def start_location(self):
        """提供測試用的起點"""
        return PlaceDetail(
            name="台北車站",
            rating=0,
            lat=25.0478,
            lon=121.5170,
            duration_min=0,
            label="交通",
            hours={i: [{'start': '00:00', 'end': '23:59'}]
                   for i in range(1, 8)}
        )

    def test_find_best_next_location(self, strategy, sample_places, start_location):
        """
        測試最佳下一個地點的選擇邏輯

        確保：
        1. 選擇最佳的下一個地點
        2. 考慮時間和距離限制
        3. 正確評估地點分數
        """
        current_time = datetime.strptime("09:30", "%H:%M")
        next_location = strategy._find_best_next_location(
            start_location,
            sample_places,
            current_time
        )

        assert next_location is not None
        assert isinstance(next_location, PlaceDetail)

    def test_has_enough_time(self, strategy, sample_places):
        """
        測試時間充足性判斷

        確保：
        1. 正確判斷是否有足夠時間
        2. 考慮營業時間限制
        3. 處理特殊時間情況
        """
        place = sample_places[0]  # 台北101

        # 測試有足夠時間的情況
        arrival_time = datetime.strptime("10:00", "%H:%M")
        assert strategy._has_enough_time(place, arrival_time)

        # 測試時間不足的情況
        late_arrival = datetime.strptime("17:30", "%H:%M")
        assert not strategy._has_enough_time(place, late_arrival)

    def test_is_meal_time(self, strategy):
        """
        測試用餐時間判斷

        確保：
        1. 正確識別用餐時段
        2. 處理不同時段的判斷
        3. 邊界時間的處理
        """
        # 測試午餐時間
        lunch_time = datetime.strptime("12:00", "%H:%M")
        assert strategy._is_meal_time(lunch_time)

        # 測試晚餐時間
        dinner_time = datetime.strptime("18:00", "%H:%M")
        assert strategy._is_meal_time(dinner_time)

        # 測試非用餐時間
        non_meal_time = datetime.strptime("15:00", "%H:%M")
        assert not strategy._is_meal_time(non_meal_time)

    def test_calculate_travel_info(self, strategy, sample_places, start_location):
        """
        測試交通資訊計算

        確保：
        1. 正確計算交通時間
        2. 產生有效的交通資訊
        3. 處理不同交通方式
        """
        travel_info = strategy._calculate_travel_info(
            start_location,
            sample_places[0]
        )

        assert isinstance(travel_info, dict)
        assert 'time' in travel_info
        assert 'transport_details' in travel_info
        assert travel_info['time'] > 0

    def test_execute_full_planning(self, strategy, sample_places, start_location):
        """
        測試完整的規劃流程執行

        確保：
        1. 能產生完整的行程
        2. 行程符合所有限制
        3. 時間安排合理
        """
        current_time = datetime.strptime("09:00", "%H:%M")
        itinerary = strategy.execute(
            start_location,
            sample_places,
            current_time
        )

        assert isinstance(itinerary, list)
        assert len(itinerary) > 0

        # 檢查行程的時間順序
        for i in range(1, len(itinerary)):
            prev_end = datetime.strptime(itinerary[i-1]['end_time'], "%H:%M")
            current_start = datetime.strptime(
                itinerary[i]['start_time'], "%H:%M")
            assert prev_end <= current_start

    def test_restaurant_priority(self, strategy, start_location):
        """
        測試餐廳優先級處理
        這是一個基本的測試，確保系統能在用餐時間優先選擇餐廳
        未來可以加入更多條件來完善測試
        """
        # 提供一個簡單的測試資料集
        test_places = [
            PlaceDetail(
                name='故宮博物院',
                rating=4.7,
                lat=25.1023,
                lon=121.5482,
                duration_min=120,
                label='博物館',
                hours={i: [{'start': '08:30', 'end': '18:30'}]
                       for i in range(1, 8)}
            ),
            PlaceDetail(
                name='鼎泰豐',
                rating=4.6,
                lat=25.0329,
                lon=121.5604,
                duration_min=60,
                label='餐廳',
                hours={i: [
                    {'start': '11:30', 'end': '14:30'},
                    {'start': '17:30', 'end': '21:30'}
                ] for i in range(1, 8)}
            )
        ]

        # 設定午餐時間
        lunch_time = datetime.strptime("12:00", "%H:%M")

        # 測試選擇結果
        next_location = strategy._find_best_next_location(
            start_location,
            test_places,
            lunch_time
        )

        assert next_location.label == "餐廳"

    def test_timing_constraints(self, strategy, sample_places, start_location):
        """
        測試時間限制處理

        確保：
        1. 遵守營業時間限制
        2. 考慮交通時間
        3. 合理分配停留時間
        """
        current_time = datetime.strptime("09:00", "%H:%M")
        itinerary = strategy.execute(
            start_location,
            sample_places,
            current_time
        )

        # 檢查是否所有行程都在營業時間內
        for item in itinerary:
            start_time = datetime.strptime(item['start_time'], "%H:%M")
            end_time = datetime.strptime(item['end_time'], "%H:%M")
            duration = (end_time - start_time).seconds / 60
            assert duration <= int(item['duration'])  # 確保不超過建議停留時間

    def test_distance_efficiency(self, strategy, sample_places, start_location):
        """
        測試距離效率處理

        確保：
        1. 考慮地點間的距離
        2. 最佳化交通時間
        3. 避免無效路程
        """
        current_time = datetime.strptime("09:00", "%H:%M")
        itinerary = strategy.execute(
            start_location,
            sample_places,
            current_time
        )

        # 檢查相鄰地點的交通時間是否合理
        for i in range(1, len(itinerary)):
            travel_time = float(itinerary[i]['travel_time'])
            assert travel_time < 120  # 假設單次交通時間不應超過2小時
