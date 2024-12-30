# src/core/utils/time.py

"""
時間工具模組
此模組提供所有與時間計算、轉換和檢查相關的工具函數

主要功能：
1. 時間格式轉換和驗證
2. 時段重疊檢查
3. 營業時間判斷
4. 時間區間計算
"""

from datetime import datetime, time, timedelta
from typing import List, Dict, Optional, Tuple
import re


class TimeHandler:
    """
    時間處理工具類別
    提供各種時間相關的運算和檢查功能

    這個類別整合了行程規劃中所需的所有時間處理邏輯，
    確保時間相關的運算都有一致的處理方式
    """

    TIME_FORMAT = '%H:%M'
    TIME_PATTERN = r'^([01][0-9]|2[0-3]):[0-5][0-9]$'

    @classmethod
    def validate_time_format(cls, time_str: str) -> bool:
        """
        驗證時間字串格式是否正確

        運作原理：
        使用正則表達式驗證時間格式是否符合 HH:MM 格式，
        並確保小時和分鐘都在合理範圍內

        輸入參數：
            time_str: 要驗證的時間字串(HH:MM格式)

        回傳：
            bool: True 表示格式正確，False 表示格式錯誤

        使用範例：
            >>> TimeHandler.validate_time_format("09:30")
            True
            >>> TimeHandler.validate_time_format("25:00")
            False
        """
        return bool(re.match(cls.TIME_PATTERN, time_str))

    @classmethod
    def parse_time_range(cls, time_range: str) -> Tuple[time, time]:
        """
        解析時間範圍字串

        運作原理：
        1. 將 "HH:MM-HH:MM" 格式的字串拆分為開始和結束時間
        2. 驗證每個時間的格式
        3. 轉換為 time 物件

        輸入參數：
            time_range: 時間範圍字串(格式：HH:MM-HH:MM)

        回傳：
            Tuple[time, time]: (開始時間, 結束時間)

        異常：
            ValueError: 當時間格式不正確時拋出

        使用範例：
            >>> start, end = TimeHandler.parse_time_range("09:00-18:00")
            >>> print(f"營業時間：{start} 到 {end}")
        """
        try:
            start_str, end_str = time_range.split('-')
            if not (cls.validate_time_format(start_str) and
                    cls.validate_time_format(end_str)):
                raise ValueError

            start = datetime.strptime(start_str, cls.TIME_FORMAT).time()
            end = datetime.strptime(end_str, cls.TIME_FORMAT).time()
            return start, end

        except ValueError:
            raise ValueError(f"時間範圍格式錯誤：{time_range}，應為 HH:MM-HH:MM")

    @classmethod
    def is_time_in_range(cls,
                         check_time: time,
                         start_time: time,
                         end_time: time,
                         allow_overnight: bool = False) -> bool:
        """
        檢查時間是否在指定的範圍內

        運作原理：
        1. 將所有時間轉換為分鐘數進行比較
        2. 考慮跨日的情況(例如營業時間 23:00-02:00)

        輸入參數：
            check_time: 要檢查的時間
            start_time: 開始時間
            end_time: 結束時間
            allow_overnight: 是否允許跨日，預設為 False

        回傳：
            bool: True 表示在範圍內，False 表示在範圍外

        使用範例：
            >>> time_to_check = datetime.strptime("20:30", "%H:%M").time()
            >>> start = datetime.strptime("18:00", "%H:%M").time()
            >>> end = datetime.strptime("22:00", "%H:%M").time()
            >>> TimeHandler.is_time_in_range(time_to_check, start, end)
            True
        """
        def time_to_minutes(t: time) -> int:
            return t.hour * 60 + t.minute

        check_minutes = time_to_minutes(check_time)
        start_minutes = time_to_minutes(start_time)
        end_minutes = time_to_minutes(end_time)

        if allow_overnight and end_minutes < start_minutes:
            # 處理跨日情況，例如 23:00-02:00
            return (check_minutes >= start_minutes or
                    check_minutes <= end_minutes)
        else:
            return start_minutes <= check_minutes <= end_minutes

    @classmethod
    def calculate_duration(cls,
                           start_time: time,
                           end_time: time,
                           allow_overnight: bool = False) -> int:
        """
        計算兩個時間點之間的時間差

        運作原理：
        1. 將時間轉換為分鐘進行計算
        2. 處理可能的跨日情況

        輸入參數：
            start_time: 開始時間
            end_time: 結束時間
            allow_overnight: 是否允許跨日計算

        回傳：
            int: 時間差(分鐘)

        使用範例：
            >>> start = datetime.strptime("09:00", "%H:%M").time()
            >>> end = datetime.strptime("17:30", "%H:%M").time()
            >>> duration = TimeHandler.calculate_duration(start, end)
            >>> print(f"持續時間：{duration} 分鐘")
        """
        start_minutes = start_time.hour * 60 + start_time.minute
        end_minutes = end_time.hour * 60 + end_time.minute

        if end_minutes < start_minutes and allow_overnight:
            # 跨日情況，加上一天的分鐘數
            return (24 * 60 - start_minutes) + end_minutes
        else:
            return end_minutes - start_minutes

    @classmethod
    def format_time_range(cls,
                          start_time: time,
                          end_time: time) -> str:
        """
        將時間範圍格式化為字串

        運作原理：
        將時間物件轉換為易讀的字串格式

        輸入參數：
            start_time: 開始時間
            end_time: 結束時間

        回傳：
            str: 格式化後的時間範圍字串(HH:MM-HH:MM)

        使用範例：
            >>> start = datetime.strptime("09:00", "%H:%M").time()
            >>> end = datetime.strptime("17:30", "%H:%M").time()
            >>> print(TimeHandler.format_time_range(start, end))
            "09:00-17:30"
        """
        return f"{start_time.strftime(cls.TIME_FORMAT)}-{end_time.strftime(cls.TIME_FORMAT)}"
