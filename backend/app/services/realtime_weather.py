"""即時天氣查詢服務

從 CWA OpenData API 取得即時氣象觀測資料。
"""

import httpx
import asyncio
from typing import Optional
from datetime import datetime, timedelta, timezone

# 台灣時區 (UTC+8)
TW_TIMEZONE = timezone(timedelta(hours=8))

from app.config import settings
from app.services.notification import notify_api_key_expired


# CWA API 端點
# O-A0003-001: 自動氣象站-氣象觀測資料
REALTIME_ENDPOINT = "O-A0003-001"


class RealtimeWeatherData:
    """即時天氣資料結構"""

    def __init__(
        self,
        station_id: str,
        station_name: str,
        obs_time: datetime,
        weather: Optional[str] = None,
        temp: Optional[float] = None,
        temp_max: Optional[float] = None,
        temp_min: Optional[float] = None,
        humidity: Optional[float] = None,
        wind_speed: Optional[float] = None,
        wind_direction: Optional[str] = None,
        precipitation: Optional[float] = None,
        sunshine_hours: Optional[float] = None,
    ):
        self.station_id = station_id
        self.station_name = station_name
        self.obs_time = obs_time
        self.weather = weather
        self.temp = temp
        self.temp_max = temp_max
        self.temp_min = temp_min
        self.humidity = humidity
        self.wind_speed = wind_speed
        self.wind_direction = wind_direction
        self.precipitation = precipitation
        self.sunshine_hours = sunshine_hours

    def to_dict(self) -> dict:
        return {
            "station_id": self.station_id,
            "station_name": self.station_name,
            "obs_time": self.obs_time.isoformat() if self.obs_time else None,
            "weather": self.weather,
            "temp": self.temp,
            "temp_max": self.temp_max,
            "temp_min": self.temp_min,
            "humidity": self.humidity,
            "wind_speed": self.wind_speed,
            "wind_direction": self.wind_direction,
            "precipitation": self.precipitation,
            "sunshine_hours": self.sunshine_hours,
        }


def parse_weather_element(elements: dict, name: str) -> Optional[float]:
    """從天氣元素物件中解析指定元素的值

    Args:
        elements: CWA API 返回的 WeatherElement 物件
        name: 元素名稱

    Returns:
        元素值（float），如果找不到或無效則返回 None
    """
    value = elements.get(name)
    if value is None:
        return None

    # 處理嵌套結構
    if isinstance(value, dict):
        # 如 Now.Precipitation
        if "Precipitation" in value:
            value = value.get("Precipitation")
        else:
            return None

    if value is not None and str(value) not in ["-99", "-99.0", ""]:
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    return None


def parse_daily_extreme(elements: dict, extreme_type: str) -> Optional[float]:
    """從 DailyExtreme 中解析最高/最低溫度

    Args:
        elements: CWA API 返回的 WeatherElement 物件
        extreme_type: "DailyHigh" 或 "DailyLow"

    Returns:
        溫度值，如果找不到則返回 None
    """
    try:
        daily_extreme = elements.get("DailyExtreme", {})
        extreme_data = daily_extreme.get(extreme_type, {})
        temp_info = extreme_data.get("TemperatureInfo", {})
        value = temp_info.get("AirTemperature")
        if value and str(value) not in ["-99", "-99.0"]:
            return float(value)
    except (ValueError, TypeError, AttributeError):
        pass
    return None


async def fetch_realtime_weather(station_id: str) -> Optional[RealtimeWeatherData]:
    """取得指定站點的即時天氣資料

    Args:
        station_id: 氣象站代碼

    Returns:
        即時天氣資料，如果查詢失敗則返回 None
    """
    url = f"{settings.cwa_api_base}/{REALTIME_ENDPOINT}"
    params = {
        "Authorization": settings.cwa_api_key,
        "StationId": station_id,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        stations = data.get("records", {}).get("Station", [])
        if not stations:
            return None

        station = stations[0]
        obs_time_str = station.get("ObsTime", {}).get("DateTime")
        obs_time = datetime.fromisoformat(obs_time_str) if obs_time_str else datetime.now(TW_TIMEZONE)

        elements = station.get("WeatherElement", {})

        # 天氣描述（直接從物件取得）
        weather = elements.get("Weather")

        return RealtimeWeatherData(
            station_id=station.get("StationId"),
            station_name=station.get("StationName"),
            obs_time=obs_time,
            weather=weather,
            temp=parse_weather_element(elements, "AirTemperature"),
            temp_max=parse_daily_extreme(elements, "DailyHigh"),
            temp_min=parse_daily_extreme(elements, "DailyLow"),
            humidity=parse_weather_element(elements, "RelativeHumidity"),
            wind_speed=parse_weather_element(elements, "WindSpeed"),
            precipitation=parse_weather_element(elements, "Now"),  # 當日累積雨量
            sunshine_hours=parse_weather_element(elements, "SunshineDuration"),
        )

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            print(f"CWA API 認證失敗 (401): API 密鑰可能已失效")
            # 非同步發送通知
            asyncio.create_task(
                notify_api_key_expired("CWA OpenData", "401 Forbidden - API 密鑰已失效或不正確")
            )
        else:
            print(f"CWA API HTTP 錯誤: {e.response.status_code}")
        return None
    except Exception as e:
        print(f"Error fetching realtime weather: {e}")
        return None


async def fetch_all_realtime_weather() -> list[RealtimeWeatherData]:
    """取得所有站點的即時天氣資料

    Returns:
        所有站點的即時天氣資料列表
    """
    url = f"{settings.cwa_api_base}/{REALTIME_ENDPOINT}"
    params = {
        "Authorization": settings.cwa_api_key,
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        stations = data.get("records", {}).get("Station", [])
        results = []

        for station in stations:
            obs_time_str = station.get("ObsTime", {}).get("DateTime")
            obs_time = datetime.fromisoformat(obs_time_str) if obs_time_str else datetime.now(TW_TIMEZONE)

            elements = station.get("WeatherElement", {})
            weather = elements.get("Weather")

            results.append(RealtimeWeatherData(
                station_id=station.get("StationId"),
                station_name=station.get("StationName"),
                obs_time=obs_time,
                weather=weather,
                temp=parse_weather_element(elements, "AirTemperature"),
                temp_max=parse_daily_extreme(elements, "DailyHigh"),
                temp_min=parse_daily_extreme(elements, "DailyLow"),
                humidity=parse_weather_element(elements, "RelativeHumidity"),
                wind_speed=parse_weather_element(elements, "WindSpeed"),
                precipitation=parse_weather_element(elements, "Now"),
                sunshine_hours=parse_weather_element(elements, "SunshineDuration"),
            ))

        return results

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            print(f"CWA API 認證失敗 (401): API 密鑰可能已失效")
            asyncio.create_task(
                notify_api_key_expired("CWA OpenData", "401 Forbidden - API 密鑰已失效或不正確")
            )
        else:
            print(f"CWA API HTTP 錯誤: {e.response.status_code}")
        return []
    except Exception as e:
        print(f"Error fetching all realtime weather: {e}")
        return []
