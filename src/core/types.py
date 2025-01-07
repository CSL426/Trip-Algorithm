# src/core/types.py
from typing import TypedDict, List, Dict, Optional


class LocationDict(TypedDict):
    """景點資料的格式定義

    當使用者傳入景點資料時，應該符合這個格式
    """
    name: str                # 景點名稱
    lat: float              # 緯度
    lon: float              # 經度
    duration: int           # 建議停留時間(分鐘)
    label: str              # 景點類型
    period: str             # 適合的時段
    hours: Dict[int, List[Dict[str, str]]]  # 營業時間


class PlanRequirement(TypedDict, total=False):
    """行程規劃需求的格式定義

    使用 total=False 表示所有欄位都是選填的
    """
    start_point: Optional[str]    # 起點
    end_point: Optional[str]      # 終點
    start_time: Optional[str]     # 開始時間
    end_time: Optional[str]       # 結束時間
    transport_mode: Optional[str]  # 交通方式
    lunch_time: Optional[str]     # 午餐時間
    dinner_time: Optional[str]    # 晚餐時間
