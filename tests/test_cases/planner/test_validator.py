# tests/test_cases/planner/test_validator.py

import pytest
from datetime import datetime
from src.core.planner.validator import InputValidator
from src.core.models.place import PlaceDetail
from src.core.models.trip import TripRequirement


class TestInputValidator:
    """
    輸入驗證器的測試類別

    測試所有輸入資料的驗證功能，確保：
    1. 地點資料的完整性和正確性
    2. 行程需求的合理性
    3. 各種格式的驗證
    """

    @pytest.fixture
    def validator(self):
        """提供測試用的驗證器實例"""
        return InputValidator()

    @pytest.fixture
    def valid_location_dict(self):
        """提供有效的地點資料字典"""
        return {
            "name": "台北101",
            "lat": 25.0339808,
            "lon": 121.561964,
            "duration": 90,
            "label": "景點",
            "hours": {
                1: [{'start': '09:00', 'end': '22:00'}],
                2: [{'start': '09:00', 'end': '22:00'}],
                3: [{'start': '09:00', 'end': '22:00'}],
                4: [{'start': '09:00', 'end': '22:00'}],
                5: [{'start': '09:00', 'end': '22:00'}],
                6: [{'start': '09:00', 'end': '22:00'}],
                7: [{'start': '09:00', 'end': '22:00'}]
            }
        }

    def test_validate_location_dict(self, validator, valid_location_dict):
        """
        測試單一地點資料的驗證

        確保驗證器能正確檢查：
        1. 必要欄位的存在
        2. 資料格式的正確性
        3. 數值範圍的合理性
        """
        # 測試有效的地點資料
        validator._validate_location_dict(valid_location_dict)

        # 測試缺少必要欄位
        invalid_location = valid_location_dict.copy()
        del invalid_location["name"]
        with pytest.raises(ValueError, match="缺少必要欄位"):
            validator._validate_location_dict(invalid_location)

        # 測試無效的經緯度
        invalid_location = valid_location_dict.copy()
        invalid_location["lat"] = 91  # 超過90度
        with pytest.raises(ValueError, match="緯度超出範圍"):
            validator._validate_location_dict(invalid_location)

    def test_validate_locations(self, validator, valid_location_dict):
        """
        測試地點列表的驗證

        確保驗證器能正確處理：
        1. 混合型態的輸入(字典和物件)
        2. 自訂起點和終點
        3. 轉換後的資料格式
        """
        # 測試單一地點
        locations = [valid_location_dict]
        validated = validator.validate_locations(locations)
        assert len(validated) == 1
        assert isinstance(validated[0], PlaceDetail)
        assert validated[0].name == "台北101"

        # 測試多個地點
        locations = [valid_location_dict, valid_location_dict]
        validated = validator.validate_locations(locations)
        assert len(validated) == 2
        assert all(isinstance(loc, PlaceDetail) for loc in validated)

        # 測試自訂起點
        custom_start = {
            "name": "台北車站",
            "lat": 25.0478,
            "lon": 121.5170
        }
        validated = validator.validate_locations(
            locations, custom_start=custom_start)
        assert len(validated) == 2

    def test_validate_requirement(self, validator):
        """
        測試行程需求的驗證

        確保驗證器能正確檢查：
        1. 時間格式和順序
        2. 交通方式的有效性
        3. 距離限制的合理性
        """
        # 測試有效的需求
        valid_requirement = {
            "start_time": "09:00",
            "end_time": "18:00",
            "start_point": "台北車站",
            "end_point": "台北101",
            "transport_mode": "transit",
            "distance_threshold": 30,
            "breakfast_time": "none",
            "lunch_time": "12:00",
            "dinner_time": "18:00",
            "budget": "none",
            "date": "12-25"
        }
        requirement = validator.validate_requirement(valid_requirement)
        assert isinstance(requirement, TripRequirement)
        assert requirement.start_time == "09:00"

        # 測試無效的時間順序
        invalid_requirement = valid_requirement.copy()
        invalid_requirement["start_time"] = "19:00"  # 開始時間晚於結束時間
        with pytest.raises(ValueError, match="開始時間必須早於結束時間"):
            validator.validate_requirement(invalid_requirement)

        # 測試無效的交通方式
        invalid_requirement = valid_requirement.copy()
        invalid_requirement["transport_mode"] = "flying"
        with pytest.raises(ValueError, match="不支援的交通方式"):
            validator.validate_requirement(invalid_requirement)

    def test_time_format_validation(self, validator):
        """
        測試時間格式驗證

        確保驗證器能正確處理：
        1. 標準時間格式
        2. 特殊格式(如 none)
        3. 無效的時間格式
        """
        # 測試有效時間格式
        validator._validate_time_format("09:00")
        validator._validate_time_format("23:59")

        # 測試無效時間格式
        invalid_times = [
            "25:00",     # 無效的小時
            "12:60",     # 無效的分鐘
            "9:30",      # 缺少前導零
            "09:5",      # 缺少前導零
            "0900",      # 缺少冒號
            "",          # 空字串
        ]
        for time_str in invalid_times:
            with pytest.raises(ValueError):
                validator._validate_time_format(time_str)

    def test_edge_cases(self, validator, valid_location_dict):
        """
        測試邊界情況

        確保驗證器能正確處理：
        1. 極限值
        2. 特殊格式
        3. 異常情況
        """
        # 測試最大/最小有效值
        edge_location = valid_location_dict.copy()

        # 測試最大有效緯度
        edge_location["lat"] = 90
        validator._validate_location_dict(edge_location)

        # 測試最小有效緯度
        edge_location["lat"] = -90
        validator._validate_location_dict(edge_location)

        # 測試空的地點列表
        validated = validator.validate_locations([])
        assert len(validated) == 0

        # 測試沒有營業時間的地點
        no_hours_location = valid_location_dict.copy()
        del no_hours_location["hours"]
        validator._validate_location_dict(no_hours_location)
