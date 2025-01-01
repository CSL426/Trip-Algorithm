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

        使用範例:
            >>> TimeCore.validate_time_str("09:30")
            True
            >>> TimeCore.validate_time_str("25:00")
            False
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

        使用範例:
            >>> start, end = TimeCore.parse_time_range("09:00", "17:30")
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

        使用範例:
            >>> start = datetime.strptime("09:00", "%H:%M").time()
            >>> end = datetime.strptime("17:00", "%H:%M").time()
            >>> check = datetime.strptime("13:00", "%H:%M").time()
            >>> TimeCore.is_time_in_range(check, start, end)
            True
        """
        if not allow_overnight:
            return start_time <= check_time <= end_time

        if start_time <= end_time:
            return start_time <= check_time <= end_time
        else:
            # 處理跨夜情況，例如 23:00-02:00
            return check_time >= start_time or check_time <= end_time
