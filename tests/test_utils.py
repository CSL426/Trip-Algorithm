# tests\test_utils.py

# fmt: off
import os
import sys
from pathlib import Path

# 獲取專案根目錄
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# 之後再導入其他模組
from src.core.utils import calculate_distance, calculate_travel_time, parse_hours
# fmt: on


def test_utils():
    # 測試距離計算
    lat1, lon1 = 25.0339808, 121.561964  # 台北101
    lat2, lon2 = 25.029677, 121.5178326  # 大安森林公園

    distance = calculate_distance(lat1, lon1, lat2, lon2)
    print(f"距離：{distance:.2f} 公里")

    # 測試營業時間解析
    hours = "09:00 - 22:00"
    open_time, close_time = parse_hours(hours)
    print(f"營業時間：{open_time} 到 {close_time}")


if __name__ == "__main__":
    test_utils()
