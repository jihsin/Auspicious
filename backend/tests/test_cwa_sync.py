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


def test_parse_station_data_missing_lat_lon():
    """測試座標欄位缺失的情況"""
    raw_data = {
        "StationId": "TEST02",
        "StationName": "測試站2",
        "GeoInfo": {
            "CountyName": "測試縣",
            "Coordinates": [
                {
                    "StationLatitude": None,
                    "StationLongitude": 121.5
                }
            ]
        }
    }

    result = parse_station_data(raw_data)

    assert result is None


def test_parse_station_data_empty_geoinfo():
    """測試 GeoInfo 為空的情況"""
    raw_data = {
        "StationId": "TEST03",
        "StationName": "測試站3",
        "GeoInfo": {}
    }

    result = parse_station_data(raw_data)

    assert result is None


class TestCWASyncService:
    """CWA 同步服務測試類別"""

    @pytest.fixture
    def mock_db(self):
        """模擬資料庫 session"""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_fetch_all_stations(self, mock_db):
        """測試取得所有站點資料"""
        mock_response_data = {
            "records": {
                "Station": [
                    {
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
                    },
                    {
                        "StationId": "INVALID",
                        "StationName": "無效站",
                        "GeoInfo": {
                            "Coordinates": []
                        }
                    }
                ]
            }
        }

        with patch("app.services.cwa_sync.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()

            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client.return_value = mock_client_instance

            service = CWASyncService(mock_db)
            stations = await service.fetch_all_stations()

            # 應該只有一個有效站點
            assert len(stations) == 1
            assert stations[0]["station_id"] == "C0TB40"
            assert stations[0]["name"] == "崇德"

    @pytest.mark.asyncio
    async def test_sync_stations_create_new(self, mock_db):
        """測試同步新站點（建立）"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch.object(CWASyncService, "fetch_all_stations") as mock_fetch:
            mock_fetch.return_value = [
                {
                    "station_id": "NEW01",
                    "name": "新站點",
                    "county": "新北市",
                    "town": "板橋區",
                    "latitude": 25.0,
                    "longitude": 121.5,
                    "altitude": 10.0
                }
            ]

            service = CWASyncService(mock_db)
            result = await service.sync_stations()

            assert result["total_fetched"] == 1
            assert result["created"] == 1
            assert result["updated"] == 0
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_stations_update_existing(self, mock_db):
        """測試同步現有站點（更新）"""
        existing_station = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = existing_station

        with patch.object(CWASyncService, "fetch_all_stations") as mock_fetch:
            mock_fetch.return_value = [
                {
                    "station_id": "EXIST01",
                    "name": "現有站點",
                    "county": "台北市",
                    "town": "信義區",
                    "latitude": 25.03,
                    "longitude": 121.56,
                    "altitude": 5.0
                }
            ]

            service = CWASyncService(mock_db)
            result = await service.sync_stations()

            assert result["total_fetched"] == 1
            assert result["created"] == 0
            assert result["updated"] == 1
            mock_db.add.assert_not_called()
            mock_db.commit.assert_called_once()
