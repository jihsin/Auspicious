"""Rule-based personality labels for DayInsightCard.

Priority: record > anomaly > solar_term > seasonal. First match wins.
"""

NORTH_STATION_IDS = {"466900", "466920", "466940", "466910", "466930", "466950"}


def match_label(ctx: dict) -> dict:
    m = ctx["month"]
    p = ctx["precip_probability"]
    am = ctx["anomaly_month"]
    tz = ctx["temp_z"]
    pz = ctx["precip_z_in_month"]

    # 紀錄級
    if pz >= 1.96:
        return {"text": "紀錄級多雨", "category": "record"}
    if tz >= 1.96:
        return {"text": "紀錄級高溫", "category": "record"}

    # 異常
    if am >= 0.15:
        return {"text": "異常多雨期", "category": "anomaly"}
    if am <= -0.15:
        return {"text": "異常乾旱期", "category": "anomaly"}
    if tz >= 1.5:
        return {"text": "異常高溫", "category": "anomaly"}
    if tz <= -1.5:
        return {"text": "寒流警報", "category": "anomaly"}

    # 節氣轉換點
    if ctx["is_solar_term_day"]:
        return {"text": "節氣轉換點", "category": "solar_term"}

    # 季節典型
    if m in (5, 6) and p >= 0.50:
        return {"text": "典型梅雨日", "category": "seasonal"}
    if m in (7, 8) and p >= 0.45 and tz >= 1:
        return {"text": "盛夏雷雨日", "category": "seasonal"}
    if m in (12, 1, 2) and tz <= -1:
        return {"text": "冬季冷氣團", "category": "seasonal"}
    if m in (9, 10) and ctx["precip_z_in_month"] <= -1:
        return {"text": "秋高氣爽", "category": "seasonal"}
    if m in (10, 11) and ctx["is_north_station"]:
        return {"text": "東北季風前緣", "category": "seasonal"}

    return {"text": None, "category": None}


def is_north_station(station_id: str) -> bool:
    return station_id in NORTH_STATION_IDS
