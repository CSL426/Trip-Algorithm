# src\core\TripNode.py
from datetime import datetime, timedelta


def format_duration(minutes):
    """將分鐘轉換為小時和分鐘格式"""
    hours = minutes // 60
    remaining_minutes = minutes % 60
    if hours > 0:
        return f"{hours}小時{remaining_minutes}分鐘" if remaining_minutes > 0 else f"{hours}小時"
    return f"{minutes}分鐘"


def get_weekday_chinese(weekday):
    """將數字星期轉換為中文"""
    weekdays = {
        0: "一",
        1: "二",
        2: "三",
        3: "四",
        4: "五",
        5: "六",
        6: "日"
    }
    return weekdays.get(weekday, "一")


def format_business_hours(hours_dict, target_date):
    """將營業時間字典轉換為易讀格式"""
    if isinstance(hours_dict, str):
        return hours_dict
    if not isinstance(hours_dict, dict):
        return "24小時開放"

    # 取得目標日期的星期(1-7)
    weekday = target_date.weekday() + 1

    if weekday in hours_dict:
        periods = hours_dict[weekday]
        if not periods:
            return "休息"

        time_periods = []
        for period in periods:
            start = period['start']
            end = period['end']
            time_periods.append(f"{start}-{end}")

        return "、".join(time_periods)

    return "24小時開放"


class TripNode:
    def __init__(self, step, name, start_time, end_time, duration, travel_time, transport_details, hours):
        self.step = step
        self.name = name
        self.start_time = start_time
        self.end_time = end_time
        self.duration = duration
        self.travel_time = travel_time
        self.transport_details = transport_details
        self.hours = hours
        self.next = None


class TripPlan:
    def __init__(self, trip_date=None):
        self.head = None
        # 如果沒有指定日期，預設為明天
        self.trip_date = trip_date or (datetime.now() + timedelta(days=1))

    def add_node(self, step, name, start_time, end_time, duration, travel_time, transport_details, hours):
        new_node = TripNode(step, name, start_time, end_time,
                            duration, travel_time, transport_details, hours)
        if not self.head:
            self.head = new_node
            return
        current = self.head
        while current.next:
            current = current.next
        current.next = new_node

    def print_itinerary(self):
        current = self.head
        total_duration = 0
        total_travel_time = 0
        visit_count = 0
        start_time = self.head.start_time
        end_time = None

        # 格式化日期顯示
        date_str = self.trip_date.strftime("%m月%d日")
        weekday = get_weekday_chinese(self.trip_date.weekday())
        print(f"\n一日行程 ({date_str} 星期{weekday})：")

        while current:
            is_start = current.step == 0
            is_end = current.next is None

            # 顯示景點資訊
            if is_start or is_end:
                print(f"步驟{current.step + 1}：{current.name}")
            else:
                business_hours = format_business_hours(
                    current.hours, self.trip_date)
                if business_hours != "24小時開放":
                    print(f"步驟{current.step + 1}：{current.name}"
                          f" (停留：{current.start_time} - {current.end_time}，"
                          f"{format_duration(current.duration)}｜營業：{business_hours})")
                else:
                    print(f"步驟{current.step + 1}：{current.name}"
                          f" (停留：{current.start_time} - {current.end_time}，"
                          f"{format_duration(current.duration)})")
                total_duration += current.duration
                visit_count += 1
                end_time = current.end_time

            # 顯示交通資訊(不包括最後一個節點)
            if current.next:
                travel_time = int(current.next.travel_time)
                print(f"↓ {current.next.transport_details} "
                      f"{format_duration(travel_time)}")
                total_travel_time += travel_time

            current = current.next

        # 計算實際總時間
        start_datetime = datetime.strptime(start_time, '%H:%M')
        end_datetime = datetime.strptime(end_time, '%H:%M')
        total_minutes = (end_datetime - start_datetime).seconds // 60

        # 顯示行程總結
        print("\n行程總結：")
        print(f"景點數量：{visit_count}個景點")
        print(f"總停留時間：約{format_duration(total_duration)}")
        print(f"總交通時間：約{format_duration(total_travel_time)}")
        print(
            f"行程時間：{start_time} - {end_time} ({format_duration(total_minutes)})")


def convert_itinerary_to_trip_plan(itinerary, locations=None, trip_date=None):
    """將行程轉換為 TripPlan 物件"""
    trip_plan = TripPlan(trip_date=trip_date)
    for entry in itinerary:
        trip_plan.add_node(
            entry['step'],
            entry['name'],
            entry['start_time'],
            entry['end_time'],
            entry['duration'],
            entry['travel_time'],
            entry['transport_details'],
            entry['hours']
        )
    return trip_plan
