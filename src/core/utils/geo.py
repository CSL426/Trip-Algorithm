# src/core/utils/geo.py

from src.core.utils.geo_core import GeoCore


class GeoCalculator:
    """地理計算工具類別，使用 GeoCore"""

    @classmethod
    def calculate_distance(cls, loc1, loc2):
        return GeoCore.calculate_distance(loc1, loc2)

    @classmethod
    def calculate_region_bounds(cls, center, radius_km):
        return GeoCore.calculate_region_bounds(center, radius_km)

    @classmethod
    def is_point_in_bounds(cls, point, bounds):
        min_lat, max_lat, min_lon, max_lon = bounds
        return (min_lat <= point['lat'] <= max_lat and
                min_lon <= point['lon'] <= max_lon)
