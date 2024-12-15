# TripPlanner.py
from datetime import datetime, timedelta
from utils import calculate_distance, calculate_travel_time, parse_hours
from TripNode import convert_itinerary_to_trip_plan


def evaluate_location_efficiency(location, current_location, travel_time, max_travel_time=120):
    """評估地點是否值得訪問"""
    if current_location == location:
        return float('inf')

    distance = calculate_distance(
        current_location['lat'], current_location['lon'],
        location['lat'], location['lon']
    ) if current_location else 0

    stay_duration = location.get('duration', 0)
    safe_distance = max(distance, 0.1)
    safe_travel_time = max(travel_time, 0.1)

    travel_time_penalty = 0.5 if travel_time > max_travel_time else 1 - \
        (travel_time / max_travel_time)

    return (stay_duration / (safe_distance * safe_travel_time)) * travel_time_penalty


def plan_trip(locations, start_time, end_time, travel_mode='transit', distance_threshold=30, efficiency_threshold=0.1):
    """智能行程規劃"""
    current_time = datetime.strptime(start_time, '%H:%M')
    end_datetime = datetime.strptime(end_time, '%H:%M')
    max_return_time = end_datetime + timedelta(minutes=30)

    # 起點資訊
    start_location = {
        'name': '台北車站',
        'lat': 25.0426731,
        'lon': 121.5170756,
        'duration': 0,
        'label': '交通樞紐',
        'hours': '24小時開放'
    }

    current_location = start_location

    # 篩選和排序地點
    selected_locations = []
    available_locations = locations.copy()  # 創建複本避免修改原始資料

    # 智能篩選
    while available_locations and current_time < end_datetime:
        best_location = None
        best_efficiency = float('-inf')
        best_departure_time = None
        best_travel_details = None

        for location in available_locations:
            # 計算交通時間
            travel_details = calculate_travel_time(
                current_location, location, travel_mode)
            travel_time = travel_details['time'].total_seconds() / 60

            # 計算時間
            estimated_arrival = current_time + travel_details['time']
            estimated_departure = estimated_arrival + \
                timedelta(minutes=location['duration'])

            # 計算返回時間
            return_details = calculate_travel_time(
                location, start_location, travel_mode)
            final_return_time = estimated_departure + return_details['time']

            # 檢查各種條件
            if final_return_time > max_return_time:
                continue

            hours = location.get('hours', '24小時開放')
            open_time_str, close_time_str = parse_hours(hours)
            open_time = datetime.strptime(open_time_str, '%H:%M')
            close_time = datetime.strptime(close_time_str, '%H:%M')

            if not (estimated_arrival.time() >= open_time.time() and
                    estimated_departure.time() <= close_time.time()):
                continue

            distance = calculate_distance(
                current_location['lat'], current_location['lon'],
                location['lat'], location['lon']
            )

            if distance > distance_threshold:
                continue

            efficiency = evaluate_location_efficiency(
                location, current_location, travel_time)

            if efficiency >= efficiency_threshold and efficiency > best_efficiency:
                best_efficiency = efficiency
                best_location = location
                best_departure_time = estimated_departure
                best_travel_details = travel_details

        if best_location:
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
        'hours': start_location['hours']
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
            'hours': location.get('hours', '24小時開放')
        }
        itinerary.append(entry)

        current_location = location
        current_time = visit_end_time

    # 添加返回起點
    if selected_locations:
        return_details = calculate_travel_time(
            current_location, start_location, travel_mode)
        return_time = current_time + return_details['time']

        if return_time <= max_return_time:
            itinerary.append({
                'step': len(selected_locations) + 1,
                'name': start_location['name'],
                'start_time': return_time.strftime('%H:%M'),
                'end_time': return_time.strftime('%H:%M'),
                'duration': 0,
                'travel_time': return_details['time'].total_seconds() / 60,
                'transport_details': return_details['transport_details'],
                'hours': start_location['hours']
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
         'duration': 30, 'label': '小吃', 'hours': '10:00 - 22:00'}
    ]

    # 規劃行程
    itinerary = plan_trip(locations, '10:00', '19:00', travel_mode='transit')

    # 轉換並印出行程
    trip_plan = convert_itinerary_to_trip_plan(itinerary, locations)
    trip_plan.print_itinerary()
    
    total_execution_time = time.time() - total_start_time
    print(f"總執行時間：{total_execution_time:.2f}秒")


if __name__ == "__main__":
    main()
