# sample_data.py

import ast
import os
from typing import List, Dict
import pandas as pd

# 預設行程需求
DEFAULT_REQUIREMENT = {
    "start_time": None,
    "end_time": "21:00",
    "start_point": "中壢火車站",
    "end_point": None,
    "transport_mode": "driving",
    "distance_threshold": 30,
    "breakfast_time": None,
    "lunch_time": None,
    "dinner_time": "18:00",
    "budget": None,
    "date": None
}


def process_csv(filepath: str) -> pd.DataFrame:
    """處理景點資料的CSV檔案

    輸入:
        filepath (str): CSV檔案路徑

    輸出:
        pd.DataFrame: 處理後的資料框架，包含以下欄位:
        - name: 景點名稱
        - rating: 評分(float)
        - lat: 緯度(float)
        - lon: 經度(float)
        - label: 類型標籤
        - period: 時段標記
        - hours: 營業時間(dict)
    """
    df = pd.read_csv(filepath)

    def convert_hours(hours_str):
        try:
            return ast.literal_eval(hours_str)
        except:
            print(f"Error parsing hours: {hours_str}")
            return {}

    processed_df = pd.DataFrame({
        'placeID': df['place_id'],
        'name': df['place_name'],
        'rating': df['rating'].astype(float),
        'lat': df['lat'].astype(float),
        'lon': df['lon'].astype(float),
        'label': df['label'],
        'period': df['period'],
        'hours': df['hours'].apply(convert_hours)
    })

    return processed_df


def get_duration_by_label(label: str) -> int:
    """根據地點標籤返回建議停留時間（分鐘）"""
    durations = {
        # 正餐餐廳 (90分鐘)
        90: [
            '中菜館', '中餐館', '台灣餐廳', '壽司店',
            '多國菜餐廳', '意大利餐廳', '日本餐廳',
            '泰國餐廳', '海鮮餐廳', '港式茶餐廳',
            '火鍋餐廳', '燒烤餐廳', '美式牛扒屋',
            '純素餐廳', '素食餐廳', '餐廳'
        ],
        # 快速餐飲 (45分鐘)
        45: [
            '小食/零食吧', '快餐店', '立食吧',
            '自助餐餐廳', '麵店'
        ],
        # 小吃/串燒 (30分鐘)
        30: [
            '小吃攤', '串燒烤肉店', '日式烤雞串餐廳',
            '炸物串與串炸餐廳'
        ],
        # 景點 (120分鐘)
        120: ['景點', '旅遊景點'],
        # 酒吧休閒 (60分鐘)
        60: ['酒吧', '酒吧扒房', '居酒屋']
    }

    for duration, labels in durations.items():
        if label in labels:
            return duration
    return 60  # 預設 60 分鐘


def convert_to_place_list(df: pd.DataFrame) -> List[Dict]:
    """將DataFrame轉換為地點列表

    輸入:
        df: 包含地點資料的DataFrame

    輸出:
        List[Dict]: 地點資料列表，依照時段分類整理
    """
    places = []

    for _, row in df.iterrows():
        # 取得停留時間
        duration = get_duration_by_label(row['label'])

        # 處理營業時間
        hours = row['hours']
        for day in range(1, 8):
            if day not in hours or hours[day] is None:
                hours[day] = [{'start': '00:00', 'end': '23:59'}]
            elif hours[day] == [None]:
                hours[day] = [{'start': '00:00', 'end': '23:59'}]

        place = {
            "placeID": row['placeID'],
            "name": row['name'],
            "rating": float(row['rating']),
            "lat": float(row['lat']),
            "lon": float(row['lon']),
            "duration": duration,
            "label": row['label'],
            "period": row['period'],
            "hours": hours
        }
        places.append(place)

    return sort_places_by_period(places)


def sort_places_by_period(places: List[Dict]) -> List[Dict]:
    """依照時段對地點進行分類排序

    輸入:
        places: 地點列表

    輸出:
        List[Dict]: 依照時段排序後的地點列表
    """
    # 定義時段順序
    period_order = ['morning', 'lunch', 'afternoon', 'dinner', 'night']

    # 依照時段排序
    return sorted(places, key=lambda x: period_order.index(x['period']))


# 取得目前檔案的目錄
current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, "sample_data.csv")

# 建立預設資料
df = process_csv(file_path)

DEFAULT_LOCATIONS = convert_to_place_list(df)
