# src\core\models.py

from typing import List, Dict, Union, Literal, Optional, Tuple
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, time, timedelta
import re


class TimeSlot(BaseModel):
    """
    營業時間時段定義

    屬性:
        start_time (str): 開始時間，格式 HH:MM
        end_time (str): 結束時間，格式 HH:MM
    """
    start_time: str
    end_time: str

    @field_validator('start_time', 'end_time')
    @classmethod
    def validate_time(cls, v: str) -> str:
        """驗證時間格式是否符合 HH:MM"""
        time_pattern = r'^([01][0-9]|2[0-3]):[0-5][0-9]$'
        if not re.match(time_pattern, v):
            raise ValueError(f'時間格式錯誤: {v}，應為HH:MM')
        return v

    @field_validator('end_time')
    @classmethod
    def validate_time_order(cls, v: str, info) -> str:
        """確保結束時間在開始時間之後"""
        if 'start_time' in info.data:
            start = datetime.strptime(info.data['start_time'], '%H:%M')
            end = datetime.strptime(v, '%H:%M')
            if end <= start:
                raise ValueError('結束時間必須晚於開始時間')
        return v


class PlaceDetail(BaseModel):
    """
    地點詳細資訊

    屬性:
        name (str): 地點名稱
        rating (float): 評分 (0.0-5.0)
        lat (float): 緯度
        lon (float): 經度
        duration_min (int): 建議停留時間(分鐘)
        label (str): 地點類型標籤(如：景點、餐廳)
        hours (Dict): 營業時間，格式為 {weekday: [{'start': 'HH:MM', 'end': 'HH:MM'}]}
        url (str): 地點相關連結
    """
    name: str
    rating: float = Field(ge=0.0, le=5.0, default=0.0)
    lat: float = Field(ge=-90.0, le=90.0)
    lon: float = Field(ge=-180.0, le=180.0)
    duration_min: int = Field(ge=0, default=60)
    label: str = "景點"
    hours: Dict[int, List[Optional[Dict[str, str]]]] = Field(
        description="營業時間，key為1-7代表星期幾，value為該天的營業時段列表"
    )
    url: str = ""

    @field_validator('hours')
    def validate_hours(cls, v: Dict) -> Dict:
        """
        驗證營業時間格式

        輸入格式範例:
        {
            1: [None],  # 週一公休
            2: [{'start': '11:30', 'end': '14:30'}]  # 週二營業時段
        }

        支援跨日營業時間，例如：
        {'start': '17:00', 'end': '00:00'}  # 晚上營業到午夜
        {'start': '23:00', 'end': '04:00'}  # 凌晨營業
        """
        time_pattern = r'^([01][0-9]|2[0-3]):[0-5][0-9]$'

        for day, time_slots in v.items():
            if not isinstance(day, int) or not 1 <= day <= 7:
                raise ValueError(f"日期必須是1-7之間的整數，收到 {day}")

            if not isinstance(time_slots, list):
                raise ValueError(f"時段必須是列表格式，收到 {time_slots}")

            for slot in time_slots:
                if slot is None:  # 允許 None 表示公休
                    continue

                if not isinstance(slot, dict) or not all(k in slot for k in ['start', 'end']):
                    raise ValueError(f"時段必須包含 start 和 end，收到 {slot}")

                for key in ['start', 'end']:
                    if not re.match(time_pattern, slot[key]):
                        raise ValueError(f"時間格式錯誤: {slot[key]}，應為HH:MM")

                # 處理跨日營業時間
                start = datetime.strptime(slot['start'], '%H:%M')
                end = datetime.strptime(slot['end'], '%H:%M')

                # 如果結束時間是 00:00，轉換為 23:59
                if end.hour == 0 and end.minute == 0:
                    slot['end'] = '23:59'

                # 跨日營業無需額外處理，is_open_at 會處理跨日邏輯
        return v

    def is_open_at(self, day_or_datetime, time: str = None) -> bool:
        """
        檢查指定時間是否在營業時間內
        
        支援兩種呼叫方式：
        1. is_open_at(datetime) -> 使用 datetime 物件
        2. is_open_at(day, time) -> 使用日期數字(1-7)和時間字串('HH:MM')
        
        參數:
            day_or_datetime: datetime 物件或整數(1-7代表星期幾)
            time: 當 day_or_datetime 為整數時，需提供時間字串('HH:MM')
            
        回傳:
            bool: True 表示營業中，False 表示未營業
        """
        # 根據參數類型決定處理方式
        if isinstance(day_or_datetime, datetime):
            check_datetime = day_or_datetime
            weekday = check_datetime.weekday() + 1
            check_time = check_datetime.time()
        else:
            if time is None:
                raise ValueError("使用日期數字時必須提供時間字串")
            weekday = day_or_datetime
            check_time = datetime.strptime(time, '%H:%M').time()

        daily_hours = self.hours.get(weekday, [])
        if not daily_hours or daily_hours[0] is None:
            return False
            
        # 檢查每個營業時段
        for period in daily_hours:
            if period is None:
                continue
                
            start_time = datetime.strptime(period['start'], '%H:%M').time()
            end_time = datetime.strptime(period['end'], '%H:%M').time()
            
            # 跨日營業的情況
            if start_time > end_time:
                if check_time >= start_time or check_time <= end_time:
                    return True
            # 一般營業時間
            else:
                if start_time <= check_time <= end_time:
                    return True
                    
        return False

    def _is_time_in_period(self, check_time: time, period: Dict[str, str]) -> bool:
        """
        檢查時間是否在特定時段內

        參數：
            check_time: 要檢查的時間
            period: 營業時段，包含 start 和 end

        回傳：
            bool: True 表示在時段內，False 表示不在
        """
        start = datetime.strptime(period['start'], '%H:%M').time()
        end = datetime.strptime(period['end'], '%H:%M').time()

        # 處理跨日營業的情況
        if start > end:  # 例如 23:00-04:00
            return check_time >= start or check_time <= end
        return start <= check_time <= end

    def get_next_open_period(self, check_datetime: datetime) -> Optional[Tuple[time, time]]:
        """
        取得下一個營業時段

        參數：
            check_datetime: 當前時間

        回傳：
            Optional[Tuple[time, time]]: 下一個營業時段的開始和結束時間，若無則為 None
        """
        weekday = check_datetime.weekday() + 1
        check_time = check_datetime.time()

        # 檢查當天剩餘時段
        daily_hours = self.hours.get(weekday, [])
        for period in daily_hours:
            if period is None:
                continue
            start_time = datetime.strptime(period['start'], '%H:%M').time()
            if start_time >= check_time:
                end_time = datetime.strptime(period['end'], '%H:%M').time()
                return start_time, end_time
        return None

    def can_visit(self, start_datetime: datetime, duration: int) -> bool:
        """
        檢查是否可以在指定時間進行參訪

        參數：
            start_datetime: 預計開始參訪的時間
            duration: 預計停留時間（分鐘)

        回傳：
            bool: True 表示可以參訪，False 表示不行
        """
        if not self.is_open_at(start_datetime):
            return False

        end_datetime = start_datetime + timedelta(minutes=duration)
        return self.is_open_at(end_datetime)


class Transport(BaseModel):
    """
    交通方式定義

    屬性:
        mode (str): 交通模式 (transit/driving/bicycling/walking)
        time (int): 交通所需時間(分鐘)
        period (str): 交通時段，格式 "HH:MM-HH:MM"
    """
    mode: Literal["transit", "driving", "bicycling", "walking"]
    time: int = Field(ge=0, default=0)
    period: str = ""


class TripPlan(BaseModel):
    """
    單一行程計畫

    屬性:
        name (str): 地點名稱
        start_time (str): 開始時間，格式 HH:MM
        end_time (str): 結束時間，格式 HH:MM
        duration (int): 停留時間(分鐘)
        hours (str): 營業時間資訊
        transport (Transport): 交通資訊
    """
    name: str
    start_time: str
    end_time: str
    duration: int = Field(ge=0)
    hours: str
    transport: Transport

    def to_dict(self) -> dict:
        """轉換為字典格式"""
        return self.model_dump()


class TripRequirement(BaseModel):
    """
    使用者旅遊需求

    屬性:
        start_time (str): 開始時間，格式 HH:MM
        end_time (str): 結束時間，格式 HH:MM
        start_point (str): 起點名稱或座標
        end_point (str): 終點名稱或座標
        transport_mode (str): 交通方式
        distance_threshold (int): 可接受的最大距離(公里)
        breakfast_time (str): 早餐時間，格式 HH:MM 或 "none"
        lunch_time (str): 午餐時間，格式 HH:MM 或 "none"
        dinner_time (str): 晚餐時間，格式 HH:MM 或 "none"
        budget (Union[int, str]): 預算金額或 "none"
        date (str): 出發日期，格式 MM-DD
    """
    start_time: str
    end_time: str
    start_point: str
    end_point: str
    transport_mode: str
    distance_threshold: int
    breakfast_time: str
    lunch_time: str
    dinner_time: str
    budget: Union[int, Literal["none"]]
    date: str

    @field_validator('start_time', 'end_time', 'breakfast_time', 'lunch_time', 'dinner_time')
    @classmethod
    def validate_time(cls, v: str) -> str:
        """驗證時間格式"""
        if v == "none":
            return v
        time_pattern = r'^([01][0-9]|2[0-3]):[0-5][0-9]$'
        if not re.match(time_pattern, v):
            raise ValueError(f'時間格式錯誤: {v}，應為 HH:MM 或 none')
        return v

    @field_validator('date')
    @classmethod
    def validate_date(cls, v: str) -> str:
        """驗證日期格式"""
        if v == "none":
            return v
        date_pattern = r'^(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$'
        if not re.match(date_pattern, v):
            raise ValueError(f'日期格式錯誤: {v}，應為 MM-DD 或 none')
        return v
