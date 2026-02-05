# backend/app/api/v1/weather.py
"""天氣查詢 API 路由"""

from datetime import datetime, date
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.statistics import DailyStatistics
from app.models.station import Station
from app.schemas.weather import (
    ApiResponse,
    AnalysisPeriod,
    BestDatesResponse,
    DailyWeatherResponse,
    DailyWeatherSummary,
    DateRangeResponse,
    PrecipitationResponse,
    RangeSummary,
    RecommendedDate,
    StationInfo,
    TemperatureRecord,
    TemperatureResponse,
    TemperatureStats,
    WeatherTendencyResponse,
)
from app.schemas.lunar import LunarDateInfo, YiJiInfo
from app.services.lunar import get_lunar_info

router = APIRouter()


def _get_station_info(station_id: str, db: Session) -> StationInfo:
    """從資料庫取得站點資訊"""
    station = db.query(Station).filter(Station.station_id == station_id).first()

    if not station:
        raise HTTPException(
            status_code=404,
            detail=f"找不到站點 {station_id}"
        )

    return StationInfo(
        station_id=station.station_id,
        name=station.name,
        city=station.county or ""
    )


def _get_lunar_info_for_date(month_day: str) -> dict:
    """取得指定日期的農曆資訊

    Args:
        month_day: MM-DD 格式的日期

    Returns:
        農曆資訊字典，包含 lunar_date, yi_ji, jieqi
    """
    today = datetime.now()
    month, day = map(int, month_day.split("-"))
    query_date = date(today.year, month, day)
    return get_lunar_info(query_date)


def _statistics_to_response(
    stats: DailyStatistics,
    station_info: StationInfo,
    lunar_info: Optional[dict] = None
) -> DailyWeatherResponse:
    """將資料庫模型轉換為 API 回應

    Args:
        stats: 資料庫統計模型
        station_info: 站點資訊
        lunar_info: 農曆資訊（可選）

    Returns:
        API 回應物件
    """
    # 處理農曆資訊
    lunar_date = None
    yi_ji = None
    jieqi = None

    if lunar_info:
        lunar_date = LunarDateInfo(**lunar_info["lunar_date"])
        yi_ji = YiJiInfo(**lunar_info["yi_ji"])
        jieqi = lunar_info.get("jieqi")

    return DailyWeatherResponse(
        station=station_info,
        month_day=stats.month_day,
        analysis_period=AnalysisPeriod(
            years_analyzed=stats.years_analyzed,
            start_year=stats.start_year,
            end_year=stats.end_year
        ),
        temperature=TemperatureResponse(
            avg=TemperatureStats(
                mean=stats.temp_avg_mean,
                median=stats.temp_avg_median,
                stddev=stats.temp_avg_stddev
            ),
            max_mean=stats.temp_max_mean,
            max_record=TemperatureRecord(value=stats.temp_max_record),
            min_mean=stats.temp_min_mean,
            min_record=TemperatureRecord(value=stats.temp_min_record)
        ),
        precipitation=PrecipitationResponse(
            probability=stats.precip_probability,
            avg_when_rain=stats.precip_avg_when_rain,
            heavy_probability=stats.precip_heavy_prob,
            max_record=stats.precip_max_record
        ),
        tendency=WeatherTendencyResponse(
            sunny=stats.tendency_sunny,
            cloudy=stats.tendency_cloudy,
            rainy=stats.tendency_rainy
        ),
        computed_at=stats.computed_at,
        lunar_date=lunar_date,
        yi_ji=yi_ji,
        jieqi=jieqi
    )


@router.get(
    "/daily/{station_id}/{month_day}",
    response_model=ApiResponse[DailyWeatherResponse],
    summary="查詢指定日期的歷史天氣統計",
    description="根據站點代碼和日期（MM-DD 格式）查詢歷史天氣統計資料"
)
async def get_daily_statistics(
    station_id: str = Path(..., description="氣象站代碼", example="466920"),
    month_day: str = Path(
        ...,
        pattern=r"^\d{2}-\d{2}$",
        description="日期 (MM-DD 格式)",
        example="02-04"
    ),
    db: Session = Depends(get_db)
) -> ApiResponse[DailyWeatherResponse]:
    """查詢指定日期的歷史天氣統計

    Args:
        station_id: 氣象站代碼（如 466920 為臺北站）
        month_day: 日期，格式為 MM-DD（如 02-04 為 2 月 4 日）
        db: 資料庫 session

    Returns:
        包含溫度、降水、天氣傾向等統計資料的回應

    Raises:
        404: 找不到指定站點或日期的統計資料
    """
    # 驗證站點
    station_info = _get_station_info(station_id, db)

    # 驗證日期格式
    try:
        month, day = map(int, month_day.split("-"))
        if not (1 <= month <= 12 and 1 <= day <= 31):
            raise ValueError("Invalid date")
        # 進一步驗證日期有效性（考慮閏年）
        datetime(2000, month, day)  # 2000 是閏年
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"無效的日期格式: {month_day}，請使用 MM-DD 格式"
        )

    # 查詢統計資料
    stats = db.query(DailyStatistics).filter(
        DailyStatistics.station_id == station_id,
        DailyStatistics.month_day == month_day
    ).first()

    if not stats:
        raise HTTPException(
            status_code=404,
            detail=f"找不到 {station_info.name} 站 {month_day} 的統計資料"
        )

    # 取得農曆資訊
    lunar_info = _get_lunar_info_for_date(month_day)

    return ApiResponse(
        success=True,
        data=_statistics_to_response(stats, station_info, lunar_info)
    )


@router.get(
    "/today/{station_id}",
    response_model=ApiResponse[DailyWeatherResponse],
    summary="查詢今日的歷史天氣統計",
    description="根據站點代碼查詢今日對應日期的歷史天氣統計資料"
)
async def get_today_statistics(
    station_id: str = Path(..., description="氣象站代碼", example="466920"),
    db: Session = Depends(get_db)
) -> ApiResponse[DailyWeatherResponse]:
    """查詢今日的歷史天氣統計

    根據系統日期自動計算 MM-DD，並查詢對應的歷史統計資料。

    Args:
        station_id: 氣象站代碼（如 466920 為臺北站）
        db: 資料庫 session

    Returns:
        包含今日歷史溫度、降水、天氣傾向等統計資料的回應

    Raises:
        404: 找不到指定站點的統計資料
    """
    # 取得今日日期
    today = datetime.now()
    month_day = today.strftime("%m-%d")

    # 驗證站點
    station_info = _get_station_info(station_id, db)

    # 查詢統計資料
    stats = db.query(DailyStatistics).filter(
        DailyStatistics.station_id == station_id,
        DailyStatistics.month_day == month_day
    ).first()

    if not stats:
        raise HTTPException(
            status_code=404,
            detail=f"找不到 {station_info.name} 站 {month_day} 的統計資料"
        )

    # 取得農曆資訊
    lunar_info = _get_lunar_info_for_date(month_day)

    return ApiResponse(
        success=True,
        data=_statistics_to_response(stats, station_info, lunar_info)
    )


def _generate_date_range(start: str, end: str) -> List[str]:
    """產生日期範圍列表

    Args:
        start: 起始日期 MM-DD
        end: 結束日期 MM-DD

    Returns:
        日期列表 ["MM-DD", ...]
    """
    dates = []
    start_month, start_day = map(int, start.split("-"))
    end_month, end_day = map(int, end.split("-"))

    # 使用 2000 年（閏年）來處理日期
    start_date = date(2000, start_month, start_day)
    end_date = date(2000, end_month, end_day)

    # 處理跨年的情況
    if end_date < start_date:
        end_date = date(2001, end_month, end_day)

    current = start_date
    while current <= end_date:
        dates.append(current.strftime("%m-%d"))
        current = date(current.year, current.month, current.day)
        # 手動增加一天
        try:
            current = date(current.year, current.month, current.day + 1)
        except ValueError:
            # 月底，跳到下個月
            if current.month == 12:
                current = date(current.year + 1, 1, 1)
            else:
                current = date(current.year, current.month + 1, 1)

    return dates


@router.get(
    "/range/{station_id}",
    response_model=ApiResponse[DateRangeResponse],
    summary="查詢日期範圍的歷史天氣統計",
    description="根據站點代碼和日期範圍查詢歷史天氣統計資料"
)
async def get_range_statistics(
    station_id: str = Path(..., description="氣象站代碼", example="466920"),
    start: str = Query(
        ...,
        pattern=r"^\d{2}-\d{2}$",
        description="起始日期 (MM-DD 格式)",
        example="03-01"
    ),
    end: str = Query(
        ...,
        pattern=r"^\d{2}-\d{2}$",
        description="結束日期 (MM-DD 格式)",
        example="03-15"
    ),
    db: Session = Depends(get_db)
) -> ApiResponse[DateRangeResponse]:
    """查詢日期範圍的歷史天氣統計

    Args:
        station_id: 氣象站代碼
        start: 起始日期 (MM-DD)
        end: 結束日期 (MM-DD)
        db: 資料庫 session

    Returns:
        包含範圍內每日統計與摘要的回應
    """
    # 驗證站點
    station_info = _get_station_info(station_id, db)

    # 驗證日期格式
    for date_str in [start, end]:
        try:
            month, day = map(int, date_str.split("-"))
            if not (1 <= month <= 12 and 1 <= day <= 31):
                raise ValueError("Invalid date")
            datetime(2000, month, day)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"無效的日期格式: {date_str}，請使用 MM-DD 格式"
            )

    # 產生日期範圍
    date_range = _generate_date_range(start, end)

    # 限制範圍（最多 31 天）
    if len(date_range) > 31:
        raise HTTPException(
            status_code=400,
            detail="日期範圍不能超過 31 天"
        )

    # 查詢所有日期的統計資料
    stats_list = db.query(DailyStatistics).filter(
        DailyStatistics.station_id == station_id,
        DailyStatistics.month_day.in_(date_range)
    ).all()

    # 建立查詢結果字典
    stats_dict = {s.month_day: s for s in stats_list}

    # 組裝每日摘要
    days = []
    total_temp = 0
    total_precip = 0
    total_sunny = 0
    valid_count = 0
    best_day = None
    best_sunny = -1
    worst_day = None
    worst_precip = -1

    for md in date_range:
        stats = stats_dict.get(md)

        if stats:
            # 取得農曆資訊
            lunar_info = _get_lunar_info_for_date(md)
            lunar_date = LunarDateInfo(**lunar_info["lunar_date"]) if lunar_info else None
            jieqi = lunar_info.get("jieqi") if lunar_info else None

            summary = DailyWeatherSummary(
                month_day=md,
                temp_avg=stats.temp_avg_mean,
                temp_max=stats.temp_max_mean,
                temp_min=stats.temp_min_mean,
                precip_prob=stats.precip_probability,
                sunny_rate=stats.tendency_sunny,
                lunar_date=lunar_date,
                jieqi=jieqi
            )
            days.append(summary)

            # 統計計算
            if stats.temp_avg_mean is not None:
                total_temp += stats.temp_avg_mean
            if stats.precip_probability is not None:
                total_precip += stats.precip_probability
            if stats.tendency_sunny is not None:
                total_sunny += stats.tendency_sunny

                # 找最佳日期（晴天率最高）
                if stats.tendency_sunny > best_sunny:
                    best_sunny = stats.tendency_sunny
                    best_day = md

            if stats.precip_probability is not None:
                # 找最差日期（降雨機率最高）
                if stats.precip_probability > worst_precip:
                    worst_precip = stats.precip_probability
                    worst_day = md

            valid_count += 1

    # 計算範圍摘要
    range_summary = RangeSummary(
        avg_temp=round(total_temp / valid_count, 1) if valid_count > 0 else None,
        avg_precip_prob=round(total_precip / valid_count, 2) if valid_count > 0 else None,
        avg_sunny_rate=round(total_sunny / valid_count, 2) if valid_count > 0 else None,
        best_day=best_day,
        worst_day=worst_day
    )

    return ApiResponse(
        success=True,
        data=DateRangeResponse(
            station=station_info,
            start_date=start,
            end_date=end,
            days=days,
            summary=range_summary
        )
    )


def _calculate_recommendation_score(
    stats: DailyStatistics,
    preference: str
) -> tuple[float, str]:
    """計算推薦分數

    Args:
        stats: 統計資料
        preference: 偏好類型 (sunny, mild, cool, outdoor, wedding)

    Returns:
        (分數, 推薦理由)
    """
    score = 50.0  # 基礎分數
    reasons = []

    sunny_rate = stats.tendency_sunny or 0
    precip_prob = stats.precip_probability or 0
    temp_avg = stats.temp_avg_mean or 20

    if preference == "sunny":
        # 戶外活動：重視晴天率和低降雨機率
        score += sunny_rate * 40  # 晴天率貢獻 0-40 分
        score -= precip_prob * 30  # 降雨機率扣 0-30 分
        if sunny_rate > 0.5:
            reasons.append("晴天機率高")
        if precip_prob < 0.3:
            reasons.append("降雨機率低")

    elif preference == "mild":
        # 舒適氣溫：18-25°C 最佳
        temp_score = 30 - abs(temp_avg - 22) * 3
        score += max(0, temp_score)
        score += sunny_rate * 20
        score -= precip_prob * 20
        if 18 <= temp_avg <= 25:
            reasons.append("氣溫舒適")
        if precip_prob < 0.4:
            reasons.append("降雨機率適中")

    elif preference == "cool":
        # 涼爽：15-20°C 最佳
        temp_score = 30 - abs(temp_avg - 17) * 3
        score += max(0, temp_score)
        score -= precip_prob * 20
        if 15 <= temp_avg <= 20:
            reasons.append("氣溫涼爽宜人")

    elif preference == "outdoor":
        # 戶外活動綜合：晴天 + 適溫 + 少雨
        score += sunny_rate * 30
        score -= precip_prob * 25
        temp_score = 20 - abs(temp_avg - 22) * 2
        score += max(0, temp_score)
        if sunny_rate > 0.4 and precip_prob < 0.4:
            reasons.append("適合戶外活動")

    elif preference == "wedding":
        # 婚禮：最重視少雨 + 適溫
        score -= precip_prob * 40  # 最重視不下雨
        score += sunny_rate * 25
        temp_score = 20 - abs(temp_avg - 23) * 2
        score += max(0, temp_score)
        if precip_prob < 0.3:
            reasons.append("降雨機率低")
        if 20 <= temp_avg <= 26:
            reasons.append("氣溫適宜")

    # 確保分數在 0-100 範圍內
    score = max(0, min(100, score))

    # 生成理由
    if not reasons:
        if score >= 70:
            reasons.append("整體條件良好")
        elif score >= 50:
            reasons.append("條件尚可")
        else:
            reasons.append("條件一般")

    return round(score, 1), "、".join(reasons)


@router.get(
    "/recommend/{station_id}",
    response_model=ApiResponse[BestDatesResponse],
    summary="推薦最佳日期",
    description="根據站點和偏好推薦指定月份的最佳日期"
)
async def get_best_dates(
    station_id: str = Path(..., description="氣象站代碼", example="466920"),
    month: int = Query(..., ge=1, le=12, description="月份 (1-12)", example=3),
    preference: str = Query(
        "sunny",
        description="偏好類型: sunny(晴天), mild(溫和), cool(涼爽), outdoor(戶外), wedding(婚禮)",
        example="sunny"
    ),
    limit: int = Query(5, ge=1, le=10, description="推薦數量 (1-10)", example=5),
    db: Session = Depends(get_db)
) -> ApiResponse[BestDatesResponse]:
    """推薦最佳日期

    根據歷史天氣統計和用戶偏好，推薦指定月份的最佳日期。

    偏好類型：
    - sunny: 戶外活動，重視晴天率
    - mild: 舒適溫度 (18-25°C)
    - cool: 涼爽天氣 (15-20°C)
    - outdoor: 戶外活動綜合評估
    - wedding: 婚禮宴客，重視少雨
    """
    # 驗證偏好類型
    valid_preferences = ["sunny", "mild", "cool", "outdoor", "wedding"]
    if preference not in valid_preferences:
        raise HTTPException(
            status_code=400,
            detail=f"無效的偏好類型: {preference}，有效選項: {', '.join(valid_preferences)}"
        )

    # 驗證站點
    station_info = _get_station_info(station_id, db)

    # 產生該月所有日期
    month_str = f"{month:02d}"
    # 取得該月天數
    if month in [1, 3, 5, 7, 8, 10, 12]:
        days_in_month = 31
    elif month in [4, 6, 9, 11]:
        days_in_month = 30
    else:  # 二月
        days_in_month = 29  # 包含閏年

    month_days = [f"{month_str}-{d:02d}" for d in range(1, days_in_month + 1)]

    # 查詢該月所有統計資料
    stats_list = db.query(DailyStatistics).filter(
        DailyStatistics.station_id == station_id,
        DailyStatistics.month_day.in_(month_days)
    ).all()

    if not stats_list:
        raise HTTPException(
            status_code=404,
            detail=f"找不到 {station_info.name} 站 {month} 月的統計資料"
        )

    # 計算每日推薦分數
    scored_days = []
    for stats in stats_list:
        score, reason = _calculate_recommendation_score(stats, preference)

        # 取得農曆資訊
        lunar_info = _get_lunar_info_for_date(stats.month_day)
        lunar_date = LunarDateInfo(**lunar_info["lunar_date"]) if lunar_info else None
        jieqi = lunar_info.get("jieqi") if lunar_info else None

        scored_days.append({
            "stats": stats,
            "score": score,
            "reason": reason,
            "lunar_date": lunar_date,
            "jieqi": jieqi
        })

    # 按分數排序，取前 N 個
    scored_days.sort(key=lambda x: x["score"], reverse=True)
    top_days = scored_days[:limit]

    # 組裝推薦結果
    recommendations = [
        RecommendedDate(
            month_day=d["stats"].month_day,
            score=d["score"],
            reason=d["reason"],
            temp_avg=d["stats"].temp_avg_mean,
            precip_prob=d["stats"].precip_probability,
            sunny_rate=d["stats"].tendency_sunny,
            lunar_date=d["lunar_date"],
            jieqi=d["jieqi"]
        )
        for d in top_days
    ]

    return ApiResponse(
        success=True,
        data=BestDatesResponse(
            station=station_info,
            month=month,
            preference=preference,
            recommendations=recommendations
        )
    )
