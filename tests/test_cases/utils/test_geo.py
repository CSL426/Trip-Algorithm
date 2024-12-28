# tests/test_cases/utils/test_geo.py

import pytest
from src.core.utils.geo import GeoCalculator


class TestGeoCalculator:
    """測試地理位置計算相關的功能。

    我們會測試幾個關鍵的地點來確保計算的準確性：
    1. 台北車站到台北101的距離
    2. 大安森林公園的區域範圍
    3. 多個地點的中心點計算
    """

    def test_calculate_distance(self):
        """測試兩點間距離計算的合理性。
        
        我們不需要完全精確的距離，
        只要確保計算出來的距離大致合理，
        能夠用於評估景點間的可及性即可。
        """
        # 設定測試資料：台北車站和台北101的實際座標
        taipei_station = {"lat": 25.0478, "lon": 121.5170}
        taipei_101 = {"lat": 25.0339, "lon": 121.5619}
        
        # 計算距離
        distance = GeoCalculator.calculate_distance(taipei_station, taipei_101)
        
        # 確保距離在合理範圍內（比如說3-6公里）
        assert 3 < distance < 6, "計算出的距離明顯不合理"

    def test_calculate_region_bounds(self):
        """測試區域範圍計算的準確性。

        我們檢查以某個中心點為基準，計算指定半徑的區域範圍。
        這個測試確保區域範圍的計算考慮了地球曲率的影響。
        """
        # 以大安森林公園為中心點
        center = {"lat": 25.0296, "lon": 121.5357}
        radius_km = 1.0  # 1公里的搜尋範圍

        # 計算區域範圍
        min_lat, max_lat, min_lon, max_lon = GeoCalculator.calculate_region_bounds(
            center, radius_km)

        # 驗證範圍的合理性
        assert min_lat < center["lat"] < max_lat, "緯度範圍計算有誤"
        assert min_lon < center["lon"] < max_lon, "經度範圍計算有誤"

        # 檢查範圍大小是否合理（1公里大約是0.01度）
        assert abs(max_lat - min_lat) < 0.02, "緯度範圍過大"
        assert abs(max_lon - min_lon) < 0.02, "經度範圍過大"

    def test_is_point_in_bounds(self):
        """測試點位是否在指定範圍內的判斷。

        我們使用實際的地標來測試範圍判斷功能，確保能正確判斷
        一個點是否落在指定的矩形範圍內。
        """
        # 設定測試範圍（以台北車站為中心的大約 1 公里範圍）
        bounds = (25.0378, 25.0578, 121.5070, 121.5270)

        # 測試範圍內的點（台北北門）
        point_in = {"lat": 25.0491, "lon": 121.5101}
        assert GeoCalculator.is_point_in_bounds(point_in, bounds), \
            "應該要判斷為在範圍內的點被判斷為範圍外"

        # 測試範圍外的點（台北101）
        point_out = {"lat": 25.0339, "lon": 121.5619}
        assert not GeoCalculator.is_point_in_bounds(point_out, bounds), \
            "應該要判斷為在範圍外的點被判斷為範圍內"

    def test_calculate_midpoint(self):
        """測試多個點的中心點計算。

        我們使用多個實際地標來測試中心點計算功能，確保計算結果
        落在所有點的合理範圍內。
        """
        # 設定測試點位
        points = [
            {"lat": 25.0478, "lon": 121.5170},  # 台北車站
            {"lat": 25.0339, "lon": 121.5619},  # 台北101
            {"lat": 25.0296, "lon": 121.5357}   # 大安森林公園
        ]

        # 計算中心點
        center = GeoCalculator.calculate_midpoint(points)

        # 驗證結果的合理性
        assert 25.02 < center["lat"] < 25.05, "中心點緯度超出合理範圍"
        assert 121.51 < center["lon"] < 121.57, "中心點經度超出合理範圍"

    def test_invalid_inputs(self):
        """測試無效輸入的處理。

        確保當提供無效的輸入時，程式能夠適當地處理並拋出正確的異常。
        """
        # 測試空的點位列表
        with pytest.raises(ValueError, match="點位列表不能為空"):
            GeoCalculator.calculate_midpoint([])

        # 測試無效的座標值
        invalid_point = {"lat": 91, "lon": 121}  # 緯度超過90度
        with pytest.raises(ValueError):
            GeoCalculator.calculate_distance(
                invalid_point, {"lat": 25, "lon": 121})
