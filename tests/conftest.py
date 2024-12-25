# test/conftest.py

#fmt: off
import os
import sys
from pathlib import Path

# 獲取專案根目錄並加入 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# 之後再導入其他模組
import pytest
from src.core.TripPlanner import TripPlanner
#fmt: on


@pytest.fixture
def sample_locations():
    """
    提供測試用的景點資料
    回傳：List[Dict] - 包含景點基本資訊的列表
    """
    return [
        {
            'name': '台北101',
            'lat': 25.0339808,
            'lon': 121.561964,
            'duration': 150,
            'label': '景點',
            'hours': {  # 改為字典格式
                1: [{'start': '09:00', 'end': '22:00'}],
                2: [{'start': '09:00', 'end': '22:00'}],
                3: [{'start': '09:00', 'end': '22:00'}],
                4: [{'start': '09:00', 'end': '22:00'}],
                5: [{'start': '09:00', 'end': '22:00'}],
                6: [{'start': '09:00', 'end': '22:00'}],
                7: [{'start': '09:00', 'end': '22:00'}]
            }
        }
    ]


@pytest.fixture
def trip_planner(sample_locations):
    """
    建立 TripPlanner 實例並規劃行程
    參數：
        sample_locations: 由上面的 fixture 提供的測試資料
    回傳：
        List[Dict] - 規劃好的行程列表
    """
    planner = TripPlanner()
    planner.initialize_locations(sample_locations)
    return planner.plan(
        start_time='09:00',
        end_time='18:00',
        travel_mode='driving'
    )


if __name__ == "__main__":
    # 這個文件通常不會直接執行，但如果需要可以加入測試代碼
    planner = trip_planner(sample_locations())
    print(planner)
