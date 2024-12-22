import time
from src.core.TripPlanner import TripPlanner
from src.core.test_data import TEST_LOCATIONS, TEST_CUSTOM_START
from src.core.TripNode import convert_itinerary_to_trip_plan
from src.line.formatter import LineFormatter

def main():
    total_start_time = time.time()

    # 建立規劃器實例
    planner = TripPlanner()
    
    try:
        # 載入測試資料
        planner.load_locations(TEST_LOCATIONS)
        
        # 規劃行程
        itinerary = planner.plan(
            start_time='09:00',
            end_time='20:00',
            travel_mode='transit',
            custom_start=TEST_CUSTOM_START,
            custom_end=TEST_CUSTOM_START  # 結束後返回住家
        )

        print("\n=== 一般格式輸出 ===")
        # 轉換並印出行程
        trip_plan = convert_itinerary_to_trip_plan(itinerary)
        trip_plan.print_itinerary()

        print("\n=== LINE 格式輸出 ===")
        # 使用 LINE formatter 輸出
        line_message = LineFormatter.format_trip_to_line_message(itinerary)
        print(line_message)

        total_execution_time = time.time() - total_start_time
        print(f"\n總執行時間：{total_execution_time:.2f}秒")
        
    except Exception as e:
        print(f"發生錯誤: {str(e)}")

if __name__ == "__main__":
    main()