# Phase 2: GPS 定位 + 835 觀測站擴展 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 擴展觀測站至全台 835 站，並透過 GPS 定位自動選擇最近的觀測站

**Architecture:**
- 後端從氣象資料開放平台 API 同步站點資料（含經緯度）存入資料庫
- 新增 `/stations/nearest` API 根據用戶經緯度計算最近站點（Haversine 公式）
- 前端使用 `navigator.geolocation` 取得用戶位置，自動選擇最近站點，並提供手動切換功能

**Tech Stack:**
- Backend: FastAPI, SQLAlchemy, httpx (async HTTP client)
- Frontend: Next.js 14, TypeScript, Geolocation API
- Data: CWA OpenData API (Authorization: `CWA-6B37748B-1E62-48B8-B173-23161C608A79`)

---

## Sprint 1: 後端站點資料模型與同步

### Task 1.1: 建立站點資料模型

**Files:**
- Create: `backend/app/models/station.py`
- Modify: `backend/app/models/__init__.py`

**Step 1: 建立站點資料模型**

```python
# backend/app/models/station.py
"""氣象站點資料模型"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.sql import func

from app.models import Base


class Station(Base):
    """氣象站點資料表

    儲存全台 835 個觀測站的基本資訊與經緯度
    """

    __tablename__ = "stations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    station_id = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(50), nullable=False)

    # 地理資訊
    county = Column(String(20), nullable=True)  # 縣市
    town = Column(String(20), nullable=True)    # 鄉鎮市區
    latitude = Column(Float, nullable=False)     # 緯度
    longitude = Column(Float, nullable=False)    # 經度
    altitude = Column(Float, nullable=True)      # 海拔高度 (公尺)

    # 狀態
    is_active = Column(Boolean, default=True)    # 是否啟用
    has_statistics = Column(Boolean, default=False)  # 是否有歷史統計資料

    # 元數據
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Station {self.station_id}: {self.name}>"
```

**Step 2: 更新 models/__init__.py**

```python
# backend/app/models/__init__.py
"""資料模型模組"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy 基底類別"""
    pass


# 匯出所有模型
from app.models.observation import RawObservation
from app.models.statistics import DailyStatistics
from app.models.station import Station

__all__ = ["Base", "RawObservation", "DailyStatistics", "Station"]
```

**Step 3: Commit**

```bash
git add backend/app/models/station.py backend/app/models/__init__.py
git commit -m "feat(models): add Station model with coordinates"
```

---

### Task 1.2: 建立 CWA API 同步服務

**Files:**
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/cwa_sync.py`
- Test: `backend/tests/test_cwa_sync.py`

**Step 1: 建立服務目錄**

```python
# backend/app/services/__init__.py
"""服務模組"""

from app.services.cwa_sync import CWASyncService

__all__ = ["CWASyncService"]
```

**Step 2: 建立測試檔案**

```python
# backend/tests/test_cwa_sync.py
"""CWA API 同步服務測試"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.cwa_sync import CWASyncService, parse_station_data


def test_parse_station_data():
    """測試解析站點資料"""
    raw_data = {
        "StationId": "C0TB40",
        "StationName": "崇德",
        "GeoInfo": {
            "CountyName": "花蓮縣",
            "TownName": "秀林鄉",
            "Coordinates": [
                {
                    "StationLatitude": 24.167948,
                    "StationLongitude": 121.649251
                }
            ],
            "StationAltitude": 26.0
        }
    }

    result = parse_station_data(raw_data)

    assert result["station_id"] == "C0TB40"
    assert result["name"] == "崇德"
    assert result["county"] == "花蓮縣"
    assert result["town"] == "秀林鄉"
    assert result["latitude"] == 24.167948
    assert result["longitude"] == 121.649251
    assert result["altitude"] == 26.0


def test_parse_station_data_missing_coords():
    """測試缺少座標的情況"""
    raw_data = {
        "StationId": "TEST01",
        "StationName": "測試站",
        "GeoInfo": {
            "CountyName": "測試縣",
            "Coordinates": []
        }
    }

    result = parse_station_data(raw_data)

    assert result is None  # 缺少座標應該返回 None
```

**Step 3: 執行測試確認失敗**

```bash
cd backend && poetry run pytest tests/test_cwa_sync.py -v
# Expected: FAILED - No module named 'app.services.cwa_sync'
```

**Step 4: 實作 CWA 同步服務**

```python
# backend/app/services/cwa_sync.py
"""中央氣象署 API 同步服務"""

import httpx
from typing import Optional
from sqlalchemy.orm import Session

from app.models.station import Station


# CWA API 設定
CWA_API_BASE = "https://opendata.cwa.gov.tw/api/v1/rest/datastore"
CWA_AUTH_KEY = "CWA-6B37748B-1E62-48B8-B173-23161C608A79"
STATION_ENDPOINT = "O-A0001-001"


def parse_station_data(raw: dict) -> Optional[dict]:
    """解析 CWA API 返回的站點資料

    Args:
        raw: CWA API 返回的原始站點資料

    Returns:
        解析後的站點資料字典，如果缺少必要欄位則返回 None
    """
    geo = raw.get("GeoInfo", {})
    coords = geo.get("Coordinates", [])

    if not coords:
        return None

    coord = coords[0]
    lat = coord.get("StationLatitude")
    lon = coord.get("StationLongitude")

    if lat is None or lon is None:
        return None

    return {
        "station_id": raw.get("StationId"),
        "name": raw.get("StationName"),
        "county": geo.get("CountyName"),
        "town": geo.get("TownName"),
        "latitude": lat,
        "longitude": lon,
        "altitude": geo.get("StationAltitude"),
    }


class CWASyncService:
    """CWA 資料同步服務"""

    def __init__(self, db: Session):
        self.db = db

    async def fetch_all_stations(self) -> list[dict]:
        """從 CWA API 取得所有站點資料

        Returns:
            站點資料列表
        """
        url = f"{CWA_API_BASE}/{STATION_ENDPOINT}"
        params = {"Authorization": CWA_AUTH_KEY}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        stations = data.get("records", {}).get("Station", [])

        # 解析並過濾有效站點
        parsed = []
        for raw in stations:
            station_data = parse_station_data(raw)
            if station_data:
                parsed.append(station_data)

        return parsed

    async def sync_stations(self) -> dict:
        """同步所有站點資料到資料庫

        Returns:
            同步結果統計
        """
        stations_data = await self.fetch_all_stations()

        created = 0
        updated = 0

        for data in stations_data:
            existing = self.db.query(Station).filter(
                Station.station_id == data["station_id"]
            ).first()

            if existing:
                # 更新現有站點
                for key, value in data.items():
                    setattr(existing, key, value)
                updated += 1
            else:
                # 新增站點
                station = Station(**data)
                self.db.add(station)
                created += 1

        self.db.commit()

        return {
            "total_fetched": len(stations_data),
            "created": created,
            "updated": updated,
        }
```

**Step 5: 執行測試確認通過**

```bash
cd backend && poetry run pytest tests/test_cwa_sync.py -v
# Expected: 2 passed
```

**Step 6: 加入 httpx 依賴**

```bash
cd backend && poetry add httpx
```

**Step 7: Commit**

```bash
git add backend/app/services/ backend/tests/test_cwa_sync.py backend/pyproject.toml backend/poetry.lock
git commit -m "feat(services): add CWA API sync service"
```

---

### Task 1.3: 建立站點同步 CLI 指令

**Files:**
- Create: `backend/app/cli.py`

**Step 1: 建立 CLI 指令**

```python
# backend/app/cli.py
"""CLI 命令列工具"""

import asyncio
import click
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import Base
from app.services.cwa_sync import CWASyncService


@click.group()
def cli():
    """好日子 CLI 工具"""
    pass


@cli.command()
def sync_stations():
    """從 CWA API 同步站點資料"""
    click.echo("正在同步站點資料...")

    engine = create_engine(settings.database_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    with Session() as db:
        service = CWASyncService(db)
        result = asyncio.run(service.sync_stations())

    click.echo(f"同步完成！")
    click.echo(f"  取得站點數: {result['total_fetched']}")
    click.echo(f"  新增站點數: {result['created']}")
    click.echo(f"  更新站點數: {result['updated']}")


@cli.command()
def init_db():
    """初始化資料庫表"""
    click.echo("正在初始化資料庫...")

    engine = create_engine(settings.database_url)
    Base.metadata.create_all(engine)

    click.echo("資料庫初始化完成！")


if __name__ == "__main__":
    cli()
```

**Step 2: 加入 click 依賴**

```bash
cd backend && poetry add click
```

**Step 3: 執行同步**

```bash
cd backend && poetry run python -m app.cli sync-stations
# Expected: 同步完成！取得站點數: ~835
```

**Step 4: Commit**

```bash
git add backend/app/cli.py backend/pyproject.toml backend/poetry.lock
git commit -m "feat(cli): add station sync command"
```

---

## Sprint 2: 最近站點 API

### Task 2.1: 建立距離計算工具（TDD）

**Files:**
- Create: `backend/app/utils/__init__.py`
- Create: `backend/app/utils/geo.py`
- Test: `backend/tests/test_geo.py`

**Step 1: 建立測試檔案**

```python
# backend/tests/test_geo.py
"""地理計算工具測試"""

import pytest
from app.utils.geo import haversine_distance, find_nearest_station


def test_haversine_distance_same_point():
    """測試同一點距離為 0"""
    dist = haversine_distance(25.0, 121.5, 25.0, 121.5)
    assert dist == 0.0


def test_haversine_distance_taipei_to_kaohsiung():
    """測試台北到高雄約 350 公里"""
    # 台北: 25.0330, 121.5654
    # 高雄: 22.6273, 120.3014
    dist = haversine_distance(25.0330, 121.5654, 22.6273, 120.3014)

    # 約 350 公里，允許 10% 誤差
    assert 300 < dist < 400


def test_haversine_distance_short():
    """測試短距離（約 1 公里）"""
    # 台北車站: 25.0478, 121.5170
    # 台北 101: 25.0339, 121.5645
    dist = haversine_distance(25.0478, 121.5170, 25.0339, 121.5645)

    # 約 5 公里
    assert 4 < dist < 6


def test_find_nearest_station():
    """測試找最近站點"""
    stations = [
        {"station_id": "A", "name": "站A", "latitude": 25.0, "longitude": 121.5},
        {"station_id": "B", "name": "站B", "latitude": 25.1, "longitude": 121.6},
        {"station_id": "C", "name": "站C", "latitude": 24.0, "longitude": 120.0},
    ]

    # 用戶位置接近站 A
    result = find_nearest_station(25.01, 121.51, stations)

    assert result["station"]["station_id"] == "A"
    assert result["distance_km"] < 5


def test_find_nearest_station_empty_list():
    """測試空站點列表"""
    result = find_nearest_station(25.0, 121.5, [])
    assert result is None
```

**Step 2: 執行測試確認失敗**

```bash
cd backend && poetry run pytest tests/test_geo.py -v
# Expected: FAILED - No module named 'app.utils.geo'
```

**Step 3: 實作地理計算工具**

```python
# backend/app/utils/__init__.py
"""工具模組"""

from app.utils.geo import haversine_distance, find_nearest_station

__all__ = ["haversine_distance", "find_nearest_station"]
```

```python
# backend/app/utils/geo.py
"""地理計算工具

使用 Haversine 公式計算兩點間的球面距離
"""

import math
from typing import Optional


# 地球半徑（公里）
EARTH_RADIUS_KM = 6371.0


def haversine_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float
) -> float:
    """計算兩個經緯度座標間的距離（公里）

    使用 Haversine 公式計算球面距離

    Args:
        lat1: 第一點緯度
        lon1: 第一點經度
        lat2: 第二點緯度
        lon2: 第二點經度

    Returns:
        兩點間的距離（公里）
    """
    # 轉換為弧度
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    # Haversine 公式
    a = (
        math.sin(delta_lat / 2) ** 2 +
        math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return EARTH_RADIUS_KM * c


def find_nearest_station(
    user_lat: float,
    user_lon: float,
    stations: list[dict]
) -> Optional[dict]:
    """找出離用戶最近的站點

    Args:
        user_lat: 用戶緯度
        user_lon: 用戶經度
        stations: 站點列表，每個站點需包含 latitude, longitude

    Returns:
        最近站點資訊與距離，格式: {"station": {...}, "distance_km": float}
        如果沒有站點則返回 None
    """
    if not stations:
        return None

    nearest = None
    min_distance = float("inf")

    for station in stations:
        dist = haversine_distance(
            user_lat,
            user_lon,
            station["latitude"],
            station["longitude"]
        )

        if dist < min_distance:
            min_distance = dist
            nearest = station

    return {
        "station": nearest,
        "distance_km": round(min_distance, 2)
    }
```

**Step 4: 執行測試確認通過**

```bash
cd backend && poetry run pytest tests/test_geo.py -v
# Expected: 5 passed
```

**Step 5: Commit**

```bash
git add backend/app/utils/ backend/tests/test_geo.py
git commit -m "feat(utils): add Haversine distance calculation"
```

---

### Task 2.2: 更新站點 API（新增最近站點端點）

**Files:**
- Modify: `backend/app/schemas/weather.py`
- Modify: `backend/app/api/v1/stations.py`
- Test: `backend/tests/test_api_stations.py`

**Step 1: 更新 Schema**

在 `backend/app/schemas/weather.py` 中新增：

```python
# 在 StationInfo 類別後新增

class StationInfoExtended(BaseModel):
    """站點詳細資訊（含座標）"""
    station_id: str
    name: str
    county: Optional[str] = None
    town: Optional[str] = None
    latitude: float
    longitude: float
    altitude: Optional[float] = None
    has_statistics: bool = False

    model_config = ConfigDict(from_attributes=True)


class NearestStationResponse(BaseModel):
    """最近站點回應"""
    station: StationInfoExtended
    distance_km: float
```

**Step 2: 建立測試檔案**

```python
# backend/tests/test_api_stations.py
"""站點 API 測試"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models import Base, Station
from app.database import get_db


# 測試用資料庫
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_stations.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """每次測試前重建資料庫"""
    Base.metadata.create_all(bind=engine)

    # 新增測試站點
    db = TestingSessionLocal()
    stations = [
        Station(station_id="466920", name="臺北", county="臺北市", town="中正區",
                latitude=25.0375, longitude=121.5148, has_statistics=True),
        Station(station_id="467490", name="臺中", county="臺中市", town="西屯區",
                latitude=24.1477, longitude=120.6844, has_statistics=True),
        Station(station_id="C0A520", name="士林", county="臺北市", town="士林區",
                latitude=25.0958, longitude=121.5247, has_statistics=False),
    ]
    db.add_all(stations)
    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=engine)


def test_list_stations():
    """測試列出所有站點"""
    response = client.get("/api/v1/stations/")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) == 3


def test_get_nearest_station():
    """測試取得最近站點"""
    # 用戶位置在台北市中心
    response = client.get("/api/v1/stations/nearest?lat=25.0330&lon=121.5654")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["data"]["station"]["station_id"] == "466920"  # 應該是台北站
    assert data["data"]["distance_km"] < 10


def test_get_nearest_station_missing_params():
    """測試缺少參數"""
    response = client.get("/api/v1/stations/nearest")
    assert response.status_code == 422  # Validation error
```

**Step 3: 更新站點 API**

```python
# backend/app/api/v1/stations.py
"""站點查詢 API 路由"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.station import Station
from app.schemas.weather import (
    ApiResponse,
    StationInfo,
    StationInfoExtended,
    NearestStationResponse,
)
from app.utils.geo import find_nearest_station

router = APIRouter()


@router.get(
    "/",
    response_model=ApiResponse[List[StationInfoExtended]],
    summary="列出所有氣象站",
    description="取得所有支援的氣象站列表"
)
async def list_stations(
    county: Optional[str] = Query(None, description="篩選縣市"),
    has_statistics: Optional[bool] = Query(None, description="只顯示有統計資料的站點"),
    db: Session = Depends(get_db)
) -> ApiResponse[List[StationInfoExtended]]:
    """列出所有氣象站"""
    query = db.query(Station).filter(Station.is_active == True)

    if county:
        query = query.filter(Station.county == county)

    if has_statistics is not None:
        query = query.filter(Station.has_statistics == has_statistics)

    stations = query.all()

    return ApiResponse(
        success=True,
        data=[StationInfoExtended.model_validate(s) for s in stations]
    )


@router.get(
    "/nearest",
    response_model=ApiResponse[NearestStationResponse],
    summary="取得最近站點",
    description="根據用戶經緯度取得最近的氣象站"
)
async def get_nearest_station(
    lat: float = Query(..., description="用戶緯度", ge=-90, le=90),
    lon: float = Query(..., description="用戶經度", ge=-180, le=180),
    has_statistics: bool = Query(False, description="只搜尋有統計資料的站點"),
    db: Session = Depends(get_db)
) -> ApiResponse[NearestStationResponse]:
    """取得最近站點"""
    query = db.query(Station).filter(Station.is_active == True)

    if has_statistics:
        query = query.filter(Station.has_statistics == True)

    stations = query.all()

    if not stations:
        raise HTTPException(status_code=404, detail="找不到可用的站點")

    # 轉換為字典格式
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
            distance_km=result["distance_km"]
        )
    )


@router.get(
    "/{station_id}",
    response_model=ApiResponse[StationInfoExtended],
    summary="取得單一站點資訊",
    description="根據站點代碼取得站點詳細資訊"
)
async def get_station(
    station_id: str,
    db: Session = Depends(get_db)
) -> ApiResponse[StationInfoExtended]:
    """取得單一站點資訊"""
    station = db.query(Station).filter(Station.station_id == station_id).first()

    if not station:
        raise HTTPException(status_code=404, detail=f"找不到站點 {station_id}")

    return ApiResponse(
        success=True,
        data=StationInfoExtended.model_validate(station)
    )
```

**Step 4: 執行測試**

```bash
cd backend && poetry run pytest tests/test_api_stations.py -v
# Expected: 3 passed
```

**Step 5: Commit**

```bash
git add backend/app/api/v1/stations.py backend/app/schemas/weather.py backend/tests/test_api_stations.py
git commit -m "feat(api): add nearest station endpoint with GPS support"
```

---

## Sprint 3: 前端 GPS 定位與站點選擇

### Task 3.1: 更新前端型別定義

**Files:**
- Modify: `frontend/src/lib/types.ts`

**Step 1: 更新型別定義**

在 `frontend/src/lib/types.ts` 中新增：

```typescript
// ============================================
// 站點相關型別（擴展）
// ============================================

export interface StationInfoExtended {
  station_id: string;
  name: string;
  county: string | null;
  town: string | null;
  latitude: number;
  longitude: number;
  altitude: number | null;
  has_statistics: boolean;
}

export interface NearestStationResponse {
  station: StationInfoExtended;
  distance_km: number;
}

// ============================================
// GPS 定位相關型別
// ============================================

export interface GeoLocation {
  latitude: number;
  longitude: number;
  accuracy: number;
}

export type LocationStatus = "idle" | "loading" | "success" | "error" | "denied";
```

**Step 2: Commit**

```bash
git add frontend/src/lib/types.ts
git commit -m "feat(types): add GPS and extended station types"
```

---

### Task 3.2: 更新前端 API 客戶端

**Files:**
- Modify: `frontend/src/lib/api.ts`

**Step 1: 更新 API 客戶端**

在 `frontend/src/lib/api.ts` 中新增：

```typescript
import {
  ApiResponse,
  DailyWeatherData,
  StationInfoExtended,
  NearestStationResponse,
} from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ... 保留現有函式 ...

/**
 * 取得所有站點
 */
export async function fetchStations(options?: {
  county?: string;
  hasStatistics?: boolean;
}): Promise<StationInfoExtended[]> {
  const params = new URLSearchParams();
  if (options?.county) params.set("county", options.county);
  if (options?.hasStatistics !== undefined) {
    params.set("has_statistics", String(options.hasStatistics));
  }

  const url = `${API_BASE_URL}/api/v1/stations/${params.toString() ? "?" + params.toString() : ""}`;
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  const result: ApiResponse<StationInfoExtended[]> = await response.json();

  if (!result.success || !result.data) {
    throw new Error(result.error || "Unknown error");
  }

  return result.data;
}

/**
 * 取得最近站點
 */
export async function fetchNearestStation(
  latitude: number,
  longitude: number,
  hasStatistics: boolean = true
): Promise<NearestStationResponse> {
  const params = new URLSearchParams({
    lat: String(latitude),
    lon: String(longitude),
    has_statistics: String(hasStatistics),
  });

  const response = await fetch(
    `${API_BASE_URL}/api/v1/stations/nearest?${params.toString()}`
  );

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  const result: ApiResponse<NearestStationResponse> = await response.json();

  if (!result.success || !result.data) {
    throw new Error(result.error || "Unknown error");
  }

  return result.data;
}
```

**Step 2: Commit**

```bash
git add frontend/src/lib/api.ts
git commit -m "feat(api): add station list and nearest station API"
```

---

### Task 3.3: 建立 GPS 定位 Hook

**Files:**
- Create: `frontend/src/hooks/useGeolocation.ts`

**Step 1: 建立 Hook**

```typescript
// frontend/src/hooks/useGeolocation.ts
"use client";

import { useState, useCallback, useEffect } from "react";
import { GeoLocation, LocationStatus } from "@/lib/types";

interface UseGeolocationOptions {
  enableHighAccuracy?: boolean;
  timeout?: number;
  maximumAge?: number;
}

interface UseGeolocationReturn {
  location: GeoLocation | null;
  status: LocationStatus;
  error: string | null;
  requestLocation: () => void;
}

const defaultOptions: UseGeolocationOptions = {
  enableHighAccuracy: true,
  timeout: 10000,
  maximumAge: 60000, // 1 分鐘快取
};

export function useGeolocation(
  options: UseGeolocationOptions = {}
): UseGeolocationReturn {
  const [location, setLocation] = useState<GeoLocation | null>(null);
  const [status, setStatus] = useState<LocationStatus>("idle");
  const [error, setError] = useState<string | null>(null);

  const mergedOptions = { ...defaultOptions, ...options };

  const requestLocation = useCallback(() => {
    if (!navigator.geolocation) {
      setStatus("error");
      setError("您的瀏覽器不支援定位功能");
      return;
    }

    setStatus("loading");
    setError(null);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocation({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy,
        });
        setStatus("success");
      },
      (err) => {
        switch (err.code) {
          case err.PERMISSION_DENIED:
            setStatus("denied");
            setError("您拒絕了定位權限請求");
            break;
          case err.POSITION_UNAVAILABLE:
            setStatus("error");
            setError("無法取得您的位置");
            break;
          case err.TIMEOUT:
            setStatus("error");
            setError("定位請求逾時");
            break;
          default:
            setStatus("error");
            setError("定位時發生未知錯誤");
        }
      },
      mergedOptions
    );
  }, [mergedOptions.enableHighAccuracy, mergedOptions.timeout, mergedOptions.maximumAge]);

  return { location, status, error, requestLocation };
}
```

**Step 2: Commit**

```bash
git add frontend/src/hooks/useGeolocation.ts
git commit -m "feat(hooks): add useGeolocation hook for GPS"
```

---

### Task 3.4: 建立站點選擇器組件

**Files:**
- Create: `frontend/src/components/StationSelector.tsx`

**Step 1: 建立組件**

```tsx
// frontend/src/components/StationSelector.tsx
"use client";

import { useState, useEffect } from "react";
import { StationInfoExtended, NearestStationResponse } from "@/lib/types";
import { fetchStations, fetchNearestStation } from "@/lib/api";
import { useGeolocation } from "@/hooks/useGeolocation";

interface StationSelectorProps {
  currentStation: StationInfoExtended | null;
  onStationChange: (station: StationInfoExtended, distance?: number) => void;
}

export function StationSelector({
  currentStation,
  onStationChange,
}: StationSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [stations, setStations] = useState<StationInfoExtended[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);

  const { location, status, error, requestLocation } = useGeolocation();

  // 載入站點列表
  useEffect(() => {
    if (isOpen && stations.length === 0) {
      setLoading(true);
      fetchStations({ hasStatistics: true })
        .then(setStations)
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [isOpen, stations.length]);

  // GPS 定位成功後取得最近站點
  useEffect(() => {
    if (location && status === "success") {
      fetchNearestStation(location.latitude, location.longitude, true)
        .then((result) => {
          onStationChange(result.station, result.distance_km);
          setIsOpen(false);
        })
        .catch(console.error);
    }
  }, [location, status, onStationChange]);

  // 過濾站點
  const filteredStations = stations.filter(
    (s) =>
      s.name.includes(searchQuery) ||
      s.county?.includes(searchQuery) ||
      s.town?.includes(searchQuery)
  );

  return (
    <div className="relative">
      {/* 當前站點顯示 */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-4 py-2 bg-white rounded-lg shadow hover:shadow-md transition-shadow"
      >
        <span className="text-lg font-semibold">
          {currentStation?.name || "選擇站點"}
        </span>
        {currentStation?.county && (
          <span className="text-sm text-gray-500">{currentStation.county}</span>
        )}
        <svg
          className={`w-4 h-4 transition-transform ${isOpen ? "rotate-180" : ""}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* 下拉選單 */}
      {isOpen && (
        <div className="absolute top-full left-0 mt-2 w-80 bg-white rounded-lg shadow-lg z-50 max-h-96 overflow-hidden">
          {/* GPS 定位按鈕 */}
          <div className="p-3 border-b">
            <button
              onClick={requestLocation}
              disabled={status === "loading"}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
            >
              {status === "loading" ? (
                <>
                  <span className="animate-spin">⏳</span>
                  定位中...
                </>
              ) : (
                <>
                  <span>📍</span>
                  使用 GPS 定位
                </>
              )}
            </button>
            {error && <p className="mt-2 text-sm text-red-500">{error}</p>}
          </div>

          {/* 搜尋框 */}
          <div className="p-3 border-b">
            <input
              type="text"
              placeholder="搜尋站點名稱或地區..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* 站點列表 */}
          <div className="max-h-60 overflow-y-auto">
            {loading ? (
              <div className="p-4 text-center text-gray-500">載入中...</div>
            ) : filteredStations.length === 0 ? (
              <div className="p-4 text-center text-gray-500">找不到符合的站點</div>
            ) : (
              filteredStations.map((station) => (
                <button
                  key={station.station_id}
                  onClick={() => {
                    onStationChange(station);
                    setIsOpen(false);
                    setSearchQuery("");
                  }}
                  className={`w-full px-4 py-3 text-left hover:bg-gray-50 border-b last:border-b-0 ${
                    currentStation?.station_id === station.station_id
                      ? "bg-blue-50"
                      : ""
                  }`}
                >
                  <div className="font-medium">{station.name}</div>
                  <div className="text-sm text-gray-500">
                    {station.county} {station.town}
                  </div>
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
```

**Step 2: 更新組件 index**

```typescript
// frontend/src/components/index.ts
export { WeatherCard } from "./WeatherCard";
export { StationSelector } from "./StationSelector";
```

**Step 3: Commit**

```bash
git add frontend/src/components/StationSelector.tsx frontend/src/components/index.ts
git commit -m "feat(components): add StationSelector with GPS support"
```

---

### Task 3.5: 更新首頁整合 GPS 定位

**Files:**
- Modify: `frontend/src/app/page.tsx`

**Step 1: 更新首頁**

```tsx
// frontend/src/app/page.tsx
"use client";

import { useEffect, useState, useCallback } from "react";
import { fetchDailyWeather, fetchNearestStation } from "@/lib/api";
import { DailyWeatherData, StationInfoExtended } from "@/lib/types";
import { WeatherCard, StationSelector } from "@/components";
import { useGeolocation } from "@/hooks/useGeolocation";

export default function Home() {
  const [data, setData] = useState<DailyWeatherData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentStation, setCurrentStation] = useState<StationInfoExtended | null>(null);
  const [distance, setDistance] = useState<number | null>(null);

  const { location, status: geoStatus, requestLocation } = useGeolocation();

  // 載入天氣資料
  const loadWeatherData = useCallback(async (stationId: string) => {
    setLoading(true);
    setError(null);

    try {
      // 取得今日日期 (MM-DD 格式)
      const today = new Date();
      const monthDay = `${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;

      const result = await fetchDailyWeather(stationId, monthDay);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "載入失敗");
    } finally {
      setLoading(false);
    }
  }, []);

  // 處理站點變更
  const handleStationChange = useCallback((station: StationInfoExtended, dist?: number) => {
    setCurrentStation(station);
    setDistance(dist ?? null);
    loadWeatherData(station.station_id);
  }, [loadWeatherData]);

  // 初始載入：嘗試 GPS 定位
  useEffect(() => {
    requestLocation();
  }, []);

  // GPS 定位成功後取得最近站點
  useEffect(() => {
    if (location && geoStatus === "success" && !currentStation) {
      fetchNearestStation(location.latitude, location.longitude, true)
        .then((result) => {
          handleStationChange(result.station, result.distance_km);
        })
        .catch(() => {
          // GPS 定位失敗，使用預設站點（台北）
          handleStationChange({
            station_id: "466920",
            name: "臺北",
            county: "臺北市",
            town: "中正區",
            latitude: 25.0375,
            longitude: 121.5148,
            altitude: 6.3,
            has_statistics: true,
          });
        });
    }
  }, [location, geoStatus, currentStation, handleStationChange]);

  // GPS 定位被拒絕或失敗，使用預設站點
  useEffect(() => {
    if ((geoStatus === "denied" || geoStatus === "error") && !currentStation) {
      handleStationChange({
        station_id: "466920",
        name: "臺北",
        county: "臺北市",
        town: "中正區",
        latitude: 25.0375,
        longitude: 121.5148,
        altitude: 6.3,
        has_statistics: true,
      });
    }
  }, [geoStatus, currentStation, handleStationChange]);

  return (
    <main className="min-h-screen bg-gradient-to-b from-blue-100 to-white p-4 md:p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <header className="text-center mb-6">
          <h1 className="text-3xl md:text-4xl font-bold text-gray-800 mb-2">
            好日子
          </h1>
          <p className="text-lg text-gray-600">
            歷史氣象大數據 × 傳統曆法智慧
          </p>
        </header>

        {/* 站點選擇器 */}
        <div className="flex justify-center mb-6">
          <StationSelector
            currentStation={currentStation}
            onStationChange={handleStationChange}
          />
        </div>

        {/* 距離資訊 */}
        {distance !== null && (
          <p className="text-center text-sm text-gray-500 mb-4">
            📍 距離你 {distance.toFixed(1)} 公里
          </p>
        )}

        {/* 載入中 */}
        {loading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin text-4xl mb-4">🌀</div>
            <p className="text-gray-500">載入中...</p>
          </div>
        )}

        {/* 錯誤訊息 */}
        {error && !loading && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <p className="text-red-600 font-medium">無法載入資料</p>
            <p className="text-red-500 text-sm mt-1">{error}</p>
            <button
              onClick={() => currentStation && loadWeatherData(currentStation.station_id)}
              className="mt-4 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600"
            >
              重新載入
            </button>
          </div>
        )}

        {/* 天氣卡片 */}
        {data && !loading && <WeatherCard data={data} />}

        {/* Footer */}
        <footer className="mt-8 text-center text-sm text-gray-400">
          <p>根據過去數十年的氣象觀測資料，統計分析每一天的天氣特性。</p>
          <p>幫助您了解特定日期「通常」會是什麼樣的天氣。</p>
        </footer>
      </div>
    </main>
  );
}
```

**Step 2: Commit**

```bash
git add frontend/src/app/page.tsx
git commit -m "feat(page): integrate GPS location and station selector"
```

---

## Sprint 4: 資料準備與測試

### Task 4.1: 執行站點同步並標記有統計資料的站點

**Step 1: 同步站點**

```bash
cd backend && poetry run python -m app.cli sync-stations
# Expected: 同步完成！取得站點數: ~835
```

**Step 2: 標記台北站有統計資料**

```bash
cd backend && poetry run python -c "
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models import Station

engine = create_engine(settings.database_url)
Session = sessionmaker(bind=engine)
db = Session()

# 標記台北站有統計資料
taipei = db.query(Station).filter(Station.station_id == '466920').first()
if taipei:
    taipei.has_statistics = True
    db.commit()
    print(f'已標記 {taipei.name} 站有統計資料')
else:
    print('找不到台北站')

db.close()
"
```

**Step 3: Commit**

```bash
git add -A
git commit -m "chore: sync stations and mark Taipei with statistics"
```

---

### Task 4.2: 整合測試

**Step 1: 啟動後端**

```bash
cd backend && poetry run uvicorn app.main:app --reload --port 8000
```

**Step 2: 啟動前端**

```bash
cd frontend && pnpm dev
```

**Step 3: 測試功能**

1. 開啟 http://localhost:3000
2. 允許 GPS 定位權限
3. 確認自動選擇最近站點
4. 測試手動切換站點
5. 確認天氣資料正確載入

**Step 4: Commit**

```bash
git add -A
git commit -m "test: verify GPS location and station selection"
```

---

## 完成清單

完成以上所有任務後，你將擁有：

- [x] Station 資料模型（含經緯度）
- [x] CWA API 同步服務（835 站點）
- [x] Haversine 距離計算工具
- [x] 最近站點 API (`/stations/nearest`)
- [x] 前端 GPS 定位 Hook
- [x] 站點選擇器組件
- [x] 首頁整合 GPS 自動定位
- [x] 手動站點切換功能

---

---

## Sprint 5: 農曆功能整合 (cnlunar)

### Task 5.1: 安裝 cnlunar 並建立農曆服務

**Files:**
- Create: `backend/app/services/lunar.py`
- Test: `backend/tests/test_lunar.py`

**Step 1: 安裝 cnlunar**

```bash
cd backend && poetry add cnlunar
```

**Step 2: 建立測試檔案**

```python
# backend/tests/test_lunar.py
"""農曆服務測試"""

import pytest
from datetime import datetime, date
from app.services.lunar import LunarService, get_lunar_info


def test_get_lunar_date():
    """測試農曆日期轉換"""
    service = LunarService(datetime(2026, 2, 4))
    lunar = service.get_lunar_date()

    assert lunar["year"] is not None
    assert lunar["month"] is not None
    assert lunar["day"] is not None
    assert "干支年" in lunar


def test_get_yi_ji():
    """測試宜忌資訊"""
    service = LunarService(datetime(2026, 2, 4))
    yi_ji = service.get_yi_ji()

    assert "yi" in yi_ji  # 宜
    assert "ji" in yi_ji  # 忌
    assert isinstance(yi_ji["yi"], list)
    assert isinstance(yi_ji["ji"], list)


def test_get_jieqi():
    """測試節氣資訊"""
    service = LunarService(datetime(2026, 2, 4))
    jieqi = service.get_jieqi()

    # 2 月 4 日可能是立春
    assert jieqi is not None or jieqi is None  # 可能有或沒有節氣


def test_get_lunar_info():
    """測試完整農曆資訊"""
    info = get_lunar_info(date(2026, 2, 4))

    assert "lunar_date" in info
    assert "yi_ji" in info
    assert "jieqi" in info
    assert "ganzhi" in info
```

**Step 3: 執行測試確認失敗**

```bash
cd backend && poetry run pytest tests/test_lunar.py -v
# Expected: FAILED - No module named 'app.services.lunar'
```

**Step 4: 實作農曆服務**

```python
# backend/app/services/lunar.py
"""農曆服務

使用 cnlunar 庫提供農曆相關功能：
- 農曆日期轉換
- 每日宜忌
- 二十四節氣
- 干支紀年
"""

from datetime import datetime, date
from typing import Optional
import cnlunar


class LunarService:
    """農曆服務"""

    def __init__(self, dt: datetime):
        """初始化農曆服務

        Args:
            dt: 要查詢的日期時間
        """
        self.dt = dt
        self._lunar = cnlunar.Lunar(dt)

    def get_lunar_date(self) -> dict:
        """取得農曆日期

        Returns:
            農曆日期資訊
        """
        return {
            "year": self._lunar.lunarYear,
            "month": self._lunar.lunarMonth,
            "day": self._lunar.lunarDay,
            "year_cn": self._lunar.lunarYearCn,
            "month_cn": self._lunar.lunarMonthCn,
            "day_cn": self._lunar.lunarDayCn,
            "干支年": self._lunar.year8Char,
            "干支月": self._lunar.month8Char,
            "干支日": self._lunar.day8Char,
            "生肖": self._lunar.chineseYearZodiac,
            "is_leap": self._lunar.isLunarLeapMonth,
        }

    def get_yi_ji(self) -> dict:
        """取得每日宜忌

        Returns:
            宜忌資訊 {"yi": [...], "ji": [...]}
        """
        return {
            "yi": list(self._lunar.goodThing) if self._lunar.goodThing else [],
            "ji": list(self._lunar.badThing) if self._lunar.badThing else [],
        }

    def get_jieqi(self) -> Optional[str]:
        """取得當日節氣（如果有的話）

        Returns:
            節氣名稱，如果當天不是節氣則返回 None
        """
        return self._lunar.todaySolarTerms if self._lunar.todaySolarTerms != "無" else None

    def get_star(self) -> dict:
        """取得星宿資訊

        Returns:
            二十八星宿等資訊
        """
        return {
            "二十八星宿": self._lunar.star,
            "十二神": self._lunar.get_today12DayOfficer(),
            "彭祖百忌": self._lunar.get_pengpiDict(),
        }

    def get_ganzhi(self) -> dict:
        """取得完整干支資訊

        Returns:
            年月日時干支
        """
        return {
            "年柱": self._lunar.year8Char,
            "月柱": self._lunar.month8Char,
            "日柱": self._lunar.day8Char,
            "時柱": self._lunar.twohour8Char,
        }


def get_lunar_info(dt: date) -> dict:
    """取得完整農曆資訊（便捷函式）

    Args:
        dt: 日期

    Returns:
        完整農曆資訊
    """
    # 轉換為 datetime
    dt_full = datetime(dt.year, dt.month, dt.day, 12, 0)
    service = LunarService(dt_full)

    return {
        "lunar_date": service.get_lunar_date(),
        "yi_ji": service.get_yi_ji(),
        "jieqi": service.get_jieqi(),
        "ganzhi": service.get_ganzhi(),
        "star": service.get_star(),
    }
```

**Step 5: 更新 services/__init__.py**

```python
# backend/app/services/__init__.py
"""服務模組"""

from app.services.cwa_sync import CWASyncService
from app.services.lunar import LunarService, get_lunar_info

__all__ = ["CWASyncService", "LunarService", "get_lunar_info"]
```

**Step 6: 執行測試確認通過**

```bash
cd backend && poetry run pytest tests/test_lunar.py -v
# Expected: 4 passed
```

**Step 7: Commit**

```bash
git add backend/app/services/lunar.py backend/tests/test_lunar.py backend/pyproject.toml backend/poetry.lock
git commit -m "feat(services): add lunar calendar service with cnlunar"
```

---

### Task 5.2: 建立農曆 API 端點

**Files:**
- Create: `backend/app/api/v1/lunar.py`
- Create: `backend/app/schemas/lunar.py`
- Modify: `backend/app/api/v1/__init__.py`

**Step 1: 建立農曆 Schema**

```python
# backend/app/schemas/lunar.py
"""農曆 API Schema"""

from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class LunarDateInfo(BaseModel):
    """農曆日期資訊"""
    year: int
    month: int
    day: int
    year_cn: str
    month_cn: str
    day_cn: str
    干支年: str
    干支月: str
    干支日: str
    生肖: str
    is_leap: bool


class YiJiInfo(BaseModel):
    """宜忌資訊"""
    yi: List[str]  # 宜
    ji: List[str]  # 忌


class GanzhiInfo(BaseModel):
    """干支資訊"""
    年柱: str
    月柱: str
    日柱: str
    時柱: str


class StarInfo(BaseModel):
    """星宿資訊"""
    二十八星宿: str
    十二神: str
    彭祖百忌: dict


class LunarResponse(BaseModel):
    """農曆完整回應"""
    date: str  # YYYY-MM-DD
    lunar_date: LunarDateInfo
    yi_ji: YiJiInfo
    jieqi: Optional[str] = None
    ganzhi: GanzhiInfo
    star: StarInfo
```

**Step 2: 建立農曆 API 端點**

```python
# backend/app/api/v1/lunar.py
"""農曆 API 路由"""

from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Query

from app.schemas.weather import ApiResponse
from app.schemas.lunar import LunarResponse
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
            query_date = date.today()
    else:
        query_date = date.today()

    # 取得農曆資訊
    info = get_lunar_info(query_date)

    return ApiResponse(
        success=True,
        data=LunarResponse(
            date=query_date.isoformat(),
            lunar_date=info["lunar_date"],
            yi_ji=info["yi_ji"],
            jieqi=info["jieqi"],
            ganzhi=info["ganzhi"],
            star=info["star"],
        )
    )
```

**Step 3: 註冊路由**

在 `backend/app/api/v1/__init__.py` 中加入：

```python
from app.api.v1.lunar import router as lunar_router

# 在 main.py 的 router 註冊處加入：
# app.include_router(lunar_router, prefix="/api/v1/lunar", tags=["lunar"])
```

**Step 4: 更新 main.py 註冊路由**

```python
# 在 backend/app/main.py 中加入
from app.api.v1.lunar import router as lunar_router

app.include_router(lunar_router, prefix="/api/v1/lunar", tags=["lunar"])
```

**Step 5: Commit**

```bash
git add backend/app/api/v1/lunar.py backend/app/schemas/lunar.py backend/app/main.py
git commit -m "feat(api): add lunar calendar API endpoint"
```

---

### Task 5.3: 更新天氣 API 包含農曆資訊

**Files:**
- Modify: `backend/app/schemas/weather.py`
- Modify: `backend/app/api/v1/weather.py`

**Step 1: 更新 Weather Schema**

在 `backend/app/schemas/weather.py` 中新增：

```python
from app.schemas.lunar import LunarDateInfo, YiJiInfo

class DailyWeatherResponse(BaseModel):
    """每日天氣完整回應（含農曆）"""
    station: StationInfo
    month_day: str
    analysis_period: AnalysisPeriod
    temperature: TemperatureResponse
    precipitation: PrecipitationResponse
    tendency: WeatherTendencyResponse
    computed_at: datetime
    # 農曆資訊
    lunar_date: Optional[LunarDateInfo] = None
    yi_ji: Optional[YiJiInfo] = None
    jieqi: Optional[str] = None
```

**Step 2: 更新 Weather API**

在 `backend/app/api/v1/weather.py` 中修改回應，加入農曆資訊：

```python
from app.services.lunar import get_lunar_info
from datetime import datetime

# 在 get_daily_weather 函式中，回傳前加入農曆資訊
lunar_info = get_lunar_info(datetime.now().date())
```

**Step 3: Commit**

```bash
git add backend/app/schemas/weather.py backend/app/api/v1/weather.py
git commit -m "feat(api): include lunar info in daily weather response"
```

---

### Task 5.4: 前端農曆顯示組件

**Files:**
- Create: `frontend/src/lib/types/lunar.ts`
- Create: `frontend/src/components/LunarCard.tsx`
- Modify: `frontend/src/app/page.tsx`

**Step 1: 建立農曆型別**

```typescript
// frontend/src/lib/types/lunar.ts
export interface LunarDateInfo {
  year: number;
  month: number;
  day: number;
  year_cn: string;
  month_cn: string;
  day_cn: string;
  干支年: string;
  干支月: string;
  干支日: string;
  生肖: string;
  is_leap: boolean;
}

export interface YiJiInfo {
  yi: string[];  // 宜
  ji: string[];  // 忌
}

export interface LunarResponse {
  date: string;
  lunar_date: LunarDateInfo;
  yi_ji: YiJiInfo;
  jieqi: string | null;
}
```

**Step 2: 建立農曆卡片組件**

```tsx
// frontend/src/components/LunarCard.tsx
"use client";

import { LunarDateInfo, YiJiInfo } from "@/lib/types/lunar";

interface LunarCardProps {
  lunarDate: LunarDateInfo;
  yiJi: YiJiInfo;
  jieqi: string | null;
}

export function LunarCard({ lunarDate, yiJi, jieqi }: LunarCardProps) {
  return (
    <div className="bg-gradient-to-br from-red-50 to-amber-50 rounded-xl p-6 shadow-lg border border-red-100">
      {/* 農曆日期 */}
      <div className="text-center mb-6">
        <div className="text-3xl font-bold text-red-800 mb-1">
          {lunarDate.month_cn}{lunarDate.day_cn}
        </div>
        <div className="text-sm text-red-600">
          {lunarDate.year_cn} {lunarDate.生肖}年
        </div>
        <div className="text-xs text-amber-700 mt-1">
          {lunarDate.干支年}年 {lunarDate.干支月}月 {lunarDate.干支日}日
        </div>
      </div>

      {/* 節氣 */}
      {jieqi && (
        <div className="text-center mb-4 py-2 bg-amber-100 rounded-lg">
          <span className="text-amber-800 font-semibold">🌿 {jieqi}</span>
        </div>
      )}

      {/* 宜忌 */}
      <div className="grid grid-cols-2 gap-4">
        {/* 宜 */}
        <div className="bg-white/60 rounded-lg p-3">
          <div className="text-green-700 font-semibold mb-2 flex items-center gap-1">
            <span className="text-lg">✓</span> 宜
          </div>
          <div className="flex flex-wrap gap-1">
            {yiJi.yi.slice(0, 6).map((item, i) => (
              <span
                key={i}
                className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded"
              >
                {item}
              </span>
            ))}
          </div>
        </div>

        {/* 忌 */}
        <div className="bg-white/60 rounded-lg p-3">
          <div className="text-red-700 font-semibold mb-2 flex items-center gap-1">
            <span className="text-lg">✗</span> 忌
          </div>
          <div className="flex flex-wrap gap-1">
            {yiJi.ji.slice(0, 6).map((item, i) => (
              <span
                key={i}
                className="px-2 py-0.5 bg-red-100 text-red-700 text-xs rounded"
              >
                {item}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
```

**Step 3: 更新組件 index**

```typescript
// frontend/src/components/index.ts
export { WeatherCard } from "./WeatherCard";
export { StationSelector } from "./StationSelector";
export { LunarCard } from "./LunarCard";
```

**Step 4: 更新首頁整合農曆卡片**

在 `frontend/src/app/page.tsx` 中加入 LunarCard：

```tsx
import { LunarCard } from "@/components";

// 在 WeatherCard 下方加入
{data?.lunar_date && data?.yi_ji && (
  <div className="mt-6">
    <LunarCard
      lunarDate={data.lunar_date}
      yiJi={data.yi_ji}
      jieqi={data.jieqi}
    />
  </div>
)}
```

**Step 5: Commit**

```bash
git add frontend/src/lib/types/lunar.ts frontend/src/components/LunarCard.tsx frontend/src/components/index.ts frontend/src/app/page.tsx
git commit -m "feat(frontend): add LunarCard component with yi-ji display"
```

---

## 完成清單

完成以上所有任務後，你將擁有：

- [x] Station 資料模型（含經緯度）
- [x] CWA API 同步服務（835 站點）
- [x] Haversine 距離計算工具
- [x] 最近站點 API (`/stations/nearest`)
- [x] 前端 GPS 定位 Hook
- [x] 站點選擇器組件
- [x] 首頁整合 GPS 自動定位
- [x] 手動站點切換功能
- [x] **cnlunar 農曆服務** (NEW)
- [x] **農曆 API 端點** (NEW)
- [x] **農曆卡片組件** (NEW)
- [x] **每日宜忌顯示** (NEW)

---

**Plan complete and saved to `docs/plans/2026-02-04-phase2-gps-stations.md`.**
