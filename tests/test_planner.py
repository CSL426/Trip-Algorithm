# tests/test_planner.py

def test_trip_planning(trip_planner):
    # 使用 conftest.py 中定義的 fixture
    assert len(trip_planner) > 0
    assert trip_planner[0]['name'] is not None
