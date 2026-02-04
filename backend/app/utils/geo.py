"""地理計算工具

使用 Haversine 公式計算兩點間的球面距離
"""

import math
from typing import Optional


# 地球半徑（公里）
EARTH_RADIUS_KM = 6371.0


def haversine_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float
) -> float:
    """計算兩個經緯度座標間的距離（公里）

    使用 Haversine 公式計算球面距離

    Args:
        lat1: 第一點緯度
        lon1: 第一點經度
        lat2: 第二點緯度
        lon2: 第二點經度

    Returns:
        兩點間的距離（公里）
    """
    # 轉換為弧度
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    # Haversine 公式
    a = (
        math.sin(delta_lat / 2) ** 2 +
        math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return EARTH_RADIUS_KM * c


def find_nearest_station(
    user_lat: float,
    user_lon: float,
    stations: list[dict]
) -> Optional[dict]:
    """找出離用戶最近的站點

    Args:
        user_lat: 用戶緯度
        user_lon: 用戶經度
        stations: 站點列表，每個站點需包含 latitude, longitude

    Returns:
        最近站點資訊與距離，格式: {"station": {...}, "distance_km": float}
        如果沒有站點則返回 None
    """
    if not stations:
        return None

    nearest = None
    min_distance = float("inf")

    for station in stations:
        dist = haversine_distance(
            user_lat,
            user_lon,
            station["latitude"],
            station["longitude"]
        )

        if dist < min_distance:
            min_distance = dist
            nearest = station

    return {
        "station": nearest,
        "distance_km": round(min_distance, 2)
    }
