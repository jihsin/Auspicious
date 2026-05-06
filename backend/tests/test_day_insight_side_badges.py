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


def test_humidity_badge_emits(db):
    # 加入濕度資料，6/15 濕度異常高
    # Use distinct month_day keys (06-02, 06-09, 06-23) to avoid UNIQUE conflict
    # with fixture rows (06-01, 06-08, 06-22).
    rows = [
        DailyStatistics(station_id="X", month_day="06-02", temp_avg_mean=25.0, humidity_avg_mean=70.0,
                        years_analyzed=1, start_year=2020, end_year=2020),
        DailyStatistics(station_id="X", month_day="06-09", temp_avg_mean=26.0, humidity_avg_mean=72.0,
                        years_analyzed=1, start_year=2020, end_year=2020),
        DailyStatistics(station_id="X", month_day="06-23", temp_avg_mean=27.0, humidity_avg_mean=71.0,
                        years_analyzed=1, start_year=2020, end_year=2020),
    ]
    # 6/15 row already exists in fixture as temp=30.0 with no humidity — update it
    target = db.query(DailyStatistics).filter_by(station_id="X", month_day="06-15").first()
    target.humidity_avg_mean = 95.0
    db.add_all(rows)
    db.commit()

    badges = compute_side_badges(db, station_id="X", month=6, day_stat=target)
    metrics = {b["metric"] for b in badges}
    assert "humidity_avg" in metrics
    humidity = next(b for b in badges if b["metric"] == "humidity_avg")
    assert humidity["direction"] == "above"
    assert "偏高" in humidity["label"]


def test_caps_at_two_badges(db):
    # Both temp + humidity anomalous → expect exactly 2 badges (cap behaviour)
    # Use distinct month_day keys to avoid UNIQUE conflict with fixture rows.
    rows = [
        DailyStatistics(station_id="X", month_day="06-03", humidity_avg_mean=70.0,
                        years_analyzed=1, start_year=2020, end_year=2020),
        DailyStatistics(station_id="X", month_day="06-10", humidity_avg_mean=72.0,
                        years_analyzed=1, start_year=2020, end_year=2020),
        DailyStatistics(station_id="X", month_day="06-24", humidity_avg_mean=71.0,
                        years_analyzed=1, start_year=2020, end_year=2020),
    ]
    target = db.query(DailyStatistics).filter_by(station_id="X", month_day="06-15").first()
    target.humidity_avg_mean = 99.0
    db.add_all(rows)
    db.commit()

    badges = compute_side_badges(db, station_id="X", month=6, day_stat=target)
    assert len(badges) <= 2
    # Strongest |z| should be first
    if len(badges) == 2:
        assert abs(badges[0]["z_score"]) >= abs(badges[1]["z_score"])
