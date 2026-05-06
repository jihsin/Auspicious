# DayInsightCard + Divination Drawer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the flat "降雨機率 44%" display with a differentiated `DayInsightCard` (label / dual-baseline anomaly / twin extremes) and add an I-Ching divination drawer that lazy-loads when the user opens "看詳細詮釋".

**Architecture:** Pure-historical-statistics card alongside existing WeatherCard / SolarTermCard. Backend exposes `/api/v1/day-insight/{station}/{month}/{day}` for the card and `/.../interpretation` for the drawer (which returns 5-hexagram payload + 3-section AI narrative). Hexagram math adopts pi-mono `iching_divination.py` (MIT) with random tossing replaced by deterministic weather-driven mapping.

**Tech Stack:** FastAPI, SQLAlchemy 2.x, Pydantic v2, SQLite, Next.js 16, React 19, TypeScript, Tailwind CSS 4, Zustand, pnpm, Google Gemini (existing `app/services/ai_engine.py`).

**Specs:**
- [DayInsightCard design](../specs/2026-05-06-day-insight-card-design.md)
- [Divination Drawer design](../specs/2026-05-06-divination-drawer-design.md)

---

## Pre-work

### Task 0: Add `humidity_avg` to `DailyStatistics`

The DayInsightCard side-badges and divination 6-line mapping both need humidity at the day-statistic level, but `DailyStatistics` currently only has temperature/precipitation/tendency. `RawObservation.humidity_avg` exists, just unused at the snapshot layer.

**Files:**
- Modify: `backend/app/models/statistics.py` (add column)
- Modify: `data-pipeline/compute_snapshots.py` (populate column)
- Modify: `backend/app/analytics/engine.py` (return humidity from `get_date_range_stats`)
- Run: `data-pipeline/rerun_after_fix.py` (recompute snapshots)

- [ ] **Step 1: Add column to model**

In `backend/app/models/statistics.py`, after the `temp_*` block (~line 79) and before the precipitation block:

```python
    # 濕度統計
    humidity_avg_mean: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    humidity_avg_stddev: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
```

- [ ] **Step 2: Update analytics engine to return humidity stats**

In `backend/app/analytics/engine.py`, find `HistoricalWeatherAnalyzer.get_date_range_stats` (~line 313 where humidity is already computed) — verify it returns `compute_basic_stats(window_data["humidity_avg"])` under key `"humidity"`. If yes, no change. If no, add it:

```python
        if "humidity_avg" in window_data.columns:
            result["humidity"] = compute_basic_stats(window_data["humidity_avg"])
```

- [ ] **Step 3: Populate humidity in `compute_snapshots.py`**

In `data-pipeline/compute_snapshots.py:131` (after the temperature stats block, before the precipitation block):

```python
        # 濕度統計
        if "humidity" in stats:
            humidity = stats["humidity"]
            record.humidity_avg_mean = humidity.get("mean")
            record.humidity_avg_stddev = humidity.get("std_dev")
```

- [ ] **Step 4: Apply schema change locally**

SQLite has limited ALTER. Easiest: drop and recompute via existing rerun script, since `Base.metadata.create_all` adds new columns through SQLAlchemy on next session creation? No — SQLAlchemy `create_all` does NOT alter existing tables. Use raw SQL:

```bash
sqlite3 /Users/tomwang/Codes/Auspicious/data/auspicious.db <<'SQL'
ALTER TABLE daily_statistics ADD COLUMN humidity_avg_mean FLOAT;
ALTER TABLE daily_statistics ADD COLUMN humidity_avg_stddev FLOAT;
SQL
```

- [ ] **Step 5: Recompute snapshots for all stations**

```bash
cd /Users/tomwang/Codes/Auspicious/data-pipeline
/Users/tomwang/Library/Caches/pypoetry/virtualenvs/auspicious-backend-i0N10exc-py3.11/bin/python3 rerun_after_fix.py
```

Expected: each station re-saves 366 rows.

- [ ] **Step 6: Verify humidity populated**

```bash
sqlite3 /Users/tomwang/Codes/Auspicious/data/auspicious.db \
  "SELECT station_id, month_day, ROUND(humidity_avg_mean,1) FROM daily_statistics WHERE station_id='466920' AND month_day='06-15';"
```

Expected: non-null humidity value (~80 for Taipei mid-June).

- [ ] **Step 7: Commit**

```bash
git add backend/app/models/statistics.py data-pipeline/compute_snapshots.py backend/app/analytics/engine.py
git commit -m "feat(stats): persist humidity_avg in daily_statistics for upcoming day-insight"
```

---

## Phase 1: DayInsightCard Backend

### Task 1: Pydantic schemas

**Files:**
- Create: `backend/app/schemas/day_insight.py`

- [ ] **Step 1: Write failing import-shape test**

Create `backend/tests/test_day_insight_schemas.py`:

```python
def test_day_insight_round_trip():
    from app.schemas.day_insight import (
        DayInsight, LabelInfo, CoreMetric, SideBadge, ExtremeRecord, Extremes, InsightMeta,
    )
    payload = DayInsight(
        station_id="466920", month=6, day=15,
        label=LabelInfo(text="典型梅雨日", category="seasonal"),
        core=CoreMetric(metric="precip_probability", value=0.52,
                        anomaly_year=0.08, anomaly_month=0.02),
        side_badges=[SideBadge(metric="temp_avg", label="氣溫比同月偏低 -2.0°C",
                               direction="below", z_score=-1.2)],
        extremes=Extremes(wettest=ExtremeRecord(year=2009, value=85.0),
                          driest=ExtremeRecord(year=2002, value=0.0)),
        meta=InsightMeta(years_analyzed=36, start_year=1991, end_year=2026),
    )
    assert payload.model_dump()["core"]["value"] == 0.52
```

- [ ] **Step 2: Run test, expect ImportError**

```bash
cd backend && poetry run pytest tests/test_day_insight_schemas.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'app.schemas.day_insight'`

- [ ] **Step 3: Implement schema module**

Create `backend/app/schemas/day_insight.py`:

```python
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
```

- [ ] **Step 4: Run test, expect PASS**

```bash
cd backend && poetry run pytest tests/test_day_insight_schemas.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas/day_insight.py backend/tests/test_day_insight_schemas.py
git commit -m "feat(schemas): add DayInsight pydantic models"
```

---

### Task 2: Anomaly computation service

**Files:**
- Create: `backend/app/services/day_insight/__init__.py` (empty)
- Create: `backend/app/services/day_insight/compute.py`
- Create: `backend/tests/test_day_insight_compute.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_day_insight_compute.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.models.statistics import DailyStatistics
from app.services.day_insight.compute import compute_anomaly


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)

    # Seed: 6 月 15 日 = 0.6, 6 月平均 = 0.5, 全年均 = 0.4
    rows = [
        DailyStatistics(station_id="X", month_day="06-15", precip_probability=0.6,
                        years_analyzed=10, start_year=2010, end_year=2019),
        DailyStatistics(station_id="X", month_day="06-01", precip_probability=0.5,
                        years_analyzed=10, start_year=2010, end_year=2019),
        DailyStatistics(station_id="X", month_day="06-30", precip_probability=0.4,
                        years_analyzed=10, start_year=2010, end_year=2019),
        DailyStatistics(station_id="X", month_day="01-01", precip_probability=0.2,
                        years_analyzed=10, start_year=2010, end_year=2019),
    ]
    session.add_all(rows)
    session.commit()
    yield session
    session.close()


def test_compute_anomaly_returns_dual_baseline(db):
    result = compute_anomaly(db, station_id="X", month=6, day=15)
    assert result is not None
    assert result["value"] == pytest.approx(0.6)
    # year mean over 4 rows = (0.6+0.5+0.4+0.2)/4 = 0.425
    assert result["anomaly_year"] == pytest.approx(0.6 - 0.425)
    # month mean over 3 rows = (0.6+0.5+0.4)/3 = 0.5
    assert result["anomaly_month"] == pytest.approx(0.6 - 0.5)


def test_compute_anomaly_returns_none_when_missing(db):
    assert compute_anomaly(db, station_id="X", month=12, day=25) is None
```

- [ ] **Step 2: Run test, expect ImportError fail**

```bash
cd backend && poetry run pytest tests/test_day_insight_compute.py -v
```

- [ ] **Step 3: Implement**

```python
# backend/app/services/day_insight/compute.py
from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.statistics import DailyStatistics


def compute_anomaly(db: Session, station_id: str, month: int, day: int) -> Optional[dict]:
    """Return value + anomaly vs year mean and month mean. None if no row."""
    month_day = f"{month:02d}-{day:02d}"

    day_stat = db.query(DailyStatistics).filter_by(
        station_id=station_id, month_day=month_day
    ).first()
    if day_stat is None or day_stat.precip_probability is None:
        return None

    year_mean = db.query(func.avg(DailyStatistics.precip_probability)) \
        .filter(DailyStatistics.station_id == station_id) \
        .scalar()

    month_pattern = f"{month:02d}-%"
    month_mean = db.query(func.avg(DailyStatistics.precip_probability)) \
        .filter(DailyStatistics.station_id == station_id) \
        .filter(DailyStatistics.month_day.like(month_pattern)) \
        .scalar()

    return {
        "value": float(day_stat.precip_probability),
        "anomaly_year": float(day_stat.precip_probability - year_mean),
        "anomaly_month": float(day_stat.precip_probability - month_mean),
        "_day_stat": day_stat,  # internal use for downstream services
    }
```

Also create empty `backend/app/services/day_insight/__init__.py`.

- [ ] **Step 4: Run test, expect PASS**

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/day_insight/ backend/tests/test_day_insight_compute.py
git commit -m "feat(day-insight): add dual-baseline anomaly computation"
```

---

### Task 3: Side-badge computation

**Files:**
- Create: `backend/app/services/day_insight/side_badges.py`
- Create: `backend/tests/test_day_insight_side_badges.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_day_insight_side_badges.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.models.statistics import DailyStatistics
from app.services.day_insight.side_badges import compute_side_badges


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    # 6 月 4 個日期，溫度 25/26/27/30，6/15 = 30 (異常高)
    rows = [
        DailyStatistics(station_id="X", month_day="06-01", temp_avg_mean=25.0,
                        years_analyzed=1, start_year=2020, end_year=2020),
        DailyStatistics(station_id="X", month_day="06-08", temp_avg_mean=26.0,
                        years_analyzed=1, start_year=2020, end_year=2020),
        DailyStatistics(station_id="X", month_day="06-22", temp_avg_mean=27.0,
                        years_analyzed=1, start_year=2020, end_year=2020),
        DailyStatistics(station_id="X", month_day="06-15", temp_avg_mean=30.0,
                        years_analyzed=1, start_year=2020, end_year=2020),
    ]
    session.add_all(rows)
    session.commit()
    yield session
    session.close()


def test_temperature_z_above_threshold_emits_badge(db):
    day = db.query(DailyStatistics).filter_by(station_id="X", month_day="06-15").first()
    badges = compute_side_badges(db, station_id="X", month=6, day_stat=day)
    assert len(badges) == 1
    badge = badges[0]
    assert badge["metric"] == "temp_avg"
    assert badge["direction"] == "above"
    assert badge["z_score"] > 1.0
    assert "偏高" in badge["label"]


def test_temperature_within_threshold_no_badge(db):
    day = db.query(DailyStatistics).filter_by(station_id="X", month_day="06-08").first()
    badges = compute_side_badges(db, station_id="X", month=6, day_stat=day)
    assert badges == []
```

- [ ] **Step 2: Run test, expect ImportError**

- [ ] **Step 3: Implement**

```python
# backend/app/services/day_insight/side_badges.py
import statistics as stats_mod
from typing import Iterable

from sqlalchemy.orm import Session

from app.models.statistics import DailyStatistics

Z_THRESHOLD = 1.0


def _compute_one_dim(values: list[float], current: float, metric: str, unit: str) -> dict | None:
    if len(values) < 2:
        return None
    mean = stats_mod.mean(values)
    stdev = stats_mod.stdev(values)
    if stdev == 0:
        return None
    z = (current - mean) / stdev
    if abs(z) < Z_THRESHOLD:
        return None
    delta = current - mean
    direction = "above" if z > 0 else "below"
    label_word = "偏高" if z > 0 else "偏低"
    if metric == "temp_avg":
        label = f"氣溫比同月{label_word} {delta:+.1f}{unit}"
    else:
        label = f"濕度比同月{label_word} {delta:+.1f}{unit}"
    return {"metric": metric, "label": label, "direction": direction, "z_score": z}


def _month_values(db: Session, station_id: str, month: int, attr: str) -> list[float]:
    rows = db.query(DailyStatistics).filter(
        DailyStatistics.station_id == station_id,
        DailyStatistics.month_day.like(f"{month:02d}-%"),
    ).all()
    return [getattr(r, attr) for r in rows if getattr(r, attr) is not None]


def compute_side_badges(db: Session, station_id: str, month: int, day_stat: DailyStatistics) -> list[dict]:
    badges: list[dict] = []

    if day_stat.temp_avg_mean is not None:
        b = _compute_one_dim(
            _month_values(db, station_id, month, "temp_avg_mean"),
            day_stat.temp_avg_mean, "temp_avg", "°C",
        )
        if b: badges.append(b)

    if day_stat.humidity_avg_mean is not None:
        b = _compute_one_dim(
            _month_values(db, station_id, month, "humidity_avg_mean"),
            day_stat.humidity_avg_mean, "humidity_avg", "%",
        )
        if b: badges.append(b)

    badges.sort(key=lambda b: -abs(b["z_score"]))
    return badges[:2]
```

- [ ] **Step 4: Run test, expect PASS**

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/day_insight/side_badges.py backend/tests/test_day_insight_side_badges.py
git commit -m "feat(day-insight): emit z-score driven side badges"
```

---

### Task 4: Extremes lookup

**Files:**
- Create: `backend/app/services/day_insight/extremes.py`
- Create: `backend/tests/test_day_insight_extremes.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_day_insight_extremes.py
from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.models.observation import RawObservation
from app.services.day_insight.extremes import compute_extremes


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    rows = [
        RawObservation(station_id="X", observed_date=date(2009, 6, 15), precipitation=85.0),
        RawObservation(station_id="X", observed_date=date(2002, 6, 15), precipitation=0.0),
        RawObservation(station_id="X", observed_date=date(2018, 6, 15), precipitation=5.0),
        RawObservation(station_id="X", observed_date=date(1997, 6, 15), precipitation=None),
    ]
    session.add_all(rows)
    session.commit()
    yield session
    session.close()


def test_extremes_picks_max_and_min_skipping_null(db):
    result = compute_extremes(db, station_id="X", month=6, day=15)
    assert result["wettest"]["year"] == 2009
    assert result["wettest"]["value"] == 85.0
    assert result["driest"]["year"] == 2002
    assert result["driest"]["value"] == 0.0
```

- [ ] **Step 2: Run test, expect ImportError**

- [ ] **Step 3: Implement**

```python
# backend/app/services/day_insight/extremes.py
from sqlalchemy import extract
from sqlalchemy.orm import Session

from app.models.observation import RawObservation


def compute_extremes(db: Session, station_id: str, month: int, day: int) -> dict:
    rows = db.query(RawObservation).filter(
        RawObservation.station_id == station_id,
        extract("month", RawObservation.observed_date) == month,
        extract("day", RawObservation.observed_date) == day,
        RawObservation.precipitation.isnot(None),
    ).all()

    if not rows:
        return {"wettest": None, "driest": None}

    wettest = max(rows, key=lambda r: r.precipitation)
    # tie-break for driest: smallest precipitation, then most recent year
    driest = min(rows, key=lambda r: (r.precipitation, -r.observed_date.year))

    return {
        "wettest": {"year": wettest.observed_date.year, "value": float(wettest.precipitation)},
        "driest": {"year": driest.observed_date.year, "value": float(driest.precipitation)},
    }
```

- [ ] **Step 4: Run test, expect PASS**

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/day_insight/extremes.py backend/tests/test_day_insight_extremes.py
git commit -m "feat(day-insight): compute wettest/driest extremes from raw observations"
```

---

### Task 5: Label rules

**Files:**
- Create: `backend/app/services/day_insight/label_rules.py`
- Create: `backend/tests/test_day_insight_label_rules.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_day_insight_label_rules.py
from app.services.day_insight.label_rules import match_label


def _ctx(**kwargs):
    base = {
        "month": 6, "day": 15,
        "precip_probability": 0.52,
        "anomaly_year": 0.08, "anomaly_month": 0.02,
        "temp_z": 0.5, "precip_z_in_month": 0.5,
        "is_solar_term_day": False,
        "is_north_station": False,
    }
    base.update(kwargs)
    return base


def test_typical_meiyu():
    label = match_label(_ctx(month=6, day=15, precip_probability=0.55))
    assert label["text"] == "典型梅雨日"
    assert label["category"] == "seasonal"


def test_anomaly_dry():
    label = match_label(_ctx(anomaly_month=-0.20))
    assert label["text"] == "異常乾旱期"
    assert label["category"] == "anomaly"


def test_no_match_returns_null():
    label = match_label(_ctx())
    assert label["text"] is None
    assert label["category"] is None


def test_record_overrides_anomaly():
    # 紀錄級多雨優先於 異常多雨期
    label = match_label(_ctx(anomaly_month=+0.20, precip_z_in_month=2.5))
    assert label["text"] == "紀錄級多雨"
```

- [ ] **Step 2: Run test, expect ImportError**

- [ ] **Step 3: Implement**

```python
# backend/app/services/day_insight/label_rules.py
"""Rule-based personality labels for DayInsightCard.

Priority: record > anomaly > solar_term > seasonal. First match wins.
"""

NORTH_STATION_IDS = {"466900", "466920", "466940", "466910", "466930", "466950"}


def match_label(ctx: dict) -> dict:
    m = ctx["month"]
    p = ctx["precip_probability"]
    am = ctx["anomaly_month"]
    tz = ctx["temp_z"]
    pz = ctx["precip_z_in_month"]

    # 紀錄級
    if pz >= 1.96:
        return {"text": "紀錄級多雨", "category": "record"}
    if tz >= 1.96:
        return {"text": "紀錄級高溫", "category": "record"}

    # 異常
    if am >= 0.15:
        return {"text": "異常多雨期", "category": "anomaly"}
    if am <= -0.15:
        return {"text": "異常乾旱期", "category": "anomaly"}
    if tz >= 1.5:
        return {"text": "異常高溫", "category": "anomaly"}
    if tz <= -1.5:
        return {"text": "寒流警報", "category": "anomaly"}

    # 節氣轉換點
    if ctx["is_solar_term_day"]:
        return {"text": "節氣轉換點", "category": "solar_term"}

    # 季節典型
    if m in (5, 6) and p >= 0.50:
        return {"text": "典型梅雨日", "category": "seasonal"}
    if m in (7, 8) and p >= 0.45 and tz >= 1:
        return {"text": "盛夏雷雨日", "category": "seasonal"}
    if m in (12, 1, 2) and tz <= -1:
        return {"text": "冬季冷氣團", "category": "seasonal"}
    if m in (9, 10) and ctx["precip_z_in_month"] <= -1:
        return {"text": "秋高氣爽", "category": "seasonal"}
    if m in (10, 11) and ctx["is_north_station"]:
        return {"text": "東北季風前緣", "category": "seasonal"}

    return {"text": None, "category": None}


def is_north_station(station_id: str) -> bool:
    return station_id in NORTH_STATION_IDS
```

- [ ] **Step 4: Run test, expect PASS**

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/day_insight/label_rules.py backend/tests/test_day_insight_label_rules.py
git commit -m "feat(day-insight): add rule-based personality label matcher"
```

---

### Task 6: Day-insight composer + endpoint

**Files:**
- Create: `backend/app/services/day_insight/service.py`
- Create: `backend/app/api/v1/day_insight.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_day_insight_api.py`

- [ ] **Step 1: Write failing API test using existing test DB fixture**

Look at `backend/tests/conftest.py` for the existing app/db test fixtures. Use them.

```python
# backend/tests/test_day_insight_api.py
def test_day_insight_taipei_06_15(client):  # existing fixture from conftest
    resp = client.get("/api/v1/day-insight/466920/6/15")
    assert resp.status_code == 200
    body = resp.json()
    assert body["station_id"] == "466920"
    assert body["core"]["metric"] == "precip_probability"
    assert 0 <= body["core"]["value"] <= 1
    assert "anomaly_year" in body["core"]
    assert "anomaly_month" in body["core"]
    assert body["meta"]["years_analyzed"] >= 30
    assert "wettest" in body["extremes"]


def test_day_insight_404_unknown_station(client):
    resp = client.get("/api/v1/day-insight/999999/6/15")
    assert resp.status_code == 404


def test_day_insight_404_invalid_month_day(client):
    resp = client.get("/api/v1/day-insight/466920/13/40")
    assert resp.status_code in (400, 422)
```

- [ ] **Step 2: Run test, expect 404 (route not registered)**

- [ ] **Step 3: Implement composer**

```python
# backend/app/services/day_insight/service.py
from sqlalchemy.orm import Session

from app.models.statistics import DailyStatistics
from app.schemas.day_insight import (
    CoreMetric, DayInsight, ExtremeRecord, Extremes, InsightMeta, LabelInfo, SideBadge,
)
from app.services.day_insight.compute import compute_anomaly
from app.services.day_insight.extremes import compute_extremes
from app.services.day_insight.label_rules import is_north_station, match_label
from app.services.day_insight.side_badges import compute_side_badges


def build_day_insight(db: Session, station_id: str, month: int, day: int) -> DayInsight | None:
    anomaly = compute_anomaly(db, station_id, month, day)
    if anomaly is None:
        return None
    day_stat: DailyStatistics = anomaly["_day_stat"]

    badges = compute_side_badges(db, station_id, month, day_stat)

    extremes = compute_extremes(db, station_id, month, day)

    # Compute precip z-score within month for "紀錄級多雨" rule
    import statistics as stats_mod
    month_precip = [
        r.precip_probability for r in db.query(DailyStatistics).filter(
            DailyStatistics.station_id == station_id,
            DailyStatistics.month_day.like(f"{month:02d}-%"),
        ).all() if r.precip_probability is not None
    ]
    if len(month_precip) >= 2:
        m_mean = stats_mod.mean(month_precip)
        m_std = stats_mod.stdev(month_precip)
        precip_z_in_month = (day_stat.precip_probability - m_mean) / m_std if m_std else 0.0
    else:
        precip_z_in_month = 0.0

    temp_z = next((b["z_score"] for b in badges if b["metric"] == "temp_avg"), 0.0)

    label = match_label({
        "month": month, "day": day,
        "precip_probability": day_stat.precip_probability,
        "anomaly_year": anomaly["anomaly_year"], "anomaly_month": anomaly["anomaly_month"],
        "temp_z": temp_z, "precip_z_in_month": precip_z_in_month,
        "is_solar_term_day": False,  # TODO: integrate with solar_term service in P3
        "is_north_station": is_north_station(station_id),
    })

    return DayInsight(
        station_id=station_id, month=month, day=day,
        label=LabelInfo(**label),
        core=CoreMetric(metric="precip_probability",
                        value=anomaly["value"],
                        anomaly_year=anomaly["anomaly_year"],
                        anomaly_month=anomaly["anomaly_month"]),
        side_badges=[SideBadge(**b) for b in badges],
        extremes=Extremes(
            wettest=ExtremeRecord(**extremes["wettest"]) if extremes["wettest"] else None,
            driest=ExtremeRecord(**extremes["driest"]) if extremes["driest"] else None,
        ),
        meta=InsightMeta(
            years_analyzed=day_stat.years_analyzed or 0,
            start_year=day_stat.start_year or 0,
            end_year=day_stat.end_year or 0,
        ),
    )
```

- [ ] **Step 4: Implement endpoint**

```python
# backend/app/api/v1/day_insight.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.day_insight import DayInsight
from app.services.day_insight.service import build_day_insight

router = APIRouter()


@router.get("/{station_id}/{month}/{day}", response_model=DayInsight)
def get_day_insight(station_id: str, month: int, day: int, db: Session = Depends(get_db)):
    if not (1 <= month <= 12) or not (1 <= day <= 31):
        raise HTTPException(status_code=400, detail="Invalid month or day")
    insight = build_day_insight(db, station_id, month, day)
    if insight is None:
        raise HTTPException(status_code=404, detail="No data for this station/date")
    return insight
```

- [ ] **Step 5: Register router in `backend/app/main.py`**

After the existing `app.include_router(daily_report.router, ...)` block:

```python
from app.api.v1 import day_insight
app.include_router(day_insight.router, prefix="/api/v1/day-insight", tags=["day-insight"])
```

- [ ] **Step 6: Run tests, expect PASS**

```bash
cd backend && poetry run pytest tests/test_day_insight_api.py -v
```

- [ ] **Step 7: Manual smoke test**

```bash
poetry run uvicorn app.main:app --reload &
sleep 2
curl -sS http://localhost:8000/api/v1/day-insight/466920/6/15 | python3 -m json.tool
kill %1
```

Expected: full JSON with label, core (with anomalies), side_badges, extremes.

- [ ] **Step 8: Commit**

```bash
git add backend/app/services/day_insight/service.py backend/app/api/v1/day_insight.py \
        backend/app/main.py backend/tests/test_day_insight_api.py
git commit -m "feat(api): add /api/v1/day-insight/{station}/{month}/{day} endpoint"
```

---

## Phase 2: DayInsightCard Frontend

### Task 7: Frontend types + API client

**Files:**
- Modify: `frontend/src/lib/types.ts`
- Modify: `frontend/src/lib/api.ts`

- [ ] **Step 1: Add types**

In `frontend/src/lib/types.ts`, append:

```typescript
export interface DayInsightLabel {
  text: string | null;
  category: "seasonal" | "anomaly" | "record" | "solar_term" | null;
}

export interface DayInsightCore {
  metric: "precip_probability";
  value: number;
  anomaly_year: number;
  anomaly_month: number;
}

export interface DayInsightSideBadge {
  metric: "temp_avg" | "humidity_avg";
  label: string;
  direction: "above" | "below";
  z_score: number;
}

export interface DayInsightExtremeRecord {
  year: number;
  value: number;
}

export interface DayInsightExtremes {
  wettest: DayInsightExtremeRecord | null;
  driest: DayInsightExtremeRecord | null;
}

export interface DayInsightMeta {
  years_analyzed: number;
  start_year: number;
  end_year: number;
}

export interface DayInsight {
  station_id: string;
  month: number;
  day: number;
  label: DayInsightLabel;
  core: DayInsightCore;
  side_badges: DayInsightSideBadge[];
  extremes: DayInsightExtremes;
  meta: DayInsightMeta;
}
```

- [ ] **Step 2: Add API client function**

In `frontend/src/lib/api.ts`, append:

```typescript
import type { DayInsight } from "./types";

export const fetchDayInsight = async (
  stationId: string, month: number, day: number,
): Promise<DayInsight> => {
  const res = await fetch(`${API_BASE}/api/v1/day-insight/${stationId}/${month}/${day}`);
  if (!res.ok) throw new Error(`day-insight ${res.status}`);
  return res.json();
};
```

(`API_BASE` should already be defined at the top of the file. If not, use `process.env.NEXT_PUBLIC_API_URL`.)

- [ ] **Step 3: Type-check**

```bash
cd frontend && pnpm exec tsc --noEmit
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/lib/types.ts frontend/src/lib/api.ts
git commit -m "feat(frontend): add DayInsight types and api client"
```

---

### Task 8: Sub-components (LabelBadge / CoreMetric / SideBadges / ExtremesAnchor)

**Files:**
- Create: `frontend/src/components/DayInsightCard/LabelBadge.tsx`
- Create: `frontend/src/components/DayInsightCard/CoreMetric.tsx`
- Create: `frontend/src/components/DayInsightCard/SideBadges.tsx`
- Create: `frontend/src/components/DayInsightCard/ExtremesAnchor.tsx`

- [ ] **Step 1: LabelBadge**

```tsx
// frontend/src/components/DayInsightCard/LabelBadge.tsx
import type { DayInsightLabel } from "@/lib/types";

const COLOR: Record<NonNullable<DayInsightLabel["category"]>, string> = {
  seasonal: "bg-emerald-100 text-emerald-800",
  anomaly: "bg-amber-100 text-amber-800",
  record: "bg-rose-100 text-rose-800",
  solar_term: "bg-sky-100 text-sky-800",
};

export function LabelBadge({ label }: { label: DayInsightLabel }) {
  if (!label.text || !label.category) return null;
  return (
    <div className={`inline-block rounded-full px-3 py-1 text-sm font-medium ${COLOR[label.category]}`}>
      {label.text}
    </div>
  );
}
```

- [ ] **Step 2: CoreMetric**

```tsx
// frontend/src/components/DayInsightCard/CoreMetric.tsx
import type { DayInsightCore } from "@/lib/types";

export function CoreMetric({ core }: { core: DayInsightCore }) {
  const pct = (core.value * 100).toFixed(0);
  const yearPct = (core.anomaly_year * 100).toFixed(1);
  const monthPct = (core.anomaly_month * 100).toFixed(1);
  const yearArrow = core.anomaly_year > 0.01 ? "↑" : core.anomaly_year < -0.01 ? "↓" : "";
  const yearColor = core.anomaly_year > 0.01 ? "text-rose-600"
                  : core.anomaly_year < -0.01 ? "text-sky-600" : "text-slate-500";

  return (
    <div>
      <div className="text-sm text-slate-500">降雨機率</div>
      <div className="text-4xl font-bold tabular-nums">{pct}%</div>
      <div className="mt-1 text-sm">
        <span className={yearColor}>
          {yearArrow}{Math.abs(core.anomaly_year * 100).toFixed(1)}% vs 年均
        </span>
        <span className="mx-2 text-slate-300">│</span>
        <span className="text-slate-600">
          {core.anomaly_month >= 0 ? "+" : ""}{monthPct}% vs 同月
        </span>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: SideBadges**

```tsx
// frontend/src/components/DayInsightCard/SideBadges.tsx
import type { DayInsightSideBadge } from "@/lib/types";

export function SideBadges({ badges }: { badges: DayInsightSideBadge[] }) {
  if (badges.length === 0) return null;
  return (
    <div className="mt-2 flex flex-wrap gap-2">
      {badges.map((b) => (
        <span
          key={b.metric}
          className={`inline-flex items-center rounded px-2 py-0.5 text-xs ${
            b.direction === "above" ? "bg-rose-50 text-rose-700" : "bg-sky-50 text-sky-700"
          }`}
        >
          ⚠️ {b.label}
        </span>
      ))}
    </div>
  );
}
```

- [ ] **Step 4: ExtremesAnchor**

```tsx
// frontend/src/components/DayInsightCard/ExtremesAnchor.tsx
import type { DayInsightExtremes } from "@/lib/types";

export function ExtremesAnchor({ extremes }: { extremes: DayInsightExtremes }) {
  if (!extremes.wettest && !extremes.driest) return null;
  return (
    <div className="text-xs text-slate-500 space-y-0.5">
      {extremes.wettest && (
        <div>最濕：{extremes.wettest.year} / {extremes.wettest.value.toFixed(1)} mm</div>
      )}
      {extremes.driest && (
        <div>最乾：{extremes.driest.year} / {extremes.driest.value.toFixed(1)} mm</div>
      )}
    </div>
  );
}
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/DayInsightCard/
git commit -m "feat(frontend): add DayInsight sub-components"
```

---

### Task 9: DayInsightCard composition (with drawer placeholder)

**Files:**
- Create: `frontend/src/components/DayInsightCard.tsx`

- [ ] **Step 1: Implement card with stub drawer**

```tsx
// frontend/src/components/DayInsightCard.tsx
"use client";

import { useState } from "react";
import { fetchDayInsight } from "@/lib/api";
import type { DayInsight } from "@/lib/types";
import { useEffect } from "react";

import { LabelBadge } from "./DayInsightCard/LabelBadge";
import { CoreMetric } from "./DayInsightCard/CoreMetric";
import { SideBadges } from "./DayInsightCard/SideBadges";
import { ExtremesAnchor } from "./DayInsightCard/ExtremesAnchor";

interface Props {
  stationId: string;
  month: number;
  day: number;
}

export function DayInsightCard({ stationId, month, day }: Props) {
  const [data, setData] = useState<DayInsight | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  useEffect(() => {
    fetchDayInsight(stationId, month, day)
      .then(setData)
      .catch((e) => setError(e.message));
  }, [stationId, month, day]);

  if (error) return <div className="rounded border p-4 text-sm text-rose-600">無歷史資料</div>;
  if (!data) return <div className="rounded border p-4 text-sm text-slate-400">載入中…</div>;

  return (
    <div className="rounded-lg border bg-white p-4 shadow-sm space-y-3">
      <LabelBadge label={data.label} />
      <CoreMetric core={data.core} />
      <SideBadges badges={data.side_badges} />
      <ExtremesAnchor extremes={data.extremes} />
      <button
        onClick={() => setDrawerOpen((o) => !o)}
        className="w-full rounded bg-slate-50 py-2 text-sm text-slate-600 hover:bg-slate-100"
      >
        {drawerOpen ? "收起詮釋 ▴" : "看詳細詮釋 ▾"}
      </button>
      {drawerOpen && (
        <div className="rounded bg-slate-50 p-3 text-sm text-slate-700">
          {/* TODO: divination drawer (Task 17) */}
          詳細詮釋載入中…（將於 Task 17 接上）
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Type-check**

```bash
cd frontend && pnpm exec tsc --noEmit
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/DayInsightCard.tsx
git commit -m "feat(frontend): compose DayInsightCard with drawer placeholder"
```

---

### Task 10: Integrate into `/planner` page

**Files:**
- Modify: `frontend/src/app/planner/page.tsx`

- [ ] **Step 1: Read existing planner page to find candidate-date list rendering**

```bash
cat frontend/src/app/planner/page.tsx | head -120
```

Locate the JSX block that maps candidate dates.

- [ ] **Step 2: Import and inject DayInsightCard**

Add at the top of the file:

```tsx
import { DayInsightCard } from "@/components/DayInsightCard";
```

Inside the candidate-date `.map(...)` block, after the existing card content:

```tsx
<DayInsightCard
  stationId={selectedStationId}
  month={candidate.month}
  day={candidate.day}
/>
```

(Adjust prop names to match the existing data shape — search for `month`/`day` in the file to find the right field names; if the candidate has only an ISO date string, parse it: `const [yyyy, mm, dd] = candidate.date.split("-")`.)

- [ ] **Step 3: Manual visual test**

```bash
cd frontend && pnpm dev
```

Open `http://localhost:3000/planner`, run a planning query, verify cards render with labels/numbers/extremes.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/app/planner/page.tsx
git commit -m "feat(planner): show DayInsightCard for each candidate date"
```

---

## Phase 3: Divination Backend

### Task 11: Hexagram TABLE + 64-hexagram database

**Files:**
- Create: `backend/app/services/divination/__init__.py` (empty)
- Create: `backend/app/services/divination/hexagram_table.py`
- Create: `backend/app/services/divination/hexagrams.py`
- Create: `backend/tests/test_hexagram_table.py`

- [ ] **Step 1: Copy TABLE from pi-mono with attribution**

```python
# backend/app/services/divination/hexagram_table.py
"""8x8 64-hexagram lookup. Attribution:
   moregatest/pi-mono iching_divination.py @ 271c9e3 (MIT License).
"""

# 八卦索引：坤0 艮1 坎2 巽3 震4 離5 兌6 乾7
TRIGRAM_NAMES = ["坤", "艮", "坎", "巽", "震", "離", "兌", "乾"]
TRIGRAM_SYMBOLS = ["☷", "☶", "☵", "☴", "☳", "☲", "☱", "☰"]
TRIGRAM_NATURE = ["地", "山", "水", "風", "雷", "火", "澤", "天"]

# TABLE[下卦][上卦] = 卦號（1-64）
TABLE = [
    [ 2, 23,  8, 20, 16, 35, 45, 12],   # 下=坤
    [15, 52, 39, 53, 62, 56, 31, 33],   # 下=艮
    [ 7,  4, 29, 59, 40, 64, 47,  6],   # 下=坎
    [46, 18, 48, 57, 32, 50, 28, 44],   # 下=巽
    [24, 27,  3, 42, 51, 21, 17, 25],   # 下=震
    [36, 22, 63, 37, 55, 30, 49, 13],   # 下=離
    [19, 41, 60, 61, 54, 38, 58, 10],   # 下=兌
    [11, 26,  5,  9, 34, 14, 43,  1],   # 下=乾
]


def validate_table() -> None:
    nums = [TABLE[r][c] for r in range(8) for c in range(8)]
    if sorted(nums) != list(range(1, 65)):
        raise RuntimeError("TABLE corrupted: not a complete 1..64 set")


validate_table()  # boot-time guard
```

- [ ] **Step 2: 64 卦資料庫初版**

```python
# backend/app/services/divination/hexagrams.py
"""64-hexagram metadata. judgement = 卦辭簡縮版（朱熹注公版）.
   Each entry: num, name, judgement (≤30字), image (大象傳簡縮 ≤30字).
"""

HEXAGRAMS: list[dict] = [
    {"num": 1,  "name": "乾為天",   "judgement": "元亨利貞",         "image": "天行健，君子以自強不息"},
    {"num": 2,  "name": "坤為地",   "judgement": "元亨利牝馬之貞", "image": "地勢坤，君子以厚德載物"},
    # ... (full 64 entries — see Step 3 fixture)
]


def get(num: int) -> dict:
    return HEXAGRAMS[num - 1]
```

- [ ] **Step 3: Populate the full 64 entries**

The plan defers writing all 64 卦辭 to in-task work. The implementer should:

1. Copy the 64 卦名 from `iching_divination.py` `HEXAGRAM_NAMES` (already in pi-mono fetch).
2. For each 卦, write a 卦辭 (≤30 字) and 大象 (≤30 字) drawing from public-domain sources (《周易本義》朱熹注 / 《彖傳》《大象傳》).
3. If unsure of phrasing for a particular 卦, leave `judgement: ""` and add a `# TODO` comment — these can be filled in later iterations without blocking the rest of the plan.

Reference template per entry:
```python
{"num": N, "name": "...", "judgement": "...", "image": "..."},
```

Acceptance: `len(HEXAGRAMS) == 64` and each `num` matches its index+1.

- [ ] **Step 4: Write validation test**

```python
# backend/tests/test_hexagram_table.py
from app.services.divination.hexagram_table import TABLE, validate_table
from app.services.divination.hexagrams import HEXAGRAMS, get


def test_table_is_complete():
    validate_table()


def test_all_64_hexagrams_present():
    assert len(HEXAGRAMS) == 64
    for i, h in enumerate(HEXAGRAMS, start=1):
        assert h["num"] == i, f"index {i} has wrong num"
        assert h["name"], f"hex {i} missing name"


def test_get_returns_correct_entry():
    assert get(1)["name"] == "乾為天"
    assert get(64)["name"] == "火水未濟"
```

- [ ] **Step 5: Run tests, expect PASS**

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/divination/ backend/tests/test_hexagram_table.py
git commit -m "feat(divination): add 64-hexagram TABLE and metadata (pi-mono attribution)"
```

---

### Task 12: Weather → 6 lines mapping

**Files:**
- Create: `backend/app/services/divination/line_mapping.py`
- Create: `backend/tests/test_line_mapping.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_line_mapping.py
from app.services.divination.line_mapping import lines_from_weather, line_value


def test_line_value_yang_changing():
    # deviation > 0 and |z| >= 1 → 老陽 = 9
    assert line_value(deviation=1.5, z_score=1.5) == 9


def test_line_value_yin_static():
    assert line_value(deviation=-0.1, z_score=-0.5) == 8


def test_lines_from_weather_basic():
    """
    Test fixture: a day where every dimension is positive vs both baselines,
    with humidity exceeding |z| >= 1.
    """
    ctx = {
        "day_temp_dev_vs_month": 0.5, "day_temp_z_vs_month": 0.5,
        "day_hum_dev_vs_month": 5,    "day_hum_z_vs_month": 1.5,
        "day_precip_dev_vs_month": 0.05, "day_precip_z_vs_month": 0.5,
        "month_temp_dev_vs_year": 2,  "month_temp_z_vs_year": 1.0,
        "month_hum_dev_vs_year": 3,   "month_hum_z_vs_year": 0.8,
        "month_precip_dev_vs_year": 0.05, "month_precip_z_vs_year": 0.6,
    }
    values = lines_from_weather(ctx)
    # Six values, ordered line 1 (bottom) to line 6 (top)
    assert len(values) == 6
    # Line 4 = day_temp (yang static)
    assert values[3] == 7
    # Line 5 = day_hum (yang changing)
    assert values[4] == 9
    # Line 1 = month_temp (yang changing)
    assert values[0] == 9
```

- [ ] **Step 2: Run test, expect ImportError**

- [ ] **Step 3: Implement**

```python
# backend/app/services/divination/line_mapping.py
"""Weather → 6 hexagram lines.
Lower trigram (lines 1-3) = month vs year.
Upper trigram (lines 4-6) = day vs month.
Each trigram in order [溫, 濕, 雨].
"""

Z_THRESHOLD = 1.0


def line_value(deviation: float, z_score: float) -> int:
    yang = deviation > 0
    changing = abs(z_score) >= Z_THRESHOLD
    if yang and changing:
        return 9   # 老陽
    if yang and not changing:
        return 7   # 少陽
    if not yang and changing:
        return 6   # 老陰
    return 8       # 少陰


def lines_from_weather(ctx: dict) -> list[int]:
    """Return 6 line values, line 1 (bottom) to line 6 (top)."""
    return [
        line_value(ctx["month_temp_dev_vs_year"],   ctx["month_temp_z_vs_year"]),
        line_value(ctx["month_hum_dev_vs_year"],    ctx["month_hum_z_vs_year"]),
        line_value(ctx["month_precip_dev_vs_year"], ctx["month_precip_z_vs_year"]),
        line_value(ctx["day_temp_dev_vs_month"],    ctx["day_temp_z_vs_month"]),
        line_value(ctx["day_hum_dev_vs_month"],     ctx["day_hum_z_vs_month"]),
        line_value(ctx["day_precip_dev_vs_month"],  ctx["day_precip_z_vs_month"]),
    ]


def lines_to_trigram(three_values: list[int]) -> int:
    """3 line values → trigram bits (yang=1 yin=0, line 1 = bit 0)."""
    bits = 0
    for i, v in enumerate(three_values):
        if v in (7, 9):  # yang
            bits |= (1 << i)
    return bits
```

- [ ] **Step 4: Run tests, expect PASS**

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/divination/line_mapping.py backend/tests/test_line_mapping.py
git commit -m "feat(divination): add deterministic weather-to-line mapping"
```

---

### Task 13: Four-methods calculation

**Files:**
- Create: `backend/app/services/divination/four_methods.py`
- Create: `backend/tests/test_four_methods.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_four_methods.py
from app.services.divination.four_methods import cast_hexagram


def test_six_static_yins_returns_kun():
    """全部少陰 (6 lines = 8) → 本卦=2 坤為地, 之卦=同, no changing."""
    result = cast_hexagram([8] * 6)
    assert result["ben_num"] == 2
    assert result["zhi_num"] == 2
    assert result["changing_positions"] == []


def test_six_static_yangs_returns_qian():
    result = cast_hexagram([7] * 6)
    assert result["ben_num"] == 1


def test_changing_line_changes_zhi():
    """5 少陰 + 1 老陽 at line 1 → 變後變少陰，之卦變化."""
    result = cast_hexagram([9, 8, 8, 8, 8, 8])
    assert result["ben_num"] != result["zhi_num"]
    assert result["changing_positions"] == [1]


def test_cuo_zong_hu_present():
    result = cast_hexagram([7, 8, 7, 8, 7, 8])
    for k in ("cuo_num", "zong_num", "hu_num"):
        assert 1 <= result[k] <= 64
```

- [ ] **Step 2: Run, expect ImportError**

- [ ] **Step 3: Implement (translates pi-mono `cast_hexagram` to take pre-computed line values)**

```python
# backend/app/services/divination/four_methods.py
"""Four-methods (本/錯/綜/互/之) calculation, adapted from pi-mono iching_divination.py.

Original (random toss) replaced by deterministic line values supplied by caller.
"""

from app.services.divination.hexagram_table import TABLE
from app.services.divination.line_mapping import lines_to_trigram


def _is_yang(value: int) -> bool:
    return value in (7, 9)


def _is_changing(value: int) -> bool:
    return value in (6, 9)


def cast_hexagram(values: list[int]) -> dict:
    assert len(values) == 6
    for v in values:
        if v not in (6, 7, 8, 9):
            raise ValueError(f"invalid line value: {v}")

    lower_bits = lines_to_trigram(values[0:3])
    upper_bits = lines_to_trigram(values[3:6])
    ben_num = TABLE[lower_bits][upper_bits]

    # 之卦：變爻取反
    changed = [(8 if _is_yang(v) else 7) if _is_changing(v) else v for v in values]
    zhi_num = TABLE[lines_to_trigram(changed[0:3])][lines_to_trigram(changed[3:6])]

    changing_positions = [i + 1 for i, v in enumerate(values) if _is_changing(v)]

    # 錯卦：陰陽全翻
    cuo_num = TABLE[lower_bits ^ 7][upper_bits ^ 7]

    # 綜卦：六爻倒序
    rev = values[::-1]
    zong_num = TABLE[lines_to_trigram(rev[0:3])][lines_to_trigram(rev[3:6])]

    # 互卦：lines[1:4] 為下卦, lines[2:5] 為上卦
    hu_num = TABLE[lines_to_trigram(values[1:4])][lines_to_trigram(values[2:5])]

    return {
        "values": values,
        "ben_num": ben_num,
        "zhi_num": zhi_num,
        "cuo_num": cuo_num,
        "zong_num": zong_num,
        "hu_num": hu_num,
        "changing_positions": changing_positions,
        "lower_bits": lower_bits,
        "upper_bits": upper_bits,
    }
```

- [ ] **Step 4: Run tests, expect PASS**

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/divination/four_methods.py backend/tests/test_four_methods.py
git commit -m "feat(divination): port four-methods (本/錯/綜/互/之) from pi-mono"
```

---

### Task 14: AI narrator (Gemini three-section)

**Files:**
- Create: `backend/app/services/divination/narrator.py`
- Modify: existing `backend/app/services/ai_engine.py` (only if a Gemini client helper isn't already exposed)
- Create: `backend/tests/test_divination_narrator.py`

- [ ] **Step 1: Inspect existing `ai_engine.py` to find the Gemini client function**

```bash
grep -n "def \|client\|GenerativeModel\|gemini" backend/app/services/ai_engine.py | head -30
```

Note the function used for one-shot text generation (likely something like `generate_text(prompt)` or direct `genai.GenerativeModel(...).generate_content`).

- [ ] **Step 2: Write narrator stub test (mocks Gemini)**

```python
# backend/tests/test_divination_narrator.py
from unittest.mock import patch

from app.services.divination.narrator import narrate


@patch("app.services.divination.narrator._call_gemini")
def test_narrate_returns_three_sections(mock_call):
    mock_call.return_value = """段一：氣候畫像示範文字。
段二：特殊度示範。
段三：想像層示範。"""

    result = narrate(
        station_name="台北", month=6, day=15,
        ben={"num": 35, "name": "火地晉"},
        zhi={"num": 8,  "name": "水地比"},
        cuo={"num": 5,  "name": "水天需"},
        zong={"num": 36, "name": "地火明夷"},
        hu={"num": 39,  "name": "水山蹇"},
        changing_positions=[6],
        anomalies={"temp_diff": 2.0, "humidity_diff": 5.0, "precip_diff_pct": 8.0},
        solar_term="芒種",
    )
    assert "climate_portrait" in result
    assert "anomaly_layer" in result
    assert "imagination" in result
    assert all(v.strip() for v in result.values())


@patch("app.services.divination.narrator._call_gemini")
def test_narrate_returns_fallback_on_exception(mock_call):
    mock_call.side_effect = RuntimeError("quota exceeded")
    result = narrate(
        station_name="台北", month=6, day=15,
        ben={"num": 1, "name": "乾為天"}, zhi={"num": 1, "name": "乾為天"},
        cuo={"num": 2, "name": "坤為地"}, zong={"num": 1, "name": "乾為天"},
        hu={"num": 1, "name": "乾為天"},
        changing_positions=[], anomalies={}, solar_term="夏至",
    )
    assert result["climate_portrait"] == ""
    assert result["anomaly_layer"] == ""
    assert result["imagination"] == ""
```

- [ ] **Step 3: Implement**

```python
# backend/app/services/divination/narrator.py
"""Three-section narrative for the divination drawer."""

from app.services.ai_engine import generate_text  # adjust import to match step 1 finding


PROMPT_TEMPLATE = """你是「好日子」app 的氣象詮釋師。請依下列卦象結果，用三段式繁體中文寫一份氣候洞察。

【日期】{station_name} {month}/{day}（節氣：{solar_term}）
【本卦】{ben_num}-{ben_name}
【互卦】{hu_num}-{hu_name}
【之卦】{zhi_num}-{zhi_name}（變爻：{changing_positions}）
【錯卦】{cuo_num}-{cuo_name}
【綜卦】{zong_num}-{zong_name}
【氣候資料】溫差={t_anom}°C 濕差={h_anom}% 雨機率差={p_anom}%

請輸出嚴格三段，格式如下（不要加其他文字）：

段一【氣候畫像】合論本卦+互卦，描寫這天的氣候本相，30-50 字
段二【特殊度】從變爻和之卦切入，描述異常維度與可能轉變，30-50 字
段三【想像層】用錯卦和綜卦延伸，給出反季節對立或半年後的對位想像，30-50 字

風格：古典文學語感、可入詩，不要硬塞卦辭原文。
"""


def _call_gemini(prompt: str) -> str:
    """Indirection so tests can patch this single call."""
    return generate_text(prompt)


def _parse_sections(text: str) -> dict:
    sections = {"climate_portrait": "", "anomaly_layer": "", "imagination": ""}
    keys = ["climate_portrait", "anomaly_layer", "imagination"]
    parts = [p.strip() for p in text.replace("段一", "§§§段一").replace("段二", "§§§段二").replace("段三", "§§§段三").split("§§§") if p.strip()]
    for i, part in enumerate(parts[-3:]):  # take last three to skip preamble
        sections[keys[i]] = part
    return sections


def narrate(*, station_name, month, day, ben, zhi, cuo, zong, hu,
            changing_positions, anomalies, solar_term) -> dict:
    prompt = PROMPT_TEMPLATE.format(
        station_name=station_name, month=month, day=day, solar_term=solar_term or "—",
        ben_num=ben["num"], ben_name=ben["name"],
        zhi_num=zhi["num"], zhi_name=zhi["name"],
        cuo_num=cuo["num"], cuo_name=cuo["name"],
        zong_num=zong["num"], zong_name=zong["name"],
        hu_num=hu["num"], hu_name=hu["name"],
        changing_positions=changing_positions or "無",
        t_anom=anomalies.get("temp_diff", 0),
        h_anom=anomalies.get("humidity_diff", 0),
        p_anom=anomalies.get("precip_diff_pct", 0),
    )
    try:
        raw = _call_gemini(prompt)
    except Exception:
        return {"climate_portrait": "", "anomaly_layer": "", "imagination": ""}
    return _parse_sections(raw)
```

> If `app.services.ai_engine` does not expose a top-level `generate_text(prompt)` helper, add one as a thin wrapper around its Gemini client in this same task.

- [ ] **Step 4: Run tests, expect PASS**

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/divination/narrator.py backend/tests/test_divination_narrator.py
git commit -m "feat(divination): add Gemini three-section narrator with fallback"
```

---

### Task 15: Interpretation endpoint

**Files:**
- Modify: `backend/app/schemas/day_insight.py` (add `Interpretation` schema)
- Modify: `backend/app/api/v1/day_insight.py` (add `/interpretation` route)
- Create: `backend/app/services/divination/service.py`

- [ ] **Step 1: Extend schema**

In `backend/app/schemas/day_insight.py`, append:

```python
class HexagramRef(BaseModel):
    num: int
    name: str
    judgement: Optional[str] = None
    image: Optional[str] = None
    upper_trigram: Optional[str] = None  # e.g. "離"
    lower_trigram: Optional[str] = None


class Narrative(BaseModel):
    climate_portrait: str
    anomaly_layer: str
    imagination: str


class Divination(BaseModel):
    ben: HexagramRef
    zhi: HexagramRef
    cuo: HexagramRef
    zong: HexagramRef
    hu: HexagramRef
    changing_positions: list[int]
    line_values: list[int]
    narrative: Narrative


class DayInsightInterpretation(BaseModel):
    station_id: str
    month: int
    day: int
    divination: Divination
```

- [ ] **Step 2: Implement composer**

```python
# backend/app/services/divination/service.py
from sqlalchemy.orm import Session
import statistics as stats_mod

from app.models.statistics import DailyStatistics
from app.services.divination.four_methods import cast_hexagram
from app.services.divination.hexagram_table import TRIGRAM_NAMES
from app.services.divination.hexagrams import get as get_hex
from app.services.divination.line_mapping import lines_from_weather, lines_to_trigram
from app.services.divination.narrator import narrate


def _stat_dist(values: list[float]):
    if len(values) < 2:
        return None, None
    return stats_mod.mean(values), stats_mod.stdev(values) or None


def _all(db, station_id: str) -> list[DailyStatistics]:
    return db.query(DailyStatistics).filter_by(station_id=station_id).all()


def build_interpretation(db: Session, station_id: str, month: int, day: int,
                          station_name: str = "", solar_term: str | None = None) -> dict | None:
    month_day = f"{month:02d}-{day:02d}"
    day_stat = db.query(DailyStatistics).filter_by(station_id=station_id, month_day=month_day).first()
    if not day_stat:
        return None

    rows = _all(db, station_id)
    if not rows:
        return None
    month_rows = [r for r in rows if r.month_day.startswith(f"{month:02d}-")]

    # Year baselines
    year_temp_mean,   year_temp_std   = _stat_dist([r.temp_avg_mean   for r in rows if r.temp_avg_mean   is not None])
    year_hum_mean,    year_hum_std    = _stat_dist([r.humidity_avg_mean for r in rows if r.humidity_avg_mean is not None])
    year_precip_mean, year_precip_std = _stat_dist([r.precip_probability for r in rows if r.precip_probability is not None])

    # Month baselines
    m_temp_mean,   m_temp_std   = _stat_dist([r.temp_avg_mean   for r in month_rows if r.temp_avg_mean   is not None])
    m_hum_mean,    m_hum_std    = _stat_dist([r.humidity_avg_mean for r in month_rows if r.humidity_avg_mean is not None])
    m_precip_mean, m_precip_std = _stat_dist([r.precip_probability for r in month_rows if r.precip_probability is not None])

    def dev_z(v, mean, std):
        if v is None or mean is None or not std:
            return 0.0, 0.0
        return v - mean, (v - mean) / std

    # Month vs year (lower trigram)
    m_temp_dev,   m_temp_z   = dev_z(m_temp_mean,   year_temp_mean,   year_temp_std)
    m_hum_dev,    m_hum_z    = dev_z(m_hum_mean,    year_hum_mean,    year_hum_std)
    m_precip_dev, m_precip_z = dev_z(m_precip_mean, year_precip_mean, year_precip_std)

    # Day vs month (upper trigram)
    d_temp_dev,   d_temp_z   = dev_z(day_stat.temp_avg_mean,   m_temp_mean,   m_temp_std)
    d_hum_dev,    d_hum_z    = dev_z(day_stat.humidity_avg_mean, m_hum_mean,  m_hum_std)
    d_precip_dev, d_precip_z = dev_z(day_stat.precip_probability, m_precip_mean, m_precip_std)

    line_values = lines_from_weather({
        "month_temp_dev_vs_year": m_temp_dev,     "month_temp_z_vs_year": m_temp_z,
        "month_hum_dev_vs_year": m_hum_dev,       "month_hum_z_vs_year": m_hum_z,
        "month_precip_dev_vs_year": m_precip_dev, "month_precip_z_vs_year": m_precip_z,
        "day_temp_dev_vs_month": d_temp_dev,      "day_temp_z_vs_month": d_temp_z,
        "day_hum_dev_vs_month": d_hum_dev,        "day_hum_z_vs_month": d_hum_z,
        "day_precip_dev_vs_month": d_precip_dev,  "day_precip_z_vs_month": d_precip_z,
    })

    cast = cast_hexagram(line_values)

    def hex_ref(num: int) -> dict:
        meta = get_hex(num)
        return {"num": num, "name": meta["name"],
                "judgement": meta.get("judgement", ""), "image": meta.get("image", "")}

    upper_name = TRIGRAM_NAMES[cast["upper_bits"]]
    lower_name = TRIGRAM_NAMES[cast["lower_bits"]]

    ben = {**hex_ref(cast["ben_num"]), "upper_trigram": upper_name, "lower_trigram": lower_name}
    zhi = hex_ref(cast["zhi_num"])
    cuo = hex_ref(cast["cuo_num"])
    zong = hex_ref(cast["zong_num"])
    hu = hex_ref(cast["hu_num"])

    narrative = narrate(
        station_name=station_name, month=month, day=day,
        ben=ben, zhi=zhi, cuo=cuo, zong=zong, hu=hu,
        changing_positions=cast["changing_positions"],
        anomalies={
            "temp_diff": d_temp_dev,
            "humidity_diff": d_hum_dev,
            "precip_diff_pct": d_precip_dev * 100,
        },
        solar_term=solar_term,
    )

    return {
        "station_id": station_id, "month": month, "day": day,
        "divination": {
            "ben": ben, "zhi": zhi, "cuo": cuo, "zong": zong, "hu": hu,
            "changing_positions": cast["changing_positions"],
            "line_values": line_values,
            "narrative": narrative,
        },
    }
```

- [ ] **Step 3: Add route + simple in-memory LRU cache**

Append to `backend/app/api/v1/day_insight.py`:

```python
from functools import lru_cache

from app.schemas.day_insight import DayInsightInterpretation
from app.services.divination.service import build_interpretation
from app.models.station import Station


@lru_cache(maxsize=512)
def _cached_interpretation(station_id: str, month: int, day: int):
    # NB: this cache is per-process; Cloud Run cold starts will rebuild it.
    # Keep cache tiny — just (station, m, d) tuple. We materialise the fresh
    # session inside to avoid stale ORM state.
    from app.database import SessionLocal  # adjust if module exposes a different name
    db = SessionLocal()
    try:
        station = db.query(Station).filter_by(station_id=station_id).first()
        name = station.name if station else ""
        return build_interpretation(db, station_id, month, day, station_name=name)
    finally:
        db.close()


@router.get("/{station_id}/{month}/{day}/interpretation",
            response_model=DayInsightInterpretation)
def get_interpretation(station_id: str, month: int, day: int):
    if not (1 <= month <= 12) or not (1 <= day <= 31):
        raise HTTPException(status_code=400, detail="Invalid month or day")
    payload = _cached_interpretation(station_id, month, day)
    if payload is None:
        raise HTTPException(status_code=404, detail="No data for this station/date")
    return payload
```

> If `SessionLocal` is not the name in `app/database.py`, adjust to whichever factory exists (e.g. `engine` + `Session(engine)`).

- [ ] **Step 4: Smoke test**

```bash
cd backend && poetry run uvicorn app.main:app --reload &
sleep 2
curl -sS http://localhost:8000/api/v1/day-insight/466920/6/15/interpretation \
  | python3 -m json.tool | head -40
kill %1
```

Expect: divination payload with 5 hexagrams + narrative (or empty narrative if Gemini fails).

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas/day_insight.py backend/app/api/v1/day_insight.py \
        backend/app/services/divination/service.py
git commit -m "feat(api): add /day-insight/.../interpretation with five-hexagram divination"
```

---

## Phase 4: Divination Frontend

### Task 16: Frontend types + interpretation API client

**Files:**
- Modify: `frontend/src/lib/types.ts`
- Modify: `frontend/src/lib/api.ts`

- [ ] **Step 1: Add types**

```typescript
// append to frontend/src/lib/types.ts
export interface HexagramRef {
  num: number;
  name: string;
  judgement?: string;
  image?: string;
  upper_trigram?: string;
  lower_trigram?: string;
}

export interface DivinationNarrative {
  climate_portrait: string;
  anomaly_layer: string;
  imagination: string;
}

export interface Divination {
  ben: HexagramRef;
  zhi: HexagramRef;
  cuo: HexagramRef;
  zong: HexagramRef;
  hu: HexagramRef;
  changing_positions: number[];
  line_values: number[];
  narrative: DivinationNarrative;
}

export interface DayInsightInterpretation {
  station_id: string;
  month: number;
  day: number;
  divination: Divination;
}
```

- [ ] **Step 2: Add API client**

```typescript
// append to frontend/src/lib/api.ts
import type { DayInsightInterpretation } from "./types";

export const fetchDayInterpretation = async (
  stationId: string, month: number, day: number,
): Promise<DayInsightInterpretation> => {
  const res = await fetch(
    `${API_BASE}/api/v1/day-insight/${stationId}/${month}/${day}/interpretation`,
  );
  if (!res.ok) throw new Error(`interpretation ${res.status}`);
  return res.json();
};
```

- [ ] **Step 3: Type-check + commit**

```bash
cd frontend && pnpm exec tsc --noEmit
git add frontend/src/lib/types.ts frontend/src/lib/api.ts
git commit -m "feat(frontend): add divination interpretation types and api client"
```

---

### Task 17: Divination drawer components

**Files:**
- Create: `frontend/src/components/DayInsightCard/divination/HexagramDisplay.tsx`
- Create: `frontend/src/components/DayInsightCard/divination/FourMethodsSummary.tsx`
- Create: `frontend/src/components/DayInsightCard/divination/NarrativeSection.tsx`

- [ ] **Step 1: HexagramDisplay**

```tsx
// frontend/src/components/DayInsightCard/divination/HexagramDisplay.tsx
import type { HexagramRef } from "@/lib/types";

const LINE_GLYPH = (value: number, isChanging: boolean) => {
  // value: 6=老陰, 7=少陽, 8=少陰, 9=老陽
  const yang = value === 7 || value === 9;
  const base = yang ? "─────" : "── ──";
  return isChanging ? `${base}  ★` : base;
};

interface Props {
  hex: HexagramRef;
  lineValues: number[];
  changingPositions: number[];
  caption?: string;
}

export function HexagramDisplay({ hex, lineValues, changingPositions, caption }: Props) {
  // Render top-to-bottom (line 6 first)
  const rows = [...lineValues].reverse();
  const positions = [6, 5, 4, 3, 2, 1];

  return (
    <div>
      <div className="mb-1 text-base font-semibold">
        第 {hex.num} 卦《{hex.name}》
        {hex.upper_trigram && hex.lower_trigram && (
          <span className="ml-2 text-sm text-slate-500">
            {hex.upper_trigram}上 {hex.lower_trigram}下
          </span>
        )}
      </div>
      <pre className="font-mono text-sm leading-tight text-slate-700">
        {rows.map((v, i) => {
          const pos = positions[i];
          const changing = changingPositions.includes(pos);
          return <div key={pos}>{LINE_GLYPH(v, changing)}</div>;
        })}
      </pre>
      {hex.judgement && <div className="mt-1 text-xs text-slate-600">卦辭：{hex.judgement}</div>}
      {caption && <div className="mt-1 text-xs text-slate-400">{caption}</div>}
    </div>
  );
}
```

- [ ] **Step 2: FourMethodsSummary**

```tsx
// frontend/src/components/DayInsightCard/divination/FourMethodsSummary.tsx
import type { HexagramRef } from "@/lib/types";

interface Props {
  cuo: HexagramRef;
  zong: HexagramRef;
  hu: HexagramRef;
}

export function FourMethodsSummary({ cuo, zong, hu }: Props) {
  return (
    <div className="text-xs text-slate-600">
      <span className="text-slate-400">四法速覽：</span>
      錯：第 {cuo.num} 卦《{cuo.name}》（對立面）
      <span className="mx-1 text-slate-300">｜</span>
      綜：第 {zong.num} 卦《{zong.name}》（半年對位）
      <span className="mx-1 text-slate-300">｜</span>
      互：第 {hu.num} 卦《{hu.name}》（內在核心）
    </div>
  );
}
```

- [ ] **Step 3: NarrativeSection**

```tsx
// frontend/src/components/DayInsightCard/divination/NarrativeSection.tsx
import type { DivinationNarrative } from "@/lib/types";

export function NarrativeSection({ narrative }: { narrative: DivinationNarrative }) {
  const empty = !narrative.climate_portrait && !narrative.anomaly_layer && !narrative.imagination;
  if (empty) {
    return <div className="text-sm text-slate-400 italic">詮釋暫時無法產生，請稍後再試。</div>;
  }
  return (
    <div className="space-y-2 text-sm leading-relaxed text-slate-700">
      {narrative.climate_portrait && <p>{narrative.climate_portrait}</p>}
      {narrative.anomaly_layer    && <p>{narrative.anomaly_layer}</p>}
      {narrative.imagination      && <p>{narrative.imagination}</p>}
    </div>
  );
}
```

- [ ] **Step 4: Type-check + commit**

```bash
cd frontend && pnpm exec tsc --noEmit
git add frontend/src/components/DayInsightCard/divination/
git commit -m "feat(frontend): add divination drawer sub-components"
```

---

### Task 18: Wire drawer into DayInsightCard

**Files:**
- Modify: `frontend/src/components/DayInsightCard.tsx`

- [ ] **Step 1: Replace placeholder drawer body**

Locate the `{drawerOpen && (...)}` block and replace its content:

```tsx
{drawerOpen && (
  <DivinationDrawer stationId={stationId} month={month} day={day} />
)}
```

Add a new sibling component above the export (in the same file, or split out):

```tsx
function DivinationDrawer({ stationId, month, day }: Props) {
  const [data, setData] = useState<DayInsightInterpretation | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDayInterpretation(stationId, month, day).then(setData).catch((e) => setError(e.message));
  }, [stationId, month, day]);

  if (error) return <div className="text-sm text-rose-600">詮釋載入失敗：{error}</div>;
  if (!data) return <div className="text-sm text-slate-400">詮釋計算中…</div>;

  const d = data.divination;
  return (
    <div className="space-y-4 rounded bg-slate-50 p-3">
      <HexagramDisplay
        hex={d.ben}
        lineValues={d.line_values}
        changingPositions={d.changing_positions}
        caption="本卦：氣候畫像"
      />
      {d.changing_positions.length > 0 && (
        <HexagramDisplay
          hex={d.zhi}
          lineValues={d.line_values.map((v, i) => d.changing_positions.includes(i + 1) ? (v === 9 ? 8 : v === 6 ? 7 : v) : v)}
          changingPositions={[]}
          caption="之卦：趨勢"
        />
      )}
      <FourMethodsSummary cuo={d.cuo} zong={d.zong} hu={d.hu} />
      <NarrativeSection narrative={d.narrative} />
    </div>
  );
}
```

Add the imports near the top of `DayInsightCard.tsx`:

```tsx
import type { DayInsightInterpretation } from "@/lib/types";
import { fetchDayInterpretation } from "@/lib/api";
import { HexagramDisplay } from "./DayInsightCard/divination/HexagramDisplay";
import { FourMethodsSummary } from "./DayInsightCard/divination/FourMethodsSummary";
import { NarrativeSection } from "./DayInsightCard/divination/NarrativeSection";
```

- [ ] **Step 2: Type-check**

```bash
cd frontend && pnpm exec tsc --noEmit
```

- [ ] **Step 3: Visual smoke test**

```bash
cd frontend && pnpm dev
```

Open `/planner`, click "看詳細詮釋 ▾" on a card. Expect 本卦、之卦（如有變爻）、四法速覽、三段敘事 全部顯示。

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/DayInsightCard.tsx
git commit -m "feat(frontend): wire divination drawer into DayInsightCard"
```

---

## Phase 5: Roll out to other pages

### Task 19: Integrate into `/compare`

**Files:**
- Modify: `frontend/src/app/compare/page.tsx`

- [ ] **Step 1: Find candidate-station list**

```bash
grep -n "ComparisonCard\|station" frontend/src/app/compare/page.tsx | head
```

- [ ] **Step 2: Add `<DayInsightCard>` per station / per date**

Inject `<DayInsightCard stationId={s.station_id} month={...} day={...} />` adjacent to or inside each ComparisonCard rendering, using the date the user selected.

- [ ] **Step 3: Visual check + commit**

```bash
git add frontend/src/app/compare/page.tsx
git commit -m "feat(compare): show DayInsightCard alongside comparison results"
```

---

### Task 20: Integrate into `/range`

**Files:**
- Modify: `frontend/src/app/range/page.tsx`

- [ ] **Step 1: Replace or augment per-day rendering**

Inside the daily-results map, render `<DayInsightCard stationId month day />` for each day.

- [ ] **Step 2: Visual check + commit**

```bash
git add frontend/src/app/range/page.tsx
git commit -m "feat(range): replace flat daily card with DayInsightCard"
```

---

### Task 21: Add to homepage

**Files:**
- Modify: `frontend/src/app/page.tsx`

- [ ] **Step 1: Render today's DayInsightCard for the user's nearest station**

If the homepage already fetches a "nearest station" via `useGeolocation`, reuse that. Pass current month/day from a `new Date()`.

```tsx
const today = new Date();
<DayInsightCard
  stationId={nearestStationId}
  month={today.getMonth() + 1}
  day={today.getDate()}
/>
```

- [ ] **Step 2: Visual check + commit**

```bash
git add frontend/src/app/page.tsx
git commit -m "feat(home): show today's DayInsightCard on homepage"
```

---

## Final Verification

### Task 22: End-to-end deploy + verification

- [ ] **Step 1: Run full backend test suite**

```bash
cd backend && poetry run pytest -q
```

Expect: all tests pass.

- [ ] **Step 2: Build frontend**

```bash
cd frontend && pnpm build
```

Expect: clean build.

- [ ] **Step 3: Push to origin**

```bash
git push origin main
```

- [ ] **Step 4: Deploy backend**

```bash
GCP_PROJECT_ID=ready-market-crm GCP_REGION=asia-east1 bash scripts/deploy-backend.sh
```

Expect: revision deploys, traffic 100% to new revision.

- [ ] **Step 5: Verify live endpoints**

```bash
curl -sS https://auspicious-api-331213739902.asia-east1.run.app/api/v1/day-insight/466920/6/15 \
  | python3 -m json.tool
curl -sS https://auspicious-api-331213739902.asia-east1.run.app/api/v1/day-insight/466920/6/15/interpretation \
  | python3 -m json.tool
```

Expect: full payloads with label / anomaly / divination + narrative.

- [ ] **Step 6: Frontend deploy** (Vercel auto-deploys on push to main; verify the new card renders on `auspicious-zeta.vercel.app/planner`)

- [ ] **Step 7: Take screenshot evidence per CLAUDE.md "品質鐵律"**

Required by user's quality rule (`部署後第一個動作必須是截圖驗證`). Capture the live page showing the new card + drawer expanded with hexagrams, attach to the implementation report.
