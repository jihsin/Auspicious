from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.models.observation import RawObservation
from app.models.statistics import DailyStatistics
from app.services.day_insight.service import build_day_insight


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)

    # 6 月四個日期，含一個高溫/濕雨 6/15 異常日
    for md, t, h, p in [
        ("06-01", 25.0, 70.0, 0.45),
        ("06-08", 26.0, 72.0, 0.42),
        ("06-22", 27.0, 71.0, 0.48),
        ("06-15", 30.0, 95.0, 0.65),  # 高溫 + 高濕 + 高雨機率
        ("01-15", 16.0, 75.0, 0.40),
    ]:
        session.add(DailyStatistics(
            station_id="466920", month_day=md,
            temp_avg_mean=t, humidity_avg_mean=h,
            precip_probability=p,
            years_analyzed=36, start_year=1991, end_year=2026,
        ))

    # 6/15 歷年 raw obs (for extremes lookup)
    for yr, mm in [(2009, 85.0), (2002, 0.0), (2018, 5.0)]:
        session.add(RawObservation(
            station_id="466920", observed_date=date(yr, 6, 15),
            precipitation=mm,
        ))

    session.commit()
    yield session
    session.close()


def test_build_day_insight_full_payload(db):
    insight = build_day_insight(db, station_id="466920", month=6, day=15)
    assert insight is not None
    assert insight.station_id == "466920"
    assert insight.month == 6
    assert insight.day == 15
    assert insight.core.metric == "precip_probability"
    assert insight.core.value == pytest.approx(0.65)
    # 6/15 anomaly_year = 0.65 - mean of (0.45, 0.42, 0.48, 0.65, 0.40) = 0.65 - 0.48 = 0.17
    assert insight.core.anomaly_year == pytest.approx(0.65 - 0.48)
    # 6/15 anomaly_month = 0.65 - mean of (0.45, 0.42, 0.48, 0.65) = 0.65 - 0.50 = 0.15
    assert insight.core.anomaly_month == pytest.approx(0.65 - 0.50)
    # extremes
    assert insight.extremes.wettest.year == 2009
    assert insight.extremes.wettest.value == 85.0
    assert insight.extremes.driest.year == 2002
    # side badges should fire (temp 30 vs 25/26/27 ≈ z>1; humidity 95 vs 70-72 ≈ z>1)
    assert len(insight.side_badges) >= 1
    # meta
    assert insight.meta.years_analyzed == 36


def test_build_day_insight_returns_none_for_missing(db):
    assert build_day_insight(db, station_id="466920", month=12, day=25) is None


def test_build_day_insight_unknown_station(db):
    assert build_day_insight(db, station_id="999999", month=6, day=15) is None
