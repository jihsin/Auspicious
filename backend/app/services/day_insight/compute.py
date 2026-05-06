from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.statistics import DailyStatistics


def compute_anomaly(db: Session, station_id: str, month: int, day: int) -> dict | None:
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

    if year_mean is None or month_mean is None:
        return None

    return {
        "value": float(day_stat.precip_probability),
        "anomaly_year": float(day_stat.precip_probability - year_mean),
        "anomaly_month": float(day_stat.precip_probability - month_mean),
        "_day_stat": day_stat,  # internal use for downstream services
    }
