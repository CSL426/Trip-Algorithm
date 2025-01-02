# src/core/models/place.py

from typing import List, Dict, Optional, Union
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, time
from src.core.utils.geo_core import GeoCore
from src.core.utils.time_core import TimeCore


class PlaceDetail(BaseModel):
    """地點詳細資訊的資料模型

    用於儲存和管理景點、餐廳等地點的完整資訊，包含：
    1. 基本資訊(名稱、位置、評分)
    2. 時間管理(營業時間、建議停留時間)
    3. 分類標籤
    4. 時段標記
    """

    name: str = Field(
        description="地點名稱",
        examples=["台北101", "故宮博物院"]
    )

    rating: float = Field(
        ge=0.0,               # 最小值
        le=5.0,               # 最大值
        default=0.0,          # 預設值
        description="地點評分 (0.0-5.0分)",
        examples=[4.5, 3.8]
    )

    lat: float = Field(
        ge=-90.0,            # 地理範圍限制
        le=90.0,
        description="緯度座標",
        examples=[25.0339808]
    )

    lon: float = Field(
        ge=-180.0,           # 地理範圍限制
        le=180.0,
        description="經度座標",
        examples=[121.561964]
    )

    duration_min: int = Field(
        ge=0,                # 不可為負數
        default=60,          # 預設停留1小時
        description="建議停留時間(分鐘)",
        examples=[90, 120]
    )

    label: str = Field(
        default="景點",
        description="地點類型標籤",
        examples=["景點", "餐廳", "購物", "文化"]
    )

    period: str = Field(
        description="適合遊玩的時段",
        examples=["morning", "lunch", "afternoon", "dinner", "night"]
    )

    hours: Dict[int, List[Optional[Dict[str, str]]]] = Field(
        description="""營業時間資訊，格式：
        {
            1: [{'start': '09:00', 'end': '17:00'}],  # 週一
            2: [{'start': '09:00', 'end': '17:00'}],  # 週二
            ...
            7: [{'start': '09:00', 'end': '17:00'}]   # 週日
        }
        - 支援多時段營業(例如中午和晚上)
        - None 表示該日店休
        - 支援跨日營業時間(例如夜市)
        """
    )

    @field_validator('period')
    def validate_period(cls, v: str) -> str:
        """驗證時段標記的正確性

        輸入參數:
            v: 時段標記

        回傳:
            str: 驗證通過的時段標記

        異常:
            ValueError: 當時段標記不正確時
        """
        """驗證時段標記"""
        valid_periods = {'morning', 'lunch', 'afternoon', 'dinner', 'night'}
        if v not in valid_periods:
            raise ValueError(f'無效的時段標記: {v}')
        return v

    @field_validator('hours')
    def validate_hours(cls, v: Dict) -> Dict:
        """驗證營業時間格式

        輸入:
            v (Dict): {
                1-7: [{'start': 'HH:MM', 'end': 'HH:MM'}, ...] 
            }

        異常:
            ValueError: 時間格式錯誤
        """
        for day, time_slots in v.items():
            if not isinstance(day, int) or not 1 <= day <= 7:
                raise ValueError(f"日期必須是1-7：{day}")

            if not isinstance(time_slots, list):
                raise ValueError(f"時段必須是列表：{time_slots}")

            for slot in time_slots:
                if slot is None:
                    continue

                if not isinstance(slot, dict):
                    raise ValueError(f"時段格式錯誤：{slot}")

                for key in ['start', 'end']:
                    if key not in slot:
                        raise ValueError(f"缺少{key}時間")
                    if not TimeCore.validate_time_str(slot[key]):
                        raise ValueError(f"時間格式錯誤：{slot[key]}")

        return v

    @field_validator('lat', 'lon')
    def validate_coordinates(cls, v: float, field: str) -> float:
        """使用 GeoCore 驗證座標"""
        try:
            if field == 'lat':
                GeoCore.validate_coordinate(v, 0)
            else:
                GeoCore.validate_coordinate(0, v)
            return v
        except ValueError as e:
            raise ValueError(f"{field} 座標錯誤: {str(e)}")

    def is_open_at(self, day: int, time_str: str) -> bool:
        """檢查指定時間是否在營業時間內

        輸入:
            day: 1-7 代表週一到週日
            time_str: "HH:MM" 格式時間
        """
        if day not in self.hours:
            return False

        time_slots = self.hours[day]
        if not time_slots or time_slots[0] is None:
            return False

        check_time = datetime.strptime(time_str, TimeCore.TIME_FORMAT).time()

        for slot in time_slots:
            if slot is None:
                continue

            start, end = TimeCore.parse_time_range(slot['start'], slot['end'])
            if TimeCore.is_time_in_range(check_time, start, end, allow_overnight=True):
                return True

        return False

    def get_next_available_time(self, current_day: int, current_time: str) -> Optional[Dict]:
        """取得下一個營業時間

        輸入:
            current_day: 1-7代表週一到週日
            current_time: "HH:MM"格式時間

        回傳:
            Dict: {
                'day': int,
                'start': str,
                'end': str
            }
        """
        current = datetime.strptime(current_time, TimeCore.TIME_FORMAT).time()

        for day_offset in range(7):
            check_day = ((current_day - 1 + day_offset) % 7) + 1
            slots = self.hours.get(check_day, [])

            if not slots or slots[0] is None:
                continue

            for slot in slots:
                if slot is None:
                    continue

                start_time = datetime.strptime(slot['start'],
                                               TimeCore.TIME_FORMAT).time()

                if day_offset == 0 and start_time <= current:
                    continue

                return {
                    'day': check_day,
                    'start': slot['start'],
                    'end': slot['end']
                }

        return None

    def is_suitable_for_current_time(self, current_time: datetime) -> bool:
        """檢查當前時間是否適合遊玩此地點

        輸入:
            current_time (datetime): 要檢查的時間

        回傳:
            bool: True 表示適合，False 表示不適合
        """
        period_times = {
            'morning': ('09:00', '11:00'),
            'lunch': ('11:00', '14:00'),
            'afternoon': ('14:00', '17:00'),
            'dinner': ('17:00', '19:00'),
            'night': ('19:00', '23:59')
        }

        if self.period not in period_times:
            return False

        start_str, end_str = period_times[self.period]
        start, end = TimeCore.parse_time_range(start_str, end_str)

        return TimeCore.is_time_in_range(current_time.time(), start, end)

    def calculate_distance(self, other: Union['PlaceDetail', Dict]) -> float:
        """計算與另一個地點的距離

        輸入:
            other: 另一個地點，可以是 PlaceDetail 物件或包含 lat/lon 的字典

        回傳:
            float: 距離(公里)
        """
        # 將自己的座標轉換為字典格式
        self_dict = {
            'lat': float(self.lat),  # 確保是浮點數
            'lon': float(self.lon)
        }

        # 如果另一個地點是字典，直接使用
        if isinstance(other, dict):
            other_dict = {
                'lat': float(other['lat']),  # 確保是浮點數
                'lon': float(other['lon'])
            }
        else:
            # 如果是 PlaceDetail 物件，轉換為字典
            other_dict = {
                'lat': float(other.lat),
                'lon': float(other.lon)
            }

        return GeoCore.calculate_distance(self_dict, other_dict)
