# utils.py
import math
import requests
from datetime import datetime, timedelta
from config import GOOGLE_MAPS_API_KEY

# Global variable to track API calls
API_CALL_COUNT = 0


def calculate_distance(lat1, lon1, lat2, lon2):
    """計算兩個地理座標點之間的直線距離（公里）"""
    R = 6371  # 地球半徑（公里）
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * \
        math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c


def get_transport_details(travel_mode, api_data):
    """解析交通詳細資訊"""
    if travel_mode == 'transit':
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


def calculate_travel_time(current_location, destination, travel_mode='transit'):
    """計算兩個地點間的交通時間"""
    global API_CALL_COUNT

    # 如果是第一個地點，返回0分鐘
    if current_location is None:
        return {'time': timedelta(minutes=0), 'transport_details': '起點'}

    # 如果目的地和當前位置相同
    if current_location == destination:
        return {'time': timedelta(minutes=0), 'transport_details': '相同地點'}

    # 對於步行和騎自行車，使用簡單的距離估算
    if travel_mode in ['walking', 'bicycling']:
        lat_diff = abs(current_location['lat'] - destination['lat'])
        lon_diff = abs(current_location['lon'] - destination['lon'])
        estimated_time = max(2, int((lat_diff + lon_diff) * 100))
        transport_details = '步行' if travel_mode == 'walking' else '騎自行車'
        return {
            'time': timedelta(minutes=estimated_time),
            'transport_details': transport_details
        }

    # Google Maps API 請求
    base_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        'origins': f"{current_location['lat']},{current_location['lon']}",
        'destinations': f"{destination['lat']},{destination['lon']}",
        'mode': travel_mode,
        'key': GOOGLE_MAPS_API_KEY,
        'language': 'zh-TW'  # 使用中文回應
    }

    try:
        print(f"Calling API: {current_location['name']} to {
              destination['name']}")  # Debug info
        response = requests.get(base_url, params=params)
        API_CALL_COUNT += 1
        print(f"API calls so far: {API_CALL_COUNT}")  # Debug info

        data = response.json()

        if data['status'] == 'OK' and data['rows'][0]['elements'][0]['status'] == 'OK':
            # 獲取行駛時間（以秒為單位）
            duration_seconds = data['rows'][0]['elements'][0]['duration']['value']
            transport_details = get_transport_details(travel_mode, data)
            return {
                'time': timedelta(seconds=duration_seconds),
                'transport_details': transport_details
            }
        else:
            print(f"API Error: {data.get('status')
                                } - Using fallback calculation")  # Debug info
    except Exception as e:
        print(f"Error calling API: {
              str(e)} - Using fallback calculation")  # Debug info

    # 如果API調用失敗，使用備用方法
    lat_diff = abs(current_location['lat'] - destination['lat'])
    lon_diff = abs(current_location['lon'] - destination['lon'])
    estimated_time = max(2, int((lat_diff + lon_diff) * 100))

    return {
        'time': timedelta(minutes=estimated_time),
        'transport_details': f'預估{travel_mode}路線'
    }


def parse_hours(hours_str):
    """解析營業時間"""
    if hours_str == '24小時開放':
        return ('00:00', '23:59')
    try:
        times = hours_str.split(' - ')
        if len(times) == 2:
            return (times[0], times[1])
    except Exception:
        pass
    return ('00:00', '23:59')
