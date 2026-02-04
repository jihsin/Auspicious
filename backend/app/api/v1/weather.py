# backend/app/api/v1/weather.py
"""天氣查詢 API 路由"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.statistics import DailyStatistics
from app.schemas.weather import (
    ApiResponse,
    AnalysisPeriod,
    DailyWeatherResponse,
    PrecipitationResponse,
    StationInfo,
    TemperatureRecord,
    TemperatureResponse,
    TemperatureStats,
    WeatherTendencyResponse,
)

# 觀測站資訊對照表
STATION_INFO = {
    "466920": {"name": "臺北", "city": "臺北市"},
    "467490": {"name": "臺中", "city": "臺中市"},
    "467410": {"name": "臺南", "city": "臺南市"},
    "467440": {"name": "高雄", "city": "高雄市"},
    "466990": {"name": "花蓮", "city": "花蓮縣"},
    "467660": {"name": "臺東", "city": "臺東縣"},
}

router = APIRouter()


def _get_station_info(station_id: str) -> StationInfo:
    """取得站點資訊"""
    if station_id not in STATION_INFO:
        raise HTTPException(
            status_code=404,
            detail=f"找不到站點 {station_id}"
        )
    info = STATION_INFO[station_id]
    return StationInfo(
        station_id=station_id,
        name=info["name"],
        city=info["city"]
    )


def _statistics_to_response(
    stats: DailyStatistics,
    station_info: StationInfo
) -> DailyWeatherResponse:
    """將資料庫模型轉換為 API 回應"""
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
        computed_at=stats.computed_at
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
    station_info = _get_station_info(station_id)

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

    return ApiResponse(
        success=True,
        data=_statistics_to_response(stats, station_info)
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
    station_info = _get_station_info(station_id)

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

    return ApiResponse(
        success=True,
        data=_statistics_to_response(stats, station_info)
    )
