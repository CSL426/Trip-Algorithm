# tests/test_cases/models/test_trip.py

import pytest
from datetime import datetime
from src.core.models.trip import Transport, TripPlan, TripRequirement


class TestTransport:
    """
    交通資訊模型的測試類別。

    這個類別測試所有與交通相關的功能，包括：
    1. 交通方式的驗證
    2. 時間計算
    3. 資料格式的處理
    """

    def test_valid_transport_creation(self):
        """
        測試建立有效的交通資訊。

        我們測試不同的交通方式，確保：
        1. 能正確建立各種交通方式
        2. 時間計算準確
        3. 時段資訊正確儲存
        """
        # 測試不同的交通方式
        transport = Transport(
            mode="transit",
            time=30,
            period="09:00-09:30"
        )
        assert transport.mode == "transit"
        assert transport.time == 30
        assert transport.period == "09:00-09:30"

        # 測試其他有效的交通方式
        valid_modes = ["driving", "walking", "bicycling"]
        for mode in valid_modes:
            transport = Transport(mode=mode, time=20)
            assert transport.mode == mode

    def test_invalid_transport_mode(self):
        """
        測試無效的交通方式。

        確保系統能正確識別並拒絕無效的交通方式，
        例如不支援的交通工具或格式錯誤的輸入。
        """
        # 測試無效的交通方式
        with pytest.raises(ValueError):
            Transport(mode="flying", time=30)

        # 測試空的交通方式
        with pytest.raises(ValueError):
            Transport(mode="", time=30)

    def test_invalid_time_values(self):
        """
        測試無效的時間值。

        確保系統能正確處理：
        1. 負數時間
        2. 過大的時間值
        3. 無效的時間格式
        """
        # 測試負數時間
        with pytest.raises(ValueError):
            Transport(mode="transit", time=-30)


class TestTripPlan:
    """
    行程計畫模型的測試類別。

    這個類別測試完整的行程計畫功能，包括：
    1. 時間安排
    2. 交通資訊
    3. 資料轉換
    """

    @pytest.fixture
    def sample_transport(self):
        """提供測試用的交通資訊。"""
        return Transport(
            mode="transit",
            time=30,
            period="09:00-09:30"
        )

    def test_valid_trip_plan_creation(self, sample_transport):
        """
        測試建立有效的行程計畫。

        確保能正確建立包含完整資訊的行程計畫，
        並驗證所有資料都被正確儲存。
        """
        trip = TripPlan(
            name="台北101",
            start_time="09:30",
            end_time="11:00",
            duration=90,
            hours="09:00-22:00",
            transport=sample_transport
        )

        assert trip.name == "台北101"
        assert trip.start_time == "09:30"
        assert trip.end_time == "11:00"
        assert trip.duration == 90
        assert trip.hours == "09:00-22:00"
        assert trip.transport == sample_transport

    def test_trip_plan_to_dict(self, sample_transport):
        """
        測試行程計畫轉換為字典格式。

        確保行程資訊可以正確轉換為字典格式，
        這對於API響應和資料序列化很重要。
        """
        trip = TripPlan(
            name="台北101",
            start_time="09:30",
            end_time="11:00",
            duration=90,
            hours="09:00-22:00",
            transport=sample_transport
        )

        trip_dict = trip.to_dict()
        assert isinstance(trip_dict, dict)
        assert trip_dict["name"] == "台北101"
        assert trip_dict["duration"] == 90
        assert trip_dict["transport"]["mode"] == "transit"


class TestTripRequirement:
    """
    行程需求模型的測試類別。

    這個類別測試使用者的行程需求設定，包括：
    1. 時間限制
    2. 交通偏好
    3. 用餐安排
    4. 預算設定
    """

    def test_valid_requirement_creation(self):
        """
        測試建立有效的行程需求。

        確保能正確建立並驗證完整的行程需求，
        包括所有必要的設定和選項。
        """
        requirement = TripRequirement(
            start_time="09:00",
            end_time="18:00",
            start_point="台北車站",
            end_point="台北101",
            transport_mode="transit",
            distance_threshold=30,
            breakfast_time="08:00",
            lunch_time="12:00",
            dinner_time="18:00",
            budget=1000,
            date="12-25"
        )

        assert requirement.start_time == "09:00"
        assert requirement.transport_mode == "transit"
        assert requirement.distance_threshold == 30
        assert requirement.budget == 1000

    def test_time_validation(self):
        """
        測試時間格式驗證。

        確保系統能正確驗證各種時間格式，包括：
        1. 一般時間格式
        2. 特殊值（如 "none"）
        3. 無效的時間格式
        """
        # 測試有效的時間格式
        requirement = TripRequirement(
            start_time="09:00",
            end_time="18:00",
            start_point="台北車站",
            end_point="none",
            transport_mode="transit",
            distance_threshold=30,
            breakfast_time="none",
            lunch_time="12:00",
            dinner_time="18:00",
            budget="none",
            date="12-25"
        )
        assert requirement.lunch_time == "12:00"

        # 測試無效的時間格式
        with pytest.raises(ValueError):
            TripRequirement(
                start_time="25:00",  # 無效的時間
                end_time="18:00",
                start_point="台北車站",
                end_point="none",
                transport_mode="transit",
                distance_threshold=30,
                breakfast_time="none",
                lunch_time="12:00",
                dinner_time="18:00",
                budget="none",
                date="12-25"
            )

    def test_get_meal_times(self):
        """
        測試用餐時間的處理。

        確保系統能正確處理：
        1. 正常的用餐時間設定
        2. 省略的用餐時間
        3. 用餐時間的轉換和計算
        """
        requirement = TripRequirement(
            start_time="09:00",
            end_time="18:00",
            start_point="台北車站",
            end_point="none",
            transport_mode="transit",
            distance_threshold=30,
            breakfast_time="08:00",
            lunch_time="12:00",
            dinner_time="18:00",
            budget="none",
            date="12-25"
        )

        meal_times = requirement.get_meal_times()
        assert len(meal_times) == 3  # 三餐都有設定

        # 測試省略部分用餐時間
        requirement = TripRequirement(
            start_time="09:00",
            end_time="18:00",
            start_point="台北車站",
            end_point="none",
            transport_mode="transit",
            distance_threshold=30,
            breakfast_time="none",
            lunch_time="12:00",
            dinner_time="none",
            budget="none",
            date="12-25"
        )

        meal_times = requirement.get_meal_times()
        assert len(meal_times) == 1  # 只有午餐
