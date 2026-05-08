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


class HexagramRef(BaseModel):
    num: int
    name: str
    judgement: str | None = None
    image: str | None = None
    upper_trigram: str | None = None  # e.g. "離"
    lower_trigram: str | None = None
    weather_persona: str | None = None  # NEW · ≤30 字 weather-relatable life advice


class Narrative(BaseModel):
    climate_portrait: str
    anomaly_layer: str
    imagination: str
    headline: str = ""        # NEW · ≤12 字大標
    subtitle: str = ""        # NEW · ≤30 字副標
    tags: list[str] = []      # NEW · 3 個，每個 ≤4 字


class YaoCiEntry(BaseModel):
    original: str             # 古文爻辭
    vernacular: str           # 白話翻譯


class Divination(BaseModel):
    ben: HexagramRef
    zhi: HexagramRef
    cuo: HexagramRef
    zong: HexagramRef
    hu: HexagramRef
    changing_positions: list[int]
    line_values: list[int]
    narrative: Narrative
    var_yao_ci: dict[int, YaoCiEntry] = {}  # NEW · key = 爻位 (1-6)


class DayInsightInterpretation(BaseModel):
    station_id: str
    month: int
    day: int
    divination: Divination
