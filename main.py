# main.py
from src.core.TripPlanner import plan_trip
from src.line.formatter import LineFormatter


def main():
    # 測試用的地點資料
    locations = [
        {'name': '台北101', 'rating': 4.6, 'lat': 25.0339808, 'lon': 121.561964,
         'duration': 150, 'label': '景點', 'hours': '09:00 - 22:00'},
        {'name': '大安森林公園', 'rating': 4.7, 'lat': 25.029677, 'lon': 121.5178326,
         'duration': 130, 'label': '景點', 'hours': '24小時開放'}
    ]

    # 產生行程
    itinerary = plan_trip(
        locations=locations,
        start_time='09:00',
        end_time='20:00'
    )

    # 輸出 LINE 格式訊息
    formatter = LineFormatter()
    message = formatter.format_trip_to_line_message(itinerary)
    print(message)


if __name__ == "__main__":
    main()
