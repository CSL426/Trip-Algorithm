import pytest
from src.core.models.place import PlaceDetail


def test_place_detail_creation():
    """測試地點物件的建立,測試不同的輸入情況"""

    # 測試案例 1: 完整資料
    place1 = PlaceDetail(
        name="台北101",
        rating=4.5,
        lat=25.0339,
        lon=121.5619,
        duration=90,
        label="景點",
        period="morning",
        hours={1: [{'start': '09:00', 'end': '17:00'}]}
    )
    assert place1.duration == 90
    assert place1.duration_min == 90

    # 測試案例 2: 使用 duration_min
    place2 = PlaceDetail(
        name="西門町",
        rating=4.0,
        lat=25.0421,
        lon=121.5079,
        duration_min=120,
        label="景點",
        period="afternoon",
        hours={1: [{'start': '09:00', 'end': '17:00'}]}
    )
    assert place2.duration == 120
    assert place2.duration_min == 120

    # 測試案例 3: 無 duration, 根據 label 判斷
    place3 = PlaceDetail(
        name="鼎泰豐",
        rating=4.8,
        lat=25.0363,
        lon=121.5222,
        label="餐廳",
        period="lunch",
        hours={1: [{'start': '09:00', 'end': '17:00'}]}
    )
    assert place3.duration == 90  # 餐廳預設90分鐘
    assert place3.duration_min == 90

    # 測試案例 4: 無 duration 且 label 不在預設清單中
    place4 = PlaceDetail(
        name="測試地點",
        rating=4.0,
        lat=25.0,
        lon=121.5,
        label="其他",
        period="morning",
        hours={1: [{'start': '09:00', 'end': '17:00'}]}
    )
    assert place4.duration == 60  # 預設60分鐘
    assert place4.duration_min == 60
