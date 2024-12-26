# main.py
import time
from src.core.trip_planner import TripPlanner
from src.core.test_data import TEST_LOCATIONS, TEST_CUSTOM_START
from src.core.trip_node import convert_itinerary_to_trip_plan
from src.line.formatter import LineFormatter
from src.core.models import StartEndPoint

def main():
    """
    主程式進入點
    執行順序：建立規劃器 -> 初始化地點 -> 規劃行程 -> 輸出結果
    """
    # 記錄開始時間，用於計算總執行時間
    total_start_time = time.time()

    # 建立行程規劃器實例
    planner = TripPlanner()
    # 測試案例們
    test_cases = [
        {
            "name": "情境1：開車 指定起終點",
            "start_time": "09:00",
            "end_time": "20:00",
            "travel_mode": "開車",
            "custom_start": "24.95364,121.223017",
            "custom_end": "行天宮"
        },
        # {
        #     "name": "情境2：大眾運輸 不指定起終點",
        #     "start_time": "08:00",
        #     "end_time": "18:00",
        #     "travel_mode": "大眾運輸",
        #     "custom_start": None,
        #     "custom_end": None
        # }
    ]
    for case in test_cases:
        print(f"\n=== 測試 {case['name']} ===")
        try:
            # 初始化地點資料
            # 輸入：
            #   - TEST_LOCATIONS: 景點清單，格式為 List[Dict]
            #     每個景點需包含：name, lat, lon, duration, label, hours 等資訊
            planner.initialize_locations(TEST_LOCATIONS)

            # 執行行程規劃
            # 輸入參數說明：
            #   - start_time: 開始時間 (格式: 'HH:MM')
            #   - end_time: 結束時間 (格式: 'HH:MM')
            #   - travel_mode: 交通方式 ("大眾運輸", "開車", "騎自行車", "步行")
            #   - custom_start: 自訂起點 (Dict，包含 name, lat, lon 等資訊)
            #   - custom_end: 自訂終點 (Dict，包含 name, lat, lon 等資訊)
            # 輸出：
            #   - itinerary: List[Dict] 格式的行程清單
            itinerary = planner.plan(
                start_time=case["start_time"],
                end_time=case["end_time"],
                travel_mode=case["travel_mode"],
                custom_start=case["custom_start"],
                custom_end=case["custom_end"]
            )

            print("\n=== 一般格式輸出 ===")
            # 轉換行程格式並印出
            # 輸入：itinerary (List[Dict])
            # 輸出：TripPlan 物件，包含完整行程資訊
            trip_plan = convert_itinerary_to_trip_plan(itinerary)
            trip_plan.print_itinerary()

            print("\n=== LINE 格式輸出 ===")
            # 轉換成 LINE 訊息格式
            # 輸入：itinerary (List[Dict])
            # 輸出：str，格式化的 LINE 訊息文字
            line_message = LineFormatter.format_trip_to_line_message(itinerary)
            print(line_message)

            # 計算並顯示總執行時間
            total_execution_time = time.time() - total_start_time
            print(f"\n總執行時間：{total_execution_time:.2f}秒")

        except Exception as e:
            print(f"發生錯誤: {str(e)}")


if __name__ == "__main__":
    main()
