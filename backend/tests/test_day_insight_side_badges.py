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
