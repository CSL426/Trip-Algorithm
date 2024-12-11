from datetime import datetime, timedelta
import requests
from config import GOOGLE_MAPS_API_KEY


def plan_trip(locations, start_time, end_time, travel_mode='transit'):
    itinerary = []
    current_time = datetime.strptime(start_time, '%H:%M')
    current_location = None

    # Sort locations by rating to prioritize high-rated spots
    sorted_locations = sorted(
        locations, key=lambda x: x['rating'], reverse=True)

    for step, location in enumerate(sorted_locations, 1):
        # Check if we've reached the end time
        if current_time >= datetime.strptime(end_time, '%H:%M'):
            break

        # Calculate travel time and details
        travel_details = calculate_travel_time(
            current_location, location, travel_mode) if current_location else {
                'time': timedelta(minutes=0),
                'transport_details': '起點'
        }

        # Update current time with travel time
        current_time += travel_details['time']

        # Calculate end time of visit
        visit_start_time = current_time
        visit_end_time = current_time + timedelta(minutes=location['duration'])

        # Create itinerary entry
        entry = {
            'step': step,
            'name': location['name'],
            'rating': location['rating'],
            'start_time': visit_start_time.strftime('%H:%M'),
            'end_time': visit_end_time.strftime('%H:%M'),
            'duration': location['duration'],
            # Convert to minutes
            'travel_time': travel_details['time'].total_seconds() / 60,
            'transport_details': travel_details['transport_details']
        }

        itinerary.append(entry)

        # Update current location and time
        current_location = location
        current_time = visit_end_time

    return itinerary


# Global variable to track API calls
API_CALL_COUNT = 0


def calculate_travel_time(current_location, destination, travel_mode='transit'):
    global API_CALL_COUNT

    # 如果是第一個地點，返回0分鐘
    if current_location is None:
        return {'time': timedelta(minutes=0), 'transport_details': '起點'}

    # 對於步行和騎自行車，使用統一的處理邏輯
    if travel_mode in ['walking', 'bicycling']:
        # 計算直線距離
        lat_diff = abs(current_location['lat'] - destination['lat'])
        lon_diff = abs(current_location['lon'] - destination['lon'])

        # 估算時間（根據緯度經度差異）
        estimated_time = max(2, int((lat_diff + lon_diff) * 100))

        # 根據模式選擇不同的描述
        transport_details = '步行' if travel_mode == 'walking' else '騎自行車'

        return {
            'time': timedelta(minutes=estimated_time),
            'transport_details': transport_details
        }

    # 構建Google Maps Distance Matrix API的請求URL
    base_url = "https://maps.googleapis.com/maps/api/distancematrix/json"

    # 準備請求參數
    params = {
        'origins': f"{current_location['lat']},{current_location['lon']}",
        'destinations': f"{destination['lat']},{destination['lon']}",
        'mode': travel_mode,
        'key': GOOGLE_MAPS_API_KEY
    }

    try:
        # 發送API請求
        response = requests.get(base_url, params=params)

        # 增加API調用計數
        API_CALL_COUNT += 1

        data = response.json()

        # 檢查API響應
        if data['status'] == 'OK' and data['rows'][0]['elements'][0]['status'] == 'OK':
            # 獲取行駛時間（以秒為單位）
            duration_seconds = data['rows'][0]['elements'][0]['duration']['value']
            transport_details = get_transport_details(travel_mode, data)

            # 轉換為timedelta
            return {
                'time': timedelta(seconds=duration_seconds),
                'transport_details': transport_details
            }
        else:
            # 如果API調用失敗，使用備用方法
            print(f"API調用失敗: {data.get('status', 'Unknown status')}")
            lat_diff = abs(current_location['lat'] - destination['lat'])
            lon_diff = abs(current_location['lon'] - destination['lon'])
            return {
                'time': timedelta(minutes=max(2, int((lat_diff + lon_diff) * 100))),
                'transport_details': f'預估{travel_mode}路線'
            }

    except Exception as e:
        # 處理可能的異常（如網絡錯誤）
        print(f"計算交通時間時發生錯誤: {e}")
        lat_diff = abs(current_location['lat'] - destination['lat'])
        lon_diff = abs(current_location['lon'] - destination['lon'])
        return {
            'time': timedelta(minutes=max(2, int((lat_diff + lon_diff) * 100))),
            'transport_details': f'預估{travel_mode}路線'
        }


def get_transport_details(travel_mode, api_data):
    """根據travel_mode和API返回的數據，提取具體的交通資訊"""
    if travel_mode == 'transit':
        # 提取公共交通資訊
        try:
            transit_info = api_data['rows'][0]['elements'][0].get(
                'transit', {}).get('steps', [])
            details = []
            for step in transit_info:
                if step.get('transit_details'):
                    details.append(f"{step['transit_details']['line']['vehicle']['type']}: {\
                                   step['transit_details']['line']['name']}")
            return ' → '.join(details) if details else '大眾運輸'
        except Exception:
            return '大眾運輸'
    elif travel_mode == 'driving':
        return '開車'
    elif travel_mode == 'bicycling':
        return '騎自行車'
    elif travel_mode == 'walking':
        return '步行'
    return travel_mode


def print_itinerary(itinerary):
    # 定義一些建議和標籤（與之前相同）
    meals = {
        '鼎泰豐（信義店）': '午餐',
        '西門町': '晚餐',
        '阿宗麵線': '小吃',
        '豐盛町便當': '午餐'
    }

    labels = {
        '大安森林公園': '綠意盎然的城市公園',
        '台北101': '台北地標、觀景台、購物中心',
        '國父紀念館': '歷史紀念館、藝文中心',
        '西門町': '年輕人商圈、購物天堂',
        '鼎泰豐（信義店）': '世界級米其林餐廳',
        '阿宗麵線': '台北知名小吃',
    }

    print("每日行程：")
    for item in itinerary:
        # 準備額外資訊
        extra_info = []

        # 檢查是否有用餐建議
        if item['name'] in meals:
            extra_info.append(meals[item['name']])

        # 檢查是否有景點標籤
        if item['name'] in labels:
            extra_info.append(labels[item['name']])

        # 格式化額外資訊
        extra_note = f" ({', '.join(extra_info)})" if extra_info else ""

        # 輸出交通時間和交通方式
        if item['travel_time'] > 0:
            print(f"  交通方式: {item['transport_details']}")
            print(f"  交通時間: {item['travel_time']:.0f}分鐘")

        # 輸出行程詳細資訊
        print(f"步驟{item['step']}：{item['name']}{extra_note} (評分: {item['rating']}, {
              item['start_time']} - {item['end_time']}, 停留時間: {item['duration']}分鐘)")

    # 在行程結束後輸出 API 調用次數
    print("\n--- API 使用統計 ---")
    print(f"本次行程規劃共使用 Google Maps API: {API_CALL_COUNT} 次")


# Example locations data
locations = [
    {'name': '士林夜市', 'rating': 4.3, 'lat': 25.0884972,
        'lon': 121.5198443, 'duration': 120, 'label': '夜市'},
    {'name': '台北101', 'rating': 4.6, 'lat': 25.0339808,
        'lon': 121.561964, 'duration': 150, 'label': '景點'},
    {'name': '大安森林公園', 'rating': 4.7, 'lat': 25.029677,
        'lon': 121.5178326, 'duration': 130, 'label': '景點'},
    {'name': '淡水老街', 'rating': 4.2, 'lat': 25.1700764,
        'lon': 121.4393937, 'duration': 120, 'label': '景點'},
    {'name': '西門町', 'rating': 4.4, 'lat': 25.0439401,
        'lon': 121.4965457, 'duration': 100, 'label': '商圈'},
    {'name': '國父紀念館', 'rating': 4.5, 'lat': 25.0400354,
        'lon': 121.5576703, 'duration': 90, 'label': '景點'},
    {'name': '基隆廟口夜市', 'rating': 4.3, 'lat': 25.1286858,
        'lon': 121.7404846, 'duration': 120, 'label': '夜市'},
    {'name': '鼎泰豐（信義店）', 'rating': 4.7, 'lat': 25.033976,
        'lon': 121.563105, 'duration': 90, 'label': '餐廳'},
    {'name': '阿宗麵線', 'rating': 4.4, 'lat': 25.046303,
        'lon': 121.508033, 'duration': 30, 'label': '小吃'},
    {'name': '豐盛町便當', 'rating': 4.3, 'lat': 25.039495,
        'lon': 121.501761, 'duration': 30, 'label': '餐廳'},
    {'name': '饒河夜市', 'rating': 4.4, 'lat': 25.047867,
        'lon': 121.577654, 'duration': 60, 'label': '夜市'}
]

# 現在您可以選擇不同的交通模式
# 可用模式：'transit', 'driving', 'bicycling', 'walking'
itinerary = plan_trip(locations, '09:00', '19:00', travel_mode='transit')

# Print the itinerary
print_itinerary(itinerary)
