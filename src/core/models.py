from typing import Optional
from pydantic import BaseModel, Field
from typing import List, Dict

class Location(BaseModel):
    name: str
    lat: float
    lon: float
    rating: Optional[float] = None
    duration: int
    label: str
    hours: Dict[int, List[Dict[str, str]]]

    class Config:
        json_schema_extra = {
            "example": {
                "name": "台北101",
                "rating": 4.6,
                "lat": 25.0339808,
                "lon": 121.561964,
                "duration": 150,
                "label": "景點",
                "hours": "09:00 - 22:00"
            }
        }


def validate_locations(locations_data: list[dict]) -> list[Location]:
    """驗證並轉換location資料"""
    return [Location(**location) for location in locations_data]
