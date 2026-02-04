# backend/app/api/v1/lunar.py
"""農曆 API 路由"""

from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Query, HTTPException

from app.schemas.weather import ApiResponse
from app.schemas.lunar import LunarResponse, LunarDateInfo, YiJiInfo, GanzhiInfo
from app.services.lunar import get_lunar_info

router = APIRouter()


@router.get(
    "/",
    response_model=ApiResponse[LunarResponse],
    summary="取得農曆資訊",
    description="根據公曆日期取得農曆資訊，包含宜忌、節氣、干支等"
)
async def get_lunar(
    date_str: Optional[str] = Query(
        None,
        alias="date",
        description="公曆日期 (YYYY-MM-DD 格式)，預設為今天",
        example="2026-02-04"
    )
) -> ApiResponse[LunarResponse]:
    """取得農曆資訊

    Args:
        date_str: 公曆日期 (YYYY-MM-DD)

    Returns:
        農曆資訊
    """
    # 解析日期，預設為今天
    if date_str:
        try:
            query_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"日期格式錯誤，請使用 YYYY-MM-DD 格式: {date_str}"
            )
    else:
        query_date = date.today()

    # 取得農曆資訊
    try:
        info = get_lunar_info(query_date)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"取得農曆資訊失敗: {str(e)}"
        )

    return ApiResponse(
        success=True,
        data=LunarResponse(
            date=query_date.isoformat(),
            lunar_date=LunarDateInfo(**info["lunar_date"]),
            yi_ji=YiJiInfo(**info["yi_ji"]),
            jieqi=info["jieqi"],
            ganzhi=GanzhiInfo(**info["ganzhi"]),
        )
    )
