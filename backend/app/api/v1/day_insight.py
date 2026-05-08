from datetime import date, datetime
from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.models.station import Station
from app.schemas.day_insight import DayInsight, DayInsightInterpretation
from app.services.day_insight.service import build_day_insight
from app.services.divination.service import build_interpretation
from app.services.solar_term import get_current_solar_term

router = APIRouter()


@router.get("/{station_id}/{month}/{day}", response_model=DayInsight)
def get_day_insight(station_id: str, month: int, day: int, db: Session = Depends(get_db)):
    if not (1 <= month <= 12) or not (1 <= day <= 31):
        raise HTTPException(status_code=400, detail="Invalid month or day")
    insight = build_day_insight(db, station_id, month, day)
    if insight is None:
        raise HTTPException(status_code=404, detail="No data for this station/date")
    return insight


@lru_cache(maxsize=512)
def _cached_interpretation(station_id: str, month: int, day: int):
    """Per-process LRU cache. Key = (station, month, day). TTL effectively
    bound to process lifetime; Cloud Run cold starts will rebuild."""
    db = SessionLocal()
    try:
        station = db.query(Station).filter_by(station_id=station_id).first()
        name = station.name if station else ""
        # Resolve solar_term for narrator's prompt. Use current year as the
        # representative date — boundaries shift ~1 day/year, accurate enough.
        try:
            solar_term = get_current_solar_term(date(datetime.now().year, month, day))
        except ValueError:
            # Feb 29 in non-leap year, etc. — narrator handles None.
            solar_term = None
        return build_interpretation(
            db, station_id, month, day,
            station_name=name, solar_term=solar_term,
        )
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
