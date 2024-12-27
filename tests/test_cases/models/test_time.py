# tests/test_cases/models/test_time.py

import pytest
from datetime import datetime, time
from src.core.models.time import TimeSlot


class TestTimeSlot:
    """
    時間區間模型的測試類別。
    這個類別測試 TimeSlot 模型的所有功能，確保它能正確處理各種時間區間的情況。

    主要測試內容：
    1. 時間格式的驗證
    2. 時間順序的驗證
    3. 時間區間的轉換和比較
    4. 特殊情況的處理
    """

    def test_valid_time_slot_creation(self):
        """
        測試建立有效的時間區間。
        我們測試多種有效的時間組合，確保它們都能被正確建立並儲存。
        """
        # 測試一般的營業時間
        time_slot = TimeSlot(start_time="09:00", end_time="17:00")
        assert time_slot.start_time == "09:00"
        assert time_slot.end_time == "17:00"

        # 測試跨越午夜的時間
        time_slot = TimeSlot(start_time="22:00", end_time="23:59")
        assert time_slot.start_time == "22:00"
        assert time_slot.end_time == "23:59"

        # 測試特殊時間點
        time_slot = TimeSlot(start_time="00:00", end_time="23:59")
        assert time_slot.start_time == "00:00"
        assert time_slot.end_time == "23:59"

    def test_invalid_time_format(self):
        """
        測試無效的時間格式。
        確保系統能正確識別並拒絕各種無效的時間格式。
        """
        # 測試無效的時間格式
        invalid_times = [
            ("25:00", "17:00"),  # 小時超過24
            ("09:60", "17:00"),  # 分鐘超過59
            ("9:00", "17:00"),   # 小時未補零
            ("09:0", "17:00"),   # 分鐘未補零
            ("0900", "1700"),    # 缺少冒號
            ("abc", "17:00"),    # 非數字
            ("", "17:00"),       # 空字串
        ]

        for start, end in invalid_times:
            with pytest.raises(ValueError, match="時間格式錯誤"):
                TimeSlot(start_time=start, end_time=end)

    def test_invalid_time_order(self):
        """
        測試無效的時間順序。
        確保結束時間必須晚於開始時間，系統應該能識別並拒絕錯誤的時間順序。
        """
        # 結束時間早於開始時間
        with pytest.raises(ValueError, match="結束時間必須晚於開始時間"):
            TimeSlot(start_time="17:00", end_time="09:00")

        # 開始時間等於結束時間
        with pytest.raises(ValueError, match="結束時間必須晚於開始時間"):
            TimeSlot(start_time="09:00", end_time="09:00")

    def test_time_slot_conversion(self):
        """
        測試時間區間轉換功能。
        確保時間區間可以正確地轉換為 datetime 物件，並保持時間的準確性。
        """
        time_slot = TimeSlot(start_time="09:30", end_time="17:45")
        start, end = time_slot.to_datetime_tuple()

        # 檢查轉換後的時間
        assert isinstance(start, datetime)
        assert isinstance(end, datetime)
        assert start.hour == 9 and start.minute == 30
        assert end.hour == 17 and end.minute == 45

    def test_duration_calculation(self):
        """
        測試時間區間長度計算。
        確保系統能正確計算不同時間區間的持續時間。
        """
        # 測試一般時間區間
        time_slot = TimeSlot(start_time="09:00", end_time="17:00")
        assert time_slot.duration_minutes() == 480  # 8小時 = 480分鐘

        # 測試跨小時的時間區間
        time_slot = TimeSlot(start_time="09:30", end_time="17:45")
        assert time_slot.duration_minutes() == 495  # 8小時15分鐘 = 495分鐘

        # 測試短時間區間
        time_slot = TimeSlot(start_time="09:00", end_time="09:30")
        assert time_slot.duration_minutes() == 30

    def test_contains_time(self):
        """
        測試時間點包含判斷。
        確保系統能正確判斷一個時間點是否落在時間區間內。
        """
        time_slot = TimeSlot(start_time="09:00", end_time="17:00")

        # 測試區間內的時間
        check_time = datetime.strptime("14:00", "%H:%M")
        assert time_slot.contains(check_time)

        # 測試區間邊界的時間
        start_time = datetime.strptime("09:00", "%H:%M")
        end_time = datetime.strptime("17:00", "%H:%M")
        assert time_slot.contains(start_time)
        assert time_slot.contains(end_time)

        # 測試區間外的時間
        outside_time = datetime.strptime("18:00", "%H:%M")
        assert not time_slot.contains(outside_time)

    def test_overlaps(self):
        """
        測試時間區間重疊判斷。
        確保系統能正確判斷兩個時間區間是否有重疊。
        """
        time_slot = TimeSlot(start_time="09:00", end_time="17:00")

        # 完全重疊
        overlapping = TimeSlot(start_time="09:00", end_time="17:00")
        assert time_slot.overlaps(overlapping)

        # 部分重疊
        partial = TimeSlot(start_time="08:00", end_time="10:00")
        assert time_slot.overlaps(partial)

        # 完全不重疊
        non_overlapping = TimeSlot(start_time="17:01", end_time="18:00")
        assert not time_slot.overlaps(non_overlapping)

    def test_create_from_datetime(self):
        """
        測試從 datetime 物件建立時間區間。
        確保系統能正確從 datetime 物件建立時間區間，並保持時間的準確性。
        """
        start = datetime.strptime("09:30", "%H:%M")
        end = datetime.strptime("17:45", "%H:%M")

        time_slot = TimeSlot.create_from_datetime(start, end)

        assert time_slot.start_time == "09:30"
        assert time_slot.end_time == "17:45"
