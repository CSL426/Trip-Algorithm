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


def convert_to_place_list(df: pd.DataFrame) -> List[Dict]:
    """
    將 DataFrame 轉換成地點資料列表

    輸入:
        df (pd.DataFrame): 包含地點資料的DataFrame

    輸出:
        List[Dict]: 地點資料列表，每個字典包含:
            - name: 地點名稱(str)
            - rating: 評分(float)
            - lat: 緯度(float)
            - lon: 經度(float)
            - duration_min: 建議停留時間(int)，預設90分鐘
            - label: 地點類型標籤(str)
            - period: 時段標記(str)
            - hours: 營業時間(Dict)
                    如果全部為None，則轉換成24小時營業
                    格式: {1-7: [{'start': '00:00', 'end': '23:59'}]}
    """
    places = []

    for _, row in df.iterrows():
        # 根據地點類型設定預設停留時間
        default_duration = {
            "餐廳": 90,
            "小食": 30,
            "景點": 120,
            "購物": 60
        }

        duration = default_duration.get(row['label'], 60)

        # 檢查營業時間
        hours = row['hours']

        # 檢查是否所有天數都是直接等於 None 或是 [None]
        all_none = all(
            hours.get(day) is None or hours.get(day) == [None]
            for day in range(1, 8)
        )

        # 如果全部是 None，設定成24小時營業
        if all_none:
            hours = {
                day: [{'start': '00:00', 'end': '23:59'}]
                for day in range(1, 8)
            }

        place = {
            "name": row['name'],
            "rating": float(row['rating']),
            "lat": float(row['lat']),
            "lon": float(row['lon']),
            "duration_min": duration,
            "label": row['label'],
            "period": row['period'],
            "hours": hours
        }
        places.append(place)

    return places


# 使用範例
if __name__ == "__main__":
    # 先讀取 CSV
    df = process_csv("sample_data.csv")

    # 轉換成地點列表
    places = convert_to_place_list(df)

    # 印出第一個地點的資訊檢查
    print("\n第100個地點資訊:")
    for key, value in places[100].items():
        print(f"{key}:", value)

    print(places[100])
