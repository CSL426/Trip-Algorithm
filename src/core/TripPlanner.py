# src/core/TripPlanner.py

# fmt: off
import os
import sys
from datetime import datetime, timedelta

# 將專案根目錄加入到 Python 路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

# 使用絕對導入
from src.core.utils import calculate_distance, calculate_travel_time, parse_hours  
from src.core.TripNode import convert_itinerary_to_trip_plan  
# fmt: on


def evaluate_location_efficiency(location, current_location, travel_time, remaining_time, current_datetime):
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

    # 基礎效率計算
    efficiency = stay_duration / (safe_distance * safe_travel_time)

    # 用餐時間調整
    is_lunch_time = current_datetime.hour in [11, 12, 13]
    is_dinner_time = current_datetime.hour in [17, 18]

    if location.get('label') in ['餐廳', '小吃', '夜市']:
        if is_lunch_time or is_dinner_time:
            efficiency *= 2
        else:
            efficiency *= 0.3
    elif is_lunch_time or is_dinner_time:
        efficiency *= 0.5

    # 交通時間調整
    if travel_time > 45:
        efficiency *= 0.5
    elif travel_time > 30:
        efficiency *= 0.7

    return efficiency


def get_dinner_location(locations, current_location, current_time):
    """尋找適合的晚餐地點"""
    dinner_spots = []
    for loc in locations:
        if loc.get('label') in ['餐廳', '小吃', '夜市']:
            # 計算到該餐廳的交通時間
            travel_details = calculate_travel_time(
                current_location, loc, 'transit')
            travel_time = travel_details['time'].total_seconds() / 60

            # 計算預計到達時間
            arrival_time = current_time + timedelta(minutes=travel_time)

            # 檢查是否在營業時間內
            hours = loc.get('hours', '24小時開放')
            open_time_str, close_time_str = parse_hours(hours)
            open_time = datetime.strptime(open_time_str, '%H:%M')
            close_time = datetime.strptime(close_time_str, '%H:%M')

            if arrival_time.time() <= close_time.time():
                dinner_spots.append({
                    'location': loc,
                    'travel_time': travel_time,
                    'travel_details': travel_details,
                    'arrival_time': arrival_time
                })

    # 根據交通時間排序，優先選擇較近的地點
    dinner_spots.sort(key=lambda x: x['travel_time'])
    return dinner_spots[0] if dinner_spots else None


def should_end_early(location, current_time):
    """判斷是否應該提前結束當前景點"""
    return (location.get('label') in ['景點', '公園'] and
            '24小時' in location.get('hours', '') and
            current_time.hour >= 16)


def plan_trip(locations, start_time='09:00', end_time='20:00', travel_mode='transit',
              custom_start=None, custom_end=None, distance_threshold=30, efficiency_threshold=0.1):
    """
    智能行程規劃
    Args:
        locations: 景點列表
        start_time: 開始時間 (HH:MM)
        end_time: 結束時間 (HH:MM)
        travel_mode: 交通方式 ('transit', 'driving', 'walking', 'bicycling')
        custom_start: 自定義起點 dict{'name','lat','lon'}
        custom_end: 自定義終點 dict{'name','lat','lon'}
        distance_threshold: 距離閾值（公里）
        efficiency_threshold: 效率閾值
    """
    current_time = datetime.strptime(start_time, '%H:%M')
    end_datetime = datetime.strptime(end_time, '%H:%M')

    # 預設起點/終點（台北車站）
    default_point = {
        'name': '台北車站',
        'lat': 25.0426731,
        'lon': 121.5170756,
        'duration': 0,
        'label': '交通樞紐',
        'hours': '24小時開放'
    }

    # 設定起點
    start_location = custom_start if custom_start else default_point.copy()
    if 'duration' not in start_location:
        start_location['duration'] = 0
    if 'hours' not in start_location:
        start_location['hours'] = '24小時開放'
    if 'label' not in start_location:
        start_location['label'] = '起點'

    # 設定終點
    end_location = custom_end if custom_end else start_location.copy()

    current_location = start_location
    selected_locations = []
    available_locations = locations.copy()
    had_lunch = False
    had_dinner = False

    while available_locations and current_time < end_datetime:
        best_location = None
        best_efficiency = float('-inf')
        best_departure_time = None
        best_travel_details = None
        is_meal_time = False
        meal_type = None

        # 檢查用餐時間
        current_hour = current_time.hour
        if not had_lunch and 11 <= current_hour <= 13:
            is_meal_time = True
            meal_type = "午餐"
        elif not had_dinner and 17 <= current_hour <= 18:
            is_meal_time = True
            meal_type = "晚餐"

        # 第一階段：距離篩選
        nearby_locations = []
        for location in available_locations:
            distance = calculate_distance(
                current_location['lat'], current_location['lon'],
                location['lat'], location['lon']
            )

            # 根據停留時間調整可接受距離
            max_distance = distance_threshold * \
                1.2 if location.get(
                    'duration', 0) >= 90 else distance_threshold

            if distance <= max_distance:
                # 營業時間檢查
                hours = location.get('hours', '24小時開放')
                open_time_str, close_time_str = parse_hours(hours)
                open_time = datetime.strptime(open_time_str, '%H:%M')
                close_time = datetime.strptime(close_time_str, '%H:%M')

                # 預估時間
                estimated_travel_time = distance * 3
                estimated_arrival = current_time + \
                    timedelta(minutes=estimated_travel_time)
                estimated_departure = estimated_arrival + \
                    timedelta(minutes=location['duration'])

                if (estimated_arrival.time() >= open_time.time() and
                        estimated_departure.time() <= close_time.time()):
                    nearby_locations.append(location)

        # 第二階段：詳細評估
        for location in nearby_locations:
            # 在用餐時間優先選擇餐廳
            if is_meal_time:
                if location.get('label') not in ['餐廳', '小吃', '夜市']:
                    continue

            travel_details = calculate_travel_time(
                current_location, location, travel_mode)
            travel_time = travel_details['time'].total_seconds() / 60

            # 計算到達和離開時間
            arrival_time = current_time + travel_details['time']
            departure_time = arrival_time + \
                timedelta(minutes=location['duration'])

            # 檢查行程是否會超過結束時間
            if departure_time > end_datetime:
                continue

            # 計算效率
            distance = calculate_distance(
                current_location['lat'], current_location['lon'],
                location['lat'], location['lon']
            )

            # 調整效率計算
            efficiency = location['duration'] / \
                (max(distance * travel_time, 1))

            # 用餐時間的效率調整
            if is_meal_time and location.get('label') in ['餐廳', '小吃', '夜市']:
                efficiency *= 2

            # 交通時間penalty
            if travel_time > 45:
                efficiency *= 0.5
            elif travel_time > 30:
                efficiency *= 0.7

            if efficiency > best_efficiency:
                best_efficiency = efficiency
                best_location = location
                best_departure_time = departure_time
                best_travel_details = travel_details

        if best_location and best_efficiency >= efficiency_threshold:
            # 處理用餐狀態
            if is_meal_time and best_location.get('label') in ['餐廳', '小吃', '夜市']:
                if meal_type == "午餐":
                    had_lunch = True
                else:
                    had_dinner = True
                best_location['is_meal'] = True
                best_location['meal_type'] = meal_type
            else:
                best_location['is_meal'] = False
                best_location['meal_type'] = None

            selected_locations.append(best_location)
            available_locations.remove(best_location)
            current_location = best_location
            current_time = best_departure_time
        else:
            break

    # 生成行程
    itinerary = []
    current_time = datetime.strptime(start_time, '%H:%M')
    current_location = start_location

    # 添加起點
    itinerary.append({
        'step': 0,
        'name': start_location['name'],
        'start_time': current_time.strftime('%H:%M'),
        'end_time': current_time.strftime('%H:%M'),
        'duration': 0,
        'travel_time': 0,
        'transport_details': '',
        'hours': start_location['hours'],
        'is_meal': False,
        'meal_type': None
    })

    # 添加其他地點
    for step, location in enumerate(selected_locations, 1):
        travel_details = calculate_travel_time(
            current_location, location, travel_mode)
        travel_time = travel_details['time'].total_seconds() / 60

        current_time += travel_details['time']
        visit_end_time = current_time + timedelta(minutes=location['duration'])

        entry = {
            'step': step,
            'name': location['name'],
            'start_time': current_time.strftime('%H:%M'),
            'end_time': visit_end_time.strftime('%H:%M'),
            'duration': location['duration'],
            'travel_time': travel_time,
            'transport_details': travel_details['transport_details'],
            'hours': location.get('hours', '24小時開放'),
            'is_meal': location.get('is_meal', False),
            'meal_type': location.get('meal_type')
        }
        itinerary.append(entry)

        current_location = location
        current_time = visit_end_time

    # 添加返回終點
    if selected_locations:
        return_details = calculate_travel_time(
            current_location, end_location, travel_mode)
        return_time = current_time + return_details['time']

        itinerary.append({
            'step': len(selected_locations) + 1,
            'name': end_location['name'],
            'start_time': return_time.strftime('%H:%M'),
            'end_time': return_time.strftime('%H:%M'),
            'duration': 0,
            'travel_time': return_details['time'].total_seconds() / 60,
            'transport_details': return_details['transport_details'],
            'hours': end_location.get('hours', '24小時開放'),
            'is_meal': False,
            'meal_type': None
        })

    return itinerary


def main():
    import time
    total_start_time = time.time()

    # 測試用的地點資料
    locations = [
        {'name': '士林夜市', 'rating': 4.3, 'lat': 25.0884972, 'lon': 121.5198443,
         'duration': 120, 'label': '夜市', 'hours': '17:00 - 00:00'},
        {'name': '台北101', 'rating': 4.6, 'lat': 25.0339808, 'lon': 121.561964,
         'duration': 150, 'label': '景點', 'hours': '09:00 - 22:00'},
        {'name': '大安森林公園', 'rating': 4.7, 'lat': 25.029677, 'lon': 121.5178326,
         'duration': 130, 'label': '景點', 'hours': '24小時開放'},
        {'name': '淡水老街', 'rating': 4.2, 'lat': 25.1700764, 'lon': 121.4393937,
         'duration': 120, 'label': '景點', 'hours': '10:00 - 22:00'},
        {'name': '西門町', 'rating': 4.4, 'lat': 25.0439401, 'lon': 121.4965457,
         'duration': 100, 'label': '商圈', 'hours': '10:00 - 22:00'},
        {'name': '國父紀念館', 'rating': 4.5, 'lat': 25.0400354, 'lon': 121.5576703,
         'duration': 90, 'label': '景點', 'hours': '09:00 - 17:00'},
        {'name': '鼎泰豐（信義店）', 'rating': 4.7, 'lat': 25.033976, 'lon': 121.563105,
         'duration': 90, 'label': '餐廳', 'hours': '11:00 - 21:00'},
        {'name': '阿宗麵線', 'rating': 4.4, 'lat': 25.046303, 'lon': 121.508033,
         'duration': 30, 'label': '小吃', 'hours': '10:00 - 22:00'},
        {'name': '信義威秀美食街', 'rating': 4.3, 'lat': 25.0333075, 'lon': 121.5677825,
         'duration': 60, 'label': '餐廳', 'hours': '11:00 - 22:00'}
    ]

    # 自訂起點（住家）
    custom_start = {
        'name': '家',
        'lat': 25.0339808,
        'lon': 121.561964
    }

    # 規劃行程
    itinerary = plan_trip(
        locations=locations,
        start_time='09:00',
        end_time='20:00',
        travel_mode='transit',
        custom_start=custom_start,
        custom_end=custom_start  # 結束後返回住家
    )

    # 轉換並印出行程
    trip_plan = convert_itinerary_to_trip_plan(itinerary)
    trip_plan.print_itinerary()

    total_execution_time = time.time() - total_start_time
    print(f"\n總執行時間：{total_execution_time:.2f}秒")


if __name__ == "__main__":
    main()
