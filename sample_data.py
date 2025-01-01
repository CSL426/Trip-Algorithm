# sample_data.py

from typing import List, Dict
import pandas as pd
import ast


def process_csv(filepath: str) -> pd.DataFrame:
    """
    處理景點資料的CSV檔案

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
    # 讀取 CSV
    df = pd.read_csv(filepath)

    # 處理 hours 欄位 (從字串轉成字典)
    def convert_hours(hours_str):
        try:
            # 使用 ast.literal_eval 比 eval 更安全
            return ast.literal_eval(hours_str)
        except:
            print(f"Error parsing hours: {hours_str}")
            return {}

    # 轉換資料
    processed_df = pd.DataFrame({
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
    """
    根據地點標籤返回建議停留時間（分鐘）
    """
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

    # 尋找對應的停留時間
    for duration, labels in durations.items():
        if label in labels:
            return duration

    return 60  # 預設 60 分鐘


def convert_to_place_list(df: pd.DataFrame) -> List[Dict]:
    places = []

    for _, row in df.iterrows():
        # 取得停留時間
        duration = get_duration_by_label(row['label'])

        # 檢查營業時間
        hours = row['hours']
        all_none = all(
            hours.get(day) is None or hours.get(day) == [None]
            for day in range(1, 8)
        )

        hours = row['hours']
        for day in range(1, 8):
            if day not in hours or hours[day] is None:
                hours[day] = [{'start': '00:00', 'end': '23:59'}]
            elif hours[day] == [None]:
                hours[day] = [{'start': '00:00', 'end': '23:59'}]

        place = {
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

    return places


def get_unique_labels(df: pd.DataFrame) -> List[str]:
    """
    取得所有不重複的地點標籤

    輸入:
        df (pd.DataFrame): 包含地點資料的DataFrame

    輸出:
        List[str]: 不重複的標籤列表
    """
    return sorted(df['label'].unique().tolist())


# 使用範例
if __name__ == "__main__":
    # 先讀取 CSV
    df = process_csv("sample_data.csv")

    # 轉換成地點列表
    places = convert_to_place_list(df)

    # 印出第一個地點的資訊檢查
    n = 99
    print(f"第{n}個地點資訊:")
    for key, value in places[n].items():
        print(f"{key}:", value)

    for place in places[:2]:  # 印出前兩筆
        print(f"\n地點: {place['name']}")
        print(f"類型: {place['label']}")
        print(f"停留時間: {place['duration']}分鐘")

    # print(places[99])
    # labels = get_unique_labels(df)
    # print("所有不重複的標籤:", labels)
