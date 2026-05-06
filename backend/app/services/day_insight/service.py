import statistics as stats_mod

from sqlalchemy.orm import Session

from app.models.statistics import DailyStatistics
from app.schemas.day_insight import (
    CoreMetric, DayInsight, ExtremeRecord, Extremes, InsightMeta, LabelInfo, SideBadge,
)
from app.services.day_insight.compute import compute_anomaly
from app.services.day_insight.extremes import compute_extremes
from app.services.day_insight.label_rules import is_north_station, match_label
from app.services.day_insight.side_badges import compute_side_badges


def build_day_insight(db: Session, station_id: str, month: int, day: int) -> DayInsight | None:
    anomaly = compute_anomaly(db, station_id, month, day)
    if anomaly is None:
        return None
    day_stat: DailyStatistics = anomaly["_day_stat"]

    badges = compute_side_badges(db, station_id, month, day_stat)
    extremes = compute_extremes(db, station_id, month, day)

    # precip z-score within month for "紀錄級多雨" rule
    month_precip = [
        r.precip_probability for r in db.query(DailyStatistics).filter(
            DailyStatistics.station_id == station_id,
            DailyStatistics.month_day.like(f"{month:02d}-%"),
        ).all() if r.precip_probability is not None
    ]
    if len(month_precip) >= 2:
        m_mean = stats_mod.mean(month_precip)
        m_std = stats_mod.stdev(month_precip)
        precip_z_in_month = (day_stat.precip_probability - m_mean) / m_std if m_std else 0.0
    else:
        precip_z_in_month = 0.0

    temp_z = next((b["z_score"] for b in badges if b["metric"] == "temp_avg"), 0.0)

    label = match_label({
        "month": month, "day": day,
        "precip_probability": day_stat.precip_probability,
        "anomaly_year": anomaly["anomaly_year"], "anomaly_month": anomaly["anomaly_month"],
        "temp_z": temp_z, "precip_z_in_month": precip_z_in_month,
        "is_solar_term_day": False,  # TODO: integrate solar_term in P3
        "is_north_station": is_north_station(station_id),
    })

    return DayInsight(
        station_id=station_id, month=month, day=day,
        label=LabelInfo(**label),
        core=CoreMetric(metric="precip_probability",
                        value=anomaly["value"],
                        anomaly_year=anomaly["anomaly_year"],
                        anomaly_month=anomaly["anomaly_month"]),
        side_badges=[SideBadge(**b) for b in badges],
        extremes=Extremes(
            wettest=ExtremeRecord(**extremes["wettest"]) if extremes["wettest"] else None,
            driest=ExtremeRecord(**extremes["driest"]) if extremes["driest"] else None,
        ),
        meta=InsightMeta(
            years_analyzed=day_stat.years_analyzed or 0,
            start_year=day_stat.start_year or 0,
            end_year=day_stat.end_year or 0,
        ),
    )
