# src/core/utils/validator_core.py

from src.core.utils.geo_core import GeoCore
from src.core.utils.time_core import TimeCore


class ValidatorCore:
    """基礎的驗證邏輯"""

    @classmethod
    def validate_place_fields(cls, data: dict) -> None:
        """驗證地點基本欄位

        輸入:
            data: 地點資料字典

        異常:
            ValueError: 缺少必要欄位或格式錯誤
        """
        required = {'name', 'lat', 'lon', 'duration', 'label', 'period'}
        missing = required - set(data.keys())
        if missing:
            raise ValueError(f"缺少必要欄位：{missing}")

        # 使用 GeoCore 驗證座標
        GeoCore.validate_coordinate(data['lat'], data['lon'])

        # 使用 TimeCore 驗證營業時間
        if 'hours' in data:
            cls.validate_business_hours(data['hours'])

    @classmethod
    def validate_business_hours(cls, hours: dict) -> None:
        """驗證營業時間格式"""
        for day, slots in hours.items():
            if not isinstance(slots, list):
                raise ValueError(f"時段必須是列表：{slots}")

            for slot in slots:
                if slot is None:
                    continue

                if not isinstance(slot, dict):
                    raise ValueError(f"時段格式錯誤：{slot}")

                # 驗證開始和結束時間格式
                if not TimeCore.validate_time_str(slot['start']):
                    raise ValueError(f"開始時間格式錯誤：{slot['start']}")
                if not TimeCore.validate_time_str(slot['end']):
                    raise ValueError(f"結束時間格式錯誤：{slot['end']}")

                # 驗證時間順序
                try:
                    TimeCore.parse_time_range(slot['start'], slot['end'])
                except ValueError as e:
                    raise ValueError(f"時間範圍錯誤：{e}")
