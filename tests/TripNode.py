# TripNode.py
import time
from utils import API_CALL_COUNT


class TripNode:
    def __init__(self, location, start_time=None, end_time=None, travel_time=None, transport_details=None):
        """初始化 TripNode"""
        self.name = location.get('name', '')
        self.lat = location.get('lat', 0)
        self.lon = location.get('lon', 0)
        self.duration = location.get('duration', 0)
        self.label = location.get('label', '')
        self.hours = location.get('hours', '24小時開放')

        self.start_time = start_time
        self.end_time = end_time
        self.travel_time = travel_time
        self.transport_details = transport_details

        self.next = None
        self.prev = None


class TripPlan:
    def __init__(self, start_location=None):
        """初始化行程規劃"""
        self.head = None
        self.tail = None

        if start_location is None:
            start_location = {
                'name': '台北車站',
                'lat': 25.0426731,
                'lon': 121.5170756,
                'duration': 0,
                'label': '交通樞紐',
                'hours': '24小時開放'
            }

        self.start_node = TripNode(start_location)

    def add_location(self, location, start_time=None, end_time=None, travel_time=None, transport_details=None):
        """新增地點到行程"""
        new_node = TripNode(
            location,
            start_time=start_time,
            end_time=end_time,
            travel_time=travel_time,
            transport_details=transport_details
        )

        if not self.head:
            self.head = new_node
            self.tail = new_node
            new_node.prev = self.start_node
            self.start_node.next = new_node
        else:
            self.tail.next = new_node
            new_node.prev = self.tail
            self.tail = new_node

        return new_node

    def print_itinerary(self):
        """列印整個行程"""
        current = self.start_node
        step = 0
        
        print("\n每日行程：")
        while current:
            if current == self.start_node and step > 0:
                break
                
            step += 1
            print(f"步驟{step}：{current.name} (營業時間: {current.hours}, {current.start_time or '10:00'} - {current.end_time or '10:00'}, 停留時間: {current.duration}分鐘)")
            
            if current.next:
                print(f"➜ 前往 {current.next.name} | 交通方式: {current.next.transport_details} | 交通時間: {int(current.next.travel_time)}分鐘")
            
            current = current.next
        
        print(f"\nAPI 呼叫次數：{API_CALL_COUNT}次")


def convert_itinerary_to_trip_plan(itinerary, locations, start_location=None):
    """將行程列表轉換為 TripPlan"""
    trip_plan = TripPlan(start_location)
    trip_plan.start_node.start_time = '10:00'
    trip_plan.start_node.end_time = '10:00'

    for item in itinerary:
        location = next(
            (loc for loc in locations if loc['name'] == item['name']), None)
        if location:
            trip_plan.add_location(
                location,
                start_time=item['start_time'],
                end_time=item['end_time'],
                travel_time=item['travel_time'],
                transport_details=item['transport_details']
            )

    return trip_plan
