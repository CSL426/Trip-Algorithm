# src/core/planner/validator.py

from datetime import datetime
from typing import List, Dict, Optional, Union
from src.core.models.place import PlaceDetail
from src.core.models.trip import TripRequirement
from src.core.utils.validator_core import ValidatorCore
from src.core.utils.time_core import TimeCore


class InputValidator:
    """行程規劃輸入驗證器

    負責驗證:
    1. 地點資料的完整性
    2. 行程需求的合理性
    3. 時間格式的正確性
    4. 交通方式的有效性
    """

    # 有效的交通方式
    VALID_TRANSPORT_MODES = {"transit", "driving", "walking", "bicycling"}

    # 預設24小時營業時間
    DEFAULT_HOURS = {i: [{'start': '00:00', 'end': '23:59'}]
                     for i in range(1, 8)}

    def validate_locations(self,
                           locations: List[Union[Dict, PlaceDetail]],
                           custom_start: Optional[Union[Dict,
                                                        PlaceDetail]] = None,
                           custom_end: Optional[Union[Dict,
                                                      PlaceDetail]] = None
                           ) -> List[PlaceDetail]:
        """驗證所有地點資訊

        輸入:
            locations: 地點列表，每個地點需包含:
                - name: 名稱
                - lat/lon: 座標
                - duration: 停留時間
                - label: 分類
                - period: 時段
                - hours: 營業時間
            custom_start: 自訂起點(選填)
            custom_end: 自訂終點(選填)

        回傳:
            List[PlaceDetail]: 驗證後的地點物件列表

        異常:
            ValueError: 資料格式錯誤
        """
        validated = []

        # 驗證一般地點
        for loc in locations:
            if isinstance(loc, Dict):
                self._validate_location_dict(loc)
                if 'duration' in loc and 'duration_min' not in loc:
                    loc['duration_min'] = loc['duration']
                validated.append(PlaceDetail(**loc))
            else:
                validated.append(loc)

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

        return validated

    def validate_requirement(self, requirement: Union[Dict, TripRequirement]) -> TripRequirement:
        """驗證行程需求

        輸入:
            requirement: 行程需求，必須包含:
                - start_time: 開始時間 (HH:MM)
                - end_time: 結束時間 (HH:MM)
                - transport_mode: 交通方式
                - distance_threshold: 距離限制(km)

        回傳:
            TripRequirement: 驗證後的需求物件

        異常:
            ValueError: 資料不完整或格式錯誤
        """
        if isinstance(requirement, TripRequirement):
            return requirement

        # 檢查必要欄位
        required = {
            'start_time', 'end_time', 'transport_mode',
            'start_point', 'end_point', 'distance_threshold'
        }
        missing = required - set(requirement.keys())
        if missing:
            raise ValueError(f"缺少必要欄位：{missing}")

        # 驗證時間格式和順序
        self._validate_time_format(requirement['start_time'])
        self._validate_time_format(requirement['end_time'])

        start = datetime.strptime(requirement['start_time'], '%H:%M')
        end = datetime.strptime(requirement['end_time'], '%H:%M')
        if start >= end:
            raise ValueError("開始時間必須早於結束時間")

        # 驗證交通方式
        self._validate_transport_mode(requirement['transport_mode'])

        # 驗證距離限制
        if not isinstance(requirement['distance_threshold'], (int, float)) or \
           requirement['distance_threshold'] <= 0:
            raise ValueError("距離限制必須是正數")

        return TripRequirement(**requirement)

    def _validate_location_dict(self, location: Dict) -> None:
        """驗證單一地點資料

        輸入:
            location: 地點資料字典

        異常:
            ValueError: 資料格式錯誤
        """
        ValidatorCore.validate_place_fields(location)

        # 設定預設營業時間
        if 'hours' not in location:
            location['hours'] = self.DEFAULT_HOURS.copy()

    def _validate_time_format(self, time_str: str) -> None:
        """驗證時間格式

        輸入:
            time_str: 時間字串 (HH:MM)

        異常:
            ValueError: 格式錯誤
        """
        TimeCore.validate_time_str(time_str)

    def _validate_transport_mode(self, mode: str) -> None:
        """驗證交通方式

        輸入:
            mode: 交通方式

        異常:
            ValueError: 不支援的交通方式
        """
        if mode not in self.VALID_TRANSPORT_MODES:
            raise ValueError(f"不支援的交通方式：{mode}")
