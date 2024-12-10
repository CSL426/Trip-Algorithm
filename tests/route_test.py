import requests
import math
import itertools
import time
from functools import lru_cache
import logging
import os
from config import GOOGLE_MAPS_API_KEY


class TravelRouteOptimizer:
    def __init__(self, locations, google_maps_api_key=None):
        """
        初始化路線優化器，支援 Google Maps API 金鑰

        :param locations: 地點列表
        :param google_maps_api_key: Google Maps API 金鑰
        """
        # 從環境變量讀取 API 金鑰（如果未直接提供）
        if google_maps_api_key is None:
            google_maps_api_key = os.getenv('GOOGLE_MAPS_API_KEY')

        self.locations = sorted(
            locations, key=lambda x: x['rating'], reverse=True)
        self.api_key = google_maps_api_key

        # 配置日誌
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    @lru_cache(maxsize=128)
    def get_travel_time(self, origin_lat, origin_lon, origin_name,
                        dest_lat, dest_lon, dest_name, max_retries=3, debug=False):
        """
        使用 Google Maps API 獲取兩地點之間的交通時間

        :param origin_lat: 起點緯度
        :param origin_lon: 起點經度
        :param origin_name: 起點名稱
        :param dest_lat: 終點緯度
        :param dest_lon: 終點經度
        :param dest_name: 終點名稱
        :param max_retries: 最大重試次數
        :param debug: 是否開啟調試模式
        :return: 交通時間（分鐘）
        """
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
                    # 取得第一個路線的總時間
                    duration = data['routes'][0]['legs'][0]['duration']['value']
                    travel_time = duration / 60  # 轉換為分鐘
                    self.logger.info(f"交通時間: {travel_time:.2f} 分鐘")
                    return travel_time
                else:
                    self.logger.warning(f"API 呼叫失敗: {data['status']}")
                    return 30
            except requests.exceptions.RequestException as e:
                self.logger.error(f"第 {attempt+1} 次嘗試失敗: {e}")
                if attempt == max_retries - 1:
                    self.logger.error("多次重試後仍無法獲取交通時間")
                    return 30
                time.sleep(1)  # 短暫等待後重試

    def optimize_route(self, top_n=15, route_length=3, max_distance=150):
        """
        優化路線，找出總交通時間最短的路線

        :param top_n: 從評分最高的地點中選擇
        :param route_length: 最終路線包含的地點數量
        :param max_distance: 兩地點間最大可接受距離（公里）
        :return: 最佳路線
        """
        def calculate_haversine_distance(lat1, lon1, lat2, lon2):
            """
            使用 Haversine 公式計算兩點間的地球表面距離（公里）

            :param lat1: 第一個點的緯度
            :param lon1: 第一個點的經度
            :param lat2: 第二個點的緯度
            :param lon2: 第二個點的經度
            :return: 兩點間的距離（公里）
            """
            R = 6371  # 地球半徑（公里）

            # 將緯度和經度轉為弧度
            lat1, lon1, lat2, lon2 = map(
                math.radians, [lat1, lon1, lat2, lon2])

            # Haversine 公式
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = math.sin(dlat/2)**2 + math.cos(lat1) * \
                math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            distance = R * c

            return distance

        def estimate_travel_time(distance):
            """
            根據距離估算預估交通時間（簡單估算）

            :param distance: 兩點間距離（公里）
            :return: 估算的交通時間（分鐘）
            """
            # 假設平均時速為 60 公里/小時
            if distance > 140:  # 超過 140 公里，視為遠距離
                return float('inf')  # 不建議此路線
            elif distance > 70:
                return distance / 1 * 60  # 假設高速公路或長途交通
            else:
                return distance / 1.5 * 60  # 假設一般道路

        top_locations = self.locations[:top_n]
        best_route = None
        min_total_travel_time = float('inf')

        for route in itertools.combinations(top_locations, route_length):
            # 先檢查地點間距離
            route_distances = [
                calculate_haversine_distance(route[i]['lat'], route[i]['lon'],
                                             route[i+1]['lat'], route[i+1]['lon'])
                for i in range(len(route)-1)
            ]

            # 如果任何兩點距離超過 max_distance，跳過此路線
            if any(dist > max_distance for dist in route_distances):
                continue

            # 使用估算時間作為初步篩選
            route_estimated_times = [
                estimate_travel_time(dist) for dist in route_distances
            ]

            # 如果有不可行的路線，跳過
            if any(time == float('inf') for time in route_estimated_times):
                continue

            # 計算實際交通時間（此時只有少數組合需要 API 呼叫）
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

    def generate_itinerary(self, route):
        """
        生成詳細行程表

        :param route: 優化後的路線
        :return: 詳細行程表
        """
        itinerary = []
        total_time = 0

        for i, location in enumerate(route, 1):
            # 計算交通時間（對於第一個地點除外）
            if i > 1:
                travel_time = self.get_travel_time(
                    route[i-2]['lat'], route[i-2]['lon'], route[i-2]['name'],
                    location['lat'], location['lon'], location['name']
                )
                total_time += travel_time

            # 加上地點停留時間
            total_time += location.get('duration', 120)  # 默認停留2小時

            itinerary.append({
                'step': i,
                'name': location['name'],
                'rating': location['rating'],
                'cumulative_time': total_time,
                'travel_time_from_previous': travel_time if i > 1 else 0
            })

        return itinerary


def main():
    # 範例地點數據
    locations = [
        {'name': '士林夜市', 'rating': 4.3, 'lat': 25.0894,
            'lon': 121.525, 'duration': 120},
        {'name': '台北101', 'rating': 4.6, 'lat': 25.0330,
            'lon': 121.5645, 'duration': 150},
        {'name': '大安森林公園', 'rating': 4.7, 'lat': 25.0270,
            'lon': 121.5435, 'duration': 130},
        {'name': '九份老街', 'rating': 4.5, 'lat': 25.1146,
            'lon': 121.8451, 'duration': 150},
        {'name': '淡水老街', 'rating': 4.2, 'lat': 25.1778,
            'lon': 121.4418, 'duration': 120},
        {'name': '西門町', 'rating': 4.4, 'lat': 25.0432,
            'lon': 121.5063, 'duration': 100},
        {'name': '國父紀念館', 'rating': 4.5, 'lat': 25.0343,
            'lon': 121.5640, 'duration': 90},
        {'name': '花蓮太魯閣國家公園', 'rating': 4.8, 'lat': 24.1586,
            'lon': 121.6933, 'duration': 240},
        {'name': '基隆廟口夜市', 'rating': 4.3, 'lat': 25.1272,
            'lon': 121.7410, 'duration': 120},
        {'name': '蓮池潭', 'rating': 4.4, 'lat': 22.6422,
            'lon': 120.3015, 'duration': 180}
    ]

    optimizer = TravelRouteOptimizer(locations, GOOGLE_MAPS_API_KEY)
    best_route = optimizer.optimize_route()
    itinerary = optimizer.generate_itinerary(best_route)

    print("最佳路線：")
    for item in itinerary:
        if item['step'] > 1:
            print(f"  交通時間: {item['travel_time_from_previous']:.0f}分鐘")
        print(f"步驟{item['step']}：{item['name']} (評分: {
            item['rating']}) - 累計時間: {item['cumulative_time']:.0f}分鐘")


if __name__ == '__main__':
    main()
