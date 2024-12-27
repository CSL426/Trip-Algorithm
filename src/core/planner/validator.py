# src/core/planner/validator.py

from datetime import datetime
from typing import List, Dict, Optional, Union
from src.core.models.place import PlaceDetail
from src.core.models.trip import TripRequirement


class InputValidator:
    """
    行程規劃輸入驗證器
    負責確保所有輸入資料的正確性和完整性

    主要功能：
    1. 驗證地點資料的格式和內容
    2. 檢查時間設定的合理性
    3. 確認交通方式的有效性
    4. 驗證行程需求的完整性
    """

    VALID_TRANSPORT_MODES = {"transit", "driving", "walking", "bicycling"}
    DEFAULT_HOURS = {i: [{'start': '00:00', 'end': '23:59'}]
                     for i in range(1, 8)}

    def validate_locations(self,
                           locations: List[Union[Dict, PlaceDetail]],
                           custom_start: Optional[Union[Dict,
                                                        PlaceDetail]] = None,
                           custom_end: Optional[Union[Dict,
                                                      PlaceDetail]] = None
                           ) -> List[PlaceDetail]:
        """
        驗證所有地點資訊的正確性

        輸入參數：
            locations: 地點列表，每個地點可以是字典或PlaceDetail物件
            custom_start: 自訂起點（選填）
            custom_end: 自訂終點（選填）

        回傳：
            List[PlaceDetail]: 驗證後的地點物件列表

        異常：
            ValueError: 當資料格式不正確時拋出
        """
        validated_locations = []

        # 驗證一般地點
        for loc in locations:
            if isinstance(loc, PlaceDetail):
                validated_locations.append(loc)
            else:
                self._validate_location_dict(loc)
                if 'duration' in loc and 'duration_min' not in loc:
                    loc['duration_min'] = loc['duration']
                validated_locations.append(PlaceDetail(**loc))

        # 驗證自訂起點
        if custom_start:
            if not isinstance(custom_start, (Dict, PlaceDetail)):
                raise ValueError("自訂起點格式錯誤")
            if isinstance(custom_start, Dict):
                self._validate_location_dict(custom_start)

        # 驗證自訂終點
        if custom_end:
            if not isinstance(custom_end, (Dict, PlaceDetail)):
                raise ValueError("自訂終點格式錯誤")
            if isinstance(custom_end, Dict):
                self._validate_location_dict(custom_end)

        return validated_locations

    def validate_requirement(self, requirement: Union[Dict, TripRequirement]) -> TripRequirement:
        """
        驗證行程需求的正確性

        輸入參數：
            requirement: 行程需求（字典或TripRequirement物件）

        回傳：
            TripRequirement: 驗證後的需求物件

        異常：
            ValueError: 當需求資料格式不正確時拋出
        """
        if isinstance(requirement, TripRequirement):
            return requirement

        required_fields = {
            'start_time', 'end_time', 'transport_mode',
            'start_point', 'end_point', 'distance_threshold'
        }

        # 檢查必要欄位
        missing_fields = required_fields - set(requirement.keys())
        if missing_fields:
            raise ValueError(f"缺少必要欄位：{', '.join(missing_fields)}")

        # 驗證時間格式
        self._validate_time_format(requirement['start_time'])
        self._validate_time_format(requirement['end_time'])

        # 驗證開始時間早於結束時間
        start = datetime.strptime(requirement['start_time'], '%H:%M')
        end = datetime.strptime(requirement['end_time'], '%H:%M')
        if start >= end:
            raise ValueError("開始時間必須早於結束時間")

        # 驗證交通方式
        if requirement['transport_mode'] not in self.VALID_TRANSPORT_MODES:
            raise ValueError(f"不支援的交通方式：{requirement['transport_mode']}")

        # 驗證距離閾值
        if not isinstance(requirement['distance_threshold'], (int, float)) or \
           requirement['distance_threshold'] <= 0:
            raise ValueError("距離閾值必須是正數")

        return TripRequirement(**requirement)

    def _validate_location_dict(self, location: Dict) -> None:
        """
        驗證單一地點資料的正確性

        輸入參數：
            location: 地點資料字典

        異常：
            ValueError: 當資料格式不正確時拋出
        """
        required_fields = {'name', 'lat', 'lon'}
        missing_fields = required_fields - set(location.keys())
        if missing_fields:
            raise ValueError(f"地點資料缺少必要欄位：{', '.join(missing_fields)}")

        # 驗證經緯度範圍
        if not (-90 <= location['lat'] <= 90):
            raise ValueError(f"緯度超出範圍：{location['lat']}")
        if not (-180 <= location['lon'] <= 180):
            raise ValueError(f"經度超出範圍：{location['lon']}")

        # 確保有營業時間資料
        if 'hours' not in location:
            location['hours'] = self.DEFAULT_HOURS.copy()

    def _validate_time_format(self, time_str: str) -> None:
        """
        驗證時間字串格式的正確性

        輸入參數：
            time_str: 時間字串（HH:MM格式）

        異常：
            ValueError: 當時間格式不正確時拋出
        """
        try:
            datetime.strptime(time_str, '%H:%M')
        except ValueError:
            raise ValueError(f"時間格式錯誤：{time_str}，應為HH:MM格式")
