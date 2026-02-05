# backend/app/schemas/weather.py
"""天氣 API Pydantic Schema 定義"""

from datetime import datetime
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.lunar import LunarDateInfo, YiJiInfo

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
    # 農曆資訊
    lunar_date: Optional[LunarDateInfo] = Field(None, description="農曆日期資訊")
    yi_ji: Optional[YiJiInfo] = Field(None, description="宜忌資訊")
    jieqi: Optional[str] = Field(None, description="當日節氣（如有）")

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
                "computed_at": "2025-01-01T00:00:00",
                "lunar_date": {
                    "year": 2025,
                    "month": 1,
                    "day": 7,
                    "year_cn": "二零二五年",
                    "month_cn": "正月",
                    "day_cn": "初七",
                    "ganzhi_year": "乙巳",
                    "ganzhi_month": "戊寅",
                    "ganzhi_day": "甲子",
                    "zodiac": "蛇",
                    "is_leap": False
                },
                "yi_ji": {
                    "yi": ["祭祀", "祈福"],
                    "ji": ["動土", "破土"]
                },
                "jieqi": "立春"
            }
        }


class DailyWeatherSummary(BaseModel):
    """每日天氣摘要（用於範圍查詢）"""

    month_day: str = Field(..., pattern=r"^\d{2}-\d{2}$", description="日期 (MM-DD)")
    temp_avg: Optional[float] = Field(None, description="平均溫度 (°C)")
    temp_max: Optional[float] = Field(None, description="最高溫平均 (°C)")
    temp_min: Optional[float] = Field(None, description="最低溫平均 (°C)")
    precip_prob: Optional[float] = Field(None, ge=0, le=1, description="降雨機率")
    sunny_rate: Optional[float] = Field(None, ge=0, le=1, description="晴天率")
    # 農曆資訊
    lunar_date: Optional[LunarDateInfo] = Field(None, description="農曆日期")
    jieqi: Optional[str] = Field(None, description="節氣")


class RangeSummary(BaseModel):
    """範圍統計摘要"""

    avg_temp: Optional[float] = Field(None, description="範圍內平均溫度")
    avg_precip_prob: Optional[float] = Field(None, description="範圍內平均降雨機率")
    avg_sunny_rate: Optional[float] = Field(None, description="範圍內平均晴天率")
    best_day: Optional[str] = Field(None, description="最佳日期 (晴天率最高)")
    worst_day: Optional[str] = Field(None, description="最差日期 (降雨機率最高)")


class DateRangeResponse(BaseModel):
    """日期範圍查詢回應"""

    station: StationInfo = Field(..., description="站點資訊")
    start_date: str = Field(..., pattern=r"^\d{2}-\d{2}$", description="起始日期")
    end_date: str = Field(..., pattern=r"^\d{2}-\d{2}$", description="結束日期")
    days: list[DailyWeatherSummary] = Field(..., description="每日統計列表")
    summary: RangeSummary = Field(..., description="範圍統計摘要")


class RecommendedDate(BaseModel):
    """推薦日期"""

    month_day: str = Field(..., pattern=r"^\d{2}-\d{2}$", description="日期 (MM-DD)")
    score: float = Field(..., ge=0, le=100, description="推薦分數 (0-100)")
    reason: str = Field(..., description="推薦理由")
    temp_avg: Optional[float] = Field(None, description="平均溫度 (°C)")
    precip_prob: Optional[float] = Field(None, ge=0, le=1, description="降雨機率")
    sunny_rate: Optional[float] = Field(None, ge=0, le=1, description="晴天率")
    lunar_date: Optional[LunarDateInfo] = Field(None, description="農曆日期")
    jieqi: Optional[str] = Field(None, description="節氣")


class BestDatesResponse(BaseModel):
    """最佳日期推薦回應"""

    station: StationInfo = Field(..., description="站點資訊")
    month: int = Field(..., ge=1, le=12, description="查詢月份")
    preference: str = Field(..., description="偏好類型")
    recommendations: list[RecommendedDate] = Field(..., description="推薦日期列表")


class StationWeatherComparison(BaseModel):
    """站點天氣比較資料"""

    station: StationInfo = Field(..., description="站點資訊")
    temp_avg: Optional[float] = Field(None, description="平均溫度 (°C)")
    temp_max: Optional[float] = Field(None, description="最高溫平均 (°C)")
    temp_min: Optional[float] = Field(None, description="最低溫平均 (°C)")
    precip_prob: Optional[float] = Field(None, ge=0, le=1, description="降雨機率")
    sunny_rate: Optional[float] = Field(None, ge=0, le=1, description="晴天率")
    years_analyzed: Optional[int] = Field(None, description="分析年數")
    rank: Optional[int] = Field(None, description="綜合排名 (晴天率優先)")


class CompareResponse(BaseModel):
    """多站點比較回應"""

    date: str = Field(..., pattern=r"^\d{2}-\d{2}$", description="比較日期 (MM-DD)")
    stations: list[StationWeatherComparison] = Field(..., description="站點天氣比較列表")
    best_station: Optional[str] = Field(None, description="最佳站點 ID (晴天率最高)")
    lunar_date: Optional[LunarDateInfo] = Field(None, description="農曆日期")
    jieqi: Optional[str] = Field(None, description="節氣")


class RealtimeWeatherInfo(BaseModel):
    """即時天氣資訊"""

    obs_time: Optional[str] = Field(None, description="觀測時間")
    weather: Optional[str] = Field(None, description="天氣描述")
    temp: Optional[float] = Field(None, description="目前溫度 (°C)")
    temp_max: Optional[float] = Field(None, description="今日最高溫 (°C)")
    temp_min: Optional[float] = Field(None, description="今日最低溫 (°C)")
    humidity: Optional[float] = Field(None, description="相對濕度 (%)")
    precipitation: Optional[float] = Field(None, description="今日累積雨量 (mm)")


# ===== Phase 3.1 年代分層統計 Schema =====

class ExtremeRecord(BaseModel):
    """極值紀錄（含年份）"""

    value: float = Field(..., description="極值數值")
    year: int = Field(..., description="發生年份")


class ExtremeRecords(BaseModel):
    """歷史極值紀錄"""

    max_temp: Optional[ExtremeRecord] = Field(None, description="歷史最高溫")
    min_temp: Optional[ExtremeRecord] = Field(None, description="歷史最低溫")
    max_precip: Optional[ExtremeRecord] = Field(None, description="歷史最大降水量")


class DecadeStats(BaseModel):
    """單一年代的統計資料"""

    decade: str = Field(..., description="年代標籤 (1990s, 2000s, 2010s, 2020s)")
    start_year: int = Field(..., description="起始年份")
    end_year: int = Field(..., description="結束年份")
    years_count: int = Field(..., description="資料年數")
    temp_avg: Optional[float] = Field(None, description="平均溫度 (°C)")
    temp_max_avg: Optional[float] = Field(None, description="最高溫平均 (°C)")
    temp_min_avg: Optional[float] = Field(None, description="最低溫平均 (°C)")
    precip_prob: Optional[float] = Field(None, ge=0, le=1, description="降雨機率")
    precip_avg: Optional[float] = Field(None, description="有雨時平均降水量 (mm)")


class ClimateTrend(BaseModel):
    """氣候趨勢分析"""

    trend_per_decade: Optional[float] = Field(None, description="每 10 年溫度變化 (°C)")
    interpretation: str = Field(..., description="趨勢解讀")
    data_years: int = Field(..., description="資料年數")


class HistoricalComparison(BaseModel):
    """歷史同期比較"""

    metric: str = Field(..., description="比較指標名稱")
    current: Optional[float] = Field(None, description="今日實際值")
    historical_avg: Optional[float] = Field(None, description="歷史平均值")
    difference: Optional[float] = Field(None, description="差異值 (今日 - 歷史)")
    percentile: Optional[float] = Field(None, description="今日值在歷史分布中的百分位")
    status: str = Field("normal", description="狀態: normal, above_normal, below_normal, extreme")


class HistoricalCompareResponse(BaseModel):
    """歷史同期比較回應"""

    station: StationInfo = Field(..., description="站點資訊")
    date: str = Field(..., pattern=r"^\d{2}-\d{2}$", description="日期 (MM-DD)")
    realtime: Optional[RealtimeWeatherInfo] = Field(None, description="即時天氣資訊")
    comparisons: list[HistoricalComparison] = Field(..., description="各項指標比較列表")
    summary: str = Field(..., description="綜合評語")
    lunar_date: Optional[LunarDateInfo] = Field(None, description="農曆日期")
    jieqi: Optional[str] = Field(None, description="節氣")
    # Phase 3.1 年代分層統計
    percentile: Optional[float] = Field(None, ge=0, le=100, description="目前溫度在歷史分布中的百分位數 (0-100)")
    extreme_records: Optional[ExtremeRecords] = Field(None, description="歷史極值紀錄（含年份）")
    decades: Optional[list[DecadeStats]] = Field(None, description="各年代分層統計")
    climate_trend: Optional[ClimateTrend] = Field(None, description="氣候變遷趨勢分析")


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
