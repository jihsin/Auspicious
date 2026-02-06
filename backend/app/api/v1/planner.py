# backend/app/api/v1/planner.py
"""智慧活動規劃 API 路由"""

from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.weather import ApiResponse
from app.services.planner import (
    ActivityType,
    plan_activity,
    get_activity_types,
    DayScore,
    PlannerResult,
)

router = APIRouter()


# ============================================
# Response Schemas
# ============================================

class ActivityTypeResponse(BaseModel):
    """活動類型"""
    type: str = Field(..., description="活動類型（中文）")
    key: str = Field(..., description="活動類型 key")
    description: str = Field(..., description="活動描述")


class DayScoreResponse(BaseModel):
    """單日評分"""
    date: str = Field(..., description="日期 (YYYY-MM-DD)")
    score: float = Field(..., description="總分 (0-100)")
    weather_score: float = Field(..., description="天氣分數")
    rain_probability: float = Field(..., description="降雨機率")
    temp_avg: float = Field(..., description="歷史平均溫度")
    sunny_ratio: float = Field(..., description="晴天比例")
    solar_term: Optional[str] = Field(None, description="節氣（若當天是）")
    lunar_date: str = Field(..., description="農曆日期")
    lunar_yi: list[str] = Field(default_factory=list, description="宜")
    lunar_ji: list[str] = Field(default_factory=list, description="忌")
    notes: list[str] = Field(default_factory=list, description="備註")


class PlannerResultResponse(BaseModel):
    """規劃結果"""
    activity_type: str = Field(..., description="活動類型")
    location: str = Field(..., description="地點")
    station_id: str = Field(..., description="站點 ID")
    station_name: str = Field(..., description="站點名稱")
    date_range: list[str] = Field(..., description="日期範圍 [start, end]")
    recommendations: list[DayScoreResponse] = Field(..., description="推薦日期列表")
    best_date: Optional[DayScoreResponse] = Field(None, description="最佳日期")
    summary: str = Field(..., description="規劃摘要")


# ============================================
# API Endpoints
# ============================================

@router.get(
    "/activity-types",
    response_model=ApiResponse[list[ActivityTypeResponse]],
    summary="取得所有活動類型",
    description="取得所有支援的活動類型及其描述"
)
async def list_activity_types():
    """取得所有活動類型"""
    types = get_activity_types()
    return ApiResponse(
        success=True,
        data=[ActivityTypeResponse(**t) for t in types]
    )


@router.get(
    "/plan",
    response_model=ApiResponse[PlannerResultResponse],
    summary="規劃活動最佳日期",
    description="根據歷史天氣、節氣、農民曆推薦最佳活動日期"
)
async def plan_activity_dates(
    activity: str = Query(..., description="活動類型（如：婚禮、野餐、登山）"),
    station_id: str = Query(..., description="氣象站 ID"),
    start_date: str = Query(..., description="開始日期 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="結束日期 (YYYY-MM-DD)"),
    top_n: int = Query(5, ge=1, le=20, description="返回前 N 個推薦日期"),
    db: Session = Depends(get_db)
):
    """規劃活動最佳日期"""
    # 解析活動類型
    activity_type = None
    for at in ActivityType:
        if at.value == activity or at.name == activity:
            activity_type = at
            break

    if not activity_type:
        # 嘗試模糊匹配
        activity_lower = activity.lower()
        for at in ActivityType:
            if activity_lower in at.value.lower() or activity_lower in at.name.lower():
                activity_type = at
                break

    if not activity_type:
        return ApiResponse(
            success=False,
            error=f"不支援的活動類型：{activity}。請使用 /activity-types 查看支援的類型。"
        )

    # 解析日期
    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
    except ValueError:
        return ApiResponse(
            success=False,
            error="日期格式錯誤，請使用 YYYY-MM-DD"
        )

    if start > end:
        return ApiResponse(
            success=False,
            error="開始日期不能晚於結束日期"
        )

    if (end - start).days > 90:
        return ApiResponse(
            success=False,
            error="日期範圍不能超過 90 天"
        )

    # 執行規劃
    result = plan_activity(
        db=db,
        activity_type=activity_type,
        station_id=station_id,
        start_date=start,
        end_date=end,
        top_n=top_n
    )

    if not result:
        return ApiResponse(
            success=False,
            error=f"找不到站點 {station_id} 或該站點沒有歷史統計資料"
        )

    # 轉換回應
    def day_score_to_response(ds: DayScore) -> DayScoreResponse:
        return DayScoreResponse(
            date=ds.date.isoformat(),
            score=ds.score,
            weather_score=ds.weather_score,
            rain_probability=ds.rain_probability,
            temp_avg=ds.temp_avg,
            sunny_ratio=ds.sunny_ratio,
            solar_term=ds.solar_term,
            lunar_date=ds.lunar_date,
            lunar_yi=ds.lunar_yi,
            lunar_ji=ds.lunar_ji,
            notes=ds.notes,
        )

    return ApiResponse(
        success=True,
        data=PlannerResultResponse(
            activity_type=result.activity_type,
            location=result.location,
            station_id=result.station_id,
            station_name=result.station_name,
            date_range=[result.date_range[0].isoformat(), result.date_range[1].isoformat()],
            recommendations=[day_score_to_response(r) for r in result.recommendations],
            best_date=day_score_to_response(result.best_date) if result.best_date else None,
            summary=result.summary,
        )
    )


@router.get(
    "/quick-plan",
    response_model=ApiResponse[PlannerResultResponse],
    summary="快速規劃（預設範圍）",
    description="快速規劃未來 30 天內的最佳日期"
)
async def quick_plan(
    activity: str = Query(..., description="活動類型"),
    station_id: str = Query("466920", description="氣象站 ID（預設臺北）"),
    db: Session = Depends(get_db)
):
    """快速規劃未來 30 天"""
    today = date.today()
    end = today + timedelta(days=30)

    # 解析活動類型
    activity_type = None
    for at in ActivityType:
        if at.value == activity or at.name == activity:
            activity_type = at
            break

    if not activity_type:
        for at in ActivityType:
            if activity.lower() in at.value.lower():
                activity_type = at
                break

    if not activity_type:
        activity_type = ActivityType.GENERAL_OUTDOOR

    result = plan_activity(
        db=db,
        activity_type=activity_type,
        station_id=station_id,
        start_date=today,
        end_date=end,
        top_n=5
    )

    if not result:
        return ApiResponse(
            success=False,
            error=f"找不到站點 {station_id} 的資料"
        )

    def day_score_to_response(ds: DayScore) -> DayScoreResponse:
        return DayScoreResponse(
            date=ds.date.isoformat(),
            score=ds.score,
            weather_score=ds.weather_score,
            rain_probability=ds.rain_probability,
            temp_avg=ds.temp_avg,
            sunny_ratio=ds.sunny_ratio,
            solar_term=ds.solar_term,
            lunar_date=ds.lunar_date,
            lunar_yi=ds.lunar_yi,
            lunar_ji=ds.lunar_ji,
            notes=ds.notes,
        )

    return ApiResponse(
        success=True,
        data=PlannerResultResponse(
            activity_type=result.activity_type,
            location=result.location,
            station_id=result.station_id,
            station_name=result.station_name,
            date_range=[result.date_range[0].isoformat(), result.date_range[1].isoformat()],
            recommendations=[day_score_to_response(r) for r in result.recommendations],
            best_date=day_score_to_response(result.best_date) if result.best_date else None,
            summary=result.summary,
        )
    )
