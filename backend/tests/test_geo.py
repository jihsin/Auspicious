"""地理計算工具測試"""

import pytest
from app.utils.geo import haversine_distance, find_nearest_station


def test_haversine_distance_same_point():
    """測試同一點距離為 0"""
    dist = haversine_distance(25.0, 121.5, 25.0, 121.5)
    assert dist == 0.0


def test_haversine_distance_taipei_to_kaohsiung():
    """測試台北到高雄約 300 公里（直線距離）"""
    # 台北: 25.0330, 121.5654
    # 高雄: 22.6273, 120.3014
    dist = haversine_distance(25.0330, 121.5654, 22.6273, 120.3014)

    # 直線距離約 297 公里，允許 10% 誤差
    assert 270 < dist < 330


def test_haversine_distance_short():
    """測試短距離（約 5 公里）"""
    # 台北車站: 25.0478, 121.5170
    # 台北 101: 25.0339, 121.5645
    dist = haversine_distance(25.0478, 121.5170, 25.0339, 121.5645)

    # 約 5 公里
    assert 4 < dist < 6


def test_find_nearest_station():
    """測試找最近站點"""
    stations = [
        {"station_id": "A", "name": "站A", "latitude": 25.0, "longitude": 121.5},
        {"station_id": "B", "name": "站B", "latitude": 25.1, "longitude": 121.6},
        {"station_id": "C", "name": "站C", "latitude": 24.0, "longitude": 120.0},
    ]

    # 用戶位置接近站 A
    result = find_nearest_station(25.01, 121.51, stations)

    assert result["station"]["station_id"] == "A"
    assert result["distance_km"] < 5


def test_find_nearest_station_empty_list():
    """測試空站點列表"""
    result = find_nearest_station(25.0, 121.5, [])
    assert result is None
