# tests\test_models.py

import pytest
from datetime import datetime
from src.core.models import (
    TimeSlot,
    PlaceDetail,
    Transport,
    TripPlan,
    TripRequirement
)


def test_time_slot_validation():
    """
    測試時間時段驗證功能

    測試重點：
    1. 正確的時間格式
    2. 錯誤的時間格式
    3. 結束時間必須晚於開始時間
    """
    # 正確格式測試
    valid_slot = TimeSlot(start_time="09:00", end_time="17:00")
    assert valid_slot.start_time == "09:00"
    assert valid_slot.end_time == "17:00"

    # 錯誤時間格式測試
    with pytest.raises(ValueError, match="時間格式錯誤"):
        TimeSlot(start_time="25:00", end_time="17:00")

    # 時間順序測試
    with pytest.raises(ValueError, match="結束時間必須晚於開始時間"):
        TimeSlot(start_time="17:00", end_time="09:00")


def test_place_detail():
    """
    測試地點詳細資訊功能

    測試重點：
    1. 基本資訊驗證
    2. 營業時間格式驗證
    3. 營業狀態查詢
    """
    # 建立測試資料
    place = PlaceDetail(
        name="測試餐廳",
        rating=4.5,
        lat=25.033,
        lon=121.561,
        duration_min=90,
        label="餐廳",
        hours={
            1: [{'start': '11:30', 'end': '14:30'},
                {'start': '17:30', 'end': '21:30'}],  # 週一兩個時段
            2: [None],  # 週二公休
            3: [{'start': '00:00', 'end': '23:59'}]  # 週三24小時
        }
    )

    # 測試基本資訊
    assert place.name == "測試餐廳"
    assert place.rating == 4.5
    assert place.duration_min == 90

    # 測試營業時間查詢
    assert place.is_open_at(1, "12:00") == True  # 週一午餐時段
    assert place.is_open_at(1, "15:00") == False  # 週一非營業時段
    assert place.is_open_at(2, "12:00") == False  # 週二公休
    assert place.is_open_at(3, "03:00") == True  # 週三24小時營業

    # 測試錯誤的營業時間格式
    with pytest.raises(ValueError):
        PlaceDetail(
            name="錯誤測試",
            rating=4.5,
            lat=25.033,
            lon=121.561,
            duration_min=90,
            label="餐廳",
            hours={
                1: [{'start': '25:00', 'end': '14:30'}]  # 錯誤的時間
            }
        )


def test_trip_requirement():
    """
    測試旅遊需求驗證功能

    測試重點：
    1. 正確的需求格式
    2. 時間格式驗證
    3. 日期格式驗證
    """
    # 正確格式測試
    valid_req = TripRequirement(
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
    assert valid_req.start_time == "09:00"
    assert valid_req.lunch_time == "12:00"

    # 錯誤時間格式測試
    with pytest.raises(ValueError, match="時間格式錯誤"):
        TripRequirement(
            start_time="25:00",  # 錯誤的時間格式
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

    # 錯誤日期格式測試
    with pytest.raises(ValueError, match="日期格式錯誤"):
        TripRequirement(
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
            date="13-45"  # 錯誤的日期格式
        )


def test_transport_and_trip_plan():
    """
    測試交通和行程計畫功能

    測試重點：
    1. 交通資訊格式
    2. 行程計畫完整性
    3. 轉換為字典格式
    """
    # 建立交通資訊
    transport = Transport(
        mode="transit",
        time=30,
        period="09:00-09:30"
    )
    assert transport.mode == "transit"
    assert transport.time == 30

    # 建立行程計畫
    trip = TripPlan(
        name="台北101",
        start_time="09:30",
        end_time="11:00",
        duration=90,
        hours="09:00-22:00",
        transport=transport
    )

    # 測試轉換為字典格式
    trip_dict = trip.to_dict()
    assert isinstance(trip_dict, dict)
    assert trip_dict["name"] == "台北101"
    assert trip_dict["duration"] == 90
    assert trip_dict["transport"]["mode"] == "transit"


def test_invalid_transport_mode():
    """
    測試無效的交通方式

    測試重點：
    1. 驗證不允許的交通方式
    """
    with pytest.raises(ValueError):
        Transport(
            mode="airplane",  # 不支援的交通方式
            time=30,
            period="09:00-09:30"
        )


def test_complete_trip_planning():
    """
    測試完整的行程規劃流程

    測試重點：
    1. 建立地點資訊
    2. 建立使用者需求
    3. 建立行程計畫
    4. 驗證完整流程
    """
    # 建立地點資訊
    place = PlaceDetail(
        name="台北101",
        rating=4.5,
        lat=25.033,
        lon=121.561,
        duration_min=90,
        label="景點",
        hours={
            1: [{'start': '09:00', 'end': '22:00'}],
            2: [{'start': '09:00', 'end': '22:00'}],
            3: [{'start': '09:00', 'end': '22:00'}],
            4: [{'start': '09:00', 'end': '22:00'}],
            5: [{'start': '09:00', 'end': '22:00'}],
            6: [{'start': '09:00', 'end': '22:00'}],
            7: [{'start': '09:00', 'end': '22:00'}]
        }
    )

    # 建立使用者需求
    requirement = TripRequirement(
        start_time="09:00",
        end_time="18:00",
        start_point="台北車站",
        end_point="台北車站",
        transport_mode="transit",
        distance_threshold=30,
        breakfast_time="none",
        lunch_time="12:00",
        dinner_time="18:00",
        budget="none",
        date="12-25"
    )

    # 建立交通資訊
    transport = Transport(
        mode="transit",
        time=30,
        period="09:00-09:30"
    )

    # 建立行程計畫
    trip = TripPlan(
        name=place.name,
        start_time="09:30",
        end_time="11:00",
        duration=place.duration_min,
        hours="09:00-22:00",
        transport=transport
    )

    # 驗證完整性
    assert place.is_open_at(1, "10:00")  # 確認營業時間
    assert requirement.transport_mode == "transit"  # 確認交通方式
    assert trip.duration == place.duration_min  # 確認停留時間

    # 轉換為輸出格式並驗證
    output = trip.to_dict()
    assert output["name"] == place.name
    assert output["transport"]["mode"] == "transit"


if __name__ == "__main__":
    pytest.main(["-v"])
