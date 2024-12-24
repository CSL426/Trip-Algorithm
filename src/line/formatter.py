# src/line/formatter.py

def format_business_hours(hours_data):
    """
    將營業時間資料轉換為易讀格式

    參數：
        hours_data (Dict): 包含每天營業時間的字典
        格式為：{weekday: [{'start': 'HH:MM', 'end': 'HH:MM'}]}

    回傳：
        str: 格式化後的營業時間字串，例如：'09:00 - 17:00'
    """
    if isinstance(hours_data, str):
        return hours_data

    # 如果是字典格式，取得第一天的營業時間作為顯示
    # 因為目前的例子中，每天的營業時間都一樣
    if isinstance(hours_data, dict) and len(hours_data) > 0:
        first_day = min(hours_data.keys())  # 取得最小的 key（通常是 1，代表週一）
        if hours_data[first_day]:  # 確認有營業時間資料
            time_period = hours_data[first_day][0]  # 取得第一個時段
            return f"{time_period['start']} - {time_period['end']}"

    return '24小時開放'  # 預設值


class LineFormatter:
    @staticmethod
    def format_trip_to_line_message(itinerary: list) -> str:
        """
        將行程轉換為 LINE 訊息格式

        參數：
            itinerary (List[Dict]): 行程清單

        回傳：
            str: 格式化後的 LINE 訊息
        """
        message_parts = ["📍 一日行程\n"]

        for entry in itinerary:
            # 起點
            if entry['step'] == 0:
                message_parts.append(
                    f"➡️ {entry['start_time']} 從 {entry['name']} 出發\n"
                )
                continue

            # 終點
            if entry['step'] == len(itinerary) - 1:
                message_parts.append(
                    f"🏁 {entry['start_time']} 抵達 {entry['name']}\n"
                )
                continue

            # 一般景點
            message_parts.append(
                f"\n{'🍽️' if entry.get('is_meal') else '🏰'} {entry['name']}"
            )
            message_parts.append(
                f"⏰ {entry['start_time']} - {entry['end_time']}"
            )

            # 處理營業時間顯示
            business_hours = format_business_hours(entry['hours'])
            if business_hours != '24小時開放':
                message_parts.append(f"📅 營業時間：{business_hours}")

            # 停留時間
            duration_text = f"{entry['duration']}分鐘"
            message_parts.append(f"⌛ 停留：{duration_text}")

            # 下一站的交通資訊
            if entry['step'] < len(itinerary) - 1:
                next_entry = itinerary[entry['step'] + 1]
                travel_time = f"{int(next_entry['travel_time'])}分鐘"
                transport = next_entry['transport_details']
                message_parts.append(f"🚉 交通：{transport}（{travel_time}）")

        return "\n".join(message_parts)
