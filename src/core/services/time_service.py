# src/core/services/time_service.py

from datetime import datetime, time, timedelta
from typing import Any, Dict, List, Union, Tuple, Optional


class TimeService:
    """時間服務類別

    這個服務負責處理所有與時間相關的操作，包括：
    1. 時間格式的驗證和轉換
    2. 時間區間的判斷
    3. 營業時間的處理
    4. 用餐時段的管理

    設計考量：
    - 所有時間相關的邏輯都應該集中在這裡
    - 提供統一的時間格式標準
    - 支援跨日期的時間處理（如夜市營業時間）
    - 考慮不同時區的可能性（預留擴充空間）
    """

    # 系統使用的時間格式常數
    TIME_FORMAT = '%H:%M'
    DATE_FORMAT = '%Y-%m-%d'

    # 預設的用餐時間區間（分鐘）
    MEAL_TIME_WINDOW = 60

    def __init__(self, lunch_time: Optional[str] = None,
                 dinner_time: Optional[str] = None,
                 time_zone: str = 'Asia/Taipei'):
        """初始化時間服務

        參數:
            lunch_time: 午餐時間，格式為 HH:MM
            dinner_time: 晚餐時間，格式為 HH:MM
            time_zone: 時區名稱，預設為台北時間
        """
        # 設定用餐時間
        self.lunch_time = self._parse_time(lunch_time) if lunch_time else None
        self.dinner_time = self._parse_time(
            dinner_time) if dinner_time else None
        self.time_zone = time_zone

    def _parse_time(self, time_str: str) -> Optional[time]:
        """解析時間字串為 time 物件

        這是內部使用的方法，用於統一時間字串的解析邏輯。
        支援 24 小時制的時間格式（HH:MM）。

        參數:
            time_str: HH:MM 格式的時間字串

        回傳:
            time: 解析後的 time 物件，如果輸入無效則回傳 None
        """
        if not time_str:
            return None

        try:
            parsed = datetime.strptime(time_str, self.TIME_FORMAT)
            return parsed.time()
        except ValueError:
            return None

    def validate_time_string(self, time_str: str) -> bool:
        """驗證時間字串格式是否正確

        支援兩種情況：
        1. HH:MM 格式的 24 小時制時間
        2. 特殊值 "none"（表示未設定時間）

        參數:
            time_str: 要驗證的時間字串

        回傳:
            bool: True 表示格式正確，False 表示格式錯誤

        使用範例:
            >>> time_service.validate_time_string("09:30")  # 回傳 True
            >>> time_service.validate_time_string("25:00")  # 回傳 False
            >>> time_service.validate_time_string("none")   # 回傳 True
        """
        if time_str == "none":
            return True

        try:
            datetime.strptime(time_str, self.TIME_FORMAT)
            return True
        except ValueError:
            return False

    def validate_time_range(self, start_time: str, end_time: str,
                            allow_overnight: bool = False) -> bool:
        """驗證時間範圍的有效性

        檢查開始時間和結束時間是否構成有效的時間範圍。
        可以處理跨日的情況（如夜市營業時間）。

        參數:
            start_time: 開始時間（HH:MM 格式）
            end_time: 結束時間（HH:MM 格式）
            allow_overnight: 是否允許跨日，預設為 False

        回傳:
            bool: True 表示有效的時間範圍

        使用範例:
            >>> time_service.validate_time_range("09:00", "17:00")          # 一般情況
            >>> time_service.validate_time_range("22:00", "02:00", True)    # 跨日營業
        """
        if not all(self.validate_time_string(t) for t in [start_time, end_time]):
            return False

        start = datetime.strptime(start_time, self.TIME_FORMAT).time()
        end = datetime.strptime(end_time, self.TIME_FORMAT).time()

        if allow_overnight:
            return True  # 允許跨日的情況都視為有效

        return start < end

    def get_time_period(self, check_time: Union[datetime, time, str]) -> str:
        """判斷指定時間屬於哪個時段

        將一天劃分為五個時段：
        - morning: 早上（開始到午餐前）
        - lunch: 午餐時段
        - afternoon: 下午（午餐後到晚餐前）
        - dinner: 晚餐時段
        - night: 晚上（晚餐後）

        參數:
            check_time: 要判斷的時間，可以是：
                     - datetime 物件
                     - time 物件
                     - HH:MM 格式的時間字串

        回傳:
            str: 時段名稱

        使用範例:
            >>> now = datetime.now()
            >>> time_service.get_time_period(now)
            >>> time_service.get_time_period("12:30")
        """
        # 統一轉換為 time 物件
        if isinstance(check_time, str):
            time_obj = datetime.strptime(check_time, self.TIME_FORMAT).time()
        elif isinstance(check_time, datetime):
            time_obj = check_time.time()
        else:
            time_obj = check_time

        # 根據用餐時間判斷時段
        if self.lunch_time:
            lunch_start = self._add_minutes_to_time(
                self.lunch_time, -self.MEAL_TIME_WINDOW)
            lunch_end = self._add_minutes_to_time(
                self.lunch_time, self.MEAL_TIME_WINDOW)

            if time_obj < lunch_start:
                return 'morning'
            elif lunch_start <= time_obj <= lunch_end:
                return 'lunch'

        if self.dinner_time:
            dinner_start = self._add_minutes_to_time(
                self.dinner_time, -self.MEAL_TIME_WINDOW)
            dinner_end = self._add_minutes_to_time(
                self.dinner_time, self.MEAL_TIME_WINDOW)

            if (self.lunch_time and time_obj > self._add_minutes_to_time(self.lunch_time, self.MEAL_TIME_WINDOW)):
                if time_obj < dinner_start:
                    return 'afternoon'
                elif dinner_start <= time_obj <= dinner_end:
                    return 'dinner'
                else:
                    return 'night'

        # 如果沒有設定用餐時間，根據時間判斷
        hour = time_obj.hour
        if hour < 11:
            return 'morning'
        elif hour < 14:
            return 'lunch'
        elif hour < 17:
            return 'afternoon'
        elif hour < 20:
            return 'dinner'
        else:
            return 'night'

    def _add_minutes_to_time(self, base_time: time, minutes: int) -> time:
        """將分鐘數加到時間上

        這個內部方法用來處理時間的加減運算。它能正確處理跨日的情況，
        例如當我們需要計算午夜前後的時間區間。

        參數:
            base_time: 基準時間
            minutes: 要增加的分鐘數（可以是負數）

        回傳:
            time: 計算後的新時間
        """
        # 先轉換為 datetime 以便計算
        base_dt = datetime.combine(datetime.today(), base_time)
        # 進行時間計算
        result_dt = base_dt + timedelta(minutes=minutes)
        # 取出時間部分
        return result_dt.time()

    def is_business_hours(self,
                          current_time: Union[datetime, str],
                          hours: Dict[int, List[Dict[str, str]]],
                          duration_minutes: int = 0) -> Tuple[bool, Optional[int]]:
        """檢查指定時間是否在營業時間內

        這個方法不只確認當前時間是否在營業時間內，還會考慮停留時間，
        確保整個遊玩時段都在營業時間內。它也能處理特殊的營業時間安排，
        例如午休時間或是分段營業。

        參數:
            current_time: 當前時間（datetime物件或HH:MM格式字串）
            hours: 營業時間設定，格式為：
                  {
                      1: [{'start': '09:00', 'end': '17:00'}],  # 週一
                      2: [{'start': '09:00', 'end': '17:00'}],  # 週二
                      ...
                  }
            duration_minutes: 預計停留時間（分鐘）

        回傳:
            Tuple[bool, Optional[int]]: 
            - 第一個值表示是否在營業時間內
            - 第二個值表示可停留時間（分鐘），若不在營業時間內則為None
        """
        # 轉換時間格式
        if isinstance(current_time, str):
            current_dt = datetime.strptime(current_time, self.TIME_FORMAT)
        else:
            current_dt = current_time

        weekday = current_dt.isoweekday()  # 1-7 代表週一到週日

        # 檢查是否有該天的營業時間設定
        if weekday not in hours or not hours[weekday]:
            return False, None

        # 取得當前時間的time物件
        current_time = current_dt.time()

        # 檢查每個營業時段
        for slot in hours[weekday]:
            if slot is None:
                continue

            start = datetime.strptime(slot['start'], self.TIME_FORMAT).time()
            end = datetime.strptime(slot['end'], self.TIME_FORMAT).time()

            # 處理跨日營業的情況
            is_overnight = end < start

            if is_overnight:
                # 跨日營業的邏輯
                if start <= current_time or current_time <= end:
                    if duration_minutes > 0:
                        # 計算剩餘可停留時間
                        if current_time >= start:
                            # 計算到午夜的時間加上隔天到結束的時間
                            remaining = self._calculate_overnight_duration(
                                current_time, end)
                        else:
                            # 計算到結束時間的分鐘數
                            remaining = self._calculate_duration(
                                current_time, end)

                        if remaining >= duration_minutes:
                            return True, duration_minutes
                        else:
                            return True, remaining
                    return True, None
            else:
                # 一般營業時間的邏輯
                if start <= current_time <= end:
                    if duration_minutes > 0:
                        remaining = self._calculate_duration(current_time, end)
                        if remaining >= duration_minutes:
                            return True, duration_minutes
                        else:
                            return True, remaining
                    return True, None

        return False, None

    def _calculate_duration(self, start: time, end: time) -> int:
        """計算兩個時間點之間的分鐘數

        用於計算一般情況下（非跨日）的時間差。

        參數:
            start: 開始時間
            end: 結束時間

        回傳:
            int: 分鐘數
        """
        start_dt = datetime.combine(datetime.today(), start)
        end_dt = datetime.combine(datetime.today(), end)
        return int((end_dt - start_dt).total_seconds() / 60)

    def _calculate_overnight_duration(self, start: time, end: time) -> int:
        """計算跨日時段的持續時間

        處理營業時間跨越午夜的特殊情況，例如從晚上10點營業到隔天早上5點。

        參數:
            start: 開始時間
            end: 結束時間（隔天）

        回傳:
            int: 分鐘數
        """
        start_dt = datetime.combine(datetime.today(), start)
        end_dt = datetime.combine(datetime.today() + timedelta(days=1), end)
        return int((end_dt - start_dt).total_seconds() / 60)

    def check_time_overlap(self,
                           interval1: Tuple[time, time],
                           interval2: Tuple[time, time],
                           allow_overnight: bool = False) -> bool:
        """檢查兩個時間區間是否重疊

        這個方法可以判斷兩個時間區間是否有重疊的部分，例如用來檢查兩個行程是否衝突。
        它能處理一般的時間區間，也支援跨日的情況（如夜市營業時間）。

        參數:
            interval1: 第一個時間區間 (開始時間, 結束時間)
            interval2: 第二個時間區間 (開始時間, 結束時間)
            allow_overnight: 是否允許跨日判斷，預設為 False

        回傳:
            bool: True 表示有重疊，False 表示無重疊

        使用範例:
            >>> # 檢查兩個白天的時段
            >>> time_service.check_time_overlap(
                    (time(9, 0), time(11, 0)),
                    (time(10, 0), time(12, 0))
                )  # 回傳 True

            >>> # 檢查跨日的營業時間
            >>> time_service.check_time_overlap(
                    (time(22, 0), time(2, 0)),
                    (time(23, 0), time(3, 0)),
                    allow_overnight=True
                )  # 回傳 True
        """
        start1, end1 = interval1
        start2, end2 = interval2

        if allow_overnight:
            # 處理跨日情況的複雜邏輯
            if end1 < start1:  # 第一個區間跨日
                return not (end1 < start2 and end2 < start1)
            elif end2 < start2:  # 第二個區間跨日
                return not (end2 < start1 and end1 < start2)
            else:  # 都不跨日
                return not (end1 <= start2 or end2 <= start1)
        else:
            # 一般情況的簡單判斷
            return not (end1 <= start2 or end2 <= start1)

    def find_next_available_time(self,
                                 current_time: Union[datetime, str],
                                 business_hours: Dict[int, List[Dict[str, str]]],
                                 duration_minutes: int = 0) -> Optional[Dict[str, Any]]:
        """尋找下一個可用的營業時間

        當目前時間不在營業時間內時，這個方法會幫助找出最近的可用時段。
        它會考慮預計停留時間，確保找到的時段足夠容納整個行程。

        參數:
            current_time: 當前時間（datetime物件或HH:MM格式字串）
            business_hours: 營業時間設定
            duration_minutes: 需要的時間長度（分鐘）

        回傳:
            Dict: 包含以下資訊的字典：
                {
                    'day': int,          # 星期幾（1-7）
                    'start': str,        # 開始時間（HH:MM）
                    'end': str,          # 結束時間（HH:MM）
                    'wait_minutes': int   # 需要等待的分鐘數
                }
            如果找不到合適的時段則回傳 None

        使用範例:
            >>> next_time = time_service.find_next_available_time(
                    "22:00",
                    business_hours,
                    duration_minutes=60
                )
            >>> if next_time:
            >>>     print(f"下一個可用時段：{next_time['start']}")
        """
        # 統一時間格式
        if isinstance(current_time, str):
            current_dt = datetime.strptime(current_time, self.TIME_FORMAT)
        else:
            current_dt = current_time

        # 檢查未來7天的時間
        for day_offset in range(7):
            # 計算要檢查的日期
            check_dt = current_dt + timedelta(days=day_offset)
            weekday = check_dt.isoweekday()

            # 檢查該天是否有營業
            if weekday not in business_hours:
                continue

            slots = business_hours[weekday]
            if not slots:
                continue

            # 檢查每個營業時段
            for slot in slots:
                if slot is None:
                    continue

                start_time = datetime.strptime(
                    slot['start'], self.TIME_FORMAT).time()
                end_time = datetime.strptime(
                    slot['end'], self.TIME_FORMAT).time()

                # 如果是當天，需要考慮現在的時間
                if day_offset == 0:
                    if start_time <= check_dt.time():
                        continue

                # 計算可用時間長度
                available_duration = self._calculate_duration(
                    start_time, end_time)
                if available_duration >= duration_minutes:
                    # 計算需要等待的時間
                    wait_minutes = self._calculate_wait_minutes(
                        current_dt, check_dt, start_time)

                    return {
                        'day': weekday,
                        'start': slot['start'],
                        'end': slot['end'],
                        'wait_minutes': wait_minutes
                    }

        return None

    def _calculate_wait_minutes(self,
                                current_dt: datetime,
                                target_dt: datetime,
                                target_time: time) -> int:
        """計算需要等待的分鐘數

        計算從當前時間到目標時間需要等待的分鐘數。
        這個內部方法支援跨日期的等待時間計算。

        參數:
            current_dt: 當前時間
            target_dt: 目標日期
            target_time: 目標時間

        回傳:
            int: 需要等待的分鐘數
        """
        target_dt = datetime.combine(target_dt.date(), target_time)
        delta = target_dt - current_dt
        return int(delta.total_seconds() / 60)
