# src/core/services/time_service.py

from datetime import datetime, timedelta
from typing import Dict, List, Union, Tuple, Optional


class TimeService:
    """時間服務類別

    統一處理所有時間相關的邏輯，包含:
    1. 時間格式轉換與驗證
    2. 營業時間判斷
    3. 時段管理與計算
    """

    def __init__(self, lunch_time: Optional[str] = None, dinner_time: Optional[str] = None):
        """初始化時間服務

        輸入:
            lunch_time: 午餐時間 (HH:MM 格式，可選)
            dinner_time: 晚餐時間 (HH:MM 格式，可選)

        若未指定用餐時間，則對應的用餐時段不會被考慮
        """
        self.lunch_time = self.parse_time(lunch_time) if lunch_time else None
        self.dinner_time = self.parse_time(
            dinner_time) if dinner_time else None

    def parse_time(self, time_input: Union[str, datetime]) -> datetime:
        """將輸入時間轉換為 datetime 物件

        輸入:
            time_input: HH:MM 格式字串或 datetime 物件

        輸出:
            datetime: 標準化後的時間物件

        若輸入為 None，則返回 None
        """
        if time_input is None:
            return None

        if isinstance(time_input, datetime):
            return time_input

        try:
            time_obj = datetime.strptime(time_input, '%H:%M').time()
            return datetime.combine(datetime.now().date(), time_obj)
        except ValueError:
            raise ValueError(f"時間格式錯誤: {time_input}, 需為 HH:MM 格式")

    def add_minutes(cls, base_time: Union[str, datetime], minutes: int) -> datetime:
        """增加或減少分鐘數

        輸入:
            base_time: 基準時間(HH:MM字串或datetime物件)
            minutes: 要增加的分鐘數(可為負數)

        輸出:
            datetime: 計算後的時間
        """
        base_dt = cls.parse_time(base_time)
        return base_dt + timedelta(minutes=minutes)

    def format_time(cls, dt: datetime) -> str:
        """將 datetime 物件格式化為時間字串

        輸入:
            dt: datetime 物件

        輸出:
            str: HH:MM 格式的時間字串
        """
        return dt.strftime(cls.TIME_FORMAT)

    def get_current_period(self, check_time: Union[str, datetime]) -> str:
        """判斷指定時間屬於哪個時段

        輸入:
            check_time: 要判斷的時間 (HH:MM字串或datetime物件)

        輸出:
            str: 時段名稱 (morning/lunch/afternoon/dinner/night)
        """
        dt = self.parse_time(check_time)

        # 如果有設定午餐時間
        if self.lunch_time:
            # 午餐時間前後一小時的區間
            lunch_start = self.add_minutes(self.lunch_time, -60)
            lunch_end = self.add_minutes(self.lunch_time, 60)

            if dt < lunch_start:
                return 'morning'
            elif lunch_start <= dt <= lunch_end:
                return 'lunch'

        # 如果有設定晚餐時間
        if self.dinner_time:
            # 晚餐時間前後一小時的區間
            dinner_start = self.add_minutes(self.dinner_time, -60)
            dinner_end = self.add_minutes(self.dinner_time, 60)

            # 如果在午餐之後，晚餐之前
            if self.lunch_time and dt > self.add_minutes(self.lunch_time, 60):
                if dt < dinner_start:
                    return 'afternoon'
                elif dinner_start <= dt <= dinner_end:
                    return 'dinner'
                else:
                    return 'night'

        # 如果沒有設定用餐時間，根據時間判斷
        hour = dt.hour
        if hour < 12:
            return 'morning'
        elif hour < 17:
            return 'afternoon'
        else:
            return 'night'

    def is_meal_time(self, check_time: Union[str, datetime]) -> bool:
        """判斷指定時間是否為用餐時間

        輸入:
            check_time: 要檢查的時間

        輸出:
            bool: True 表示在用餐時段內
        """
        dt = self.parse_time(check_time)

        # 檢查午餐時間
        if self.lunch_time:
            lunch_start = self.add_minutes(self.lunch_time, -60)
            lunch_end = self.add_minutes(self.lunch_time, 60)
            if lunch_start <= dt <= lunch_end:
                return True

        # 檢查晚餐時間
        if self.dinner_time:
            dinner_start = self.add_minutes(self.dinner_time, -60)
            dinner_end = self.add_minutes(self.dinner_time, 60)
            if dinner_start <= dt <= dinner_end:
                return True

        return False

    def check_business_hours(self,
                             check_time: Union[str, datetime],
                             business_hours: Dict[int, List[Dict[str, str]]],
                             duration_minutes: int = 0) -> Tuple[bool, Optional[int]]:
        """檢查指定時間是否在營業時間內，並計算可停留時間

        輸入:
            check_time: 要檢查的時間
            business_hours: 營業時間設定
            duration_minutes: 預計停留時間(分鐘)

        輸出:
            Tuple[bool, Optional[int]]: 
            - 第一個值表示是否在營業時間內
            - 第二個值表示可停留時間(分鐘)，若不在營業時間內則為 None
        """
        dt = self.parse_time(check_time)
        weekday = dt.isoweekday()  # 1-7 代表週一到週日

        # 檢查是否有該天的營業時間
        if weekday not in business_hours:
            return False, None

        time_slots = business_hours[weekday]
        if not time_slots or time_slots[0] is None:
            return False, None

        for slot in time_slots:
            if slot is None:
                continue

            start_dt = self.parse_time(slot['start'])
            end_dt = self.parse_time(slot['end'])

            # 處理跨日營業
            if end_dt < start_dt:
                end_dt = end_dt + timedelta(days=1)

            # 檢查是否在營業時間內
            if start_dt <= dt <= end_dt:
                # 計算剩餘可停留時間
                remaining_minutes = int((end_dt - dt).total_seconds() / 60)

                # 如果指定了停留時間，檢查是否足夠
                if duration_minutes > 0:
                    if remaining_minutes >= duration_minutes:
                        return True, duration_minutes
                    else:
                        return True, remaining_minutes

                return True, remaining_minutes

        return False, None
