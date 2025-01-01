# src/core/models/time.py

from datetime import datetime, time, timedelta
from typing import Tuple
from pydantic import BaseModel, field_validator
from src.core.utils.time_core import TimeCore


class TimeSlot(BaseModel):
    """時間區間的資料模型

    用於表示營業時間、活動時段等時間範圍
    整合 TimeCore 的基礎功能

    屬性：
        start_time (str): 開始時間，格式必須為 "HH:MM"
        end_time (str): 結束時間，格式必須為 "HH:MM"
    """

    start_time: str
    end_time: str

    @field_validator('start_time', 'end_time')
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        """驗證時間格式
        使用 TimeCore 的驗證功能
        """
        if not TimeCore.validate_time_str(v):
            raise ValueError(f'時間格式錯誤: {v}，必須為 HH:MM 格式')
        return v

    @field_validator('end_time')
    @classmethod
    def validate_time_order(cls, v: str, info) -> str:
        """確保結束時間在開始時間之後"""
        if 'start_time' in info.data:
            start, end = TimeCore.parse_time_range(info.data['start_time'], v)
            if end <= start:
                raise ValueError('結束時間必須晚於開始時間')
        return v

    def contains(self, check_time: datetime) -> bool:
        """檢查指定時間是否在此時間區間內

        輸入參數：
            check_time (datetime): 要檢查的時間點

        回傳：
            bool: True 表示在區間內，False 表示在區間外
        """
        start, end = TimeCore.parse_time_range(self.start_time, self.end_time)
        return TimeCore.is_time_in_range(check_time.time(), start, end)
