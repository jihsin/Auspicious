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
