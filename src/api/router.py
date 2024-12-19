# src/api/router.py

import os
import sys
from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict
from pydantic import BaseModel

# fmt: off
# 將專案根目錄加入到 Python 路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from src.core.TripPlanner import plan_trip
from src.line.formatter import LineFormatter
# fmt: on

router = APIRouter(prefix="/api", tags=["trip"])


class Location(BaseModel):
    name: str
    rating: float
    lat: float
    lon: float
    duration: int
    label: str
    hours: str


class CustomPoint(BaseModel):
    name: str
    lat: float
    lon: float


class TripRequest(BaseModel):
    locations: List[Location]
    start_time: str = "09:00"
    end_time: str = "21:00"
    travel_mode: str = "transit"
    custom_start: Optional[CustomPoint] = None
    custom_end: Optional[CustomPoint] = None


@router.post("/plan")
async def create_trip_plan(request: TripRequest):
    """
    產生行程規劃並回傳 LINE 格式訊息

    Args:
        request: 包含地點清單和其他設定的請求物件

    Returns:
        dict: 包含行程資訊和 LINE 格式訊息
    """
    try:
        # 轉換地點資料格式
        locations = [location.dict() for location in request.locations]

        # 處理自訂起終點
        custom_start = request.custom_start.dict() if request.custom_start else None
        custom_end = request.custom_end.dict() if request.custom_end else None

        # 產生行程
        itinerary = plan_trip(
            locations=locations,
            start_time=request.start_time,
            end_time=request.end_time,
            travel_mode=request.travel_mode,
            custom_start=custom_start,
            custom_end=custom_end
        )

        # 格式化成 LINE 訊息
        formatter = LineFormatter()
        line_message = formatter.format_trip_to_line_message(itinerary)

        return {
            "status": "success",
            "line_message": line_message,
            "itinerary": itinerary
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get("/healthcheck")
async def healthcheck():
    """健康檢查端點"""
    return {"status": "ok"}
