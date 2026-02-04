"""中央氣象署 API 同步服務

從 CWA OpenData API 取得全台觀測站資料並同步到資料庫。
"""

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
    """CWA 資料同步服務

    負責從中央氣象署 OpenData API 取得觀測站資料，
    並同步到本地資料庫。

    Attributes:
        db: SQLAlchemy Session 物件
    """

    def __init__(self, db: Session):
        """初始化同步服務

        Args:
            db: 資料庫 session
        """
        self.db = db

    async def fetch_all_stations(self) -> list[dict]:
        """從 CWA API 取得所有站點資料

        Returns:
            站點資料列表（已解析並過濾無效資料）

        Raises:
            httpx.HTTPError: API 請求失敗時
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

        從 CWA API 取得最新站點資料，並與資料庫同步：
        - 新站點會被建立
        - 已存在的站點會被更新

        Returns:
            同步結果統計，包含：
            - total_fetched: 從 API 取得的有效站點數
            - created: 新建立的站點數
            - updated: 更新的站點數
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
