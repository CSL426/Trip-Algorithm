# src/core/planner/strategy.py

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from src.core.models.place import PlaceDetail
from src.core.services.time_service import TimeService
from src.core.services.geo_service import GeoService
from src.core.evaluator.place_scoring import PlaceScoring


class BasePlanningStrategy(ABC):
    """行程規劃策略的基礎類別

    這是所有規劃策略的抽象基類，定義了策略應該具備的基本功能。
    透過策略模式，我們可以實現不同的規劃方法，例如：
    - 標準規劃策略：平衡各種因素的一般性策略
    - 輕鬆規劃策略：減少交通時間，適合悠閒旅遊
    - 緊湊規劃策略：最大化景點數量，適合短期旅遊
    - 主題規劃策略：根據特定主題（如美食、文化）選擇景點

    每個具體的策略都需要實現：
    1. 如何選擇下一個景點
    2. 如何評估行程的可行性
    3. 如何最佳化整體行程
    """

    def __init__(self,
                 time_service: TimeService,
                 geo_service: GeoService,
                 place_scoring: PlaceScoring,
                 config: Dict):
        """初始化策略

        參數:
            time_service: 時間服務，處理所有時間相關的運算
            geo_service: 地理服務，處理所有位置相關的運算
            place_scoring: 評分服務，計算地點的綜合評分
            config: 策略配置，包含：
                - start_time: 開始時間
                - end_time: 結束時間
                - travel_mode: 交通方式
                - meal_times: 用餐時間設定
                - other_preferences: 其他偏好設定
        """
        self.time_service = time_service
        self.geo_service = geo_service
        self.place_scoring = place_scoring

        # 設定基本參數
        self.start_time = config['start_time']
        self.end_time = config['end_time']
        self.travel_mode = config['travel_mode']
        self.meal_times = config.get('meal_times', {})
        self.preferences = config.get('other_preferences', {})

        # 策略內部狀態
        self.visited_places = []
        self.current_time = self.start_time
        self.total_distance = 0.0

    @abstractmethod
    def select_next_place(self,
                          current_location: PlaceDetail,
                          available_places: List[PlaceDetail],
                          current_time: datetime) -> Optional[Tuple[PlaceDetail, Dict]]:
        """選擇下一個要遊玩的地點

        這是策略最核心的方法，決定下一個最適合的地點。
        每個具體策略都需要實現自己的選擇邏輯。

        參數:
            current_location: 當前位置
            available_places: 可選擇的地點列表
            current_time: 當前時間

        回傳:
            Tuple[PlaceDetail, Dict]: (選中的地點, 交通資訊)
            如果沒有合適的地點則回傳 None
        """
        pass

    @abstractmethod
    def is_feasible(self,
                    place: PlaceDetail,
                    current_location: PlaceDetail,
                    current_time: datetime,
                    travel_info: Dict) -> bool:
        """判斷是否可以將地點加入行程

        檢查加入新地點是否符合所有限制條件：
        1. 時間限制（包含交通和遊玩時間）
        2. 距離限制
        3. 其他策略特定的限制

        參數:
            place: 要檢查的地點
            current_location: 當前位置
            current_time: 當前時間
            travel_info: 交通資訊

        回傳:
            bool: 是否可以加入行程
        """
        pass

    def execute(self,
                current_location: PlaceDetail,
                available_places: List[PlaceDetail],
                current_time: datetime) -> List[Dict]:
        """執行行程規劃

        這是策略的主要執行方法，會：
        1. 反覆選擇下一個最佳地點
        2. 檢查行程可行性
        3. 更新行程狀態
        4. 最佳化整體行程

        參數:
            current_location: 起點位置
            available_places: 所有可選擇的地點
            current_time: 開始時間

        回傳:
            List[Dict]: 規劃好的行程列表
        """
        itinerary = []
        remaining_places = available_places.copy()
        current_loc = current_location
        visit_time = current_time

        while remaining_places and visit_time < self.end_time:
            # 尋找下一個最佳地點
            next_place = self.select_next_place(
                current_loc,
                remaining_places,
                visit_time
            )

            if not next_place:
                break

            place, travel_info = next_place

            # 檢查可行性
            if not self.is_feasible(place, current_loc, visit_time, travel_info):
                break

            # 計算到達和離開時間
            arrival_time = self._calculate_arrival_time(
                visit_time, travel_info['duration_minutes'])
            departure_time = self._calculate_departure_time(
                arrival_time, place.duration_min)

            # 加入行程
            itinerary.append(self._create_itinerary_item(
                place, arrival_time, departure_time, travel_info))

            # 更新狀態
            current_loc = place
            visit_time = departure_time
            remaining_places.remove(place)
            self.visited_places.append(place)
            self.total_distance += travel_info['distance_km']

        return self.optimize_itinerary(itinerary)


class StandardPlanningStrategy(BasePlanningStrategy):
    """標準行程規劃策略

    這是一個平衡各種因素的通用策略，它會：
    1. 平衡考慮時間效率和遊玩體驗
    2. 合理安排用餐時間
    3. 避免過度密集的行程
    4. 優先選擇高評分且交通便利的地點

    策略特色：
    - 使用綜合評分機制選擇地點
    - 自動調整評分權重以適應不同時段
    - 考慮天氣和人潮等外部因素
    - 提供彈性的時間緩衝
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 策略特定的參數
        self.time_buffer = 15  # 每個行程間的緩衝時間（分鐘）
        self.max_continuous_visits = 3  # 連續遊玩的最大景點數
        self.meal_window = 60  # 用餐時間的彈性範圍（分鐘）

    def select_next_place(self,
                          current_location: PlaceDetail,
                          available_places: List[PlaceDetail],
                          current_time: datetime) -> Optional[Tuple[PlaceDetail, Dict]]:
        """選擇下一個遊玩地點

        標準策略的選擇邏輯：
        1. 檢查是否需要安排用餐
        2. 計算每個地點的綜合評分
        3. 為了避免局部最優，從高分地點中隨機選擇
        4. 考慮連續遊玩的疲勞度

        這個方法會動態調整評分權重，例如：
        - 在用餐時間接近時，提高餐廳的權重
        - 連續遊玩多個景點後，提高休息地點的權重
        - 天氣不好時，提高室內景點的權重
        """
        scored_places = []
        current_period = self.time_service.get_current_period(current_time)

        # 檢查是否需要優先安排用餐
        if self._should_arrange_meal(current_time):
            available_places = [p for p in available_places
                                if p.label in ['餐廳', '小吃']]
            if not available_places:
                return None

        for place in available_places:
            # 計算交通資訊
            travel_info = self.geo_service.get_route(
                origin={"lat": current_location.lat,
                        "lon": current_location.lon},
                destination={"lat": place.lat, "lon": place.lon},
                mode=self.travel_mode,
                departure_time=current_time
            )

            # 根據當前情況調整評分權重
            weights = self._adjust_weights(
                place=place,
                current_time=current_time,
                travel_info=travel_info
            )

            # 計算綜合評分
            score = self.place_scoring.calculate_score(
                place=place,
                current_location=current_location,
                current_time=current_time,
                travel_time=travel_info['duration_minutes']
            )

            if score > float('-inf'):
                scored_places.append((place, score, travel_info))

        if not scored_places:
            return None

        # 選擇評分最高的前三個地點之一
        import random
        scored_places.sort(key=lambda x: x[1], reverse=True)
        top_places = scored_places[:3]
        selected = random.choice(top_places)

        return selected[0], selected[2]

    def is_feasible(self,
                    place: PlaceDetail,
                    current_location: PlaceDetail,
                    current_time: datetime,
                    travel_info: Dict) -> bool:
        """檢查將地點加入行程是否可行

        標準策略的可行性檢查包括：
        1. 基本的時間限制（含緩衝時間）
        2. 連續遊玩景點數的限制
        3. 用餐時間的合理性
        4. 交通時間的合理性

        同時考慮：
        - 營業時間的限制
        - 預約限制（如果有）
        - 天氣影響
        """
        # 計算預計到達和離開時間
        arrival_time = self._calculate_arrival_time(
            current_time,
            travel_info['duration_minutes']
        )
        departure_time = self._calculate_departure_time(
            arrival_time,
            place.duration_min
        )

        # 檢查是否超過結束時間
        if departure_time > self.end_time:
            return False

        # 檢查連續遊玩限制
        if (len(self.visited_places) >= self.max_continuous_visits and
                all(p.label == '景點' for p in self.visited_places[-3:])):
            return False

        # 檢查用餐時間合理性
        if place.label in ['餐廳', '小吃']:
            if not self._is_reasonable_meal_time(arrival_time):
                return False

        # 檢查交通時間合理性
        if travel_info['duration_minutes'] > 60:  # 單程超過1小時
            if place.label not in ['景點', '主要景點']:
                return False

        return True

    def _should_arrange_meal(self, current_time: datetime) -> bool:
        """判斷是否應該安排用餐

        根據時間和用餐設定判斷是否需要優先安排用餐。
        考慮：
        1. 是否接近用餐時間
        2. 是否已經安排過這個時段的用餐
        3. 用餐的優先級
        """
        for meal_time in self.meal_times.values():
            if meal_time == 'none':
                continue

            meal_dt = datetime.strptime(meal_time, '%H:%M').time()
            current_dt = current_time.time()

            # 計算距離用餐時間的分鐘數
            time_diff = ((meal_dt.hour - current_dt.hour) * 60 +
                         (meal_dt.minute - current_dt.minute))

            # 如果在用餐時間前後的窗口期內
            if abs(time_diff) <= self.meal_window:
                # 檢查是否已經安排過這頓飯
                meal_arranged = any(
                    p.label in ['餐廳', '小吃'] and
                    abs((datetime.combine(current_time.date(), meal_dt) -
                         p.visit_time).total_seconds() / 60) <= self.meal_window
                    for p in self.visited_places
                )

                if not meal_arranged:
                    return True

        return False


class RelaxedPlanningStrategy(BasePlanningStrategy):
    """輕鬆的行程規劃策略

    這個策略專注於提供一個舒適、不緊湊的旅遊體驗。它的特點是：
    1. 減少交通時間和轉換次數
    2. 提供充足的休息時間
    3. 避免時間緊迫的安排
    4. 優先選擇輕鬆的活動

    策略的設計理念：
    - 寧可景點少一些，也要確保每個景點都能充分遊玩
    - 確保用餐時間充足，不會因趕行程而匆忙用餐
    - 根據天氣和季節自動調整行程密度
    - 在景點之間安排適當的休息時間
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 輕鬆策略的特定參數
        self.time_buffer = 30           # 更長的緩衝時間（分鐘）
        self.max_places_per_day = 4     # 限制每天的景點數量
        self.min_rest_time = 20         # 最短休息時間（分鐘）
        self.max_travel_time = 45       # 最長可接受的交通時間（分鐘）

    def select_next_place(self,
                          current_location: PlaceDetail,
                          available_places: List[PlaceDetail],
                          current_time: datetime) -> Optional[Tuple[PlaceDetail, Dict]]:
        """選擇下一個遊玩地點

        輕鬆策略的選擇邏輯特別注重：
        1. 優先選擇交通便利的地點
        2. 傾向選擇可以慢慢體驗的景點
        3. 避免需要趕時間的景點
        4. 根據天氣調整室內外景點的選擇
        """
        # 如果已達到每日景點上限，不再新增景點
        if len(self.visited_places) >= self.max_places_per_day:
            return None

        scored_places = []
        for place in available_places:
            # 獲取交通資訊
            travel_info = self.geo_service.get_route(
                origin={"lat": current_location.lat,
                        "lon": current_location.lon},
                destination={"lat": place.lat, "lon": place.lon},
                mode=self.travel_mode,
                departure_time=current_time
            )

            # 如果交通時間太長，直接跳過
            if travel_info['duration_minutes'] > self.max_travel_time:
                continue

            # 計算輕鬆策略的特殊評分
            relaxed_score = self._calculate_relaxed_score(
                place=place,
                current_time=current_time,
                travel_info=travel_info
            )

            if relaxed_score > float('-inf'):
                scored_places.append((place, relaxed_score, travel_info))

        if not scored_places:
            return None

        # 從高分地點中選擇，但加入一些隨機性
        scored_places.sort(key=lambda x: x[1], reverse=True)
        top_places = scored_places[:2]  # 只考慮前兩名
        import random
        selected = random.choice(top_places)

        return selected[0], selected[2]

    def is_feasible(self,
                    place: PlaceDetail,
                    current_location: PlaceDetail,
                    current_time: datetime,
                    travel_info: Dict) -> bool:
        """檢查地點是否適合加入輕鬆行程

        輕鬆策略的可行性檢查更為嚴格：
        1. 要求更多的時間緩衝
        2. 更嚴格的交通時間限制
        3. 確保有足夠的休息時間
        4. 考慮天氣和季節的影響
        """
        # 基本時間檢查
        arrival_time = self._calculate_arrival_time(
            current_time,
            travel_info['duration_minutes']
        )
        departure_time = self._calculate_departure_time(
            arrival_time,
            place.duration_min + self.time_buffer  # 加入額外緩衝
        )

        # 檢查是否會超過結束時間
        if departure_time > self.end_time:
            return False

        # 確保有足夠的休息時間
        if self.visited_places:
            last_place = self.visited_places[-1]
            time_since_last = (
                current_time - last_place.departure_time).total_seconds() / 60
            if time_since_last < self.min_rest_time:
                return False

        # 用餐地點的特殊處理
        if place.label in ['餐廳', '小吃']:
            # 確保有充足的用餐時間
            meal_time = place.duration_min + self.time_buffer
            if departure_time + timedelta(minutes=meal_time) > self.end_time:
                return False

        return True

    def _calculate_relaxed_score(self,
                                 place: PlaceDetail,
                                 current_time: datetime,
                                 travel_info: Dict) -> float:
        """計算輕鬆策略的特殊評分

        考慮因素：
        1. 交通便利性（佔比較大）
        2. 停留時間的靈活性
        3. 天氣適合度
        4. 擁擠程度（如果有相關資訊）
        """
        # 基礎評分
        base_score = self.place_scoring.calculate_score(
            place, self.current_location, current_time,
            travel_info['duration_minutes']
        )

        if base_score == float('-inf'):
            return float('-inf')

        # 交通便利性加權（越近分數越高）
        travel_factor = 1.0 - \
            (travel_info['duration_minutes'] / self.max_travel_time)

        # 停留時間靈活度（較長的停留時間得分較高）
        time_flexibility = min(1.0, place.duration_min / 120.0)

        # 綜合評分
        relaxed_score = (
            base_score * 0.4 +
            travel_factor * 0.4 +
            time_flexibility * 0.2
        )

        return relaxed_score


class CompactPlanningStrategy(BasePlanningStrategy):
    """緊湊的行程規劃策略

    這個策略專門為時間有限的旅客設計，目標是在有限時間內體驗最多景點。
    策略的核心理念是透過精確的時間管理和路線優化，在保證基本遊覽品質
    的前提下最大化景點數量。

    策略特色：
    1. 精確的時間管理：將緩衝時間最小化，但保持合理範圍
    2. 智能的路線規劃：優先選擇可以串連的景點群
    3. 動態的時間調整：根據實際情況即時調整停留時間
    4. 區域最佳化：優先完成同一區域的景點再移動到新區域

    使用情境：
    - 短期旅遊（1-2天）想體驗更多景點
    - 中轉旅客有限時間遊覽
    - 針對特定區域的密集探索
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 緊湊策略的特定參數
        self.min_buffer = 10           # 最小緩衝時間（分鐘）
        self.cluster_radius = 2.0      # 景點群聚半徑（公里）
        self.max_travel_ratio = 0.3    # 交通時間占比上限
        self.min_stay_time = 30        # 最短停留時間（分鐘）

    def select_next_place(self,
                          current_location: PlaceDetail,
                          available_places: List[PlaceDetail],
                          current_time: datetime) -> Optional[Tuple[PlaceDetail, Dict]]:
        """選擇下一個遊玩地點

        緊湊策略的選擇邏輯著重於：
        1. 優先考慮同區域內的景點，減少長途移動
        2. 根據景點群聚情況進行選擇
        3. 動態調整遊玩時間以適應整體行程
        4. 在不同時段選擇最適合的景點類型
        """
        # 尋找當前位置周圍的景點群
        nearby_cluster = self._find_nearby_cluster(
            current_location,
            available_places
        )

        # 計算每個地點的綜合效率分數
        scored_places = []
        places_to_evaluate = nearby_cluster if nearby_cluster else available_places

        for place in places_to_evaluate:
            travel_info = self.geo_service.get_route(
                origin={"lat": current_location.lat,
                        "lon": current_location.lon},
                destination={"lat": place.lat, "lon": place.lon},
                mode=self.travel_mode,
                departure_time=current_time
            )

            # 計算效率分數
            efficiency_score = self._calculate_efficiency_score(
                place=place,
                current_time=current_time,
                travel_info=travel_info
            )

            if efficiency_score > float('-inf'):
                # 計算該點作為下一站的潛力價值
                potential_value = self._evaluate_potential_value(
                    place=place,
                    available_places=available_places
                )

                # 綜合分數結合效率和潛力
                final_score = efficiency_score * 0.7 + potential_value * 0.3
                scored_places.append((place, final_score, travel_info))

        if not scored_places:
            return None

        # 選擇分數最高的地點
        scored_places.sort(key=lambda x: x[1], reverse=True)
        return scored_places[0][0], scored_places[0][2]

    def is_feasible(self,
                    place: PlaceDetail,
                    current_location: PlaceDetail,
                    current_time: datetime,
                    travel_info: Dict) -> bool:
        """評估地點是否適合加入緊湊行程

        緊湊策略的可行性判斷更注重效率：
        1. 確保總體時間分配合理
        2. 評估對後續行程的影響
        3. 檢查是否符合最小遊玩時間要求
        4. 考慮交通時間比例
        """
        # 計算時間相關數據
        travel_time = travel_info['duration_minutes']
        total_time = sum(p.duration_min for p in self.visited_places)
        total_travel = sum(p.travel_time for p in self.visited_places)

        # 檢查交通時間比例
        if (total_travel + travel_time) / (total_time + place.duration_min) > self.max_travel_ratio:
            return False

        # 確保最小停留時間
        adjusted_duration = max(self.min_stay_time, place.duration_min)

        # 計算預計時間
        arrival_time = self._calculate_arrival_time(
            current_time, travel_time)
        departure_time = self._calculate_departure_time(
            arrival_time, adjusted_duration)

        # 檢查時間限制
        if departure_time > self.end_time:
            return False

        # 如果是用餐地點，確保基本用餐時間
        if place.label in ['餐廳', '小吃']:
            min_meal_time = 45  # 最短用餐時間
            if adjusted_duration < min_meal_time:
                return False

        return True

    def _find_nearby_cluster(self,
                             center: PlaceDetail,
                             places: List[PlaceDetail]) -> List[PlaceDetail]:
        """尋找中心點附近的景點群

        使用空間聚類的概念，找出可以一起遊玩的景點群：
        1. 計算與中心點的距離
        2. 考慮景點間的連通性
        3. 評估群聚的整體價值
        """
        cluster = []
        center_coords = {"lat": center.lat, "lon": center.lon}

        for place in places:
            place_coords = {"lat": place.lat, "lon": place.lon}
            distance = self.geo_service.calculate_distance(
                center_coords, place_coords)

            if distance <= self.cluster_radius:
                cluster.append(place)

        return cluster

    def _evaluate_potential_value(self,
                                  place: PlaceDetail,
                                  available_places: List[PlaceDetail]) -> float:
        """評估地點的潛在價值

        計算選擇該地點對後續行程的影響：
        1. 評估周圍景點的密集程度
        2. 計算與其他景點的連接性
        3. 考慮時間和空間的協同效應
        """
        # 計算在指定半徑內的景點數量
        nearby_count = len(self._find_nearby_cluster(place, available_places))

        # 計算標準化的密度分數
        density_score = min(1.0, nearby_count / 5.0)

        return density_score

    def _calculate_efficiency_score(self,
                                    place: PlaceDetail,
                                    current_time: datetime,
                                    travel_info: Dict) -> float:
        """計算緊湊策略的效率分數"""
        # 基礎評分
        base_score = self.place_scoring.calculate_score(
            place=place,
            current_location=place,  # 改用 travel_info 中的資訊
            current_time=current_time,
            travel_time=travel_info['duration_minutes']
        )

        if base_score == float('-inf'):
            return float('-inf')

        # 時間效率（停留時間/交通時間的比例）
        efficiency_base = 1.5  # 加入這個基準值
        time_ratio = place.duration_min / \
            max(travel_info['duration_minutes'], 1)
        efficiency_factor = min(1.0, time_ratio / efficiency_base)

        # 群聚效應
        cluster_factor = self._calculate_cluster_factor(place)

        # 綜合評分
        final_score = (
            base_score * 0.4 +
            efficiency_factor * 0.4 +
            cluster_factor * 0.2
        )

        return final_score

    def _calculate_cluster_factor(self, place: PlaceDetail) -> float:
        """計算地點的群聚因子

        評估地點與已訪問地點的群聚程度：
        1. 計算與已訪問地點的平均距離
        2. 評估是否形成有效的景點群
        3. 考慮路線的連貫性

        參數:
            place: 要評估的地點

        回傳:
            float: 0-1 之間的群聚分數
        """
        if not self.visited_places:
            return 1.0

        # 計算與最近的已訪問地點的距離
        distances = []
        for visited in self.visited_places[-3:]:  # 只考慮最近的3個地點
            distance = self.geo_service.calculate_distance(
                {'lat': visited.lat, 'lon': visited.lon},
                {'lat': place.lat, 'lon': place.lon}
            )
            distances.append(distance)

        # 取最小距離
        min_distance = min(distances)

        # 根據群聚半徑計算分數
        cluster_score = 1.0 - (min_distance / (self.cluster_radius * 2))
        return max(0.0, min(1.0, cluster_score))


class ThematicPlanningStrategy(BasePlanningStrategy):
    """主題式行程規劃策略

    這個策略根據特定主題（如美食、文化、購物等）來規劃行程。它不只是
    簡單地篩選特定類型的景點，而是會考慮整體體驗的連貫性和豐富度。

    策略特色：
    1. 深度體驗：在特定主題上提供更深入的探索
    2. 主題連貫：確保行程中的景點能形成有意義的主題脈絡
    3. 體驗多樣：在主題內部提供不同面向的體驗
    4. 彈性調整：根據實際情況加入輔助性的配套景點

    使用情境：
    - 美食愛好者的餐廳探索之旅
    - 歷史文化愛好者的深度文化之旅
    - 購物愛好者的商圈巡禮
    - 藝術愛好者的藝術館巡禮
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 取得主題設定
        self.theme = self.preferences.get('theme', 'general')
        self.theme_settings = self._get_theme_settings(self.theme)

        # 主題策略的特定參數
        self.theme_ratio = 0.7          # 主題相關景點的最低比例
        self.max_similar = 2            # 連續相似景點的最大數量
        self.complementary_ratio = 0.3   # 配套景點的比例

    def _get_theme_settings(self, theme: str) -> Dict:
        """取得主題相關的設定

        根據不同的主題返回相應的設定，包括：
        1. 主要景點類型
        2. 輔助景點類型
        3. 時間分配建議
        4. 特殊規則
        """
        themes = {
            'food': {
                'primary_labels': ['餐廳', '小吃', '美食街'],
                'secondary_labels': ['咖啡廳', '甜點店'],
                'complementary_labels': ['公園', '休息區'],
                'min_meal_time': 60,
                'max_continuous_eating': 2
            },
            'culture': {
                'primary_labels': ['博物館', '古蹟', '寺廟'],
                'secondary_labels': ['藝文中心', '展覽館'],
                'complementary_labels': ['公園', '咖啡廳'],
                'min_visit_time': 90,
                'max_continuous_visits': 3
            },
            'shopping': {
                'primary_labels': ['百貨公司', '商圈', '市場'],
                'secondary_labels': ['精品店', '伴手禮店'],
                'complementary_labels': ['餐廳', '咖啡廳'],
                'min_shopping_time': 60,
                'rest_interval': 120
            }
        }

        return themes.get(theme, {
            'primary_labels': ['景點'],
            'secondary_labels': ['公園'],
            'complementary_labels': ['餐廳', '咖啡廳'],
            'min_visit_time': 45,
            'max_continuous_visits': 3
        })

    def select_next_place(self,
                          current_location: PlaceDetail,
                          available_places: List[PlaceDetail],
                          current_time: datetime) -> Optional[Tuple[PlaceDetail, Dict]]:
        """選擇下一個地點

        主題策略的選擇邏輯著重於：
        1. 優先選擇主題相關的景點
        2. 確保主題體驗的多樣性
        3. 適時加入輔助景點保持體驗的平衡
        4. 考慮整體行程的節奏和連貫性
        """
        # 檢查是否需要安排休息或配套活動
        if self._need_complementary_place():
            available_places = [p for p in available_places
                                if p.label in self.theme_settings['complementary_labels']]
        else:
            # 計算已訪問的主題景點比例
            theme_count = sum(1 for p in self.visited_places
                              if p.label in self.theme_settings['primary_labels'])
            total_count = len(self.visited_places)

            # 如果主題景點比例過低，優先選擇主題景點
            if total_count > 0 and theme_count / total_count < self.theme_ratio:
                available_places = [p for p in available_places
                                    if p.label in self.theme_settings['primary_labels']]

        scored_places = []
        for place in available_places:
            travel_info = self.geo_service.get_route(
                origin={"lat": current_location.lat,
                        "lon": current_location.lon},
                destination={"lat": place.lat, "lon": place.lon},
                mode=self.travel_mode,
                departure_time=current_time
            )

            theme_score = self._calculate_theme_score(
                place=place,
                current_time=current_time,
                travel_info=travel_info
            )

            if theme_score > float('-inf'):
                scored_places.append((place, theme_score, travel_info))

        if not scored_places:
            return None

        # 選擇分數最高的地點
        scored_places.sort(key=lambda x: x[1], reverse=True)
        return scored_places[0][0], scored_places[0][2]

    def _calculate_theme_score(self,
                               place: PlaceDetail,
                               current_time: datetime,
                               travel_info: Dict) -> float:
        """計算主題相關分數

        主題評分考慮：
        1. 與主題的相關度
        2. 體驗的多樣性
        3. 時間的合適度
        4. 地理位置的便利性
        """
        # 基礎評分
        base_score = self.place_scoring.calculate_score(
            place, self.current_location, current_time,
            travel_info['duration_minutes']
        )

        if base_score == float('-inf'):
            return float('-inf')

        # 計算主題相關度
        if place.label in self.theme_settings['primary_labels']:
            theme_relevance = 1.0
        elif place.label in self.theme_settings['secondary_labels']:
            theme_relevance = 0.8
        elif place.label in self.theme_settings['complementary_labels']:
            theme_relevance = 0.6
        else:
            theme_relevance = 0.3

        # 考慮體驗多樣性
        diversity_factor = self._calculate_diversity_factor(place)

        # 綜合評分
        final_score = (
            base_score * 0.4 +
            theme_relevance * 0.4 +
            diversity_factor * 0.2
        )

        return final_score


class PlanningStrategyFactory:
    """行程規劃策略工廠

    這個工廠類別負責創建和管理不同的行程規劃策略。它不只是簡單地實例化策略物件，
    還會根據使用者的需求和環境條件，選擇最適合的策略或策略組合。

    工廠的主要職責包括：
    1. 策略的創建和初始化
    2. 策略參數的配置和調整
    3. 策略的動態切換和組合
    4. 策略執行的監控和優化
    """

    def __init__(self,
                 time_service: TimeService,
                 geo_service: GeoService,
                 place_scoring: PlaceScoring):
        """初始化策略工廠

        參數:
            time_service: 時間服務實例，處理所有時間相關的計算
            geo_service: 地理服務實例，處理所有位置相關的計算
            place_scoring: 景點評分服務，提供基礎的評分機制
        """
        self.time_service = time_service
        self.geo_service = geo_service
        self.place_scoring = place_scoring

        # 註冊可用的策略類型
        self.strategies = {
            'standard': StandardPlanningStrategy,
            'relaxed': RelaxedPlanningStrategy,
            'compact': CompactPlanningStrategy,
            'thematic': ThematicPlanningStrategy
        }

    def create_strategy(self,
                        strategy_type: str,
                        config: Dict) -> BasePlanningStrategy:
        """創建指定類型的策略實例

        這個方法會根據提供的配置創建並初始化一個策略實例。它會：
        1. 驗證策略類型的有效性
        2. 調整策略的配置參數
        3. 初始化相關的服務實例
        4. 設定策略的監控機制

        參數:
            strategy_type: 策略類型（standard/relaxed/compact/thematic）
            config: 策略的配置參數

        回傳:
            BasePlanningStrategy: 初始化好的策略實例
        """
        # 驗證策略類型
        if strategy_type not in self.strategies:
            raise ValueError(f"不支援的策略類型: {strategy_type}")

        # 根據不同策略類型調整配置
        adjusted_config = self._adjust_config(strategy_type, config)

        # 創建策略實例
        strategy_class = self.strategies[strategy_type]
        return strategy_class(
            time_service=self.time_service,
            geo_service=self.geo_service,
            place_scoring=self.place_scoring,
            config=adjusted_config
        )

    def _adjust_config(self, strategy_type: str, config: Dict) -> Dict:
        """調整策略配置

        根據策略類型和實際情況調整配置參數。這包括：
        1. 設定合適的預設值
        2. 驗證參數的合理性
        3. 加入策略特定的參數
        """
        adjusted = config.copy()

        # 基本配置調整
        if strategy_type == 'relaxed':
            # 輕鬆策略需要更多緩衝時間
            adjusted['time_buffer'] = max(
                adjusted.get('time_buffer', 15),
                30  # 最小緩衝時間
            )
            adjusted['max_places_per_day'] = min(
                adjusted.get('max_places_per_day', 6),
                4  # 限制每天景點數
            )

        elif strategy_type == 'compact':
            # 緊湊策略最小化緩衝時間
            adjusted['time_buffer'] = min(
                adjusted.get('time_buffer', 15),
                10  # 最大緩衝時間
            )
            # 增加可接受的交通時間比例
            adjusted['max_travel_ratio'] = 0.4

        elif strategy_type == 'thematic':
            # 確保主題設定的存在
            if 'theme' not in adjusted:
                adjusted['theme'] = 'general'
            # 設定主題相關的參數
            adjusted['theme_ratio'] = 0.7
            adjusted['complementary_ratio'] = 0.3

        # 共同配置調整
        adjusted['min_stay_time'] = adjusted.get('min_stay_time', 30)
        adjusted['max_travel_time'] = adjusted.get('max_travel_time', 60)

        return adjusted

    def recommend_strategy(self, context: Dict) -> str:
        """根據上下文推薦合適的策略

        通過分析各種因素來推薦最適合的策略類型，考慮：
        1. 可用時間的長度
        2. 景點的分布情況
        3. 使用者的偏好
        4. 外部環境因素

        參數:
            context: 包含各種上下文信息的字典

        回傳:
            str: 推薦的策略類型
        """
        available_time = context.get('available_time', 8 * 60)  # 預設8小時
        total_places = len(context.get('available_places', []))
        has_theme = bool(context.get('theme'))

        # 根據不同因素評估最適合的策略
        if has_theme and context.get('theme_priority', False):
            return 'thematic'
        elif available_time < 4 * 60:  # 少於4小時
            return 'compact'
        elif available_time > 10 * 60:  # 超過10小時
            return 'relaxed'
        elif total_places > 20:  # 景點數量較多
            return 'compact'
        else:
            return 'standard'


class StrategyManager:
    """策略管理器

    這個管理器負責監控行程執行的狀況，並在需要時動態調整策略。它就像是
    一個經驗豐富的導遊，會根據實際情況靈活調整行程安排的方式。

    主要職責：
    1. 監控行程執行狀況
    2. 評估策略切換的時機
    3. 平滑地進行策略轉換
    4. 維護行程的連續性
    """

    def __init__(self, strategy_factory: PlanningStrategyFactory):
        self.strategy_factory = strategy_factory
        self.current_strategy = None
        self.execution_history = []

        # 設定策略切換的閾值
        self.change_thresholds = {
            'time_deviation': 30,    # 時間偏差超過30分鐘考慮切換
            'satisfaction_low': 0.6,  # 滿意度低於0.6考慮切換
            'progress_slow': 0.7     # 進度低於預期70%考慮切換
        }

    def initialize_strategy(self, context: Dict) -> BasePlanningStrategy:
        """初始化策略

        根據初始情況選擇最適合的策略。這就像是在旅程開始前，
        根據天氣、時間、體力等因素來決定如何安排行程。
        """
        strategy_type = self.strategy_factory.recommend_strategy(context)
        self.current_strategy = self.strategy_factory.create_strategy(
            strategy_type, context)
        return self.current_strategy

    def monitor_execution(self,
                          execution_state: Dict,
                          current_time: datetime) -> None:
        """監控行程執行狀況

        持續評估行程執行的效果，包括：
        1. 時間進度是否符合預期
        2. 景點遊覽是否順利
        3. 整體行程是否需要調整
        """
        # 記錄執行狀態
        self.execution_history.append({
            'time': current_time,
            'state': execution_state,
            'metrics': self._calculate_metrics(execution_state)
        })

        # 如果需要切換策略
        if self._should_change_strategy():
            self._switch_strategy()

    def _calculate_metrics(self, state: Dict) -> Dict:
        """計算執行效果指標

        評估行程執行的各項指標，就像是檢查行程的健康狀況：
        1. 時間利用率
        2. 景點完成度
        3. 交通效率
        """
        visited_count = len(state.get('visited_places', []))
        total_time = state.get('total_time', 0)
        travel_time = state.get('total_travel_time', 0)

        return {
            'time_efficiency': 1 - (travel_time / total_time),
            'progress_rate': visited_count / state.get('planned_count', 1),
            'satisfaction': state.get('average_rating', 0)
        }

    def _should_change_strategy(self) -> bool:
        """判斷是否需要切換策略

        通過分析各種指標來決定是否需要調整策略。就像是在旅途中
        發現當前的安排方式不太適合，需要作出調整。
        """
        if len(self.execution_history) < 2:
            return False

        current_metrics = self.execution_history[-1]['metrics']

        # 檢查是否有需要切換的指標
        time_issue = self._check_time_deviation()
        satisfaction_issue = (
            current_metrics['satisfaction'] <
            self.change_thresholds['satisfaction_low']
        )
        progress_issue = (
            current_metrics['progress_rate'] <
            self.change_thresholds['progress_slow']
        )

        return time_issue or satisfaction_issue or progress_issue

    def _check_time_deviation(self) -> bool:
        """檢查時間偏差

        計算實際執行時間與計畫的偏差程度，就像是檢查是否
        嚴重偏離原定行程表。
        """
        latest_state = self.execution_history[-1]['state']
        planned_time = latest_state.get('planned_time', 0)
        actual_time = latest_state.get('actual_time', 0)

        deviation = abs(actual_time - planned_time)
        return deviation > self.change_thresholds['time_deviation']

    def _switch_strategy(self) -> None:
        """執行策略切換

        根據當前情況選擇新的策略，並確保平滑過渡。這就像是
        在旅途中靈活調整行程安排的方式，但要確保不會造成太大的混亂。
        """
        latest_state = self.execution_history[-1]['state']
        metrics = self.execution_history[-1]['metrics']

        # 根據問題選擇新策略
        if metrics['time_efficiency'] < 0.6:
            # 時間效率太低，切換到緊湊策略
            new_type = 'compact'
        elif metrics['satisfaction'] < 0.6:
            # 滿意度太低，切換到輕鬆策略
            new_type = 'relaxed'
        else:
            # 其他情況回到標準策略
            new_type = 'standard'

        # 創建新策略並轉移必要的狀態
        new_strategy = self.strategy_factory.create_strategy(
            new_type,
            self._create_transition_config(latest_state)
        )

        # 更新當前策略
        self.current_strategy = new_strategy

    def _create_transition_config(self, state: Dict) -> Dict:
        """創建策略轉換時的配置

        確保新策略能夠平滑接手當前的行程狀態，避免轉換造成的混亂。
        """
        return {
            'start_time': state['current_time'],
            'end_time': state['end_time'],
            'visited_places': state['visited_places'].copy(),
            'remaining_time': state['remaining_time'],
            'travel_mode': state['travel_mode'],
            'current_location': state['current_location'],
            'transition_from': self.current_strategy.__class__.__name__
        }
