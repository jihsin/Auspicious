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


def test_extremes_returns_none_when_no_data(db):
    result = compute_extremes(db, station_id="UNKNOWN", month=6, day=15)
    assert result["wettest"] is None
    assert result["driest"] is None
