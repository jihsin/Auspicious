# backend/app/api/v1/stations.py
"""站點查詢 API 路由"""

from typing import List

from fastapi import APIRouter, HTTPException, Path

from app.schemas.weather import ApiResponse, StationInfo

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


@router.get(
    "/",
    response_model=ApiResponse[List[StationInfo]],
    summary="列出所有氣象站",
    description="取得所有支援的氣象站列表"
)
async def list_stations() -> ApiResponse[List[StationInfo]]:
    """列出所有氣象站

    Returns:
        包含所有站點資訊的列表
    """
    stations = [
        StationInfo(
            station_id=station_id,
            name=info["name"],
            city=info["city"]
        )
        for station_id, info in STATION_INFO.items()
    ]

    return ApiResponse(
        success=True,
        data=stations
    )


@router.get(
    "/{station_id}",
    response_model=ApiResponse[StationInfo],
    summary="取得單一站點資訊",
    description="根據站點代碼取得站點詳細資訊"
)
async def get_station(
    station_id: str = Path(..., description="氣象站代碼", example="466920")
) -> ApiResponse[StationInfo]:
    """取得單一站點資訊

    Args:
        station_id: 氣象站代碼

    Returns:
        站點詳細資訊

    Raises:
        404: 找不到指定站點
    """
    if station_id not in STATION_INFO:
        raise HTTPException(
            status_code=404,
            detail=f"找不到站點 {station_id}"
        )

    info = STATION_INFO[station_id]
    station = StationInfo(
        station_id=station_id,
        name=info["name"],
        city=info["city"]
    )

    return ApiResponse(
        success=True,
        data=station
    )
