# src/core/utils/time.py

from datetime import datetime, time, timedelta
from typing import List, Dict, Optional, Tuple
from .time_core import TimeCore


class TimeHandler:
    """時間處理工具類別

    整合 TimeCore 的基礎功能，並提供更多實用的時間處理方法

    主要功能：
    1. 時間格式轉換和驗證
    2. 時段重疊檢查
    3. 營業時間判斷
    4. 時間區間計算
    """

    @classmethod
    def validate_time_format(cls, time_str: str) -> bool:
        """驗證時間字串格式

        輸入參數：
            time_str (str): 要驗證的時間字串，格式必須是 "HH:MM"

        回傳：
            bool: 格式正確回傳 True，否則回傳 False
        """
        return TimeCore.validate_time_str(time_str)

    @classmethod
    def parse_time_range(cls, time_range: str) -> Tuple[time, time]:
        """解析時間範圍字串

        輸入參數：
            time_range (str): 時間範圍字串，格式必須是 "HH:MM-HH:MM"

        回傳：
            Tuple[time, time]: (開始時間, 結束時間)

        異常：
            ValueError: 當時間格式不正確時
        """
        try:
            start_str, end_str = time_range.split('-')
            return TimeCore.parse_time_range(start_str, end_str)
        except ValueError as e:
            raise ValueError(f"時間範圍格式錯誤：{time_range}，應為 HH:MM-HH:MM") from e

    @classmethod
    def is_time_in_range(cls,
                         check_time: time,
                         start_time: time,
                         end_time: time,
                         allow_overnight: bool = False) -> bool:
        """檢查時間是否在指定範圍內

        輸入參數：
            check_time (time): 要檢查的時間
            start_time (time): 開始時間
            end_time (time): 結束時間
            allow_overnight (bool): 是否允許跨夜，預設 False

        回傳：
            bool: 在範圍內回傳 True，否則回傳 False
        """
        return TimeCore.is_time_in_range(check_time, start_time, end_time, allow_overnight)

    @classmethod
    def calculate_duration(cls,
                           start_time: time,
                           end_time: time,
                           allow_overnight: bool = False) -> int:
        """計算兩個時間點之間的時間差

        輸入參數：
            start_time (time): 開始時間
            end_time (time): 結束時間
            allow_overnight (bool): 是否允許跨夜計算

        回傳：
            int: 時間差（分鐘）
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
        """將時間範圍格式化為字串

        輸入參數：
            start_time (time): 開始時間
            end_time (time): 結束時間

        回傳：
            str: 格式化後的時間範圍字串（HH:MM-HH:MM）
        """
        return (f"{start_time.strftime(TimeCore.TIME_FORMAT)}-"
                f"{end_time.strftime(TimeCore.TIME_FORMAT)}")
