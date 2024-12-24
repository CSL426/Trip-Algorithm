from datetime import datetime, time, timedelta
from typing import Dict, List


class BusinessHours:
    """處理營業時間相關的邏輯"""

    def __init__(self, hours_data: Dict):
        self.hours_data = hours_data

    def is_open_at(self, check_datetime: datetime) -> bool:
        """檢查指定時間是否在營業時間內"""
        weekday = check_datetime.weekday() + 1  # Python的0-6轉換為1-7

        # 取得當天的營業時間區間
        daily_hours = self.hours_data.get(weekday, [])
        if not daily_hours:
            return False

        # 檢查是否在任一營業時間區間內
        check_time = check_datetime.time()
        for period in daily_hours:
            start_time = datetime.strptime(period['start'], '%H:%M').time()
            end_time = datetime.strptime(period['end'], '%H:%M').time()
            if start_time <= check_time <= end_time:
                return True
        return False

    def get_next_open_period(self, check_datetime: datetime) -> tuple[time, time]:
        """取得下一個營業時間區間"""
        weekday = check_datetime.weekday() + 1
        check_time = check_datetime.time()

        # 檢查當天剩餘時間
        daily_hours = self.hours_data.get(weekday, [])
        for period in daily_hours:
            start_time = datetime.strptime(period['start'], '%H:%M').time()
            if start_time >= check_time:
                end_time = datetime.strptime(period['end'], '%H:%M').time()
                return start_time, end_time

        return None

    def is_valid_stay(self, start_datetime: datetime, duration: int) -> bool:
        """檢查從指定時間開始的停留時間是否有效"""
        end_datetime = start_datetime + timedelta(minutes=duration)

        weekday = start_datetime.weekday() + 1
        daily_hours = self.hours_data.get(weekday, [])

        # 檢查開始和結束時間是否在同一營業時間區間內
        for period in daily_hours:
            period_start = datetime.strptime(period['start'], '%H:%M').time()
            period_end = datetime.strptime(period['end'], '%H:%M').time()

            if (period_start <= start_datetime.time() <= period_end and
                    period_start <= end_datetime.time() <= period_end):
                return True

        return False
