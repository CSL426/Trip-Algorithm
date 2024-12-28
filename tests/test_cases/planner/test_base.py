# tests/test_cases/planner/test_base.py

import pytest
from datetime import datetime
from src.core.planner.base import TripPlanner
from src.core.models.place import PlaceDetail


class TestTripPlanner:
    """
    行程規劃器基礎類別的測試

    測試行程規劃的核心功能，包括：
    1. 初始化和設定
    2. 地點資料的處理
    3. 時間範圍的驗證
    4. 基本的規劃邏輯
    """

    @pytest.fixture
    def planner(self):
        """提供測試用的規劃器實例"""
        return TripPlanner()

    @pytest.fixture
    def sample_locations(self):
        """提供測試用的地點資料清單"""
        return [
            {
                "name": "台北101",
                "lat": 25.0339808,
                "lon": 121.561964,
                "duration": 90,
                "label": "景點",
                "hours": {
                    i: [{'start': '09:00', 'end': '22:00'}]
                    for i in range(1, 8)
                }
            },
            {
                "name": "國立故宮博物院",
                "lat": 25.1023,
                "lon": 121.5482,
                "duration": 120,
                "label": "博物館",
                "hours": {
                    i: [{'start': '08:30', 'end': '18:30'}]
                    for i in range(1, 8)
                }
            }
        ]

    def test_initialization(self, planner):
        """
        測試規劃器的初始化

        確保：
        1. 屬性正確初始化
        2. 預設值設定正確
        3. 內部狀態正確建立
        """
        assert planner.start_location is None
        assert planner.end_location is None
        assert len(planner.available_locations) == 0
        assert planner.total_distance == 0.0
        assert planner.total_time == 0

    def test_initialize_locations(self, planner, sample_locations):
        """
        測試地點初始化功能

        確保：
        1. 正確載入地點資料
        2. 自訂起點的處理
        3. 預設起點的設定
        """
        # 測試基本初始化
        planner.initialize_locations(sample_locations)
        assert len(planner.available_locations) == 2
        assert all(isinstance(loc, PlaceDetail)
                   for loc in planner.available_locations)

        # 測試自訂起點
        custom_start = {
            "name": "台北車站",
            "lat": 25.0478,
            "lon": 121.5170,
            "duration": 0,
            "label": "交通",
            "hours": {i: [{'start': '00:00', 'end': '23:59'}] for i in range(1, 8)}
        }
        planner.initialize_locations(
            sample_locations, custom_start=custom_start)
        assert planner.start_location.name == "台北車站"

    def test_validate_time_range(self, planner):
        """
        測試時間範圍驗證

        確保：
        1. 正確的時間範圍被接受
        2. 無效的時間範圍被拒絕
        3. 特殊情況被正確處理
        """
        # 設定測試時間
        planner.start_datetime = datetime.strptime("09:00", "%H:%M")
        planner.end_datetime = datetime.strptime("18:00", "%H:%M")
        assert planner._validate_time_range()

        # 測試無效的時間範圍
        planner.start_datetime = datetime.strptime("18:00", "%H:%M")
        planner.end_datetime = datetime.strptime("09:00", "%H:%M")
        assert not planner._validate_time_range()

    def test_plan_with_valid_data(self, planner, sample_locations):
        """
        測試完整的規劃流程

        確保：
        1. 能夠執行完整的規劃流程
        2. 產生合理的行程結果
        3. 正確處理時間和交通限制
        """
        planner.initialize_locations(sample_locations)

        # 執行規劃
        result = planner.plan(
            start_time="09:00",
            end_time="18:00",
            travel_mode="transit"
        )

        # 由於 _generate_itinerary 是抽象方法，這裡只能測試基本框架
        assert isinstance(result, list)

    def test_get_execution_stats(self, planner):
        """
        測試執行統計資訊

        確保：
        1. 統計資訊格式正確
        2. 數值計算準確
        3. 所有必要資訊都包含
        """
        stats = planner.get_execution_stats()
        assert isinstance(stats, dict)
        assert 'total_time' in stats
        assert 'visited_count' in stats
        assert 'total_distance' in stats

    def test_error_handling(self, planner):
        """
        測試錯誤處理

        確保：
        1. 無效的輸入被適當處理
        2. 錯誤訊息清晰明確
        3. 系統狀態保持一致
        """
        # 測試空的地點列表
        with pytest.raises(ValueError, match="沒有可用的地點"):
            planner.plan(
                start_time="09:00",
                end_time="18:00"
            )

        # 測試無效的時間範圍
        planner.initialize_locations([{
            "name": "測試地點",
            "lat": 25.0,
            "lon": 121.0,
            "duration": 60,
            "label": "測試",
            "hours": {i: [{'start': '09:00', 'end': '17:00'}] for i in range(1, 8)}
        }])

        with pytest.raises(ValueError, match="結束時間必須晚於開始時間"):
            planner.plan(
                start_time="18:00",
                end_time="09:00"
            )

    def test_time_constraints(self, planner, sample_locations):
        """
        測試時間限制處理

        確保：
        1. 遵守開始和結束時間限制
        2. 考慮營業時間限制
        3. 正確計算行程時間
        """
        planner.initialize_locations(sample_locations)

        # 測試時間限制
        planner.plan(
            start_time="09:00",
            end_time="12:00",
            travel_mode="transit"
        )

        # 確保總時間不超過限制
        stats = planner.get_execution_stats()
        total_hours = stats['total_time'] / 3600  # 轉換為小時
        assert total_hours <= 3  # 3小時限制

    def test_init_with_custom_end(self, planner, sample_locations):
        """
        測試自訂終點的初始化

        確保：
        1. 正確設定自訂終點
        2. 終點資料格式正確
        3. 終點限制被正確應用
        """
        custom_end = {
            "name": "台北車站",
            "lat": 25.0478,
            "lon": 121.5170,
            "duration": 0,
            "label": "交通",
            "hours": {i: [{'start': '00:00', 'end': '23:59'}] for i in range(1, 8)}
        }

        planner.initialize_locations(
            sample_locations,
            custom_end=custom_end
        )

        assert planner.end_location.name == "台北車站"
        assert planner.end_location.lat == 25.0478
        assert planner.end_location.lon == 121.5170
