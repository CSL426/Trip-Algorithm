import requests
import math
import itertools
import time
from functools import lru_cache
import logging
import os
from datetime import datetime, timedelta
from config import GOOGLE_MAPS_API_KEY


class TravelRouteOptimizer:
    def __init__(self, locations, google_maps_api_key=None):
        if google_maps_api_key is None:
            google_maps_api_key = os.getenv('GOOGLE_MAPS_API_KEY')

        self.locations = sorted(
            locations, key=lambda x: x['rating'], reverse=True)
        self.api_key = google_maps_api_key

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    @lru_cache(maxsize=128)
    def get_travel_time(self, origin_lat, origin_lon, origin_name,
                        dest_lat, dest_lon, dest_name, max_retries=3, debug=False):
        if not self.api_key:
            self.logger.warning("未提供 Google Maps API 金鑰，使用預設交通時間")
            return 30

        base_url = "https://maps.googleapis.com/maps/api/directions/json"
        params = {
            "origin": f"{origin_lat},{origin_lon}",
            "destination": f"{dest_lat},{dest_lon}",
            "key": self.api_key
        }

        for attempt in range(max_retries):
            try:
                self.logger.info(f"嘗試獲取 {origin_name} 到 {dest_name} 的交通時間")

                response = requests.get(base_url, params=params)
                data = response.json()

                if debug:
                    self.logger.debug(f"API 返回數據: {data}")

                if data['status'] == 'OK':
                    duration = data['routes'][0]['legs'][0]['duration']['value']
                    travel_time = duration / 60  # 轉換為分鐘
                    self.logger.info(f"交通時間: {travel_time:.0f} 分鐘")
                    return travel_time
                else:
                    self.logger.warning(f"API 呼叫失敗: {data['status']}")
                    return 30
            except requests.exceptions.RequestException as e:
                self.logger.error(f"第 {attempt+1} 次嘗試失敗: {e}")
                if attempt == max_retries - 1:
                    self.logger.error("多次重試後仍無法獲取交通時間")
                    return 30
                time.sleep(1)

    def optimize_route(self, top_n=15, route_length=3, max_distance=150):
        def calculate_haversine_distance(lat1, lon1, lat2, lon2):
            R = 6371  # 地球半徑（公里）

            lat1, lon1, lat2, lon2 = map(
                math.radians, [lat1, lon1, lat2, lon2])

            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = math.sin(dlat/2)**2 + math.cos(lat1) * \
                math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            distance = R * c

            return distance

        def estimate_travel_time(distance):
            if distance > 120:
                return float('inf')
            elif distance > 30:
                return distance / 1 * 60
            else:
                return distance / 1.5 * 60

        top_locations = self.locations[:top_n]
        best_route = None
        min_total_travel_time = float('inf')

        for route in itertools.combinations(top_locations, route_length):
            route_distances = [
                calculate_haversine_distance(route[i]['lat'], route[i]['lon'],
                                             route[i+1]['lat'], route[i+1]['lon'])
                for i in range(len(route)-1)
            ]

            if any(dist > max_distance for dist in route_distances):
                continue

            route_estimated_times = [
                estimate_travel_time(dist) for dist in route_distances
            ]

            if any(time == float('inf') for time in route_estimated_times):
                continue

            total_travel_time = sum(
                self.get_travel_time(
                    route[i]['lat'], route[i]['lon'], route[i]['name'],
                    route[i+1]['lat'], route[i+1]['lon'], route[i+1]['name']
                )
                for i in range(len(route)-1)
            )

            if total_travel_time < min_total_travel_time:
                min_total_travel_time = total_travel_time
                best_route = route

        return best_route

    def generate_itinerary(self, route, start_time='09:00', end_time='18:00'):
        start = datetime.strptime(start_time, '%H:%M')
        end = datetime.strptime(end_time, '%H:%M')
        total_available_time = (end - start).total_seconds() / 60

        itinerary = []
        current_time = start
        total_time = 0

        for i, location in enumerate(route, 1):
            if i > 1:
                travel_time = self.get_travel_time(
                    route[i-2]['lat'], route[i-2]['lon'], route[i-2]['name'],
                    location['lat'], location['lon'], location['name']
                )

                current_time += timedelta(minutes=travel_time)
                total_time += travel_time

            location_duration = location.get('duration', 120)
            stay_start_time = current_time
            current_time += timedelta(minutes=location_duration)
            total_time += location_duration

            itinerary.append({
                'step': i,
                'name': location['name'],
                'rating': location['rating'],
                'duration': location_duration,
                'travel_time_from_previous': travel_time if i > 1 else 0,
                'arrival_time': stay_start_time.strftime('%H:%M'),
                'departure_time': current_time.strftime('%H:%M')
            })

            if total_time > total_available_time:
                break

        return itinerary


def main():
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

    optimizer = TravelRouteOptimizer(locations, GOOGLE_MAPS_API_KEY)
    best_route = optimizer.optimize_route()
    itinerary = optimizer.generate_itinerary(best_route)

    print("每日行程：")
    for item in itinerary:
        if item['step'] > 1:
            print(f"  交通時間: {item['travel_time_from_previous']:.0f}分鐘")
        print(f"步驟{item['step']}：{item['name']} (評分: {item['rating']}", end="")
        print(f",  {item['arrival_time']} - {item['departure_time']}", end="")
        print(f",  停留時間: {item['duration']}分鐘)")


if __name__ == '__main__':
    main()
