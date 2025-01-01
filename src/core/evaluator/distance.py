# src/core/evaluator/distance.py

from src.core.utils.geo_core import GeoCore


class DistanceCalculator:
    """距離計算工具類別，使用 GeoCore 計算"""

    @classmethod
    def calculate_distance(cls, loc1, loc2) -> float:
        return GeoCore.calculate_distance(loc1, loc2)

    @classmethod
    def get_distance_factor(cls, distance: float, threshold: float) -> float:
        """計算距離評分因子"""
        return 0.0 if distance >= threshold else 1.0 - (distance / threshold)
