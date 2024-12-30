# src/core/models/place.py

from typing import List, Dict, Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, time
from .time import TimeSlot
import re


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
        valid_periods = {'morning', 'lunch', 'afternoon', 'dinner', 'night'}
        if v not in valid_periods:
            raise ValueError(f'無效的時段標記: {v}，必須是 {valid_periods} 其中之一')
        return v

    @field_validator('hours')
    def validate_hours(cls, v: Dict) -> Dict:
        """驗證營業時間格式的正確性

        輸入參數:
            v: 營業時間資料

        回傳:
            Dict: 驗證通過的營業時間資料

        異常:
            ValueError: 當資料格式不正確時
        """
        time_pattern = r'^([01][0-9]|2[0-3]):[0-5][0-9]$'

        for day, time_slots in v.items():
            # 檢查星期格式
            if not isinstance(day, int) or not 1 <= day <= 7:
                raise ValueError(f"日期必須是1-7之間的整數，收到 {day}")

            # 檢查時段列表格式
            if not isinstance(time_slots, list):
                raise ValueError(f"時段必須是列表格式，收到 {time_slots}")

            # 處理每個時段
            for slot in time_slots:
                # 允許 None 表示公休
                if slot is None:
                    continue

                # 檢查時段格式
                if not isinstance(slot, dict) or 'start' not in slot or 'end' not in slot:
                    raise ValueError(f"時段必須包含 start 和 end，收到 {slot}")

                # 驗證時間格式
                for key in ['start', 'end']:
                    if not re.match(time_pattern, slot[key]):
                        raise ValueError(f"時間格式錯誤: {slot[key]}，必須為 HH:MM 格式")

                # 驗證時間順序
                start = datetime.strptime(slot['start'], '%H:%M').time()
                end = datetime.strptime(slot['end'], '%H:%M').time()

                # 特殊處理：凌晨結束的情況
                if end == time(0, 0):
                    end = time(23, 59)
                elif end < start:
                    raise ValueError(f"結束時間必須晚於開始時間: {slot}")

        return v

    def is_open_at(self, day: int, time_str: str) -> bool:
        """判斷指定時間是否在營業時間內

        輸入參數:
            day: 星期幾 (1-7分別代表週一到週日)
            time_str: 時間字串 (HH:MM格式)

        回傳:
            bool: True 表示營業中，False 表示未營業
        """
        # 檢查是否有該天的營業時間資料
        if day not in self.hours:
            return False

        time_slots = self.hours[day]
        if not time_slots or time_slots[0] is None:
            return False

        # 將檢查時間轉換為 datetime.time 物件
        check_time = datetime.strptime(time_str, '%H:%M').time()

        # 檢查每個營業時段
        for slot in time_slots:
            if slot is None:
                continue

            start = datetime.strptime(slot['start'], '%H:%M').time()
            end = datetime.strptime(slot['end'], '%H:%M').time()

            # 處理跨日營業的情況
            if end < start:  # 表示跨越午夜
                if check_time >= start or check_time <= end:
                    return True
            else:
                if start <= check_time <= end:
                    return True

        return False

    def get_next_available_time(self, from_day: int, from_time: str) -> Optional[Dict[str, str]]:
        """取得下一個可用的營業時間

        輸入參數:
            from_day: 起始日期 (1-7)
            from_time: 起始時間 (HH:MM格式)

        回傳:
            Optional[Dict[str, str]]: 下一個營業時間，包含:
                - day: 星期幾 (1-7)
                - start: 開始時間 (HH:MM)
                - end: 結束時間 (HH:MM)
                如果找不到則回傳 None
        """
        check_time = datetime.strptime(from_time, '%H:%M').time()

        # 檢查未來7天
        for day_offset in range(7):
            check_day = ((from_day - 1 + day_offset) % 7) + 1

            if check_day not in self.hours:
                continue

            slots = self.hours[check_day]
            if not slots or slots[0] is None:
                continue

            for slot in slots:
                if slot is None:
                    continue

                start_time = datetime.strptime(slot['start'], '%H:%M').time()

                # 同一天的情況，需要檢查時間是否已過
                if day_offset == 0 and start_time <= check_time:
                    continue

                return {
                    'day': check_day,
                    'start': slot['start'],
                    'end': slot['end']
                }

        return None

    def is_suitable_for_current_time(self, current_time: datetime) -> bool:
        """檢查當前時間是否適合遊玩此地點

        基於地點的 period 屬性和當前時間判斷

        輸入參數:
            current_time: 當前時間

        回傳:
            bool: True 表示適合，False 表示不適合
        """
        hour = current_time.hour

        # 根據時段判斷是否適合
        if self.period == 'morning' and 9 <= hour < 11:
            return True
        elif self.period == 'lunch' and 11 <= hour < 14:
            return True
        elif self.period == 'afternoon' and 14 <= hour < 17:
            return True
        elif self.period == 'dinner' and 17 <= hour < 19:
            return True
        elif self.period == 'night' and hour >= 19:
            return True

        return False
