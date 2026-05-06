"""Z-score driven side badges for day insight.

Computes up to 2 badges (sorted by |z|) for temperature and humidity,
emitting a badge when a dimension's z-score exceeds Z_THRESHOLD.
"""

import statistics as stats_mod

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
    # NOTE: includes the target month_day itself in the sample (consistent with
    # T2 compute_anomaly which uses func.avg over all same-station rows). With
    # ~28-31 rows per month in production, the inclusive-self bias on z-score
    # is < 5%; deliberate consistency choice over statistical purity.
    rows = db.query(DailyStatistics).filter(
        DailyStatistics.station_id == station_id,
        DailyStatistics.month_day.like(f"{month:02d}-%"),
    ).all()
    return [getattr(r, attr) for r in rows if getattr(r, attr) is not None]


def compute_side_badges(
    db: Session, station_id: str, month: int, day_stat: DailyStatistics
) -> list[dict]:
    """Return up to 2 z-score driven side badges for the given day statistics.

    Args:
        db: SQLAlchemy session.
        station_id: Station identifier used for peer comparison.
        month: Calendar month (1–12) for same-month peer lookup.
        day_stat: The DailyStatistics row for the target day.

    Returns:
        List of badge dicts (at most 2), sorted descending by |z_score|.
        Each dict contains: metric, label, direction, z_score.
    """
    badges: list[dict] = []

    if day_stat.temp_avg_mean is not None:
        b = _compute_one_dim(
            _month_values(db, station_id, month, "temp_avg_mean"),
            day_stat.temp_avg_mean,
            "temp_avg",
            "°C",
        )
        if b:
            badges.append(b)

    if day_stat.humidity_avg_mean is not None:
        b = _compute_one_dim(
            _month_values(db, station_id, month, "humidity_avg_mean"),
            day_stat.humidity_avg_mean,
            "humidity_avg",
            "%",
        )
        if b:
            badges.append(b)

    badges.sort(key=lambda b: -abs(b["z_score"]))
    return badges[:2]
