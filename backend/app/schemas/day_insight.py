from typing import Literal

from pydantic import BaseModel

from app.schemas.common import ExtremeRecord  # noqa: F401 — re-exported for consumers


class LabelInfo(BaseModel):
    text: str | None = None
    category: Literal["seasonal", "anomaly", "record", "solar_term"] | None = None


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


class Extremes(BaseModel):
    wettest: ExtremeRecord | None = None
    driest: ExtremeRecord | None = None


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
