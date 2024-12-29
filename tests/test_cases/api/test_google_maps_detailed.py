# test_google_maps_detailed.py

import googlemaps
from datetime import datetime
import requests


def test_basic_geocoding():
    """測試基本的地理編碼功能"""
    from src.config.config import GOOGLE_MAPS_API_KEY

    # 使用最基本的 Geocoding API
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        'address': '台北車站',
        'key': GOOGLE_MAPS_API_KEY
    }

    try:
        response = requests.get(url, params=params)
        print("\n=== Geocoding API 測試 ===")
        print(f"狀態碼: {response.status_code}")
        data = response.json()
        print(f"API 回應狀態: {data.get('status')}")
        if 'error_message' in data:
            print(f"錯誤訊息: {data['error_message']}")
        return response.status_code == 200 and data.get('status') == 'OK'

    except Exception as e:
        print(f"錯誤: {str(e)}")
        return False


def test_basic_directions():
    """測試基本的路線規劃功能"""
    from src.config.config import GOOGLE_MAPS_API_KEY

    # 使用 Directions API
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        'origin': '台北車站',
        'destination': '台北101',
        'mode': 'transit',
        'key': GOOGLE_MAPS_API_KEY
    }

    try:
        response = requests.get(url, params=params)
        print("\n=== Directions API 測試 ===")
        print(f"狀態碼: {response.status_code}")
        data = response.json()
        print(f"API 回應狀態: {data.get('status')}")
        if 'error_message' in data:
            print(f"錯誤訊息: {data['error_message']}")
            print(f"完整回應: {data}")
        return response.status_code == 200 and data.get('status') == 'OK'

    except Exception as e:
        print(f"錯誤: {str(e)}")
        return False


if __name__ == "__main__":
    print("開始測試 Google Maps API...")

    # 測試 Geocoding
    geocoding_ok = test_basic_geocoding()
    print(f"\nGeocoding 測試結果: {'成功' if geocoding_ok else '失敗'}")

    # 測試 Directions
    directions_ok = test_basic_directions()
    print(f"\nDirections 測試結果: {'成功' if directions_ok else '失敗'}")
