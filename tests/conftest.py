import pytest


@pytest.fixture
def sample_locations():
    return [
        {
            'name': '台北101',
            'lat': 25.0339808,
            'lon': 121.561964,
            'duration': 150,
            'label': '景點',
            'hours': '09:00 - 22:00'
        },
        # ... 其他測試資料
    ]


@pytest.fixture
def test_plan(sample_locations):
    from src.core.TripPlanner import plan_trip
    return plan_trip(locations=sample_locations)
