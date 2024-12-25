# tests\test_models.py
from src.core.models import TripRequirement, StartEndPoint


def test_input_formats():
    """測試不同的輸入格式"""
    print("=== 測試輸入輸出格式 ===")

    # 測試需求輸入
    test_requirement = {
        "出發時間": "09:00",
        "結束時間": "18:00",
        "出發地點": "中壢火車站",
        "結束地點": "25.0339808,121.561964",  # 用經緯度
        "交通方式": "大眾運輸",
        "可接受距離門檻": 30,
        "早餐時間": "none",
        "午餐時間": "12:00",
        "晚餐時間": "18:00",
        "預算": 0,
        "出發日": "none"
    }

    try:
        # 驗證需求格式
        requirement = TripRequirement(**test_requirement)
        print("\n1. 需求驗證成功：")
        print(f"出發地點: {requirement.出發地點}")
        print(f"結束地點: {requirement.結束地點}")
    except Exception as e:
        print(f"需求格式錯誤: {str(e)}")


def test_custom_locations():
    """測試自訂起訖點"""
    print("\n=== 測試自訂起訖點 ===")

    # 測試地點名稱
    print("\n1. 用地點名稱：")
    start_point = StartEndPoint.parse_input("中壢火車站")
    print(f"名稱: {start_point.name}")
    print(f"位置: {start_point.lat}, {start_point.lon}")

    # 測試經緯度
    print("\n2. 用經緯度：")
    end_point = StartEndPoint.parse_input("25.0339808,121.561964")
    print(f"名稱: {end_point.name}")
    print(f"位置: {end_point.lat}, {end_point.lon}")


if __name__ == "__main__":
    test_input_formats()
    test_custom_locations()
