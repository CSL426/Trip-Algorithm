# src/core/TripPlanner.py

# fmt: off
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any

# 將專案根目錄加入到 Python 路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

# 使用絕對導入
from src.core.utils import calculate_distance, calculate_travel_time
from src.core.TripNode import convert_itinerary_to_trip_plan
from src.core.planners.advanced_planner import AdvancedTripPlanner
from src.core.planners.business_hours import BusinessHours
# fmt: on


class TripPlanner:
    def __init__(self):
        self.planner = None

    def plan(self, locations, **kwargs):
        print("規劃參數：", kwargs)  # 除錯用
        self.planner = AdvancedTripPlanner(**kwargs)
        self.planner.initialize_locations(locations)
        return self.planner.plan()


def evaluate_location_efficiency(location, current_location, travel_time,
                                 remaining_time, current_datetime):
    """評估地點效率"""
    if current_location == location:
        return float('-inf')

    distance = calculate_distance(
        current_location['lat'], current_location['lon'],
        location['lat'], location['lon']
    ) if current_location else 0

    stay_duration = location.get('duration', 0)
    safe_distance = max(distance, 0.1)
    safe_travel_time = max(travel_time, 0.1)

    efficiency = stay_duration / (safe_distance * safe_travel_time)

    # 用餐時間調整
    hours_handler = BusinessHours(location['hours'])
    is_lunch_time = current_datetime.hour in [11, 12, 13]
    is_dinner_time = current_datetime.hour in [17, 18]

    if location.get('label') in ['餐廳', '小吃', '夜市']:
        if is_lunch_time or is_dinner_time:
            efficiency *= 2.0
        else:
            efficiency *= 0.3
    elif is_lunch_time or is_dinner_time:
        efficiency *= 0.5

    # 交通時間調整
    if travel_time > 45:
        efficiency *= 0.5
    elif travel_time > 30:
        efficiency *= 0.7

    # 營業時間檢查
    if not hours_handler.is_open_at(current_datetime):
        return float('-inf')

    return efficiency


def get_dinner_location(locations, current_location, current_time):
    """尋找適合的晚餐地點"""
    dinner_spots = []
    for loc in locations:
        if loc.get('label') in ['餐廳', '小吃', '夜市']:
            travel_details = calculate_travel_time(
                current_location, loc, 'transit')
            travel_time = travel_details['time'].total_seconds() / 60
            arrival_time = current_time + timedelta(minutes=travel_time)

            hours_handler = BusinessHours(loc['hours'])
            if hours_handler.is_open_at(arrival_time):
                dinner_spots.append({
                    'location': loc,
                    'travel_time': travel_time,
                    'travel_details': travel_details,
                    'arrival_time': arrival_time
                })


def should_end_early(location, current_time):
    """判斷是否應該提前結束當前景點"""
    hours_handler = BusinessHours(location['hours'])
    return (location.get('label') in ['景點', '公園'] and
            hours_handler.is_open_at(current_time) and
            current_time.hour >= 16)


def main():
    import time
    from src.core.test_data import TEST_LOCATIONS, TEST_CUSTOM_START

    total_start_time = time.time()

    planner = TripPlanner()
    itinerary = planner.plan(
        locations=TEST_LOCATIONS,
        start_time='08:00',
        end_time='18:00',
        travel_mode='driving',
        custom_start=TEST_CUSTOM_START,
        custom_end=TEST_CUSTOM_START
    )

    trip_plan = convert_itinerary_to_trip_plan(itinerary)
    trip_plan.print_itinerary()

    total_execution_time = time.time() - total_start_time
    print(f"\n總執行時間：{total_execution_time:.2f}秒")


if __name__ == "__main__":
    main()
