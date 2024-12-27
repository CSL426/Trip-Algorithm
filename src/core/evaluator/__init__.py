# src/core/evaluator/__init__.py

"""
評分器模組
此模組負責處理所有與地點評分相關的功能，包括：
1. 距離計算與評估
2. 地點適合度評分
3. 時間效率計算

主要組件：
- LocationEvaluator: 地點評分的核心類別
- DistanceCalculator: 處理距離計算的工具類別

使用方式：
from src.core.evaluator import LocationEvaluator, DistanceCalculator

# 建立評分器實例
evaluator = LocationEvaluator(current_time=datetime.now(), 
                            distance_threshold=30.0)

# 計算地點評分
score = evaluator.calculate_score(location, current_location, 
                                travel_time, is_meal_time)
"""

from .location import LocationEvaluator
from .distance import DistanceCalculator

__all__ = [
    'LocationEvaluator',
    'DistanceCalculator'
]
