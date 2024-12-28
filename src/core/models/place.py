# src/core/models/place.py

from typing import List, Dict, Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, time
from .time import TimeSlot
import re


class PlaceDetail(BaseModel):
    """
    地點詳細資訊的資料模型
    用於儲存和管理景點、餐廳等地點的完整資訊

    這個模型整合了：
    1. 基本資訊（名稱、評分、位置）
    2. 時間管理（營業時間、建議停留時間）
    3. 分類標籤
    4. 相關連結

    主要用途：
    - 提供行程規劃器使用的標準化地點資訊
    - 確保資料的完整性和正確性
    - 提供營業時間的智能判斷功能
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
        examples=[25.0339808]  # 台北101的緯度
    )

    lon: float = Field(
        ge=-180.0,           # 地理範圍限制
        le=180.0,
        description="經度座標",
        examples=[121.561964]  # 台北101的經度
    )

    duration_min: int = Field(
        ge=0,                # 不可為負數
        default=60,          # 預設停留1小時
        description="建議停留時間（分鐘）",
        examples=[90, 120]
    )

    label: str = Field(
        default="景點",
        description="地點類型標籤",
        examples=["景點", "餐廳", "購物", "文化"]
    )

    hours: Dict[int, List[Optional[Dict[str, str]]]] = Field(
        description="""
        營業時間資訊，格式為：
        {
            1: [{'start': '09:00', 'end': '17:00'}],  # 週一
            2: [{'start': '09:00', 'end': '17:00'}],  # 週二
            ...
            7: [{'start': '09:00', 'end': '17:00'}]   # 週日
        }
        - 支援多時段營業 (例如: 午餐和晚餐分開的餐廳)
        - None 表示該日店休
        - 支援跨日營業時間 (例如: 23:00-02:00)
        """
    )

    url: str = Field(
        default="",
        description="相關網頁連結",
    )

    @field_validator('hours')
    def validate_hours(cls, v: Dict) -> Dict:
        """
        驗證營業時間格式的正確性

        主要驗證項目：
        1. 星期格式（必須是1-7的整數）
        2. 時間格式（必須是HH:MM格式）
        3. 時間順序（結束時間必須晚於開始時間）
        4. 特殊情況處理（跨日營業、公休日）

        輸入參數:
            v (Dict): 要驗證的營業時間資料

        回傳:
            Dict: 驗證通過的營業時間資料

        異常:
            ValueError: 當資料格式不正確時拋出，並說明錯誤原因
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
                if not isinstance(slot, dict) or not all(k in slot for k in ['start', 'end']):
                    raise ValueError(f"時段必須包含 start 和 end，收到 {slot}")

                # 驗證時間格式
                for key in ['start', 'end']:
                    if not re.match(time_pattern, slot[key]):
                        raise ValueError(f"時間格式錯誤: {slot[key]}，必須為HH:MM格式")

                # 處理特殊情況：凌晨結束時間
                if slot['end'] == '00:00':
                    slot['end'] = '23:59'

                start_time = datetime.strptime(slot['start'], '%H:%M')
                end_time = datetime.strptime(slot['end'], '%H:%M')
                if end_time <= start_time:
                    raise ValueError(f"結束時間必須晚於開始時間: {slot}")

        return v

    def is_open_at(self, day: int, time_str: str) -> bool:
        """
        判斷指定時間是否在營業時間內

        輸入說明：
        day: 1-7 代表星期一到星期日
        time_str: 'HH:MM' 格式的時間字串，例如 '12:00'

        運作原理：
        1. 首先檢查是否有該天的營業時間資料
        2. 針對該天的每個營業時段檢查：
        - 例如可能有午餐時段 11:30-14:30
        - 和晚餐時段 17:30-21:30
        3. 只要在任一時段內，就回傳 True

        舉例：
        - 現在是週一中午12點
        - 檢查 hours[1] 的時段
        - 12:00 在 11:30-14:30 之間
        - 所以應該回傳 True
        """
        # 重要：加入除錯輸出
        print(f"\n檢查營業時間")
        print(f"checking day: {day}, time: {time_str}")
        print(f"venue hours: {self.hours}")

        # 檢查是否有該天的營業時間資料
        if day not in self.hours:
            print(f"沒有星期 {day} 的營業時間資料")
            return False

        time_slots = self.hours[day]
        if not time_slots or time_slots[0] is None:
            print("該天公休")
            return False

        # 將檢查時間轉換為 datetime.time 物件
        check_time = datetime.strptime(time_str, '%H:%M').time()

        # 檢查每個營業時段
        for slot in time_slots:
            if slot is None:
                continue

            start = datetime.strptime(slot['start'], '%H:%M').time()
            end = datetime.strptime(slot['end'], '%H:%M').time()

            print(f"checking slot: {start} - {end}")

            # 檢查是否在這個時段內
            if start <= check_time <= end:
                print("在營業時間內！")
                return True

        print("不在任何營業時段內")
        return False

    def get_next_available_time(self, from_day: int, from_time: str) -> Optional[Dict[str, str]]:
        """
        取得下一個可用的營業時間

        輸入參數:
            from_day (int): 起始日期（1-7）
            from_time (str): 起始時間（HH:MM）

        回傳:
            Optional[Dict[str, str]]: 下一個營業時段，格式為
            {
                'day': int,    # 星期幾（1-7）
                'start': str,  # 開始時間（HH:MM）
                'end': str     # 結束時間（HH:MM）
            }
            如果找不到下一個營業時間，回傳 None
        """
        check_time = datetime.strptime(from_time, '%H:%M').time()

        # 檢查未來7天
        for day_offset in range(7):
            check_day = ((from_day - 1 + day_offset) % 7) + 1

            if check_day in self.hours:
                slots = self.hours[check_day]
                if slots and slots[0] is not None:
                    for slot in slots:
                        if slot is None:
                            continue

                        start_time = datetime.strptime(
                            slot['start'], '%H:%M').time()

                        # 如果是當天，檢查是否已經過了開始時間
                        if day_offset == 0 and start_time <= check_time:
                            continue

                        return {
                            'day': check_day,
                            'start': slot['start'],
                            'end': slot['end']
                        }

        return None
