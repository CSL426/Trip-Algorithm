# src/core/utils/time_core.py

from datetime import datetime, time, timedelta
from typing import Tuple, Optional
import re


class TimeCore:
    """時間處理核心類別

    負責所有基礎的時間運算，包含：
    1. 時間格式驗證
    2. 時間區間計算
    3. 時間比較功能
    4. 跨夜時間處理

    使用方式：
    - 所有方法都是類別方法，可直接通過類別呼叫
    - 時間格式統一使用 "HH:MM" 字串
    - 跨夜判斷透過 allow_overnight 參數控制
    """

    # 時間相關常數
    TIME_FORMAT = '%H:%M'
    TIME_PATTERN = r'^([01][0-9]|2[0-3]):[0-5][0-9]$'

    @classmethod
    def validate_time_str(cls, time_str: str) -> bool:
        """驗證時間字串格式

        輸入參數:
            time_str (str): 要驗證的時間字串，格式必須是 "HH:MM"

        回傳:
            bool: 格式正確回傳 True，否則回傳 False
        """
        if not isinstance(time_str, str):
            return False
        return bool(re.match(cls.TIME_PATTERN, time_str))

    @classmethod
    def parse_time_range(cls, start_str: str, end_str: str) -> Tuple[time, time]:
        """解析時間範圍字串為 time 物件

        輸入參數:
            start_str (str): 開始時間字串 ("HH:MM" 格式)
            end_str (str): 結束時間字串 ("HH:MM" 格式)

        回傳:
            Tuple[time, time]: (開始時間, 結束時間)

        異常:
            ValueError: 當時間格式不正確時拋出
        """
        if not (cls.validate_time_str(start_str) and cls.validate_time_str(end_str)):
            raise ValueError(f"時間格式錯誤: {start_str} 或 {end_str}")

        start = datetime.strptime(start_str, cls.TIME_FORMAT).time()
        end = datetime.strptime(end_str, cls.TIME_FORMAT).time()
        return start, end

    @classmethod
    def is_time_in_range(cls,
                         check_time: time,
                         start_time: time,
                         end_time: time,
                         allow_overnight: bool = False) -> bool:
        """檢查時間是否在指定範圍內

        輸入參數:
            check_time (time): 要檢查的時間
            start_time (time): 開始時間
            end_time (time): 結束時間
            allow_overnight (bool): 是否允許跨夜，預設 False

        回傳:
            bool: 在範圍內回傳 True，否則回傳 False
        """
        if not allow_overnight:
            return start_time <= check_time <= end_time

        if start_time <= end_time:
            return start_time <= check_time <= end_time
        else:
            # 處理跨夜情況，例如 23:00-02:00
            return check_time >= start_time or check_time <= end_time

    @classmethod
    def add_minutes(cls, t: time, minutes: int) -> time:
        """增加或減少分鐘數

        輸入:
            t: time 物件
            minutes: 要增加的分鐘數（可以是負數）

        回傳:
            time: 調整後的時間
        """
        # 將 time 轉換為 datetime 以便計算
        dt = datetime.combine(datetime.min, t)

        # 加上分鐘數
        dt = dt + timedelta(minutes=minutes)

        # 取出調整後的 time
        return dt.time()

    @classmethod
    def calculate_duration(cls, start: time, end: time, allow_overnight: bool = False) -> int:
        """計算時間區間的長度（分鐘）

        輸入:
            start: 開始時間
            end: 結束時間
            allow_overnight: 是否允許跨夜

        回傳:
            int: 時間差（分鐘）
        """
        start_minutes = start.hour * 60 + start.minute
        end_minutes = end.hour * 60 + end.minute

        if end_minutes < start_minutes and allow_overnight:
            # 跨夜情況，加上一天的分鐘數
            return (24 * 60 - start_minutes) + end_minutes

        return end_minutes - start_minutes
