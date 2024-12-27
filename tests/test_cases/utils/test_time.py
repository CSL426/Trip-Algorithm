# tests/test_cases/utils/test_time.py

import pytest
from datetime import datetime, time
from src.core.utils.time import TimeHandler


class TestTimeHandler:
    """
    時間處理工具的測試類別。

    我們會測試所有與時間相關的功能，包括：
    1. 時間格式的驗證
    2. 時間範圍的解析
    3. 時間區間的判斷
    4. 時間長度的計算
    """

    def test_validate_time_format(self):
        """
        測試時間格式驗證功能。

        這個測試確保時間格式驗證可以：
        1. 接受正確的時間格式
        2. 拒絕錯誤的時間格式
        3. 正確處理邊界情況
        """
        # 測試有效的時間格式
        valid_times = [
            "00:00",  # 午夜
            "12:00",  # 中午
            "23:59",  # 一天的最後一分鐘
            "09:30",  # 一般時間
            "14:45"   # 一般時間
        ]
        for time_str in valid_times:
            assert TimeHandler.validate_time_format(time_str), \
                f"有效的時間格式 {time_str} 被判定為無效"

        # 測試無效的時間格式
        invalid_times = [
            "24:00",     # 小時超過23
            "12:60",     # 分鐘超過59
            "9:30",      # 小時未補零
            "09:5",      # 分鐘未補零
            "0900",      # 缺少冒號
            "09-30",     # 錯誤的分隔符
            "abc",       # 非數字
            ""          # 空字串
        ]
        for time_str in invalid_times:
            assert not TimeHandler.validate_time_format(time_str), \
                f"無效的時間格式 {time_str} 被判定為有效"

    def test_parse_time_range(self):
        """
        測試時間範圍解析功能。

        這個測試確保時間範圍解析可以：
        1. 正確解析有效的時間範圍
        2. 適當處理無效的格式
        3. 轉換成正確的 time 物件
        """
        # 測試有效的時間範圍
        start, end = TimeHandler.parse_time_range("09:00-17:30")
        assert isinstance(start, time), "開始時間應該是 time 物件"
        assert isinstance(end, time), "結束時間應該是 time 物件"
        assert start.hour == 9 and start.minute == 0, "開始時間解析錯誤"
        assert end.hour == 17 and end.minute == 30, "結束時間解析錯誤"

        # 測試無效的時間範圍格式
        invalid_ranges = [
            "0900-1730",     # 缺少冒號
            "09:00~17:30",   # 錯誤的分隔符
            "09:00",         # 缺少結束時間
            "24:00-17:30",   # 無效的時間
            "09:00-17:60"    # 無效的分鐘
        ]
        for time_range in invalid_ranges:
            with pytest.raises(ValueError):
                TimeHandler.parse_time_range(time_range)

    def test_is_time_in_range(self):
        """
        測試時間區間判斷功能。

        這個測試確保時間區間判斷可以：
        1. 正確判斷時間是否在區間內
        2. 處理跨日的時間範圍
        3. 正確處理邊界情況
        """
        # 建立測試用的時間物件
        test_time = datetime.strptime("14:00", "%H:%M").time()
        start = datetime.strptime("09:00", "%H:%M").time()
        end = datetime.strptime("17:00", "%H:%M").time()

        # 測試一般情況
        assert TimeHandler.is_time_in_range(test_time, start, end), \
            "時間應該在範圍內"

        # 測試邊界情況
        assert TimeHandler.is_time_in_range(start, start, end), \
            "開始時間應該算在範圍內"
        assert TimeHandler.is_time_in_range(end, start, end), \
            "結束時間應該算在範圍內"

        # 測試範圍外的時間
        outside_time = datetime.strptime("18:00", "%H:%M").time()
        assert not TimeHandler.is_time_in_range(outside_time, start, end), \
            "範圍外的時間被判斷為在範圍內"

        # 測試跨日情況
        night_start = datetime.strptime("22:00", "%H:%M").time()
        night_end = datetime.strptime("02:00", "%H:%M").time()
        midnight = datetime.strptime("00:00", "%H:%M").time()

        assert TimeHandler.is_time_in_range(midnight, night_start, night_end,
                                            allow_overnight=True), \
            "跨日範圍判斷錯誤"

    def test_calculate_duration(self):
        """
        測試時間長度計算功能。

        這個測試確保時間長度計算可以：
        1. 正確計算一般時間區間的長度
        2. 處理跨日的時間長度計算
        3. 正確處理特殊情況
        """
        # 建立測試用的時間物件
        start = datetime.strptime("09:00", "%H:%M").time()
        end = datetime.strptime("17:30", "%H:%M").time()

        # 測試一般情況
        duration = TimeHandler.calculate_duration(start, end)
        assert duration == 510, "8小時30分鐘應該是510分鐘"

        # 測試跨日情況
        night_start = datetime.strptime("23:00", "%H:%M").time()
        night_end = datetime.strptime("01:00", "%H:%M").time()

        duration = TimeHandler.calculate_duration(night_start, night_end,
                                                  allow_overnight=True)
        assert duration == 120, "跨日2小時應該是120分鐘"

    def test_format_time_range(self):
        """
        測試時間範圍格式化功能。

        這個測試確保時間範圍格式化可以：
        1. 正確格式化時間範圍
        2. 保持一致的格式
        3. 處理不同的時間物件
        """
        # 建立測試用的時間物件
        start = datetime.strptime("09:00", "%H:%M").time()
        end = datetime.strptime("17:30", "%H:%M").time()

        # 測試格式化
        formatted = TimeHandler.format_time_range(start, end)
        assert formatted == "09:00-17:30", "時間範圍格式化錯誤"

        # 測試不同的時間組合
        test_cases = [
            (time(9, 0), time(17, 30), "09:00-17:30"),
            (time(0, 0), time(23, 59), "00:00-23:59"),
            (time(12, 30), time(13, 45), "12:30-13:45")
        ]

        for start, end, expected in test_cases:
            assert TimeHandler.format_time_range(start, end) == expected, \
                f"時間範圍 {start}-{end} 格式化錯誤"
