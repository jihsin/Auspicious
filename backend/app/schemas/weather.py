# backend/app/schemas/weather.py
"""天氣 API Pydantic Schema 定義"""

from datetime import datetime
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class StationInfo(BaseModel):
    """站點資訊"""

    station_id: str = Field(..., description="氣象站代碼")
    name: str = Field(..., description="站點名稱")
    city: str = Field(..., description="所在城市")

    class Config:
        json_schema_extra = {
            "example": {
                "station_id": "466920",
                "name": "臺北",
                "city": "臺北市"
            }
        }


class StationInfoExtended(BaseModel):
    """站點詳細資訊（含座標）"""

    station_id: str = Field(..., description="氣象站代碼")
    name: str = Field(..., description="站點名稱")
    county: Optional[str] = Field(None, description="縣市")
    town: Optional[str] = Field(None, description="鄉鎮市區")
    latitude: float = Field(..., description="緯度")
    longitude: float = Field(..., description="經度")
    altitude: Optional[float] = Field(None, description="海拔高度 (公尺)")
    has_statistics: bool = Field(False, description="是否有統計資料")

    model_config = ConfigDict(from_attributes=True)


class NearestStationResponse(BaseModel):
    """最近站點回應"""

    station: StationInfoExtended = Field(..., description="站點資訊")
    distance_km: float = Field(..., description="距離 (公里)")


class TemperatureStats(BaseModel):
    """溫度統計數據"""

    mean: Optional[float] = Field(None, description="平均值 (°C)")
    median: Optional[float] = Field(None, description="中位數 (°C)")
    stddev: Optional[float] = Field(None, description="標準差 (°C)")


class TemperatureRecord(BaseModel):
    """溫度紀錄"""

    value: Optional[float] = Field(None, description="溫度值 (°C)")
    # 未來可擴充：紀錄年份、日期等


class TemperatureResponse(BaseModel):
    """溫度回應"""

    avg: TemperatureStats = Field(..., description="平均溫度統計")
    max_mean: Optional[float] = Field(None, description="最高溫平均值 (°C)")
    max_record: TemperatureRecord = Field(..., description="歷史最高溫紀錄")
    min_mean: Optional[float] = Field(None, description="最低溫平均值 (°C)")
    min_record: TemperatureRecord = Field(..., description="歷史最低溫紀錄")


class PrecipitationResponse(BaseModel):
    """降水回應"""

    probability: Optional[float] = Field(None, ge=0, le=1, description="降雨機率 (0-1)")
    avg_when_rain: Optional[float] = Field(None, ge=0, description="有雨日平均降水量 (mm)")
    heavy_probability: Optional[float] = Field(None, ge=0, le=1, description="大雨機率 (>50mm)")
    max_record: Optional[float] = Field(None, ge=0, description="歷史最大降水量 (mm)")


class WeatherTendencyResponse(BaseModel):
    """天氣傾向"""

    sunny: Optional[float] = Field(None, ge=0, le=1, description="晴天比例")
    cloudy: Optional[float] = Field(None, ge=0, le=1, description="陰天比例")
    rainy: Optional[float] = Field(None, ge=0, le=1, description="雨天比例")


class AnalysisPeriod(BaseModel):
    """分析期間"""

    years_analyzed: Optional[int] = Field(None, description="分析年數")
    start_year: Optional[int] = Field(None, description="起始年份")
    end_year: Optional[int] = Field(None, description="結束年份")


class DailyWeatherResponse(BaseModel):
    """每日天氣回應"""

    station: StationInfo = Field(..., description="站點資訊")
    month_day: str = Field(..., pattern=r"^\d{2}-\d{2}$", description="日期 (MM-DD)")
    analysis_period: AnalysisPeriod = Field(..., description="分析期間")
    temperature: TemperatureResponse = Field(..., description="溫度統計")
    precipitation: PrecipitationResponse = Field(..., description="降水統計")
    tendency: WeatherTendencyResponse = Field(..., description="天氣傾向")
    computed_at: datetime = Field(..., description="統計計算時間")

    class Config:
        json_schema_extra = {
            "example": {
                "station": {
                    "station_id": "466920",
                    "name": "臺北",
                    "city": "臺北市"
                },
                "month_day": "02-04",
                "analysis_period": {
                    "years_analyzed": 30,
                    "start_year": 1994,
                    "end_year": 2024
                },
                "temperature": {
                    "avg": {
                        "mean": 16.5,
                        "median": 16.2,
                        "stddev": 2.8
                    },
                    "max_mean": 20.3,
                    "max_record": {"value": 28.5},
                    "min_mean": 13.8,
                    "min_record": {"value": 5.2}
                },
                "precipitation": {
                    "probability": 0.35,
                    "avg_when_rain": 8.5,
                    "heavy_probability": 0.02,
                    "max_record": 85.0
                },
                "tendency": {
                    "sunny": 0.4,
                    "cloudy": 0.35,
                    "rainy": 0.25
                },
                "computed_at": "2025-01-01T00:00:00"
            }
        }


class ApiResponse(BaseModel, Generic[T]):
    """API 回應包裝"""

    success: bool = Field(True, description="請求是否成功")
    data: Optional[T] = Field(None, description="回應資料")
    error: Optional[str] = Field(None, description="錯誤訊息")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {},
                "error": None
            }
        }
