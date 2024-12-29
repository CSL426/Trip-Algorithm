# test_google_maps.py

import googlemaps
from datetime import datetime
from src.config.config import GOOGLE_MAPS_API_KEY


def test_google_maps_api():
    """測試 Google Maps API 的連線狀態

    測試項目：
    1. API 連線是否成功
    2. 基本路線規劃功能
    3. 錯誤處理機制
    """
    try:
        # 初始化 Google Maps 客戶端
        print("正在初始化 Google Maps 客戶端...")
        gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

        # 測試資料：台北車站到台北101
        origin = "台北車站"
        destination = "台北101"

        print(f"\n測試路線規劃: {origin} -> {destination}")

        # 執行路線規劃
        now = datetime.now()
        result = gmaps.directions(
            origin=origin,
            destination=destination,
            mode="transit",
            departure_time=now
        )

        if result:
            route = result[0]
            leg = route['legs'][0]

            print("\n路線規劃成功！")
            print(f"預估時間: {leg['duration']['text']}")
            print(f"預估距離: {leg['distance']['text']}")
            print(f"起點地址: {leg['start_address']}")
            print(f"終點地址: {leg['end_address']}")

            print("\n詳細路線:")
            for i, step in enumerate(leg['steps'], 1):
                print(
                    f"{i}. {step.get('html_instructions', '').replace('<b>', '').replace('</b>', '')}")

        else:
            print("錯誤：沒有找到路線")

    except Exception as e:
        print(f"\n錯誤：{str(e)}")
        print("API 可能出現問題，請檢查：")
        print("1. API 金鑰是否正確")
        print("2. 相關 API 服務是否已啟用")
        print("3. 是否有足夠的配額")
        print("4. 專案帳單是否正常")


if __name__ == "__main__":
    test_google_maps_api()
