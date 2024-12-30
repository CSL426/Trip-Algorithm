# src/core/planner/__init__.py

"""
行程規劃模組
此模組整合了所有行程規劃相關的功能，提供了一個統一的介面來處理行程規劃需求。

主要功能：
1. 行程規劃的核心邏輯
2. 地點評分和選擇策略
3. 輸入驗證和資料處理
4. 時間和交通管理

使用範例：
    from src.core.planner import TripPlanner

    # 建立規劃器實例
    planner = TripPlanner()

    # 初始化地點資料
    locations = [
        {
            'name': '台北101',
            'lat': 25.0339,
            'lon': 121.5619,
            'duration': 90,
            'label': '景點'
        }
        # ... 其他地點
    ]

    # 設定自訂起點(可選)
    custom_start = {
        'name': '台北車站',
        'lat': 25.0478,
        'lon': 121.5170
    }

    # 初始化地點資料
    planner.initialize_locations(locations, custom_start=custom_start)

    # 執行規劃
    itinerary = planner.plan(
        start_time='09:00',
        end_time='18:00',
        travel_mode='transit'
    )
"""

from datetime import datetime, timedelta
from typing import Any, List, Dict, Optional, Union

from .base import TripPlanner as BasePlanner
from .strategy import PlanningStrategy
from .validator import InputValidator


class TripPlanner(BasePlanner):
    """
    行程規劃器整合類別
    將基礎功能、規劃策略和驗證邏輯整合成一個易用的介面

    這個類別繼承了基礎規劃器的功能，並加入了：
    1. 智能的規劃策略
    2. 完整的資料驗證
    3. 彈性的配置選項
    """

    def _generate_itinerary(self) -> List[Dict[str, Any]]:
        """
        實作行程生成的具體邏輯

        這個方法整合了：
        1. 規劃策略的執行
        2. 起點和終點的處理
        3. 完整的行程格式化

        回傳：
            List[Dict]: 完整的行程安排列表，包含：
            - step: 順序編號
            - name: 地點名稱
            - start_time: 開始時間
            - end_time: 結束時間
            - duration: 停留時間
            - transport_details: 交通方式說明
            - travel_time: 交通時間
        """
        # 建立規劃策略
        strategy = PlanningStrategy(
            start_time=self.start_datetime,
            end_time=self.end_datetime,
            travel_mode=self.travel_mode,
            distance_threshold=self.distance_threshold,
            efficiency_threshold=self.efficiency_threshold
        )

        # 執行規劃
        itinerary = strategy.execute(
            current_location=self.start_location,
            available_locations=self.available_locations,
            current_time=self.start_datetime
        )

        # 如果有行程且終點不同於起點，加入返回終點的路線
        if itinerary and self.end_location != self.start_location:
            last_location = self.end_location
            last_visit_time = datetime.strptime(
                itinerary[-1]['end_time'], '%H:%M')

            # 計算返回終點的交通資訊
            travel_info = strategy._calculate_travel_info(
                from_location=last_location,
                to_location=self.end_location
            )

            # 加入終點資訊
            final_arrival = last_visit_time + timedelta(
                minutes=travel_info['time'])

            itinerary.append({
                'step': len(itinerary) + 1,
                'name': self.end_location.name,
                'start_time': final_arrival.strftime('%H:%M'),
                'end_time': final_arrival.strftime('%H:%M'),
                'duration': 0,
                'transport_details': travel_info['transport_details'],
                'travel_time': travel_info['time']
            })

        return itinerary


# 對外公開的類別和函數
__all__ = ['TripPlanner']
