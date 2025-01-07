# src/core/models/trip.py

from datetime import datetime, timedelta
from typing import List, Union, Literal
from pydantic import BaseModel, Field, field_validator
import re
from .time import TimeSlot
from ..utils.validator import TripValidator  # 更新引用


class Transport(BaseModel):
    """交通資訊的資料模型"""

    mode: Literal["transit", "driving", "bicycling", "walking"] = Field(
        description="交通方式，可選值：大眾運輸、開車、腳踏車、步行",
        examples=["transit"]
    )

    @field_validator('mode')
    @classmethod
    def validate_mode(cls, v: str) -> str:
        """驗證交通方式"""
        try:
            TripValidator.validate_transport_mode(v)
            return v
        except ValueError as e:
            raise ValueError(str(e))


class TripPlan(BaseModel):
    """單一景點行程的資料模型"""

    name: str = Field(description="地點名稱")
    start_time: str = Field(description="開始時間(HH:MM格式)")
    end_time: str = Field(description="結束時間(HH:MM格式)")
    duration: int = Field(ge=0, description="停留時間(分鐘)")
    hours: str = Field(description="營業時間資訊")
    transport: Transport = Field(description="到達此地點的交通資訊")

    @field_validator('start_time', 'end_time')
    @classmethod
    def validate_time(cls, v: str) -> str:
        """驗證時間格式"""
        if not TripValidator.validate_time_string(v):
            raise ValueError(f'時間格式錯誤: {v}')
        return v


class TripRequirement(BaseModel):
    """使用者的行程需求資料模型"""

    start_time: str = Field(description="行程開始時間(HH:MM格式)")
    end_time: str = Field(description="行程結束時間(HH:MM格式)")
    start_point: str = Field(description="起點位置(地點名稱或座標)")
    end_point: str = Field(description="終點位置(地點名稱或座標)")
    transport_mode: str = Field(description="偏好的交通方式")
    distance_threshold: int = Field(description="可接受的最大距離(公里)")
    breakfast_time: str = Field(description="早餐時間(HH:MM或none)")
    lunch_time: str = Field(description="午餐時間(HH:MM或none)")
    dinner_time: str = Field(description="晚餐時間(HH:MM或none)")
    budget: Union[int, Literal["none"]] = Field(description="預算金額或無預算限制")
    date: str = Field(description="出發日期(MM-DD格式)")

    @field_validator('start_time', 'end_time', 'breakfast_time', 'lunch_time', 'dinner_time')
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        """驗證時間格式"""
        if not TripValidator.validate_time_string(v):
            raise ValueError(f'時間格式錯誤: {v}')
        return v

    @field_validator('date')
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """驗證日期格式"""
        if not TripValidator.validate_date_string(v):
            raise ValueError(f'日期格式錯誤: {v}')
        return v

    @field_validator('transport_mode')
    @classmethod
    def validate_transport(cls, v: str) -> str:
        """驗證交通方式"""
        try:
            TripValidator.validate_transport_mode(v)
            return v
        except ValueError as e:
            raise ValueError(str(e))

    def get_meal_times(self) -> List[TimeSlot]:
        """取得所有設定的用餐時間"""
        meal_times = []
        for meal_time in [self.breakfast_time, self.lunch_time, self.dinner_time]:
            if meal_time != "none":
                start_time = datetime.strptime(meal_time, '%H:%M')
                end_time = start_time + timedelta(hours=1)
                meal_times.append(TimeSlot(
                    start_time=start_time.strftime('%H:%M'),
                    end_time=end_time.strftime('%H:%M')
                ))
        return meal_times
