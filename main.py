# main.py

"""行程規劃系統主程式

此模組負責：
1. 資料驗證和轉換
2. 規劃流程控制
3. 結果輸出與格式化
"""

import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from src.config.config import GOOGLE_MAPS_API_KEY
from src.core.models import TripRequirement, PlaceDetail
from data import TEST_LOCATIONS, TEST_REQUIREMENT, TEST_CUSTOM_START
from src.core.utils.navigation_translator import NavigationTranslator


class TripPlanningSystem:
    """行程規劃系統

    整合各個元件並執行完整的行程規劃流程：
    1. 驗證輸入資料
    2. 執行規劃
    3. 格式化輸出
    """

    def __init__(self):
        """初始化規劃系統"""
        self.execution_time = 0
        from src.core.planner.base import TripPlanner
        self.planner = TripPlanner()

    def validate_locations(self, locations: List[Dict]) -> List[PlaceDetail]:
        """驗證並轉換地點資料

        輸入參數:
            locations: 地點資料列表，每個地點必須包含：
                - name: str          # 地點名稱
                - lat: float         # 緯度
                - lon: float         # 經度
                - duration: int      # 建議停留時間(分鐘)
                - label: str         # 地點類型
                # 時段標記(morning/lunch/afternoon/dinner/night)
                - period: str
                - hours: Dict        # 營業時間
                - rating: float      # 評分(選填)

        回傳：
            List[PlaceDetail]: 驗證後的地點物件列表

        異常：
            ValueError: 當資料格式不正確時
        """
        try:
            validated = []
            for loc in locations:
                # 確保所需欄位都存在
                required_fields = ['name', 'lat', 'lon',
                                   'duration', 'label', 'period', 'hours']
                missing = [
                    field for field in required_fields if field not in loc]
                if missing:
                    raise ValueError(
                        f"地點 {loc.get('name', 'Unknown')} 缺少必要欄位: {missing}")

                # duration_min 相容性處理
                if 'duration' in loc and 'duration_min' not in loc:
                    loc['duration_min'] = loc['duration']

                # 驗證 period 值
                valid_periods = {'morning', 'lunch',
                                 'afternoon', 'dinner', 'night'}
                if loc['period'] not in valid_periods:
                    raise ValueError(
                        f"地點 {loc['name']} 的 period 值無效: {loc['period']}")

                validated.append(PlaceDetail(**loc))
            return validated

        except Exception as e:
            raise ValueError(f"地點資料驗證錯誤: {str(e)}")

    def validate_requirement(self, requirement: Dict) -> TripRequirement:
        """驗證並轉換行程需求

        輸入參數:
            requirement: 需求資料，必須包含：
                - start_time: str        # 開始時間 (HH:MM)
                - end_time: str          # 結束時間 (HH:MM)
                - start_point: str       # 起點名稱
                - end_point: str         # 終點名稱
                - transport_mode: str    # 交通方式
                - distance_threshold: int # 距離限制(公里)
                - lunch_time: str        # 午餐時間 (HH:MM 或 none)
                - dinner_time: str       # 晚餐時間 (HH:MM 或 none)

        回傳：
            TripRequirement: 驗證後的需求物件

        異常：
            ValueError: 當資料格式不正確時
        """
        try:
            # 驗證時間格式
            time_fields = ['start_time', 'end_time']
            meal_fields = ['lunch_time', 'dinner_time']

            for field in time_fields:
                if not self._is_valid_time_format(requirement[field]):
                    raise ValueError(f"時間格式錯誤: {field}={requirement[field]}")

            for field in meal_fields:
                if requirement[field] != 'none' and not self._is_valid_time_format(requirement[field]):
                    raise ValueError(f"用餐時間格式錯誤: {field}={requirement[field]}")

            return TripRequirement(**requirement)

        except Exception as e:
            raise ValueError(f"需求資料驗證錯誤: {str(e)}")

    def _is_valid_time_format(self, time_str: str) -> bool:
        """檢查時間格式是否正確 (HH:MM)"""
        if time_str == 'none':
            return True

        try:
            datetime.strptime(time_str, '%H:%M')
            return True
        except ValueError:
            return False

    def set_default_requirement(self, requirement: Dict) -> Dict:
        """
        設定行程需求的預設值

        輸入:
            requirement: 使用者輸入的需求字典，可能包含空值

        輸出:
            Dict: 處理後的需求字典，所有欄位都有合理的預設值

        預設值邏輯:
            - start_time: 預設 "09:00"
            - end_time: 預設 "21:00"
            - start_point: 預設 "台北車站"
            - end_point: 預設 None (代表與起點相同)
            - transport_mode: 預設 "driving"
            - distance_threshold: 預設 30 (公里)
            - breakfast_time: 預設 "none"
            - lunch_time: 預設 "12:00"
            - dinner_time: 預設 "18:00"
            - budget: 預設 "none"
            - date: 預設今天日期
        """
        from datetime import datetime, timedelta
        
        # 取得明天日期
        tomorrow = datetime.now() + timedelta(days=1)
        
        # 交通方式對照表
        transport_modes = {
            "driving": "開車",
            "transit": "大眾運輸",
            "walking": "步行",
            "bicycling": "騎腳踏車",
        }

        defaults = {
            "start_time": "09:00",
            "end_time": "21:00",
            "start_point": "台北車站",
            "end_point": None,
            "transport_mode": "driving",
            "distance_threshold": 30,
            "breakfast_time": "none",
            "lunch_time": "12:00",
            "dinner_time": "18:00",
            "budget": "none",
            "date": tomorrow.strftime("%m-%d")
        }

        # 合併使用者輸入和預設值
        result = defaults.copy()
        for key, value in requirement.items():
            if value is not None:  # 只覆蓋非 None 的值
                result[key] = value
                
        # 轉換交通方式為中文
        result["transport_mode_display"] = transport_modes.get(
            result["transport_mode"], result["transport_mode"]
        )

        # 檢查時間合理性
        if result["start_time"] >= result["end_time"]:
            raise ValueError("結束時間必須晚於開始時間")

        return result

    def plan_trip(self, locations: List[Dict], requirement: Dict) -> List[Dict]:
        """
        執行行程規劃主函式

        輸入參數:
            locations: 所有可用地點列表
                每個地點需包含:
                - name: 地點名稱
                - lat: 緯度 
                - lon: 經度
                - rating: 評分
                - label: 分類標籤
                - period: 建議遊玩時段
                - hours: 營業時間

            requirement: 行程需求
                - start_point: 起點名稱，None則預設為台北車站
                - end_point: 終點名稱，None則與起點相同
                - start_time: 開始時間 (HH:MM)
                - end_time: 結束時間 (HH:MM)
                - transport_mode: 交通方式
                - distance_threshold: 距離限制(km)
                - breakfast_time: 早餐時間(none或HH:MM)
                - lunch_time: 午餐時間(none或HH:MM)
                - dinner_time: 晚餐時間(none或HH:MM)

        輸出:
            List[Dict]: 規劃後的行程列表
                每個行程包含:
                - step: 順序編號
                - name: 地點名稱
                - start_time: 到達時間
                - end_time: 離開時間 
                - duration: 停留時間(分鐘)
                - transport_details: 交通方式說明
                - travel_time: 交通時間(分鐘)

        異常:
            ValueError: 
                - 無法取得起點或終點座標
                - 地點資料格式錯誤
                - 規劃失敗
        """
        start_time = time.time()

        try:
            # 先設定預設值
            requirement = self.set_default_requirement(requirement)

            # 初始化 Google Maps 服務
            from src.core.services.google_maps import GoogleMapsService
            maps_service = GoogleMapsService(GOOGLE_MAPS_API_KEY)

            # 處理起點
            start_point = requirement.get('start_point')
            custom_start = None

            if start_point is None or start_point == "台北車站":
                # 使用預設的台北車站資訊
                custom_start = PlaceDetail(
                    name="台北車站",
                    rating=0.0,
                    lat=25.0466369,
                    lon=121.5139236,
                    duration_min=0,
                    label='交通',
                    period='morning',
                    hours={i: [{'start': '00:00', 'end': '23:59'}]
                           for i in range(1, 8)}
                )
                start_point = "台北車站"
            else:
                # 使用 API 取得其他起點座標
                try:
                    result = maps_service.geocode(start_point)
                    custom_start = PlaceDetail(
                        name=start_point,
                        rating=0.0,
                        lat=result['lat'],
                        lon=result['lng'],
                        duration_min=0,
                        label='交通',
                        period='morning',
                        hours={i: [{'start': '00:00', 'end': '23:59'}]
                               for i in range(1, 8)}
                    )
                except Exception as e:
                    raise ValueError(f"無法取得起點座標: {str(e)}")

            # 處理終點 - None 就使用起點資訊
            end_point = requirement.get('end_point')
            custom_end = None

            if end_point is None:
                custom_end = custom_start  # 直接使用起點資訊
                requirement['end_point'] = start_point  # 更新 requirement
            elif end_point != start_point:
                try:
                    result = maps_service.geocode(end_point)
                    custom_end = PlaceDetail(
                        name=end_point,
                        rating=0.0,
                        lat=result['lat'],
                        lon=result['lng'],
                        duration_min=0,
                        label='交通',
                        period='morning',
                        hours={i: [{'start': '00:00', 'end': '23:59'}]
                               for i in range(1, 8)}
                    )
                except Exception as e:
                    raise ValueError(f"無法取得終點座標: {str(e)}")

            # 資料驗證與初始化
            validated_locations = self.validate_locations(locations)
            self.planner.initialize_locations(
                validated_locations, custom_start, custom_end)

            # 建立起點行程
            result = []
            start = {
                'step': 0,
                'name': custom_start.name,
                'start_time': requirement['start_time'],
                'end_time': requirement['start_time'],
                'duration': 0,
                'transport_details': '起點',
                'travel_time': 0
            }
            result.append(start)

            # 執行主要規劃
            main_itinerary = self.planner.plan(
                start_time=requirement['start_time'],
                end_time=requirement['end_time'],
                travel_mode=requirement['transport_mode'],
                requirement=requirement
            )

            # 更新順序編號
            for i, item in enumerate(main_itinerary, 1):
                item['step'] = i
                result.append(item)

            # 驗證並調整行程
            result = self._verify_and_adjust_itinerary(
                result,
                requirement['end_point'],
                requirement['end_time']
            )

            self.execution_time = time.time() - start_time
            return result

        except Exception as e:
            print(f"行程規劃錯誤: {str(e)}")
            raise

    def _verify_and_adjust_itinerary(self,
                                     itinerary: List[Dict],
                                     end_point: Optional[str],
                                     end_time: str,
                                     min_duration: int = 30) -> List[Dict]:
        """驗證並調整行程,確保能返回終點

        輸入參數:
            itinerary: List[Dict] - 當前行程列表
            end_point: str - 終點名稱
            end_time: str - 結束時間
            min_duration: int - 最少停留時間(分鐘)

        回傳:
            List[Dict]: 調整後的行程列表
        """
        if len(itinerary) <= 1:  # 只有起點
            return itinerary

        # 如果終點是 None，使用起點
        if end_point is None:
            end_point = itinerary[0]['name']

        while True:
            # 計算返回終點的時間
            last_location = self.planner.get_location_by_name(
                itinerary[-1]['name'])
            end_location = self.planner.get_location_by_name(end_point)
            travel_info = self.planner.get_travel_info(
                last_location,
                end_location,
                itinerary[-1]['end_time']
            )

            # 計算預計抵達終點時間
            last_end_time = datetime.strptime(
                itinerary[-1]['end_time'], '%H:%M')
            end_arrival = last_end_time + \
                timedelta(minutes=travel_info['time'])
            required_end = datetime.strptime(end_time, '%H:%M')

            # 如果可以準時返回,加入終點行程
            if end_arrival <= required_end:
                end = {
                    'step': len(itinerary),
                    'name': end_point,
                    'start_time': end_arrival.strftime('%H:%M'),
                    'end_time': end_arrival.strftime('%H:%M'),
                    'duration': 0,
                    'transport_details': travel_info['transport_details'],
                    'travel_time': travel_info['time']
                }
                itinerary.append(end)
                return itinerary

            # 嘗試縮短最後一個景點的停留時間
            last_point = itinerary[-1]
            if last_point['duration'] > min_duration:
                # 縮短停留時間
                reduced_duration = max(
                    min_duration, last_point['duration'] - 30)
                reduced_end_time = (datetime.strptime(last_point['start_time'], '%H:%M') +
                                    timedelta(minutes=reduced_duration))

                # 更新最後一個景點
                last_point['duration'] = reduced_duration
                last_point['end_time'] = reduced_end_time.strftime('%H:%M')
                continue

            # 如果無法透過縮短時間解決,移除最後一個景點
            itinerary.pop()

            # 如果只剩下起點,表示無法規劃
            if len(itinerary) <= 1:
                raise RuntimeError("無法找到合適的行程安排")

            # 重新進行驗證
            continue

    def get_execution_time(self) -> float:
        """取得執行時間(秒)"""
        return self.execution_time

    def print_itinerary(self, itinerary: List[Dict], show_navigation: bool = False) -> None:
        """列印行程結果

        輸入參數:
            itinerary: 行程列表
            show_navigation: 是否顯示導航說明(預設False)
        """
        print("\n=== 行程規劃結果 ===")

        total_travel_time = 0
        total_duration = 0

        for plan in itinerary:
            print(f"\n[地點 {plan['step']}]", end=' ')
            print(f"名稱: {plan['name']}")
            print(f"時間: {plan['start_time']} - {plan['end_time']}")
            print(f"停留: {plan['duration']}分鐘", end=' ')
            print(f"交通: {plan['transport_details']}"
                  f"({int(plan['travel_time'])}分鐘)")

            # 只在需要時顯示導航資訊
            if show_navigation and 'route_info' in plan:
                print("\n前往下一站的導航:")
                print(NavigationTranslator.format_navigation(
                    plan['route_info']))

            total_travel_time += plan['travel_time']
            total_duration += plan['duration']

        # 輸出統計資訊
        print("\n=== 統計資訊 ===")
        print(f"總景點數: {len(itinerary)}個")
        print(f"總停留時間: {total_duration}分鐘 ({total_duration/60:.1f}小時)")
        print(
            f"總交通時間: {total_travel_time:.0f}分鐘 ({total_travel_time/60:.1f}小時)")
        print(f"規劃耗時: {self.execution_time:.2f}秒")


def main():
    """主程式進入點"""
    try:
        # 建立規劃系統
        system = TripPlanningSystem()

        # 處理預設值
        processed_requirement = system.set_default_requirement(
            TEST_REQUIREMENT
        )

        # 顯示規劃參數
        print("=== 行程規劃系統 ===")
        print(f"起點：{processed_requirement['start_point']}")
        print(f"時間：{processed_requirement['start_time']} - "
              f"{processed_requirement['end_time']}")
        print(f"午餐：{processed_requirement['lunch_time']}")
        print(f"晚餐：{processed_requirement['dinner_time']}")
        print(f"景點數量：{len(TEST_LOCATIONS)}個")
        print(f"交通方式：{processed_requirement['transport_mode_display']}")

        print("\n開始規劃行程...")

        # 執行規劃
        result = system.plan_trip(
            locations=TEST_LOCATIONS,
            requirement=processed_requirement,
        )

        # 輸出結果
        system.print_itinerary(result, show_navigation=False)

        # 印出原始資料結構（如果需要的話）
        # import pprint
        # pprint.pprint(result)

    except Exception as e:
        print(f"\n發生錯誤: {str(e)}")
        raise


if __name__ == "__main__":
    main()
