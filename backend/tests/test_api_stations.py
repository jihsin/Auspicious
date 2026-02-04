# backend/tests/test_api_stations.py
"""站點 API 測試"""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import get_db
from app.main import app
from app.models import Base, Station


# 測試用資料庫（使用記憶體 SQLite）
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_stations.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """覆蓋資料庫依賴"""
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
    # 建立資料表
    Base.metadata.create_all(bind=engine)

    # 新增測試站點
    db = TestingSessionLocal()
    stations = [
        Station(
            station_id="466920",
            name="臺北",
            county="臺北市",
            town="中正區",
            latitude=25.0375,
            longitude=121.5148,
            has_statistics=True,
            is_active=True,
        ),
        Station(
            station_id="467490",
            name="臺中",
            county="臺中市",
            town="西屯區",
            latitude=24.1477,
            longitude=120.6844,
            has_statistics=True,
            is_active=True,
        ),
        Station(
            station_id="C0A520",
            name="士林",
            county="臺北市",
            town="士林區",
            latitude=25.0958,
            longitude=121.5247,
            has_statistics=False,
            is_active=True,
        ),
        Station(
            station_id="INACTIVE",
            name="已停用站",
            county="臺北市",
            town="大安區",
            latitude=25.0260,
            longitude=121.5435,
            has_statistics=False,
            is_active=False,
        ),
    ]
    db.add_all(stations)
    db.commit()
    db.close()

    yield

    # 清理
    Base.metadata.drop_all(bind=engine)


def test_list_stations():
    """測試列出所有站點"""
    response = client.get("/api/v1/stations/")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    # 應該只有 3 個啟用的站點（排除 INACTIVE）
    assert len(data["data"]) == 3


def test_list_stations_filter_by_county():
    """測試依縣市篩選"""
    response = client.get("/api/v1/stations/?county=臺北市")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    # 台北市有 2 個啟用站點（臺北、士林）
    assert len(data["data"]) == 2
    for station in data["data"]:
        assert station["county"] == "臺北市"


def test_list_stations_filter_by_has_statistics():
    """測試篩選有統計資料的站點"""
    response = client.get("/api/v1/stations/?has_statistics=true")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    # 只有 2 個有統計資料（臺北、臺中）
    assert len(data["data"]) == 2
    for station in data["data"]:
        assert station["has_statistics"] is True


def test_get_station():
    """測試取得單一站點"""
    response = client.get("/api/v1/stations/466920")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["data"]["station_id"] == "466920"
    assert data["data"]["name"] == "臺北"
    assert data["data"]["county"] == "臺北市"
    assert data["data"]["latitude"] == 25.0375


def test_get_station_not_found():
    """測試找不到站點"""
    response = client.get("/api/v1/stations/NOTEXIST")
    assert response.status_code == 404


def test_get_nearest_station():
    """測試取得最近站點"""
    # 用戶位置在台北市中心
    response = client.get("/api/v1/stations/nearest?lat=25.0330&lon=121.5654")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    # 應該找到臺北站（最近）
    assert data["data"]["station"]["station_id"] == "466920"
    assert data["data"]["distance_km"] < 10


def test_get_nearest_station_with_statistics_filter():
    """測試最近站點篩選有統計資料"""
    # 用戶位置接近士林，但士林沒有統計資料
    response = client.get(
        "/api/v1/stations/nearest?lat=25.0958&lon=121.5247&has_statistics=true"
    )
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    # 士林沒有統計資料，應該找到臺北站
    assert data["data"]["station"]["station_id"] == "466920"
    assert data["data"]["station"]["has_statistics"] is True


def test_get_nearest_station_missing_params():
    """測試缺少參數"""
    response = client.get("/api/v1/stations/nearest")
    assert response.status_code == 422  # Validation error


def test_get_nearest_station_invalid_lat():
    """測試無效緯度"""
    response = client.get("/api/v1/stations/nearest?lat=100&lon=121.5")
    assert response.status_code == 422  # lat 超出 -90 ~ 90


def test_get_nearest_station_invalid_lon():
    """測試無效經度"""
    response = client.get("/api/v1/stations/nearest?lat=25.0&lon=200")
    assert response.status_code == 422  # lon 超出 -180 ~ 180


# 清理測試資料庫檔案
@pytest.fixture(scope="session", autouse=True)
def cleanup():
    """測試結束後清理"""
    yield
    # 刪除測試資料庫檔案
    if os.path.exists("./test_stations.db"):
        os.remove("./test_stations.db")
