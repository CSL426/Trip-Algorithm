# src/core/models/time.py

from datetime import datetime, time, timedelta
from typing import Tuple
from pydantic import BaseModel, field_validator
import re


class TimeSlot(BaseModel):
    """
    時間區間的資料模型
    用於表示營業時間、活動時段等時間範圍

    屬性:
        start_time (str): 開始時間，格式必須為 'HH:MM'，例如 '09:30'
        end_time (str): 結束時間，格式必須為 'HH:MM'，例如 '18:00'

    使用範例:
        morning_slot = TimeSlot(start_time='09:00', end_time='12:00')
        afternoon_slot = TimeSlot(start_time='13:00', end_time='17:00')
    """

    start_time: str
    end_time: str

    @field_validator('start_time', 'end_time')
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        """
        驗證時間字串格式是否正確

        輸入參數:
            v (str): 要驗證的時間字串

        回傳:
            str: 驗證通過的時間字串

        異常:
            ValueError: 當時間格式不符合 HH:MM 格式時拋出
        """
        time_pattern = r'^([01][0-9]|2[0-3]):[0-5][0-9]$'
        if not re.match(time_pattern, v):
            raise ValueError(f'時間格式錯誤: {v}，必須為HH:MM格式')
        return v

    @field_validator('end_time')
    @classmethod
    def validate_time_order(cls, v: str, info) -> str:
        """
        確保結束時間在開始時間之後

        輸入參數:
            v (str): 結束時間字串
            info: pydantic的驗證資訊，包含其他欄位的值

        回傳:
            str: 驗證通過的結束時間字串

        異常:
            ValueError: 當結束時間早於或等於開始時間時拋出
        """
        if 'start_time' in info.data:
            start = datetime.strptime(info.data['start_time'], '%H:%M')
            end = datetime.strptime(v, '%H:%M')
            if end <= start:
                raise ValueError('結束時間必須晚於開始時間')
        return v

    def to_datetime_tuple(self) -> Tuple[datetime, datetime]:
        """
        將時間字串轉換為datetime物件

        回傳:
            Tuple[datetime, datetime]: (開始時間, 結束時間)的元組
        """
        today = datetime.now().date()
        start = datetime.combine(today,
                                 datetime.strptime(self.start_time, '%H:%M').time())
        end = datetime.combine(today,
                               datetime.strptime(self.end_time, '%H:%M').time())
        return start, end

    def contains(self, check_time: datetime) -> bool:
        """
        檢查指定時間是否在此時間區間內

        輸入參數:
            check_time (datetime): 要檢查的時間點

        回傳:
            bool: True 表示在區間內，False 表示在區間外

        使用範例:
            time_slot = TimeSlot(start_time="09:00", end_time="17:00")
            now = datetime.now()
            is_open = time_slot.contains(now)
        """
        # 只比較時間部分，忽略日期
        check_time_only = check_time.time()
        start = datetime.strptime(self.start_time, '%H:%M').time()
        end = datetime.strptime(self.end_time, '%H:%M').time()

        return start <= check_time_only <= end

    def duration_minutes(self) -> int:
        """
        計算此時間區間的持續時間

        回傳:
            int: 持續的分鐘數
        """
        start, end = self.to_datetime_tuple()
        duration = end - start
        return int(duration.total_seconds() / 60)

    def overlaps(self, other: 'TimeSlot') -> bool:
        """
        檢查是否與另一個時間區間重疊

        輸入參數:
            other (TimeSlot): 另一個時間區間

        回傳:
            bool: True表示有重疊，False表示無重疊
        """
        this_start, this_end = self.to_datetime_tuple()
        other_start, other_end = other.to_datetime_tuple()
        return (this_start <= other_end and other_start <= this_end)

    @classmethod
    def create_from_datetime(cls, start: datetime, end: datetime) -> 'TimeSlot':
        """
        從datetime物件建立TimeSlot

        輸入參數:
            start (datetime): 開始時間
            end (datetime): 結束時間

        回傳:
            TimeSlot: 新建立的時間區間物件
        """
        return cls(
            start_time=start.strftime('%H:%M'),
            end_time=end.strftime('%H:%M')
        )
