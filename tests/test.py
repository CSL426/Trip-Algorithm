from datetime import datetime, timedelta
import requests
from config import GOOGLE_MAPS_API_KEY


def parse_hours(hours_str):
    """安全地解析營業時間"""
    if hours_str == '24小時開放':
        return ('00:00', '23:59')
    
    try:
        # 拆分時間，並處理可能的異常情況
        times = hours_str.split(' - ')
        if len(times) == 2:
            return (times[0], times[1])
        return ('00:00', '23:59')
    except Exception:
        return ('00:00', '23:59')

def plan_trip(locations, start_time, end_time, travel_mode='transit'):
    itinerary = []
    current_time = datetime.strptime(start_time, '%H:%M')
    current_location = None

    # 安全地篩選早上可以去的景點和小吃
    morning_locations = [
        loc for loc in locations 
        if loc.get('label') in ['景點', '小吃'] and 
        (lambda x: True 
         if x.get('hours') == '24小時開放' 
         else datetime.strptime(parse_hours(x.get('hours', '24小時開放'))[1], '%H:%M').time() >= datetime.strptime('11:00', '%H:%M').time()
        )(loc)
    ]

    # 篩選餐廳
    restaurant_locations = [
        loc for loc in locations
        if loc.get('label') in ['餐廳', '小吃'] and
        (lambda x: 
         datetime.strptime(parse_hours(x.get('hours', '24小時開放'))[0], '%H:%M').time() <= datetime.strptime('11:00', '%H:%M').time()
        )(loc)
    ]

    # 排序早上景點和小吃
    morning_locations.sort(key=lambda x: x.get('rating', 0), reverse=True)

    # 排序餐廳，優先考慮高評分
    restaurant_locations.sort(key=lambda x: x.get('rating', 0), reverse=True)

    # 組合新的位置順序：早上景點/小吃 + 午餐 + 其他地點
    if morning_locations and restaurant_locations:
        first_morning_spot = morning_locations[0]
        first_restaurant = restaurant_locations[0]

        # 移除已選擇的地點
        locations = [loc for loc in locations if loc not in [first_morning_spot, first_restaurant]]

        # 重新排序其他地點
        sorted_locations = sorted(
            locations, key=lambda x: x.get('rating', 0), reverse=True)

        # 重組行程順序
        sorted_locations = [first_morning_spot, first_restaurant] + sorted_locations
    else:
        # 如果沒有合適的早上景點，則按原邏輯排序
        sorted_locations = sorted(
            locations, key=lambda x: x.get('rating', 0), reverse=True)

    for step, location in enumerate(sorted_locations, 1):
        # 檢查是否已超過結束時間
        if current_time >= datetime.strptime(end_time, '%H:%M'):
            break

        # 解析營業時間
        hours = location.get('hours', '24小時開放')
        open_time_str, close_time_str = parse_hours(hours)

        try:
            # 解析營業時間範圍
            open_time = datetime.strptime(open_time_str, '%H:%M')
            close_time = datetime.strptime(close_time_str, '%H:%M')

            # 檢查當前時間是否在營業時間內
            if current_time.time() < open_time.time():
                # 如果當前時間早於開放時間，調整到開放時間
                current_time = open_time
            elif current_time.time() > close_time.time():
                # 如果當前時間晚於關閉時間，跳過此地點
                continue
        except Exception as e:
            print(f"解析 {location['name']} 的營業時間時出錯: {e}")

        # 計算travel time
        travel_details = calculate_travel_time(
            current_location, location, travel_mode) if current_location else {
                'time': timedelta(minutes=0),
                'transport_details': '起點'
        }

        # 更新當前時間（包括travel time）
        current_time += travel_details['time']

        # 計算參觀結束時間
        visit_start_time = current_time
        visit_end_time = current_time + timedelta(minutes=location['duration'])

        # 創建行程
        entry = {
            'step': step,
            'name': location['name'],
            'rating': location['rating'],
            'start_time': visit_start_time.strftime('%H:%M'),
            'end_time': visit_end_time.strftime('%H:%M'),
            'duration': location['duration'],
            'travel_time': travel_details['time'].total_seconds() / 60,
            'transport_details': travel_details['transport_details'],
            'hours': hours  # 添加營業時間資訊
        }

        itinerary.append(entry)

        # 更新當前位置和時間
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
                    details.append(f"{step['transit_details']['line']['vehicle']['type']}: {
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
    # 定義一些建議和標籤
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
    for index, item in enumerate(itinerary):
        # 準備額外資訊
        extra_info = []

        # 標記第一個地點
        if index == 0:
            extra_info.append('早上景點/小吃')

        # 標記午餐地點
        if index == 1:
            extra_info.append('午餐')

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

        # 添加營業時間到輸出
        print(f"步驟{item['step']}：{item['name']} (營業時間: {item['hours']}, 評分: {item['rating']}, "
              f"{item['start_time']} - {item['end_time']}, 停留時間: {item['duration']}分鐘){extra_note}")

    # 在行程結束後輸出 API 調用次數
    print("\n--- API 使用統計 ---")
    print(f"本次行程規劃共使用 Google Maps API: {API_CALL_COUNT} 次")


# Example locations data
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
    {'name': '基隆廟口夜市', 'rating': 4.3, 'lat': 25.1286858, 'lon': 121.7404846,
     'duration': 120, 'label': '夜市', 'hours': '17:00 - 00:00'},
    {'name': '鼎泰豐（信義店）', 'rating': 4.7, 'lat': 25.033976, 'lon': 121.563105,
     'duration': 90, 'label': '餐廳', 'hours': '11:00 - 21:00'},
    {'name': '阿宗麵線', 'rating': 4.4, 'lat': 25.046303, 'lon': 121.508033,
     'duration': 30, 'label': '小吃', 'hours': '10:00 - 22:00'},
    {'name': '豐盛町便當', 'rating': 4.3, 'lat': 25.039495, 'lon': 121.501761,
     'duration': 30, 'label': '餐廳', 'hours': '10:00 - 20:00'},
    {'name': '饒河夜市', 'rating': 4.4, 'lat': 25.047867, 'lon': 121.577654,
     'duration': 60, 'label': '夜市', 'hours': '17:00 - 00:00'}
]

# 現在您可以選擇不同的交通模式
# 可用模式：'transit', 'driving', 'bicycling', 'walking'
itinerary = plan_trip(locations, '10:00', '19:00', travel_mode='transit')

# Print the itinerary
print_itinerary(itinerary)
