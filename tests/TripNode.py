def format_duration(minutes):
    """將分鐘轉換為小時和分鐘格式"""
    hours = minutes // 60
    remaining_minutes = minutes % 60
    if hours > 0:
        return f"{hours}小時{remaining_minutes}分鐘" if remaining_minutes > 0 else f"{hours}小時"
    return f"{minutes}分鐘"


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
    def __init__(self):
        self.head = None

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
        from datetime import datetime

        current = self.head
        total_duration = 0
        total_travel_time = 0
        visit_count = 0
        start_time = self.head.start_time
        end_time = None

        print("每日行程：")

        while current:
            is_start = current.step == 0
            is_end = current.next is None

            # 顯示景點資訊
            if is_start or is_end:
                print(f"步驟{current.step + 1}：{current.name}")
            else:
                # 如果不是24小時營業，顯示營業時間
                if current.hours != '24小時開放':
                    print(f"步驟{current.step + 1}：{current.name}（停留：{current.start_time} - {
                          current.end_time}，{format_duration(current.duration)}｜營業：{current.hours}）")
                else:
                    print(f"步驟{current.step + 1}：{current.name}（停留：{current.start_time} - {
                          current.end_time}，{format_duration(current.duration)}）")
                total_duration += current.duration
                visit_count += 1
                end_time = current.end_time

            # 顯示交通資訊（不包括最後一個節點）
            if current.next:
                transport_text = "大眾運輸" if "預估" in current.next.transport_details else current.next.transport_details
                travel_time = int(current.next.travel_time)
                print(f"↓ {transport_text} {format_duration(travel_time)}")
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


def convert_itinerary_to_trip_plan(itinerary, locations=None):
    trip_plan = TripPlan()
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
