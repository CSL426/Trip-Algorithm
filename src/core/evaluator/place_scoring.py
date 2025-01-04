# src/core/evaluator/place_scoring.py

from datetime import datetime
from typing import Dict, Optional
from dataclasses import dataclass
from src.core.models.place import PlaceDetail
from src.core.services.time_service import TimeService
from src.core.services.geo_service import GeoService


@dataclass
class ScoreWeights:
    """評分權重設定

    這個類別定義了各個評分因素的權重，讓評分系統可以靈活調整。
    權重值介於 0-1 之間，總和應為 1。
    """
    rating_weight: float = 0.3       # 基礎評分權重
    efficiency_weight: float = 0.3   # 時間效率權重
    time_slot_weight: float = 0.2    # 時段適合度權重
    distance_weight: float = 0.2     # 距離合理性權重


class PlaceScoring:
    """地點評分系統

    這個系統負責為每個地點計算綜合評分，考慮多個維度：
    1. 地點本身的評分（rating）- 反映地點的基本品質
    2. 時間效率 - 考慮交通時間與停留時間的比例
    3. 時段適合度 - 評估是否在建議的遊玩時段
    4. 距離合理性 - 考慮與當前位置的距離

    系統特色：
    - 多維度評分確保全面考量
    - 權重可調整以適應不同需求
    - 提供詳細的評分過程資訊
    - 支援自定義評分策略
    """

    def __init__(self,
                 time_service: TimeService,
                 geo_service: GeoService,
                 weights: Optional[ScoreWeights] = None,
                 distance_threshold: float = 30.0):
        """初始化評分系統

        參數:
            time_service: 時間服務實例，用於時間相關的判斷
            geo_service: 地理服務實例，用於距離計算
            weights: 評分權重設定，如果不提供則使用預設值
            distance_threshold: 可接受的最大距離（公里）
        """
        self.time_service = time_service
        self.geo_service = geo_service
        self.weights = weights or ScoreWeights()
        self.distance_threshold = distance_threshold

        # 評分基準值設定
        self.efficiency_base = 1.5  # 效率分數的基準值
        self.min_score = 0.0       # 最低評分
        self.max_score = 1.0       # 最高評分

    def calculate_score(self,
                        place: PlaceDetail,
                        current_location: PlaceDetail,
                        current_time: datetime,
                        travel_time: float) -> float:
        """計算地點的綜合評分

        這個方法整合了所有評分因素，產生一個綜合評分。
        如果地點完全不適合（如不在營業時間），則回傳負無限大。

        參數:
            place: 要評分的地點
            current_location: 當前位置
            current_time: 當前時間
            travel_time: 預估交通時間（分鐘）

        回傳:
            float: 0-1 之間的評分，或 float('-inf') 表示不適合

        評分過程：
        1. 檢查基本條件（如營業時間）
        2. 計算各個維度的分數
        3. 根據權重計算加權平均
        4. 標準化最終分數
        """
        # 檢查是否在營業時間內
        if not self._check_business_hours(place, current_time):
            return float('-inf')

        # 計算各維度的分數
        rating_score = self._calculate_rating_score(place)
        efficiency_score = self._calculate_efficiency_score(
            place, travel_time)
        time_slot_score = self._calculate_time_slot_score(
            place, current_time)
        distance_score = self._calculate_distance_score(
            place, current_location)

        # 計算加權平均
        weighted_score = (
            rating_score * self.weights.rating_weight +
            efficiency_score * self.weights.efficiency_weight +
            time_slot_score * self.weights.time_slot_weight +
            distance_score * self.weights.distance_weight
        )

        return self._normalize_score(weighted_score)

    def _calculate_rating_score(self, place: PlaceDetail) -> float:
        """計算基礎評分分數

        將地點原始評分（通常是 0-5 分）轉換為 0-1 的標準分數。
        這個分數反映了地點的基本品質和受歡迎程度。

        評分考慮：
        - 原始評分（rating）會線性映射到 0-1 區間
        - 如果評分特別高（4.5以上），會給予額外加分
        - 如果沒有評分，會給予一個中等的預設分數

        參數:
            place: 要評分的地點

        回傳:
            float: 0-1 之間的標準化評分
        """
        if not place.rating:
            return 0.5  # 無評分時給予中等分數

        # 基本分數：將 0-5 轉換為 0-1
        base_score = min(1.0, place.rating / 5.0)

        # 優質場所加分（評分 4.5 以上的地點）
        if place.rating >= 4.5:
            bonus = (place.rating - 4.5) * 0.1  # 最多加 0.05 分
            return min(1.0, base_score + bonus)

        return base_score

    def _calculate_efficiency_score(self,
                                    place: PlaceDetail,
                                    travel_time: float) -> float:
        """計算時間效率分數

        評估到達地點所需的時間成本與停留價值的比例。
        這個分數反映了時間投資的效益。

        評分考慮：
        - 停留時間與交通時間的比例
        - 交通時間的合理性（過長的交通時間會降低分數）
        - 地點的類型（某些地點值得較長的交通時間）

        參數:
            place: 要評分的地點
            travel_time: 預估交通時間（分鐘）

        回傳:
            float: 0-1 之間的效率分數
        """
        if travel_time <= 0:
            return 1.0  # 如果就在當前位置，給予最高分

        # 計算效率比率（停留時間/交通時間）
        efficiency_ratio = place.duration_min / travel_time

        # 根據地點類型調整期望效率
        expected_ratio = self.efficiency_base
        if place.label in ['景點', '主要景點']:
            expected_ratio *= 0.8  # 景點可以接受較低的效率
        elif place.label in ['餐廳', '小吃']:
            expected_ratio *= 1.2  # 用餐地點要求較高效率

        # 標準化分數
        score = efficiency_ratio / expected_ratio
        return min(1.0, score)

    def _calculate_time_slot_score(self,
                                   place: PlaceDetail,
                                   current_time: datetime) -> float:
        """計算時段適合度分數

        評估當前時間是否適合遊玩該地點。
        結合了營業時間和建議遊玩時段的考量。

        評分考慮：
        - 是否在建議的遊玩時段
        - 與建議時段的時間差距
        - 營業時間的剩餘時間

        參數:
            place: 要評分的地點
            current_time: 當前時間

        回傳:
            float: 0-1 之間的時段適合度分數
        """
        # 取得當前時段
        current_period = self.time_service.get_time_period(current_time)

        # 基本分數：是否在建議時段
        if current_period == place.period:
            base_score = 1.0
        else:
            # 不在建議時段，但如果是相鄰時段，給予部分分數
            periods = ['morning', 'lunch', 'afternoon', 'dinner', 'night']
            current_idx = periods.index(current_period)
            place_idx = periods.index(place.period)
            period_diff = abs(current_idx - place_idx)

            base_score = max(0.3, 1.0 - (period_diff * 0.2))

        # 考慮營業時間的影響
        hours_score = self._evaluate_business_hours_fit(place, current_time)

        return min(1.0, base_score * hours_score)

    def _calculate_distance_score(self,
                                  place: PlaceDetail,
                                  current_location: PlaceDetail) -> float:
        """計算距離合理性分數

        評估地點與當前位置的距離是否合理。
        距離越近分數越高，但會根據地點類型調整期望。

        評分考慮：
        - 實際距離與可接受距離的比例
        - 地點類型（不同類型的可接受距離不同）
        - 位置的集中程度

        參數:
            place: 要評分的地點
            current_location: 當前位置

        回傳:
            float: 0-1 之間的距離分數
        """
        distance = self.geo_service.calculate_distance(
            {'lat': current_location.lat, 'lon': current_location.lon},
            {'lat': place.lat, 'lon': place.lon}
        )

        # 根據地點類型調整可接受距離
        adjusted_threshold = self.distance_threshold
        if place.label in ['景點', '主要景點']:
            adjusted_threshold *= 1.2  # 景點可以接受較遠的距離
        elif place.label in ['餐廳', '小吃']:
            adjusted_threshold *= 0.8  # 用餐地點最好要近一點

        # 計算距離分數
        score = 1.0 - (distance / adjusted_threshold)
        return max(0.0, min(1.0, score))

    def _evaluate_business_hours_fit(self,
                                     place: PlaceDetail,
                                     current_time: datetime) -> float:
        """評估營業時間的適合度

        這個方法不只確認是否在營業時間內，還會評估：
        1. 距離打烊還有多久（避免太接近打烊時間）
        2. 是否有足夠的遊玩時間
        3. 營業時間的連續性（避免中間休息的時段）

        參數:
            place: 要評分的地點
            current_time: 當前時間

        回傳:
            float: 0-1 之間的營業時間適合度分數
        """
        weekday = current_time.isoweekday()
        time_str = current_time.strftime(self.time_service.TIME_FORMAT)

        # 檢查是否在營業時間內
        is_open = place.is_open_at(weekday, time_str)
        if not is_open:
            return 0.0

        # 計算距離打烊還有多久
        closing_time = self._get_closing_time(place, weekday, current_time)
        if closing_time is None:
            return 0.8  # 24小時營業的地點給予較高基礎分數

        remaining_minutes = self._calculate_remaining_time(
            current_time, closing_time)

        # 根據剩餘時間評分
        if remaining_minutes < place.duration_min:
            return 0.0  # 剩餘時間不足
        elif remaining_minutes < place.duration_min * 1.5:
            # 時間稍嫌緊湊
            return 0.5
        else:
            # 有充足時間
            return 1.0

    def get_scoring_details(self,
                            place: PlaceDetail,
                            current_location: PlaceDetail,
                            current_time: datetime,
                            travel_time: float) -> Dict:
        """取得詳細的評分資訊

        這個方法不只計算總分，還會提供每個維度的詳細評分和原因。
        這些資訊可以：
        1. 幫助使用者理解評分邏輯
        2. 用於調整和優化評分系統
        3. 提供更好的行程建議

        參數:
            place: 要評分的地點
            current_location: 當前位置
            current_time: 當前時間
            travel_time: 預估交通時間

        回傳:
            Dict: {
                'total_score': float,     # 綜合評分
                'components': {           # 各維度的評分
                    'rating': float,
                    'efficiency': float,
                    'time_slot': float,
                    'distance': float
                },
                'reasons': List[str],     # 評分說明
                'suggestions': List[str]   # 改善建議
            }
        """
        # 計算各維度分數
        rating_score = self._calculate_rating_score(place)
        efficiency_score = self._calculate_efficiency_score(
            place, travel_time)
        time_slot_score = self._calculate_time_slot_score(
            place, current_time)
        distance_score = self._calculate_distance_score(
            place, current_location)

        # 計算總分
        total_score = self.calculate_score(
            place, current_location, current_time, travel_time)

        # 準備評分原因
        reasons = []
        suggestions = []

        # 評估評分結果並給出說明
        if rating_score >= 0.8:
            reasons.append("這是一個評價很高的地點")
        elif rating_score <= 0.3:
            reasons.append("這個地點的評價較低")
            suggestions.append("建議考慮其他類似的熱門地點")

        if efficiency_score < 0.5:
            reasons.append("交通時間相對停留時間較長")
            suggestions.append("建議與附近其他景點組合")

        if time_slot_score < 0.5:
            reasons.append("現在不是最佳的遊玩時段")
            next_slot = self._suggest_better_time_slot(place, current_time)
            if next_slot:
                suggestions.append(f"建議改在{next_slot}前往")

        if distance_score < 0.5:
            reasons.append("距離當前位置較遠")
            suggestions.append("建議先遊覽附近的景點")

        return {
            'total_score': total_score,
            'components': {
                'rating': rating_score,
                'efficiency': efficiency_score,
                'time_slot': time_slot_score,
                'distance': distance_score
            },
            'reasons': reasons,
            'suggestions': suggestions
        }

    def _normalize_score(self, score: float) -> float:
        """標準化評分到 0-1 區間

        使用 sigmoid 函數進行平滑的標準化，避免極端值。
        """
        return max(self.min_score,
                   min(self.max_score, score))

    def _suggest_better_time_slot(self,
                                  place: PlaceDetail,
                                  current_time: datetime) -> Optional[str]:
        """建議更好的遊玩時段

        根據地點特性和營業時間，建議更適合的遊玩時間。
        """
        suggested_period = place.period
        periods_map = {
            'morning': '上午',
            'lunch': '午餐時間',
            'afternoon': '下午',
            'dinner': '晚餐時間',
            'night': '晚上'
        }
        return periods_map.get(suggested_period)
