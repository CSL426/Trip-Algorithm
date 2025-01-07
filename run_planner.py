# run_planner.py

from src.core.planner import TripPlanningSystem
from sample_data import DEFAULT_LOCATIONS, DEFAULT_REQUIREMENT


def main():
    """主程式入口

    這是系統的啟動點，負責：
    1. 初始化系統
    2. 讀取必要的資料
    3. 執行規劃流程
    4. 處理可能的錯誤
    """
    try:
        # 初始化規劃系統
        system = TripPlanningSystem()

        # 顯示規劃參數
        print("=== 行程規劃系統 ===")
        print(f"起點：{DEFAULT_REQUIREMENT['start_point']}")
        print(f"時間：{DEFAULT_REQUIREMENT['start_time']} - "
              f"{DEFAULT_REQUIREMENT['end_time']}")
        print(f"午餐：{DEFAULT_REQUIREMENT['lunch_time']}")
        print(f"晚餐：{DEFAULT_REQUIREMENT['dinner_time']}")
        print(f"景點數量：{len(DEFAULT_LOCATIONS)}個")
        print(f"交通方式：{DEFAULT_REQUIREMENT['transport_mode']}")

        print("\n開始規劃行程...")

        # 執行行程規劃
        result = system.plan_trip(
            locations=DEFAULT_LOCATIONS,
            requirement=DEFAULT_REQUIREMENT
        )

        # 輸出結果
        system.print_itinerary(result, show_navigation=False)
        import pprint
        # pprint.pprint(result)

    except Exception as e:
        print(f"\n發生錯誤: {str(e)}")
        raise


if __name__ == "__main__":
    main()
