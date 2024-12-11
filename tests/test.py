from datetime import datetime, timedelta
import requests
from config import GOOGLE_MAPS_API_KEY


def plan_trip(locations, start_time, end_time):
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

        # Calculate travel time (you might want to replace this with a real API)
        travel_time = calculate_travel_time(
            current_location, location) if current_location else timedelta(minutes=0)

        # Update current time with travel time
        current_time += travel_time

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
            'travel_time': travel_time.total_seconds() / 60  # Convert to minutes
        }

        itinerary.append(entry)

        # Update current location and time
        current_location = location
        current_time = visit_end_time

    return itinerary


# Global variable to track API calls
API_CALL_COUNT = 0


def calculate_travel_time(current_location, destination, travel_mode='driving'):
    global API_CALL_COUNT

    # 如果是第一個地點，返回0分鐘
    if current_location is None:
        return timedelta(minutes=0)

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
        if data['status'] == 'OK':
            # 獲取行駛時間（以秒為單位）
            duration_seconds = data['rows'][0]['elements'][0]['duration']['value']

            # 轉換為timedelta
            return timedelta(seconds=duration_seconds)
        else:
            # 如果API調用失敗，回退到默認估算方法
            print(f"API調用失敗: {data['status']}")
            lat_diff = abs(current_location['lat'] - destination['lat'])
            lon_diff = abs(current_location['lon'] - destination['lon'])
            return timedelta(minutes=max(2, int((lat_diff + lon_diff) * 100)))

    except Exception as e:
        # 處理可能的異常（如網絡錯誤）
        print(f"計算交通時間時發生錯誤: {e}")
        lat_diff = abs(current_location['lat'] - destination['lat'])
        lon_diff = abs(current_location['lon'] - destination['lon'])
        return timedelta(minutes=max(2, int((lat_diff + lon_diff) * 100)))





def print_itinerary(itinerary):
    # 定義一些建議和標籤
    meals = {
        '鼎泰豐（信義店）': '午餐',
        '西門町': '晚餐',
        '阿宗麵線': '小吃',
        '豐盛町便當': '午餐'
    }

    # 特別景點標籤
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

        # 輸出交通時間
        if item['travel_time'] > 0:
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

# Plan the trip
itinerary = plan_trip(locations, '09:00', '19:00')

# Print the itinerary
print_itinerary(itinerary)
