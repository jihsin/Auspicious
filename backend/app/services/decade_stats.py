"""年代分層統計服務

從 raw_observations 計算各年代的氣象統計，
展示氣候變遷趨勢。
"""

from typing import Optional
from dataclasses import dataclass
from sqlalchemy import text
from sqlalchemy.orm import Session


@dataclass
class DecadeData:
    """單一年代的統計資料"""
    decade: str  # "1990s", "2000s", "2010s", "2020s"
    start_year: int
    end_year: int
    years_count: int
    temp_avg: Optional[float]
    temp_max_avg: Optional[float]
    temp_min_avg: Optional[float]
    precip_prob: Optional[float]  # 降雨機率
    precip_avg: Optional[float]   # 平均降水量


@dataclass
class DecadeComparison:
    """年代比較結果"""
    station_id: str
    month_day: str
    decades: list[DecadeData]
    recent_10y: Optional[DecadeData]  # 近 10 年統計
    all_time: Optional[DecadeData]     # 全期統計
    trend_temp: Optional[float]        # 溫度趨勢（每 10 年變化）
    trend_precip: Optional[float]      # 降雨趨勢


def get_decade_label(year: int) -> str:
    """將年份轉換為年代標籤"""
    decade = (year // 10) * 10
    return f"{decade}s"


def calculate_decade_stats(
    db: Session,
    station_id: str,
    month_day: str
) -> Optional[DecadeComparison]:
    """計算指定站點和日期的年代分層統計

    Args:
        db: 資料庫 session
        station_id: 氣象站代碼
        month_day: 日期 (MM-DD 格式)

    Returns:
        DecadeComparison 或 None（如果沒有資料）
    """

    # 查詢該日期所有年份的原始資料
    query = text("""
        SELECT
            strftime('%Y', observed_date) as year,
            temperature_avg,
            temperature_max,
            temperature_min,
            precipitation
        FROM raw_observations
        WHERE station_id = :station_id
        AND strftime('%m-%d', observed_date) = :month_day
        ORDER BY year
    """)

    result = db.execute(query, {
        "station_id": station_id,
        "month_day": month_day
    })
    rows = result.fetchall()

    if not rows:
        return None

    # 按年代分組
    decade_data: dict[str, list] = {}
    all_data = []
    recent_data = []  # 近 10 年

    current_year = 2026  # 當前年份

    for row in rows:
        year = int(row[0])
        temp_avg = row[1]
        temp_max = row[2]
        temp_min = row[3]
        precip = row[4]

        # 跳過無效資料
        if temp_avg is None:
            continue

        record = {
            "year": year,
            "temp_avg": temp_avg,
            "temp_max": temp_max,
            "temp_min": temp_min,
            "precip": precip
        }

        # 加入全部資料
        all_data.append(record)

        # 加入近 10 年
        if year >= current_year - 10:
            recent_data.append(record)

        # 按年代分組
        decade = get_decade_label(year)
        if decade not in decade_data:
            decade_data[decade] = []
        decade_data[decade].append(record)

    if not all_data:
        return None

    # 計算各年代統計
    decades = []
    for decade_label in sorted(decade_data.keys()):
        data = decade_data[decade_label]
        decades.append(_calculate_stats(decade_label, data))

    # 計算近 10 年統計
    recent_10y = None
    if recent_data:
        recent_10y = _calculate_stats("recent_10y", recent_data)

    # 計算全期統計
    all_time = _calculate_stats("all_time", all_data)

    # 計算趨勢（簡單線性回歸）
    trend_temp = _calculate_trend([d["year"] for d in all_data],
                                   [d["temp_avg"] for d in all_data])

    return DecadeComparison(
        station_id=station_id,
        month_day=month_day,
        decades=decades,
        recent_10y=recent_10y,
        all_time=all_time,
        trend_temp=trend_temp,
        trend_precip=None  # 降雨趨勢較複雜，暫不計算
    )


def _calculate_stats(label: str, data: list[dict]) -> DecadeData:
    """計算單一組資料的統計"""
    years = [d["year"] for d in data]
    temps = [d["temp_avg"] for d in data if d["temp_avg"] is not None]
    temp_maxs = [d["temp_max"] for d in data if d["temp_max"] is not None]
    temp_mins = [d["temp_min"] for d in data if d["temp_min"] is not None]
    precips = [d["precip"] for d in data if d["precip"] is not None]

    # 降雨機率 = 有降雨的天數 / 總天數
    rain_days = len([p for p in precips if p and p > 0])
    precip_prob = rain_days / len(precips) if precips else None

    # 平均降水量（有雨時）
    rain_amounts = [p for p in precips if p and p > 0]
    precip_avg = sum(rain_amounts) / len(rain_amounts) if rain_amounts else None

    return DecadeData(
        decade=label,
        start_year=min(years),
        end_year=max(years),
        years_count=len(years),
        temp_avg=sum(temps) / len(temps) if temps else None,
        temp_max_avg=sum(temp_maxs) / len(temp_maxs) if temp_maxs else None,
        temp_min_avg=sum(temp_mins) / len(temp_mins) if temp_mins else None,
        precip_prob=precip_prob,
        precip_avg=precip_avg
    )


def _calculate_trend(years: list[int], values: list[float]) -> Optional[float]:
    """計算簡單線性趨勢（每 10 年變化量）

    使用最小二乘法計算斜率
    """
    if len(years) < 5 or len(values) < 5:
        return None

    n = len(years)
    sum_x = sum(years)
    sum_y = sum(values)
    sum_xy = sum(x * y for x, y in zip(years, values))
    sum_x2 = sum(x * x for x in years)

    # 斜率 = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x^2)
    denominator = n * sum_x2 - sum_x * sum_x
    if denominator == 0:
        return None

    slope = (n * sum_xy - sum_x * sum_y) / denominator

    # 轉換為每 10 年變化量
    return round(slope * 10, 2)


def get_percentile_rank(
    db: Session,
    station_id: str,
    month_day: str,
    current_temp: float
) -> Optional[float]:
    """計算當前溫度在歷史中的百分位數

    Args:
        db: 資料庫 session
        station_id: 氣象站代碼
        month_day: 日期
        current_temp: 當前溫度

    Returns:
        百分位數 (0-100)，表示「高於歷史 X% 的紀錄」
    """
    query = text("""
        SELECT temperature_avg
        FROM raw_observations
        WHERE station_id = :station_id
        AND strftime('%m-%d', observed_date) = :month_day
        AND temperature_avg IS NOT NULL
        ORDER BY temperature_avg
    """)

    result = db.execute(query, {
        "station_id": station_id,
        "month_day": month_day
    })
    temps = [row[0] for row in result.fetchall()]

    if not temps:
        return None

    # 計算有多少比例的歷史值小於當前值
    below_count = sum(1 for t in temps if t < current_temp)
    percentile = (below_count / len(temps)) * 100

    return round(percentile, 1)


def get_extreme_records(
    db: Session,
    station_id: str,
    month_day: str
) -> dict:
    """取得歷史極值紀錄（含年份）

    Returns:
        {
            "max_temp": {"value": 31.2, "year": 2019},
            "min_temp": {"value": 6.3, "year": 1993},
            "max_precip": {"value": 125.5, "year": 2001}
        }
    """
    # 最高溫
    max_temp_query = text("""
        SELECT temperature_max, strftime('%Y', observed_date) as year
        FROM raw_observations
        WHERE station_id = :station_id
        AND strftime('%m-%d', observed_date) = :month_day
        AND temperature_max IS NOT NULL
        ORDER BY temperature_max DESC
        LIMIT 1
    """)

    # 最低溫
    min_temp_query = text("""
        SELECT temperature_min, strftime('%Y', observed_date) as year
        FROM raw_observations
        WHERE station_id = :station_id
        AND strftime('%m-%d', observed_date) = :month_day
        AND temperature_min IS NOT NULL
        ORDER BY temperature_min ASC
        LIMIT 1
    """)

    # 最大降水
    max_precip_query = text("""
        SELECT precipitation, strftime('%Y', observed_date) as year
        FROM raw_observations
        WHERE station_id = :station_id
        AND strftime('%m-%d', observed_date) = :month_day
        AND precipitation IS NOT NULL
        ORDER BY precipitation DESC
        LIMIT 1
    """)

    records = {}

    result = db.execute(max_temp_query, {"station_id": station_id, "month_day": month_day})
    row = result.fetchone()
    if row:
        records["max_temp"] = {"value": row[0], "year": int(row[1])}

    result = db.execute(min_temp_query, {"station_id": station_id, "month_day": month_day})
    row = result.fetchone()
    if row:
        records["min_temp"] = {"value": row[0], "year": int(row[1])}

    result = db.execute(max_precip_query, {"station_id": station_id, "month_day": month_day})
    row = result.fetchone()
    if row and row[0] and row[0] > 0:
        records["max_precip"] = {"value": row[0], "year": int(row[1])}

    return records
