# backend/app/api/v1/stations.py
"""站點查詢 API 路由"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.station import Station
from app.schemas.weather import (
    ApiResponse,
    NearestStationResponse,
    StationInfoExtended,
)
from app.utils.geo import find_nearest_station

router = APIRouter()


@router.get(
    "/",
    response_model=ApiResponse[List[StationInfoExtended]],
    summary="列出所有氣象站",
    description="取得所有支援的氣象站列表",
)
async def list_stations(
    county: Optional[str] = Query(None, description="篩選縣市"),
    has_statistics: Optional[bool] = Query(None, description="只顯示有統計資料的站點"),
    db: Session = Depends(get_db),
) -> ApiResponse[List[StationInfoExtended]]:
    """列出所有氣象站

    Args:
        county: 篩選縣市
        has_statistics: 只顯示有統計資料的站點
        db: 資料庫 session

    Returns:
        包含所有站點資訊的列表
    """
    query = db.query(Station).filter(Station.is_active == True)

    if county:
        query = query.filter(Station.county == county)

    if has_statistics is not None:
        query = query.filter(Station.has_statistics == has_statistics)

    stations = query.all()

    return ApiResponse(
        success=True,
        data=[StationInfoExtended.model_validate(s) for s in stations],
    )


@router.get(
    "/nearest",
    response_model=ApiResponse[NearestStationResponse],
    summary="取得最近站點",
    description="根據用戶經緯度取得最近的氣象站",
)
async def get_nearest_station(
    lat: float = Query(..., description="用戶緯度", ge=-90, le=90),
    lon: float = Query(..., description="用戶經度", ge=-180, le=180),
    has_statistics: bool = Query(False, description="只搜尋有統計資料的站點"),
    db: Session = Depends(get_db),
) -> ApiResponse[NearestStationResponse]:
    """取得最近站點

    Args:
        lat: 用戶緯度
        lon: 用戶經度
        has_statistics: 只搜尋有統計資料的站點
        db: 資料庫 session

    Returns:
        最近站點資訊與距離

    Raises:
        404: 找不到可用的站點
    """
    query = db.query(Station).filter(Station.is_active == True)

    if has_statistics:
        query = query.filter(Station.has_statistics == True)

    stations = query.all()

    if not stations:
        raise HTTPException(status_code=404, detail="找不到可用的站點")

    # 轉換為字典格式供 find_nearest_station 使用
    station_dicts = [
        {
            "station_id": s.station_id,
            "name": s.name,
            "county": s.county,
            "town": s.town,
            "latitude": s.latitude,
            "longitude": s.longitude,
            "altitude": s.altitude,
            "has_statistics": s.has_statistics,
        }
        for s in stations
    ]

    result = find_nearest_station(lat, lon, station_dicts)

    return ApiResponse(
        success=True,
        data=NearestStationResponse(
            station=StationInfoExtended(**result["station"]),
            distance_km=result["distance_km"],
        ),
    )


@router.get(
    "/{station_id}",
    response_model=ApiResponse[StationInfoExtended],
    summary="取得單一站點資訊",
    description="根據站點代碼取得站點詳細資訊",
)
async def get_station(
    station_id: str,
    db: Session = Depends(get_db),
) -> ApiResponse[StationInfoExtended]:
    """取得單一站點資訊

    Args:
        station_id: 氣象站代碼
        db: 資料庫 session

    Returns:
        站點詳細資訊

    Raises:
        404: 找不到指定站點
    """
    station = db.query(Station).filter(Station.station_id == station_id).first()

    if not station:
        raise HTTPException(status_code=404, detail=f"找不到站點 {station_id}")

    return ApiResponse(
        success=True,
        data=StationInfoExtended.model_validate(station),
    )
