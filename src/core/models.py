# src/core/test_models.py
from typing import List
from pydantic import BaseModel
import re
from src.config.config import GOOGLE_MAPS_API_KEY
import requests

# 預設起訖點資訊
DEFAULT_TAIPEI_STATION = {
    "name": "台北車站",
    "lat": 25.0476133,
    "lon": 121.5173835,
    "rating": 4.5,
    "duration_min": 0,
    "label": "交通樞紐",
    "hours": ["00:00-23:59"],
    "url": ""
}


class PlaceInfo(BaseModel):
    """單一景點的詳細資訊

    必填欄位:
        name: 地點名稱
        lat: 緯度
        lon: 經度

    選填欄位（有預設值）:
        rating: 評分 (0-5分)
        duration_min: 建議停留時間
        label: 地點類型
        hours: 營業時間列表
        url: 網址
    """
    name: str
    lat: float
    lon: float
    rating: float = 0.0
    duration_min: int = 60
    label: str = "景點"
    hours: List[str] = []
    url: str = ""


class StartEndPoint(BaseModel):
    """起訖點資訊，預設為台北車站

    可用方法:
        parse_input: 解析輸入的地點資訊（地點名稱或經緯度）
    """
    name: str = DEFAULT_TAIPEI_STATION["name"]
    lat: float = DEFAULT_TAIPEI_STATION["lat"]
    lon: float = DEFAULT_TAIPEI_STATION["lon"]
    rating: float = DEFAULT_TAIPEI_STATION["rating"]
    duration_min: int = DEFAULT_TAIPEI_STATION["duration_min"]
    label: str = DEFAULT_TAIPEI_STATION["label"]
    hours: List[str] = DEFAULT_TAIPEI_STATION["hours"]
    url: str = DEFAULT_TAIPEI_STATION["url"]

    @classmethod
    def parse_input(cls, location_input: str):
        """處理輸入的地點資訊

        輸入:
            location_input: 地點名稱或經緯度字串
            例如: "台北車站" 或 "25.0476133,121.5173835"

        輸出:
            StartEndPoint: 包含完整地點資訊的物件
        """
        coord_pattern = r'^[-+]?([1-8]?\d(\.\d+)?|90(\.0+)?),\s*[-+]?(180(\.0+)?|((1[0-7]\d)|([1-9]?\d))(\.\d+)?)$'

        if re.match(coord_pattern, location_input):
            lat, lon = map(float, location_input.split(','))
            place_info = get_place_info_by_coordinates(lat, lon)
            return cls(**place_info)
        else:
            place_info = get_place_info_by_name(location_input)
            return cls(**place_info)


class TripRequirement(BaseModel):
    """使用者的行程需求

    必填欄位: 無（全都有預設值）
    """
    出發時間: str = "09:00"          # 格式: HH:MM
    結束時間: str = "18:00"          # 格式: HH:MM
    出發地點: StartEndPoint = StartEndPoint()
    結束地點: StartEndPoint = StartEndPoint()
    交通方式: str = "大眾運輸"        # 可選: 大眾運輸/開車/騎自行車/步行
    可接受距離門檻: int = 30          # 單位: 公里
    早餐時間: str = "none"           # 格式: HH:MM 或 none
    午餐時間: str = "12:00"          # 格式: HH:MM 或 none
    晚餐時間: str = "18:00"          # 格式: HH:MM 或 none
    預算: int = 0                    # 0 表示無預算限制
    出發日: str = "none"             # 格式: MM-DD 或 none


class Transport(BaseModel):
    """交通資訊"""
    mode: str = "大眾運輸"           # 交通方式
    time: int = 20                    # 交通時間（分鐘）
    period: str = ""                 # 交通時段（HH:MM-HH:MM）


class ItinerarySpot(BaseModel):
    """行程中的單一地點"""
    name: str = ""                   # 地點名稱
    start_time: str = ""             # 到達時間（HH:MM）
    end_time: str = ""               # 離開時間（HH:MM）
    duration: int = 0                # 停留時間（分鐘）
    hours: str = ""                  # 營業時間（HH:MM-HH:MM）
    transport: Transport = Transport()  # 交通資訊


def get_place_info_by_coordinates(lat: float, lon: float) -> dict:
    """
    根據經緯度取得地點資訊

    輸入：
        lat: 緯度
        lon: 經度
    輸出：
        回傳字典包含:
        - name: 地點名稱，優先順序：建築物 > 地標 > 路名
        - lat: 緯度
        - lon: 經度
    """
    try:
        # 1. Places API Nearby Search
        nearby_params = {
            "location": f"{lat},{lon}",
            "rankby": "distance",  # 改用距離排序
            "language": "zh-TW",
            "key": GOOGLE_MAPS_API_KEY
        }

        response = requests.get(
            "https://maps.googleapis.com/maps/api/place/nearbysearch/json",
            params=nearby_params
        )

        if response.status_code == 200:
            results = response.json().get("results", [])

            if results:
                # 過濾掉行政區
                valid_results = [r for r in results if not (
                    'locality' in r.get('types', []) or
                    'administrative_area' in r.get('types', []) or
                    'political' in r.get('types', [])
                )]

                if valid_results:
                    result = valid_results[0]  # 取最近的有效結果
                    name = result.get("name")
                    vicinity = result.get("vicinity")
                    if vicinity:
                        return {
                            "name": f"{name} ({vicinity})",
                            "lat": lat,
                            "lon": lon
                        }
                    return {
                        "name": name,
                        "lat": lat,
                        "lon": lon
                    }

        # 2. 如果找不到，用 Geocoding API
        geocode_params = {
            "latlng": f"{lat},{lon}",
            "language": "zh-TW",
            "key": GOOGLE_MAPS_API_KEY
        }

        response = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params=geocode_params
        )

        if response.status_code == 200:
            results = response.json().get("results", [])
            if results:
                return {
                    "name": results[0].get("formatted_address"),
                    "lat": lat,
                    "lon": lon
                }

    except Exception as e:
        print(f"API 錯誤: {str(e)}")

    return {
        "name": f"未命名地點({lat}, {lon})",
        "lat": lat,
        "lon": lon
    }


def get_place_info_by_name(name: str) -> dict:
    """用地點名稱查詢資訊

    輸入:
        name: 地點名稱

    輸出:
        dict: 只包含必要的地點資訊（名稱和經緯度）
    """
    try:
        response = requests.get(
            "https://maps.googleapis.com/maps/api/place/textsearch/json",
            params={
                "query": name,
                "language": "zh-TW",
                "key": GOOGLE_MAPS_API_KEY,
            }
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("results"):
                place = data["results"][0]
                return {
                    "name": place.get("name", name),
                    "lat": place["geometry"]["location"].get("lat", DEFAULT_TAIPEI_STATION["lat"]),
                    "lon": place["geometry"]["location"].get("lng", DEFAULT_TAIPEI_STATION["lon"])
                }

    except Exception as e:
        print(f"Google Places API 錯誤: {str(e)}")

    # API 失敗時回傳預設資訊
    return {
        "name": name,
        "lat": DEFAULT_TAIPEI_STATION["lat"],
        "lon": DEFAULT_TAIPEI_STATION["lon"]
    }


def validate_requirements(data: dict) -> TripRequirement:
    """驗證使用者需求資料"""
    return TripRequirement(**data)


def validate_itinerary(data: List[dict]) -> List[ItinerarySpot]:
    """驗證行程輸出格式"""
    return [ItinerarySpot(**spot) for spot in data]
