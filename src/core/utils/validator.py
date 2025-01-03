# src/core/utils/validator.py

from datetime import datetime, time, timedelta
from typing import List, Dict, Optional, Union
import re


class ValidationError(Exception):
    """驗證錯誤的基礎類別"""

    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


class TripValidator:
    """行程驗證器"""

    # 常數定義
    VALID_TRANSPORT_MODES = {"transit", "driving", "walking", "bicycling"}
    DEFAULT_HOURS = {i: [{'start': '00:00', 'end': '23:59'}]
                     for i in range(1, 8)}
    REQUIRED_PLACE_FIELDS = {'name', 'lat',
                             'lon', 'duration', 'label', 'period'}
    TIME_PATTERN = r'^([01][0-9]|2[0-3]):[0-5][0-9]$'
    DATE_PATTERN = r'^(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$'

    @classmethod
    def validate_coordinates(cls, lat: float, lon: float) -> bool:
        """驗證座標是否在有效範圍內

        輸入:
            lat: 緯度, -90 到 90 度
            lon: 經度, -180 到 180 度

        回傳:
            bool: True=有效, False=無效

        使用範例:
            >>> TripValidator.validate_coordinates(25.0, 121.5)
            True
            >>> TripValidator.validate_coordinates(91.0, 121.5)
            False
        """
        try:
            return -90 <= float(lat) <= 90 and -180 <= float(lon) <= 180
        except (TypeError, ValueError):
            return False

    @classmethod
    def validate_time_string(cls, time_str: str) -> bool:
        """驗證時間字串格式

        輸入:
            time_str: HH:MM 格式時間字串
                     支援 "none" 作為特殊值

        回傳:
            bool: True=格式正確, False=格式錯誤

        使用範例:
            >>> TripValidator.validate_time_string("09:30")
            True
            >>> TripValidator.validate_time_string("25:00")
            False
            >>> TripValidator.validate_time_string("none")
            True
        """
        if time_str == "none":
            return True
        return bool(re.match(cls.TIME_PATTERN, time_str))

    @classmethod
    def validate_date_string(cls, date_str: str) -> bool:
        """驗證日期字串格式

        輸入:
            date_str: MM-DD 格式日期字串
                     支援 "none" 作為特殊值

        回傳:
            bool: True=格式正確, False=格式錯誤

        使用範例:
            >>> TripValidator.validate_date_string("12-25")
            True
            >>> TripValidator.validate_date_string("13-01")
            False
            >>> TripValidator.validate_date_string("none")
            True
        """
        if date_str == "none":
            return True
        return bool(re.match(cls.DATE_PATTERN, date_str))

    @classmethod
    def validate_time_range(cls, start_time: str, end_time: str) -> bool:
        """驗證時間範圍的有效性

        輸入:
            start_time: 開始時間 (HH:MM)
            end_time: 結束時間 (HH:MM)

        回傳:
            bool: True=有效範圍, False=無效範圍

        使用範例:
            >>> TripValidator.validate_time_range("09:00", "17:00")
            True
            >>> TripValidator.validate_time_range("17:00", "09:00")
            False
        """
        if not all([cls.validate_time_string(t) for t in [start_time, end_time]]):
            return False

        start = datetime.strptime(start_time, '%H:%M').time()
        end = datetime.strptime(end_time, '%H:%M').time()

        # 允許跨日營業時間(如夜市)
        if end < start:
            return True

        return start < end

    @classmethod
    def validate_place(cls, place_data: Dict) -> None:
        """驗證地點資料的完整性與正確性

        輸入:
            place_data: Dict, 地點資料字典，必須包含:
                - name: 名稱
                - lat/lon: 座標
                - duration: 停留時間(分鐘)
                - label: 分類標籤
                - period: 時段
                - hours: 營業時間(選填)

        異常:
            ValidationError: 資料不完整或格式錯誤

        使用範例:
            >>> place = {
                    "name": "台北101",
                    "lat": 25.0339,
                    "lon": 121.5619,
                    "duration": 90,
                    "label": "景點",
                    "period": "morning"
                }
            >>> TripValidator.validate_place(place)
        """
        # 檢查必要欄位
        missing = cls.REQUIRED_PLACE_FIELDS - set(place_data.keys())
        if missing:
            raise ValidationError(f"缺少必要欄位：{missing}")

        # 驗證座標
        if not cls.validate_coordinates(place_data['lat'], place_data['lon']):
            raise ValidationError("座標格式錯誤或超出範圍", "coordinates")

        # 驗證停留時間
        try:
            duration = int(place_data['duration'])
            if duration <= 0:
                raise ValidationError("停留時間必須大於0", "duration")
        except (TypeError, ValueError):
            raise ValidationError("停留時間必須為整數", "duration")

        # 驗證時段標記
        valid_periods = {'morning', 'lunch',
                         'afternoon', 'dinner', 'night'}
        if place_data['period'] not in valid_periods:
            raise ValidationError(
                f"無效的時段標記：{place_data['period']}", "period")

        # 如果有提供營業時間，進行驗證
        if 'hours' in place_data:
            cls.validate_business_hours(place_data['hours'])

    @classmethod
    def validate_business_hours(cls, hours: Dict) -> None:
        """驗證營業時間格式與邏輯

        輸入:
            hours: Dict, 營業時間字典，格式為:
                {
                    1: [{'start': '09:00', 'end': '17:00'}],  # 週一
                    2: [{'start': '09:00', 'end': '17:00'}],  # 週二
                    ...
                    7: [{'start': '09:00', 'end': '17:00'}]   # 週日
                }
                - 支援多時段營業(陣列)
                - None 表示該日店休
                - 支援跨日營業時間

        異常:
            ValidationError: 格式錯誤或時間無效

        使用範例:
            >>> hours = {
                    1: [{'start': '09:00', 'end': '17:00'}],
                    2: [{'start': '09:00', 'end': '17:00'}]
                }
            >>> TripValidator.validate_business_hours(hours)
        """
        # 檢查每天的營業時間
        for day, slots in hours.items():
            # 驗證星期格式
            if not isinstance(day, int) or day < 1 or day > 7:
                raise ValidationError(f"無效的星期格式：{day}", "business_hours")

            # 允許 None 值表示店休
            if slots is None:
                continue

            # 必須是時段列表
            if not isinstance(slots, list):
                raise ValidationError(f"時段必須是列表：{slots}", "business_hours")

            # 驗證每個時段
            for slot in slots:
                if slot is None:
                    continue

                if not isinstance(slot, dict):
                    raise ValidationError(f"時段格式錯誤：{slot}", "business_hours")

                # 檢查必要的時間欄位
                for key in ['start', 'end']:
                    if key not in slot:
                        raise ValidationError(f"時段缺少{key}時間", "business_hours")
                    if not cls.validate_time_string(slot[key]):
                        raise ValidationError(
                            f"時間格式錯誤：{slot[key]}", "business_hours")

                # 檢查時間範圍有效性
                if not cls.validate_time_range(slot['start'], slot['end']):
                    raise ValidationError(
                        f"無效的營業時間範圍：{slot['start']}-{slot['end']}",
                        "business_hours"
                    )

    @classmethod
    def validate_trip_requirement(cls, requirement: Dict) -> None:
        """驗證行程需求的完整性與正確性

        輸入:
            requirement: Dict, 行程需求字典，必須包含:
                - start_time: 開始時間 (HH:MM)
                - end_time: 結束時間 (HH:MM)
                - start_point: 起點名稱或座標
                - end_point: 終點名稱或座標 (可為 none)
                - transport_mode: 交通方式
                - distance_threshold: 可接受的最大距離(公里)
                - breakfast_time: 早餐時間 (HH:MM 或 none)
                - lunch_time: 午餐時間 (HH:MM 或 none)
                - dinner_time: 晚餐時間 (HH:MM 或 none)
                - budget: 預算金額 或 'none'
                - date: 出發日期 (MM-DD 或 none)

        異常:
            ValidationError: 資料不完整或格式錯誤

        使用範例:
            >>> req = {
                    "start_time": "09:00",
                    "end_time": "18:00",
                    "start_point": "台北車站",
                    "end_point": "none",
                    "transport_mode": "driving",
                    "distance_threshold": 30,
                    "breakfast_time": "none",
                    "lunch_time": "12:00",
                    "dinner_time": "18:00",
                    "budget": "none",
                    "date": "12-25"
                }
            >>> TripValidator.validate_trip_requirement(req)
        """
        # 檢查必要欄位
        required_fields = {
            'start_time', 'end_time', 'start_point', 'transport_mode',
            'distance_threshold'
        }
        missing = required_fields - set(requirement.keys())
        if missing:
            raise ValidationError(f"缺少必要欄位：{missing}")

        # 驗證時間格式和順序
        for key in ['start_time', 'end_time']:
            if not cls.validate_time_string(requirement[key]):
                raise ValidationError(f"時間格式錯誤：{requirement[key]}", key)

        start = datetime.strptime(requirement['start_time'], '%H:%M')
        end = datetime.strptime(requirement['end_time'], '%H:%M')
        if start >= end:
            raise ValidationError("結束時間必須晚於開始時間", "time_range")

        # 驗證用餐時間格式
        for meal in ['breakfast_time', 'lunch_time', 'dinner_time']:
            if meal in requirement:
                time_str = requirement[meal]
                if time_str != "none" and not cls.validate_time_string(time_str):
                    raise ValidationError(f"用餐時間格式錯誤：{time_str}", meal)

        # 驗證日期格式
        if 'date' in requirement:
            date_str = requirement['date']
            if not cls.validate_date_string(date_str):
                raise ValidationError(f"日期格式錯誤：{date_str}", "date")

        # 驗證交通方式
        cls.validate_transport_mode(requirement['transport_mode'])

        # 驗證距離限制
        try:
            distance = float(requirement['distance_threshold'])
            if distance <= 0:
                raise ValidationError("距離限制必須大於0", "distance_threshold")
        except (TypeError, ValueError):
            raise ValidationError("距離限制必須為數字", "distance_threshold")

        # 驗證預算格式
        if 'budget' in requirement:
            budget = requirement['budget']
            if budget != "none":
                try:
                    budget_value = int(budget)
                    if budget_value <= 0:
                        raise ValidationError("預算必須大於0", "budget")
                except (TypeError, ValueError):
                    raise ValidationError("預算必須為整數或 'none'", "budget")

    @classmethod
    def validate_transport_mode(cls, mode: str) -> None:
        """驗證交通方式

        輸入:
            mode: 交通方式字串
                 有效值: transit, driving, walking, bicycling

        異常:
            ValidationError: 無效的交通方式

        使用範例:
            >>> TripValidator.validate_transport_mode("driving")
            >>> TripValidator.validate_transport_mode("flying")  # 會拋出錯誤
        """
        if mode not in cls.VALID_TRANSPORT_MODES:
            raise ValidationError(f"不支援的交通方式：{mode}", "transport_mode")

    @classmethod
    def set_default_requirement(cls, requirement: Dict) -> Dict:
        """設定預設的行程需求值

        輸入:
            requirement: Dict, 原始需求字典
                        可能包含部分設定值

        回傳:
            Dict: 包含所有必要欄位的完整需求字典

        使用範例:
            >>> req = {"start_time": "10:00"}
            >>> complete_req = TripValidator.set_default_requirement(req)
            # 會包含所有預設值，包括明天的日期
        """
        # 計算明天的日期
        tomorrow = datetime.now() + timedelta(days=1)
        default_date = tomorrow.strftime('%m-%d')  # 格式化為 MM-DD

        # 預設值定義
        defaults = {
            "start_time": "09:00",        # 預設早上9點開始
            "end_time": "21:00",          # 預設晚上9點結束
            "start_point": "台北車站",     # 預設起點
            "end_point": "none",          # 預設終點(同起點)
            "transport_mode": "driving",   # 預設開車
            "transport_mode_display": "開車",  # 顯示用
            "distance_threshold": 30,      # 預設最大30公里
            "breakfast_time": "none",      # 預設不安排早餐
            "lunch_time": "12:00",        # 預設中午12點午餐
            "dinner_time": "18:00",       # 預設晚上6點晚餐
            "budget": "none",             # 預設無預算限制
            "date": default_date          # 預設為明天日期
        }

        # 其他邏輯保持不變
        result = defaults.copy()
        if requirement:
            result.update(
                {k: v for k, v in requirement.items() if v is not None})

        # 設定交通方式顯示文字
        if requirement and requirement.get('transport_mode'):
            result['transport_mode_display'] = {
                'transit': '大眾運輸',
                'driving': '開車',
                'walking': '步行',
                'bicycling': '騎車'
            }.get(requirement['transport_mode'], requirement['transport_mode'])

        return result

    @classmethod
    def convert_coordinates(cls, coord_str: str) -> Optional[Dict[str, float]]:
        """轉換座標字串為經緯度字典
        
        輸入:
            coord_str: 座標字串，格式：
                      "lat,lon" 或 "lat, lon"
                
        回傳:
            Dict: {'lat': float, 'lon': float} 或 None
            
        使用範例:
            >>> TripValidator.convert_coordinates("25.0478, 121.5170")
            {'lat': 25.0478, 'lon': 121.5170}
        """
        if not coord_str:
            return None

        try:
            # 清理並分割座標
            parts = coord_str.replace(' ', '').split(',')
            if len(parts) != 2:
                return None

            lat = float(parts[0])
            lon = float(parts[1])

            # 驗證座標範圍
            if not cls.validate_coordinates(lat, lon):
                return None

            return {'lat': lat, 'lon': lon}
        except (ValueError, TypeError):
            return None

    @classmethod
    def format_business_hours(cls, hours: Dict) -> Dict:
        """格式化營業時間，確保格式一致
        
        輸入:
            hours: 原始營業時間字典
                
        回傳:
            Dict: 標準格式的營業時間字典
            
        使用範例:
            >>> hours = {1: [{'start': '09:00', 'end': '17:00'}]}
            >>> formatted = TripValidator.format_business_hours(hours)
        """
        formatted = {}
        for day in range(1, 8):
            # 如果沒有設定該天，使用預設24小時
            if day not in hours or hours[day] is None:
                formatted[day] = cls.DEFAULT_HOURS[day]
            else:
                slots = hours[day]
                # 處理空列表或 None 值
                if not slots or slots == [None]:
                    formatted[day] = cls.DEFAULT_HOURS[day]
                else:
                    formatted[day] = slots

        return formatted