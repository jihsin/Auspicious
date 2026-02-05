# backend/app/api/v1/solar_term.py
"""節氣 API 路由"""

from datetime import datetime, date
from typing import Optional

from fastapi import APIRouter, Path
from pydantic import BaseModel, Field

from app.services.solar_term import (
    get_solar_term_info,
    get_all_solar_terms,
    get_current_solar_term,
    get_nearest_solar_term,
    get_solar_terms_by_season,
    SolarTermInfo,
)
from app.schemas.weather import ApiResponse

router = APIRouter()


# ============================================
# Response Schemas
# ============================================

class SolarTermResponse(BaseModel):
    """節氣回應"""
    name: str = Field(..., description="節氣名稱")
    name_en: str = Field(..., description="英文名稱")
    order: int = Field(..., description="序號 (1-24)")
    solar_longitude: int = Field(..., description="太陽黃經度數")
    typical_date: str = Field(..., description="典型日期 (MM-DD)")
    season: str = Field(..., description="所屬季節")
    is_major: bool = Field(..., description="是否為中氣")
    astronomy: str = Field(..., description="天文意義")
    agriculture: str = Field(..., description="農業意義")
    weather: str = Field(..., description="氣象特徵（臺灣）")
    phenology: list[str] = Field(..., description="物候（三候）")
    proverbs: list[str] = Field(..., description="相關諺語")
    health_tips: str = Field(..., description="養生建議")


class NearestSolarTermResponse(BaseModel):
    """最近節氣回應"""
    current: Optional[SolarTermResponse] = Field(None, description="當前所處的節氣")
    next: Optional[SolarTermResponse] = Field(None, description="下一個節氣")
    days_to_next: Optional[int] = Field(None, description="距離下一個節氣的天數")
    today_is_solar_term: bool = Field(..., description="今天是否為節氣")
    today_term_name: Optional[str] = Field(None, description="今天的節氣名稱（如果是）")


def _convert_to_response(info: SolarTermInfo) -> SolarTermResponse:
    """將 SolarTermInfo 轉換為回應格式"""
    return SolarTermResponse(
        name=info.name,
        name_en=info.name_en,
        order=info.order,
        solar_longitude=info.solar_longitude,
        typical_date=info.typical_date,
        season=info.season,
        is_major=info.is_major,
        astronomy=info.astronomy,
        agriculture=info.agriculture,
        weather=info.weather,
        phenology=info.phenology,
        proverbs=info.proverbs,
        health_tips=info.health_tips,
    )


# ============================================
# API Endpoints
# ============================================

@router.get(
    "/all",
    response_model=ApiResponse[list[SolarTermResponse]],
    summary="取得所有節氣資訊",
    description="取得二十四節氣的完整資訊列表"
)
async def get_all_terms():
    """取得所有節氣資訊"""
    terms = get_all_solar_terms()
    return ApiResponse(
        success=True,
        data=[_convert_to_response(t) for t in terms]
    )


@router.get(
    "/current",
    response_model=ApiResponse[NearestSolarTermResponse],
    summary="取得當前節氣資訊",
    description="取得今日所處的節氣、下一個節氣，以及距離天數"
)
async def get_current_term():
    """取得當前節氣資訊"""
    today = date.today()

    # 檢查今天是否為節氣
    today_term = get_current_solar_term(today)

    # 取得最近的節氣資訊
    nearest = get_nearest_solar_term(today)

    return ApiResponse(
        success=True,
        data=NearestSolarTermResponse(
            current=_convert_to_response(nearest["current"]) if nearest["current"] else None,
            next=_convert_to_response(nearest["next"]) if nearest["next"] else None,
            days_to_next=nearest["days_to_next"],
            today_is_solar_term=today_term is not None,
            today_term_name=today_term,
        )
    )


@router.get(
    "/by-name/{name}",
    response_model=ApiResponse[SolarTermResponse],
    summary="依名稱查詢節氣",
    description="取得指定節氣的完整資訊"
)
async def get_term_by_name(name: str):
    """依名稱查詢節氣

    Args:
        name: 節氣名稱（如：立春、雨水）
    """
    info = get_solar_term_info(name)
    if not info:
        return ApiResponse(
            success=False,
            error=f"找不到節氣：{name}"
        )

    return ApiResponse(
        success=True,
        data=_convert_to_response(info)
    )


@router.get(
    "/by-season/{season}",
    response_model=ApiResponse[list[SolarTermResponse]],
    summary="依季節查詢節氣",
    description="取得指定季節的所有節氣"
)
async def get_terms_by_season(
    season: str = Path(..., description="季節 (春/夏/秋/冬)", example="春")
):
    """依季節查詢節氣

    Args:
        season: 季節名稱（春/夏/秋/冬）
    """
    valid_seasons = ["春", "夏", "秋", "冬"]
    if season not in valid_seasons:
        return ApiResponse(
            success=False,
            error=f"無效的季節：{season}，有效選項：{', '.join(valid_seasons)}"
        )

    terms = get_solar_terms_by_season(season)
    return ApiResponse(
        success=True,
        data=[_convert_to_response(t) for t in terms]
    )


@router.get(
    "/proverbs",
    response_model=ApiResponse[list[dict]],
    summary="取得所有節氣諺語",
    description="取得二十四節氣的相關諺語列表"
)
async def get_all_proverbs():
    """取得所有節氣諺語"""
    terms = get_all_solar_terms()
    proverbs = []

    for term in terms:
        for proverb in term.proverbs:
            proverbs.append({
                "solar_term": term.name,
                "season": term.season,
                "proverb": proverb,
            })

    return ApiResponse(
        success=True,
        data=proverbs
    )
