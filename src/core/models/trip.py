# src/core/models/trip.py

from datetime import datetime, timedelta
from typing import List, Union, Literal
from pydantic import BaseModel, Field, field_validator
import re
from .time import TimeSlot


class Transport(BaseModel):
    """
    交通資訊的資料模型
    用於描述兩個地點之間的交通細節，包括交通方式、所需時間和交通時段

    這個模型主要用於：
    1. 記錄行程中的交通安排
    2. 計算總體行程時間
    3. 提供交通建議
    """

    mode: Literal["transit", "driving", "bicycling", "walking"] = Field(
        description="交通方式，可選值：大眾運輸、開車、腳踏車、步行",
        examples=["transit"]
    )

    time: int = Field(
        ge=0,
        default=0,
        description="交通所需時間(分鐘)",
        examples=[30, 45]
    )

    period: str = Field(
        default="",
        description="交通時段，格式為 'HH:MM-HH:MM'，例如 '09:00-09:30'",
        examples=["09:00-09:30"]
    )


class TripPlan(BaseModel):
    """
    單一景點行程的資料模型
    描述在行程中造訪某個地點的完整資訊

    這個模型整合了：
    1. 地點基本資訊
    2. 時間安排
    3. 交通資訊

    主要用於：
    - 記錄行程中每個地點的詳細安排
    - 提供給使用者檢視的行程資訊
    - 作為行程最佳化的基礎資料
    """

    name: str = Field(
        description="地點名稱",
        examples=["台北101觀景台"]
    )

    start_time: str = Field(
        description="開始時間(HH:MM格式)",
        examples=["09:30"]
    )

    end_time: str = Field(
        description="結束時間(HH:MM格式)",
        examples=["11:00"]
    )

    duration: int = Field(
        ge=0,
        description="停留時間(分鐘)",
        examples=[90]
    )

    hours: str = Field(
        description="營業時間資訊",
        examples=["09:00-22:00"]
    )

    transport: Transport = Field(
        description="到達此地點的交通資訊"
    )

    def to_dict(self) -> dict:
        """
        將行程資訊轉換為字典格式

        主要用於：
        - API回應格式
        - 資料序列化
        - 前端顯示

        回傳:
            dict: 包含所有行程資訊的字典
        """
        return self.model_dump()


class TripRequirement(BaseModel):
    """
    使用者的行程需求資料模型
    整合所有使用者對行程的偏好和限制

    這個模型處理：
    1. 時間範圍設定
    2. 交通偏好
    3. 用餐安排
    4. 預算限制

    主要用於：
    - 接收使用者的行程規劃需求
    - 提供行程規劃的限制條件
    - 客製化行程推薦
    """

    start_time: str = Field(
        description="行程開始時間(HH:MM格式)",
        examples=["09:00"]
    )

    end_time: str = Field(
        description="行程結束時間(HH:MM格式)",
        examples=["18:00"]
    )

    start_point: str = Field(
        description="起點位置(地點名稱或座標)",
        examples=["台北車站"]
    )

    end_point: str = Field(
        description="終點位置(地點名稱或座標)",
        examples=["台北車站", "none"]
    )

    transport_mode: str = Field(
        description="偏好的交通方式",
        examples=["transit", "driving"]
    )

    distance_threshold: int = Field(
        description="可接受的最大距離(公里)",
        examples=[30]
    )

    breakfast_time: str = Field(
        description="早餐時間(HH:MM或none)",
        examples=["08:00", "none"]
    )

    lunch_time: str = Field(
        description="午餐時間(HH:MM或none)",
        examples=["12:00", "none"]
    )

    dinner_time: str = Field(
        description="晚餐時間(HH:MM或none)",
        examples=["18:00", "none"]
    )

    budget: Union[int, Literal["none"]] = Field(
        description="預算金額或無預算限制",
        examples=[1000, "none"]
    )

    date: str = Field(
        description="出發日期(MM-DD格式)",
        examples=["12-25"]
    )

    @field_validator('start_time', 'end_time', 'breakfast_time', 'lunch_time', 'dinner_time')
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        """
        驗證時間格式的正確性

        驗證重點：
        1. 檢查是否為有效的時間格式(HH:MM)
        2. 允許特殊值 "none"

        輸入參數:
            v (str): 要驗證的時間字串

        回傳:
            str: 驗證通過的時間字串

        異常:
            ValueError: 當時間格式不正確時拋出
        """
        if v == "none":
            return v
        time_pattern = r'^([01][0-9]|2[0-3]):[0-5][0-9]$'
        if not re.match(time_pattern, v):
            raise ValueError(f'時間格式錯誤: {v}，必須為 HH:MM 或 none')
        return v

    @field_validator('date')
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """
        驗證日期格式的正確性

        驗證重點：
        1. 檢查是否為有效的日期格式(MM-DD)
        2. 允許特殊值 "none"

        輸入參數:
            v (str): 要驗證的日期字串

        回傳:
            str: 驗證通過的日期字串

        異常:
            ValueError: 當日期格式不正確時拋出
        """
        if v == "none":
            return v
        date_pattern = r'^(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$'
        if not re.match(date_pattern, v):
            raise ValueError(f'日期格式錯誤: {v}，必須為 MM-DD 或 none')
        return v

    def get_meal_times(self) -> List[TimeSlot]:
        """
        取得所有設定的用餐時間

        主要用於：
        - 行程規劃時的用餐安排
        - 餐廳選擇的時間限制

        回傳:
            List[TimeSlot]: 用餐時間清單，每個元素都是一個TimeSlot物件
        """
        meal_times = []
        for meal_time in [self.breakfast_time, self.lunch_time, self.dinner_time]:
            if meal_time != "none":
                # 假設每餐時間為1小時
                start_time = datetime.strptime(meal_time, '%H:%M')
                end_time = start_time + timedelta(hours=1)
                meal_times.append(
                    TimeSlot.create_from_datetime(start_time, end_time))
        return meal_times
