# tests/test_cases/models/test_place.py

import pytest
from datetime import datetime
from src.core.models.place import PlaceDetail


class TestPlaceDetail:
    """
    地點詳細資訊模型的測試類別。

    這個類別全面測試 PlaceDetail 模型的功能，確保它能正確處理地點的各種資訊：
    1. 基本資訊（名稱、位置、評分）
    2. 營業時間的複雜邏輯
    3. 資料驗證機制
    4. 時間相關的判斷功能
    """

    @pytest.fixture
    def basic_place(self):
        """建立一個基本的測試地點。

        這個 fixture 提供一個標準的測試資料，包含必要的基本資訊。
        營業時間設定為每天 9:00-17:00。
        """
        return PlaceDetail(
            name="測試餐廳",
            rating=4.5,
            lat=25.0339808,
            lon=121.561964,
            duration_min=90,
            label="餐廳",
            hours={
                # 週一到週日，每天 9:00-17:00
                i: [{'start': '09:00', 'end': '17:00'}] for i in range(1, 8)
            }
        )

    @pytest.fixture
    def complex_place(self):
        """建立一個有複雜營業時間的測試地點。

        這個 fixture 提供更複雜的測試案例，包含：
        - 不同的營業時段（午餐、晚餐）
        - 公休日
        - 特殊營業時間
        """
        return PlaceDetail(
            name="進階餐廳",
            rating=4.8,
            lat=25.0339808,
            lon=121.561964,
            duration_min=120,
            label="餐廳",
            hours={
                1: [{'start': '11:30', 'end': '14:30'},  # 週一（午餐、晚餐）
                    {'start': '17:30', 'end': '21:30'}],
                2: [None],  # 週二公休
                3: [{'start': '11:30', 'end': '21:30'}],  # 週三（全天營業）
                4: [{'start': '11:30', 'end': '14:30'},  # 週四（午餐、晚餐）
                    {'start': '17:30', 'end': '21:30'}],
                5: [{'start': '11:30', 'end': '14:30'},  # 週五（午餐、晚餐）
                    {'start': '17:30', 'end': '22:00'}],
                6: [{'start': '11:00', 'end': '22:00'}],  # 週六（延長營業）
                7: [{'start': '11:00', 'end': '21:00'}]   # 週日（正常營業）
            }
        )

    def test_basic_attributes(self, basic_place):
        """測試基本屬性的正確性。

        確保所有基本資訊都被正確儲存和讀取：
        - 名稱、評分、位置等基本資料
        - 資料型別的正確性
        - 預設值的處理
        """
        assert basic_place.name == "測試餐廳"
        assert basic_place.rating == 4.5
        assert basic_place.lat == 25.0339808
        assert basic_place.lon == 121.561964
        assert basic_place.duration_min == 90
        assert basic_place.label == "餐廳"

    def test_invalid_data(self):
        """測試無效資料的驗證。

        確保系統能正確識別和拒絕無效的資料：
        - 超出範圍的評分
        - 無效的經緯度
        - 缺少必要欄位
        - 格式錯誤的資料
        """
        # 測試評分超出範圍
        with pytest.raises(ValueError):
            PlaceDetail(
                name="錯誤測試",
                rating=6.0,  # 超過5.0
                lat=25.0,
                lon=121.0,
                duration_min=60,
                label="測試",
                hours={}
            )

        # 測試無效的經緯度
        with pytest.raises(ValueError):
            PlaceDetail(
                name="錯誤測試",
                rating=4.0,
                lat=91.0,  # 超過90度
                lon=121.0,
                duration_min=60,
                label="測試",
                hours={}
            )

    def test_business_hours_validation(self):
        """測試營業時間驗證功能。

        確保營業時間的格式和內容都正確：
        - 時間格式的驗證
        - 時間順序的檢查
        - 特殊情況的處理
        """
        # 測試無效的時間格式
        with pytest.raises(ValueError):
            PlaceDetail(
                name="時間測試",
                rating=4.0,
                lat=25.0,
                lon=121.0,
                duration_min=60,
                label="測試",
                hours={
                    1: [{'start': '25:00', 'end': '17:00'}]  # 無效的小時
                }
            )

        # 測試時間順序錯誤
        with pytest.raises(ValueError):
            PlaceDetail(
                name="時間測試",
                rating=4.0,
                lat=25.0,
                lon=121.0,
                duration_min=60,
                label="測試",
                hours={
                    1: [{'start': '17:00', 'end': '09:00'}]  # 結束時間早於開始時間
                }
            )

    def test_is_open_at(self, complex_place):
        """測試營業狀態判斷功能。

        測試各種不同時間點的營業狀態：
        - 一般營業時間
        - 公休日
        - 多時段營業
        - 特殊營業時間
        """
        # 測試正常營業時間
        assert complex_place.is_open_at(1, "12:00")  # 週一中午
        assert complex_place.is_open_at(1, "19:00")  # 週一晚上

        # 測試公休日
        assert not complex_place.is_open_at(2, "12:00")  # 週二公休

        # 測試營業時間外
        assert not complex_place.is_open_at(1, "15:00")  # 週一下午休息時段
        assert not complex_place.is_open_at(1, "22:00")  # 週一打烊後

        # 測試特殊營業時間
        assert complex_place.is_open_at(6, "21:30")  # 週六延長營業

    def test_get_next_available_time(self, complex_place):
        """測試下一個可用時間的查詢功能。

        測試在不同情況下查詢下一個營業時段：
        - 當前時段結束後的下一個時段
        - 跨日的情況
        - 公休日後的營業時間
        """
        # 測試當天下一個時段
        next_time = complex_place.get_next_available_time(1, "15:00")
        assert next_time['start'] == "17:30"  # 週一下午的下一個時段

        # 測試公休日的下一個時段
        next_time = complex_place.get_next_available_time(2, "12:00")
        assert next_time['day'] == 3  # 應該找到週三的時段

        # 測試最後一天的處理
        next_time = complex_place.get_next_available_time(7, "22:00")
        assert next_time['day'] == 1  # 應該回到週一

    def test_edge_cases(self, complex_place):
        """測試邊界情況。

        處理各種特殊和邊界情況：
        - 午夜前後的時間
        - 時段交界的時間
        - 連續時段的處理
        """
        # 測試時段交界時間
        assert complex_place.is_open_at(1, "14:30")  # 第一個時段的結束時間
        assert complex_place.is_open_at(1, "17:30")  # 第二個時段的開始時間

        # 測試連續營業時段
        assert complex_place.is_open_at(3, "14:30")  # 週三全天營業
        assert complex_place.is_open_at(3, "17:30")  # 不應該有中間休息

        # 測試特殊營業時間
        assert complex_place.is_open_at(5, "21:59")  # 週五延長營業
        assert not complex_place.is_open_at(5, "22:01")  # 週五打烊後
