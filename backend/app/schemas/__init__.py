# backend/app/schemas/__init__.py
"""Pydantic Schema 模組"""

from app.schemas.weather import (
    StationInfo,
    TemperatureStats,
    TemperatureRecord,
    TemperatureResponse,
    PrecipitationResponse,
    WeatherTendencyResponse,
    AnalysisPeriod,
    DailyWeatherResponse,
    ApiResponse,
)

__all__ = [
    "StationInfo",
    "TemperatureStats",
    "TemperatureRecord",
    "TemperatureResponse",
    "PrecipitationResponse",
    "WeatherTendencyResponse",
    "AnalysisPeriod",
    "DailyWeatherResponse",
    "ApiResponse",
]
