# backend/app/services/planner.py
"""智慧活動規劃服務

根據歷史天氣、節氣、農民曆推薦最佳活動日期。
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional
from enum import Enum

from sqlalchemy.orm import Session

from app.models import DailyStatistics, Station
from app.services.lunar import get_lunar_info
from app.services.solar_term import get_current_solar_term, get_solar_term_info


class ActivityType(str, Enum):
    """活動類型"""
    WEDDING = "婚禮"
    OUTDOOR_WEDDING = "戶外婚禮"
    PICNIC = "野餐"
    HIKING = "登山"
    CAMPING = "露營"
    BEACH = "海邊活動"
    CYCLING = "騎車"
    RUNNING = "跑步"
    PHOTOGRAPHY = "攝影"
    FESTIVAL = "節慶活動"
    MARKET = "市集"
    BBQ = "烤肉"
    STARGAZING = "觀星"
    SUNRISE = "看日出"
    FLOWER_VIEWING = "賞花"
    GENERAL_OUTDOOR = "一般戶外"


# 活動對天氣的偏好設定
ACTIVITY_PREFERENCES = {
    ActivityType.WEDDING: {
        "rain_tolerance": 0.2,      # 可接受的降雨機率
        "temp_min": 18,             # 最低溫度
        "temp_max": 30,             # 最高溫度
        "temp_ideal": 24,           # 理想溫度
        "sunny_weight": 0.4,        # 晴天重要性
        "description": "婚禮需要好天氣，但室內可以避雨",
    },
    ActivityType.OUTDOOR_WEDDING: {
        "rain_tolerance": 0.1,
        "temp_min": 20,
        "temp_max": 28,
        "temp_ideal": 24,
        "sunny_weight": 0.6,
        "description": "戶外婚禮對天氣要求最高",
    },
    ActivityType.PICNIC: {
        "rain_tolerance": 0.15,
        "temp_min": 18,
        "temp_max": 30,
        "temp_ideal": 25,
        "sunny_weight": 0.5,
        "description": "野餐需要晴朗舒適的天氣",
    },
    ActivityType.HIKING: {
        "rain_tolerance": 0.25,
        "temp_min": 12,
        "temp_max": 28,
        "temp_ideal": 20,
        "sunny_weight": 0.3,
        "description": "登山可接受些許雲雨，涼爽更佳",
    },
    ActivityType.CAMPING: {
        "rain_tolerance": 0.15,
        "temp_min": 15,
        "temp_max": 30,
        "temp_ideal": 22,
        "sunny_weight": 0.4,
        "description": "露營需要乾燥天氣",
    },
    ActivityType.BEACH: {
        "rain_tolerance": 0.2,
        "temp_min": 25,
        "temp_max": 35,
        "temp_ideal": 30,
        "sunny_weight": 0.6,
        "description": "海邊活動需要陽光和溫暖",
    },
    ActivityType.CYCLING: {
        "rain_tolerance": 0.15,
        "temp_min": 15,
        "temp_max": 32,
        "temp_ideal": 23,
        "sunny_weight": 0.3,
        "description": "騎車避免下雨，涼爽較佳",
    },
    ActivityType.RUNNING: {
        "rain_tolerance": 0.2,
        "temp_min": 10,
        "temp_max": 28,
        "temp_ideal": 18,
        "sunny_weight": 0.2,
        "description": "跑步偏好涼爽天氣",
    },
    ActivityType.PHOTOGRAPHY: {
        "rain_tolerance": 0.3,
        "temp_min": 10,
        "temp_max": 35,
        "temp_ideal": 22,
        "sunny_weight": 0.3,
        "description": "攝影各種天氣都有不同美感",
    },
    ActivityType.FESTIVAL: {
        "rain_tolerance": 0.25,
        "temp_min": 15,
        "temp_max": 32,
        "temp_ideal": 25,
        "sunny_weight": 0.4,
        "description": "節慶活動希望人潮舒適",
    },
    ActivityType.MARKET: {
        "rain_tolerance": 0.2,
        "temp_min": 15,
        "temp_max": 32,
        "temp_ideal": 25,
        "sunny_weight": 0.3,
        "description": "市集活動希望天氣舒適",
    },
    ActivityType.BBQ: {
        "rain_tolerance": 0.1,
        "temp_min": 18,
        "temp_max": 32,
        "temp_ideal": 26,
        "sunny_weight": 0.5,
        "description": "烤肉需要乾燥天氣",
    },
    ActivityType.STARGAZING: {
        "rain_tolerance": 0.05,
        "temp_min": 10,
        "temp_max": 30,
        "temp_ideal": 20,
        "sunny_weight": 0.7,
        "description": "觀星需要晴朗無雲",
    },
    ActivityType.SUNRISE: {
        "rain_tolerance": 0.1,
        "temp_min": 10,
        "temp_max": 30,
        "temp_ideal": 20,
        "sunny_weight": 0.6,
        "description": "看日出需要晴朗天空",
    },
    ActivityType.FLOWER_VIEWING: {
        "rain_tolerance": 0.3,
        "temp_min": 15,
        "temp_max": 28,
        "temp_ideal": 22,
        "sunny_weight": 0.3,
        "description": "賞花適合舒適天氣，小雨也別有風味",
    },
    ActivityType.GENERAL_OUTDOOR: {
        "rain_tolerance": 0.2,
        "temp_min": 15,
        "temp_max": 32,
        "temp_ideal": 24,
        "sunny_weight": 0.4,
        "description": "一般戶外活動",
    },
}


@dataclass
class DayScore:
    """單日評分"""
    date: date
    score: float                    # 0-100 分
    weather_score: float            # 天氣分數
    rain_probability: float         # 降雨機率
    temp_avg: float                 # 平均溫度
    sunny_ratio: float              # 晴天比例
    solar_term: Optional[str]       # 節氣（如果當天是）
    lunar_date: str                 # 農曆日期
    lunar_yi: list[str]             # 宜
    lunar_ji: list[str]             # 忌
    notes: list[str] = field(default_factory=list)  # 備註


@dataclass
class PlannerResult:
    """規劃結果"""
    activity_type: str
    location: str
    station_id: str
    station_name: str
    date_range: tuple[date, date]
    recommendations: list[DayScore]
    best_date: Optional[DayScore]
    summary: str


def _calculate_weather_score(
    stats: DailyStatistics,
    prefs: dict,
) -> tuple[float, list[str]]:
    """計算天氣分數

    Returns:
        (分數 0-100, 備註列表)
    """
    notes = []
    score = 100.0

    # 降雨機率扣分
    rain_prob = stats.precip_probability or 0
    if rain_prob > prefs["rain_tolerance"]:
        penalty = (rain_prob - prefs["rain_tolerance"]) * 100
        score -= penalty
        if rain_prob > 0.5:
            notes.append(f"降雨機率高 ({rain_prob*100:.0f}%)")
        elif rain_prob > 0.3:
            notes.append(f"可能有雨 ({rain_prob*100:.0f}%)")

    # 溫度分數
    temp = stats.temp_avg_mean or 25
    temp_ideal = prefs["temp_ideal"]
    temp_min = prefs["temp_min"]
    temp_max = prefs["temp_max"]

    if temp < temp_min:
        penalty = (temp_min - temp) * 5
        score -= penalty
        notes.append(f"偏冷 ({temp:.1f}°C)")
    elif temp > temp_max:
        penalty = (temp - temp_max) * 5
        score -= penalty
        notes.append(f"偏熱 ({temp:.1f}°C)")
    else:
        # 離理想溫度的距離
        temp_diff = abs(temp - temp_ideal)
        score -= temp_diff * 2

    # 晴天加分
    sunny = stats.tendency_sunny or 0
    sunny_weight = prefs["sunny_weight"]
    sunny_bonus = sunny * sunny_weight * 30
    score += sunny_bonus

    if sunny > 0.6:
        notes.append("晴天機率高")
    elif sunny < 0.3:
        notes.append("多雲或陰天")

    return max(0, min(100, score)), notes


def _get_lunar_score_notes(lunar_info: dict, activity_type: ActivityType) -> tuple[float, list[str]]:
    """根據農民曆宜忌計算分數和備註

    Args:
        lunar_info: 農曆資訊 dict，包含 yi_ji 等欄位
        activity_type: 活動類型
    """
    notes = []
    score_adj = 0

    # 檢查宜
    yi_keywords = {
        ActivityType.WEDDING: ["嫁娶", "訂盟", "納采"],
        ActivityType.OUTDOOR_WEDDING: ["嫁娶", "訂盟"],
        ActivityType.HIKING: ["出行", "遠行", "登山"],
        ActivityType.CAMPING: ["出行", "遠行"],
        ActivityType.GENERAL_OUTDOOR: ["出行"],
    }

    # 檢查忌
    ji_keywords = {
        ActivityType.WEDDING: ["嫁娶"],
        ActivityType.OUTDOOR_WEDDING: ["嫁娶"],
        ActivityType.HIKING: ["出行", "遠行"],
        ActivityType.CAMPING: ["出行", "遠行"],
    }

    yi_ji = lunar_info.get("yi_ji", {})
    yi_list = yi_ji.get("yi", [])
    ji_list = yi_ji.get("ji", [])

    # 檢查宜
    if activity_type in yi_keywords:
        for kw in yi_keywords[activity_type]:
            if any(kw in yi for yi in yi_list):
                score_adj += 5
                notes.append(f"宜{kw}")
                break

    # 檢查忌
    if activity_type in ji_keywords:
        for kw in ji_keywords[activity_type]:
            if any(kw in ji for ji in ji_list):
                score_adj -= 10
                notes.append(f"忌{kw}")
                break

    return score_adj, notes


def plan_activity(
    db: Session,
    activity_type: ActivityType,
    station_id: str,
    start_date: date,
    end_date: date,
    top_n: int = 5,
) -> Optional[PlannerResult]:
    """規劃活動最佳日期

    Args:
        db: 資料庫 session
        activity_type: 活動類型
        station_id: 氣象站 ID
        start_date: 開始日期
        end_date: 結束日期
        top_n: 返回前 N 個推薦日期

    Returns:
        PlannerResult 或 None
    """
    # 取得站點資訊
    station = db.query(Station).filter(Station.station_id == station_id).first()
    if not station:
        return None

    # 取得活動偏好
    prefs = ACTIVITY_PREFERENCES.get(activity_type, ACTIVITY_PREFERENCES[ActivityType.GENERAL_OUTDOOR])

    # 計算每日分數
    day_scores: list[DayScore] = []

    current = start_date
    while current <= end_date:
        month_day = current.strftime("%m-%d")

        # 取得歷史統計
        stats = db.query(DailyStatistics).filter(
            DailyStatistics.station_id == station_id,
            DailyStatistics.month_day == month_day
        ).first()

        if not stats:
            current += timedelta(days=1)
            continue

        # 計算天氣分數
        weather_score, weather_notes = _calculate_weather_score(stats, prefs)

        # 取得農曆資訊
        lunar_info = get_lunar_info(current)
        lunar_adj, lunar_notes = _get_lunar_score_notes(lunar_info, activity_type)

        # 取得節氣
        solar_term = get_current_solar_term(current)
        solar_notes = []
        if solar_term:
            solar_notes.append(f"節氣：{solar_term}")

        # 總分
        total_score = weather_score + lunar_adj

        # 取得農曆日期
        lunar_date_info = lunar_info.get("lunar_date", {})
        lunar_month = lunar_date_info.get("month_cn", "")
        lunar_day = lunar_date_info.get("day_cn", "")
        yi_ji = lunar_info.get("yi_ji", {})

        day_scores.append(DayScore(
            date=current,
            score=max(0, min(100, total_score)),
            weather_score=weather_score,
            rain_probability=stats.precip_probability or 0,
            temp_avg=stats.temp_avg_mean or 25,
            sunny_ratio=stats.tendency_sunny or 0,
            solar_term=solar_term,
            lunar_date=f"{lunar_month}{lunar_day}",
            lunar_yi=yi_ji.get("yi", [])[:3],
            lunar_ji=yi_ji.get("ji", [])[:3],
            notes=weather_notes + lunar_notes + solar_notes,
        ))

        current += timedelta(days=1)

    if not day_scores:
        return None

    # 排序取前 N
    day_scores.sort(key=lambda x: x.score, reverse=True)
    recommendations = day_scores[:top_n]
    best = recommendations[0] if recommendations else None

    # 生成摘要
    summary = _generate_summary(activity_type, station.name, recommendations, prefs)

    return PlannerResult(
        activity_type=activity_type.value,
        location=station.county or "",
        station_id=station_id,
        station_name=station.name,
        date_range=(start_date, end_date),
        recommendations=recommendations,
        best_date=best,
        summary=summary,
    )


def _generate_summary(
    activity_type: ActivityType,
    station_name: str,
    recommendations: list[DayScore],
    prefs: dict,
) -> str:
    """生成規劃摘要"""
    if not recommendations:
        return "在指定日期範圍內沒有找到適合的日期。"

    best = recommendations[0]

    if best.score >= 80:
        quality = "非常適合"
    elif best.score >= 65:
        quality = "適合"
    elif best.score >= 50:
        quality = "尚可"
    else:
        quality = "條件較差"

    summary = f"在{station_name}地區，{best.date.strftime('%m/%d')} {quality}{activity_type.value}。"

    if best.rain_probability < 0.2:
        summary += f"降雨機率低（{best.rain_probability*100:.0f}%）。"
    elif best.rain_probability < 0.4:
        summary += f"有些許降雨可能（{best.rain_probability*100:.0f}%）。"
    else:
        summary += f"需注意降雨（{best.rain_probability*100:.0f}%）。"

    summary += f"歷史平均溫度 {best.temp_avg:.1f}°C。"

    if best.solar_term:
        summary += f"當天為{best.solar_term}。"

    if len(recommendations) > 1:
        alternatives = [r.date.strftime('%m/%d') for r in recommendations[1:3]]
        summary += f"備選日期：{', '.join(alternatives)}。"

    return summary


def get_activity_types() -> list[dict]:
    """取得所有活動類型及描述"""
    return [
        {
            "type": at.value,
            "key": at.name,
            "description": ACTIVITY_PREFERENCES[at]["description"],
        }
        for at in ActivityType
    ]
