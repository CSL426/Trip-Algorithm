# tests/__init__.py

"""
行程規劃系統測試套件
此套件包含所有測試案例，確保系統功能的正確性和穩定性

測試架構：
1. test_cases/ - 所有測試案例
   - models/ - 資料模型測試
   - utils/ - 工具函數測試
   - planner/ - 規劃器測試
2. data/ - 測試資料
   - test_data.py - 測試用的範例資料

使用說明：
1. 執行所有測試：
   pytest tests/

2. 執行特定模組測試：
   pytest tests/test_cases/models/
   pytest tests/test_cases/utils/
   pytest tests/test_cases/planner/

3. 執行特定檔案測試：
   pytest tests/test_cases/models/test_time.py
"""

import os
import sys
import pytest
from datetime import datetime, timedelta

# 將專案根目錄加入 Python 路徑
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 共用的測試常數
TEST_CONSTANTS = {
    "DEFAULT_START_TIME": "09:00",
    "DEFAULT_END_TIME": "18:00",
    "DEFAULT_TRAVEL_MODE": "transit",
    "DEFAULT_DISTANCE_THRESHOLD": 30.0,
    "DEFAULT_EFFICIENCY_THRESHOLD": 0.1
}

# 共用的測試資料
SAMPLE_LOCATIONS = [
    {
        "name": "台北101",
        "lat": 25.0339808,
        "lon": 121.561964,
        "duration": 90,
        "label": "景點",
        "hours": {
            i: [{'start': '09:00', 'end': '22:00'}]
            for i in range(1, 8)
        }
    },
    {
        "name": "國立故宮博物院",
        "lat": 25.1023,
        "lon": 121.5482,
        "duration": 120,
        "label": "博物館",
        "hours": {
            i: [{'start': '08:30', 'end': '18:30'}]
            for i in range(1, 8)
        }
    },
    {
        "name": "鼎泰豐",
        "lat": 25.0329,
        "lon": 121.5604,
        "duration": 60,
        "label": "餐廳",
        "hours": {
            i: [
                {'start': '11:30', 'end': '14:30'},
                {'start': '17:30', 'end': '21:30'}
            ] for i in range(1, 8)
        }
    }
]

# 共用的輔助函數


def create_test_datetime(time_str: str) -> datetime:
    """
    建立測試用的日期時間物件

    輸入參數：
        time_str: 時間字串(格式：HH:MM)

    回傳：
        datetime: 當天的指定時間
    """
    return datetime.strptime(time_str, "%H:%M")


def get_default_test_range() -> tuple:
    """
    取得預設的測試時間範圍

    回傳：
        tuple: (開始時間, 結束時間)，皆為 datetime 物件
    """
    start = create_test_datetime(TEST_CONSTANTS["DEFAULT_START_TIME"])
    end = create_test_datetime(TEST_CONSTANTS["DEFAULT_END_TIME"])
    return start, end


def skip_if_no_api_key(func):
    """
    當沒有 API 金鑰時跳過測試的裝飾器

    使用方式：
        @skip_if_no_api_key
        def test_api_function():
            ...
    """
    return pytest.mark.skipif(
        "MAPS_API_KEY" not in os.environ,
        reason="需要 Google Maps API 金鑰"
    )(func)

# 註冊全域的 fixtures


def pytest_configure(config):
    """
    設定 pytest 的全域配置
    """
    config.addinivalue_line(
        "markers",
        "integration: 標記整合測試"
    )
    config.addinivalue_line(
        "markers",
        "slow: 標記執行較慢的測試"
    )


def pytest_collection_modifyitems(items):
    """
    修改測試項目的收集方式
    可以在這裡添加自訂的測試標記
    """
    for item in items:
        # 標記所有超過2秒的測試為慢速測試
        if "test_execute_full_planning" in item.name:
            item.add_marker(pytest.mark.slow)

        # 標記所有需要外部服務的測試
        if "test_api" in item.name:
            item.add_marker(pytest.mark.integration)
