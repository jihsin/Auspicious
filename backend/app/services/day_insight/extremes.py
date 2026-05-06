"""Day insight: wettest / driest extremes lookup.

Queries raw observations for a given station + calendar day (month/day),
skips NULL precipitation rows, and returns the wettest and driest years.

Tiebreak for driest: when two records share the same minimum precipitation,
the most recent year wins (spec §12).
"""

from sqlalchemy import extract
from sqlalchemy.orm import Session

from app.models.observation import RawObservation


def compute_extremes(db: Session, station_id: str, month: int, day: int) -> dict:
    """Return wettest and driest historical records for a calendar day.

    Args:
        db: SQLAlchemy session.
        station_id: Weather station identifier.
        month: Calendar month (1–12).
        day: Calendar day (1–31).

    Returns:
        Dict with keys ``wettest`` and ``driest``, each either ``None``
        (no data) or ``{"year": int, "value": float}``.
    """
    rows = (
        db.query(RawObservation)
        .filter(
            RawObservation.station_id == station_id,
            extract("month", RawObservation.observed_date) == month,
            extract("day", RawObservation.observed_date) == day,
            RawObservation.precipitation.isnot(None),
        )
        .all()
    )

    if not rows:
        return {"wettest": None, "driest": None}

    wettest = max(rows, key=lambda r: r.precipitation)
    # Tiebreak for driest: smallest precipitation first, then most recent year (spec §12)
    driest = min(rows, key=lambda r: (r.precipitation, -r.observed_date.year))

    return {
        "wettest": {"year": wettest.observed_date.year, "value": float(wettest.precipitation)},
        "driest": {"year": driest.observed_date.year, "value": float(driest.precipitation)},
    }
