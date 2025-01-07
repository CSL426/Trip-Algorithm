# trip/__init__.py

"""
行程規劃模組
匯出 TripPlanningSystem 供其他模組使用
"""
from .src.core.planner.system import TripPlanningSystem

__all__ = ['TripPlanningSystem']
__version__ = '0.1.0'
__author__ = "Spark Liao"
