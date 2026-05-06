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
