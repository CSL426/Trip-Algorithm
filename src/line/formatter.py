# src/line/formatter.py
import os
import sys
from pathlib import Path

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from src.core.TripNode import TripNode, TripPlan

class LineFormatter:
    @staticmethod
    def format_trip_to_line_message(itinerary: list) -> str:
        """將行程轉換為 LINE 訊息格式"""
        message_parts = ["📍 今日行程\n"]
        
        for entry in itinerary:
            # 起點
            if entry['step'] == 0:
                message_parts.append(f"➡️ {entry['start_time']} 從 {entry['name']} 出發\n")
                continue
                
            # 終點
            if entry['step'] == len(itinerary) - 1:
                message_parts.append(f"🏁 {entry['start_time']} 抵達 {entry['name']}\n")
                continue
            
            # 一般景點
            message_parts.append(f"\n{'🍽️' if entry.get('is_meal') else '🏰'} {entry['name']}")
            message_parts.append(f"⏰ {entry['start_time']} - {entry['end_time']}")
            
            if entry['hours'] != '24小時開放':
                message_parts.append(f"📅 營業時間：{entry['hours']}")
            
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