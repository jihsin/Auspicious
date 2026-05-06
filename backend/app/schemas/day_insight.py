from typing import Literal, Optional
from pydantic import BaseModel


class LabelInfo(BaseModel):
    text: Optional[str] = None
    category: Optional[Literal["seasonal", "anomaly", "record", "solar_term"]] = None


class CoreMetric(BaseModel):
    metric: Literal["precip_probability"]
    value: float
    anomaly_year: float
    anomaly_month: float


class SideBadge(BaseModel):
    metric: Literal["temp_avg", "humidity_avg"]
    label: str
    direction: Literal["above", "below"]
    z_score: float


class ExtremeRecord(BaseModel):
    year: int
    value: float


class Extremes(BaseModel):
    wettest: Optional[ExtremeRecord] = None
    driest: Optional[ExtremeRecord] = None


class InsightMeta(BaseModel):
    years_analyzed: int
    start_year: int
    end_year: int


class DayInsight(BaseModel):
    station_id: str
    month: int
    day: int
    label: LabelInfo
    core: CoreMetric
    side_badges: list[SideBadge]
    extremes: Extremes
    meta: InsightMeta
