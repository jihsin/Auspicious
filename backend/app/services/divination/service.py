"""Compose the divination payload from daily_statistics + raw observations."""

import statistics as stats_mod

from sqlalchemy.orm import Session

from app.models.statistics import DailyStatistics
from app.services.divination.four_methods import cast_hexagram
from app.services.divination.hexagram_table import TRIGRAM_NAMES
from app.services.divination.hexagrams import get as get_hex
from app.services.divination.line_mapping import lines_from_weather
from app.services.divination.narrator import narrate
from app.services.divination.yao_ci import get_yao_ci


def _stat_dist(values: list[float]) -> tuple[float | None, float | None]:
    if len(values) < 2:
        return None, None
    return stats_mod.mean(values), stats_mod.stdev(values) or None


def _all(db: Session, station_id: str) -> list[DailyStatistics]:
    return db.query(DailyStatistics).filter_by(station_id=station_id).all()


def build_interpretation(
    db: Session,
    station_id: str,
    month: int,
    day: int,
    station_name: str = "",
    solar_term: str | None = None,
) -> dict | None:
    month_day = f"{month:02d}-{day:02d}"
    day_stat = db.query(DailyStatistics).filter_by(
        station_id=station_id, month_day=month_day
    ).first()
    if not day_stat:
        return None

    rows = _all(db, station_id)
    if not rows:
        return None
    month_rows = [r for r in rows if r.month_day.startswith(f"{month:02d}-")]

    # Year baselines
    year_temp_mean, year_temp_std = _stat_dist(
        [r.temp_avg_mean for r in rows if r.temp_avg_mean is not None]
    )
    year_hum_mean, year_hum_std = _stat_dist(
        [r.humidity_avg_mean for r in rows if r.humidity_avg_mean is not None]
    )
    year_precip_mean, year_precip_std = _stat_dist(
        [r.precip_probability for r in rows if r.precip_probability is not None]
    )

    # Month baselines
    m_temp_mean, m_temp_std = _stat_dist(
        [r.temp_avg_mean for r in month_rows if r.temp_avg_mean is not None]
    )
    m_hum_mean, m_hum_std = _stat_dist(
        [r.humidity_avg_mean for r in month_rows if r.humidity_avg_mean is not None]
    )
    m_precip_mean, m_precip_std = _stat_dist(
        [r.precip_probability for r in month_rows if r.precip_probability is not None]
    )

    def dev_z(v: float | None, mean: float | None, std: float | None) -> tuple[float, float]:
        if v is None or mean is None or not std:
            return 0.0, 0.0
        return v - mean, (v - mean) / std

    # Month vs year (lower trigram)
    m_temp_dev, m_temp_z = dev_z(m_temp_mean, year_temp_mean, year_temp_std)
    m_hum_dev, m_hum_z = dev_z(m_hum_mean, year_hum_mean, year_hum_std)
    m_precip_dev, m_precip_z = dev_z(m_precip_mean, year_precip_mean, year_precip_std)

    # Day vs month (upper trigram)
    d_temp_dev, d_temp_z = dev_z(day_stat.temp_avg_mean, m_temp_mean, m_temp_std)
    d_hum_dev, d_hum_z = dev_z(day_stat.humidity_avg_mean, m_hum_mean, m_hum_std)
    d_precip_dev, d_precip_z = dev_z(day_stat.precip_probability, m_precip_mean, m_precip_std)

    line_values = lines_from_weather({
        "month_temp_dev_vs_year": m_temp_dev,     "month_temp_z_vs_year": m_temp_z,
        "month_hum_dev_vs_year": m_hum_dev,       "month_hum_z_vs_year": m_hum_z,
        "month_precip_dev_vs_year": m_precip_dev, "month_precip_z_vs_year": m_precip_z,
        "day_temp_dev_vs_month": d_temp_dev,      "day_temp_z_vs_month": d_temp_z,
        "day_hum_dev_vs_month": d_hum_dev,        "day_hum_z_vs_month": d_hum_z,
        "day_precip_dev_vs_month": d_precip_dev,  "day_precip_z_vs_month": d_precip_z,
    })

    cast = cast_hexagram(line_values)

    def hex_ref(num: int) -> dict:
        meta = get_hex(num)
        return {
            "num": num,
            "name": meta["name"],
            "judgement": meta.get("judgement", ""),
            "image": meta.get("image", ""),
        }

    upper_name = TRIGRAM_NAMES[cast["upper_bits"]]
    lower_name = TRIGRAM_NAMES[cast["lower_bits"]]

    ben = {**hex_ref(cast["ben_num"]),
           "upper_trigram": upper_name, "lower_trigram": lower_name}
    zhi = hex_ref(cast["zhi_num"])
    cuo = hex_ref(cast["cuo_num"])
    zong = hex_ref(cast["zong_num"])
    hu = hex_ref(cast["hu_num"])

    narrative = narrate(
        station_name=station_name, month=month, day=day,
        ben=ben, zhi=zhi, cuo=cuo, zong=zong, hu=hu,
        changing_positions=cast["changing_positions"],
        anomalies={
            "temp_diff": d_temp_dev,
            "humidity_diff": d_hum_dev,
            "precip_diff_pct": d_precip_dev * 100,
        },
        solar_term=solar_term,
    )

    var_yao_ci = {
        pos: get_yao_ci(cast["ben_num"], pos).model_dump()
        for pos in cast["changing_positions"]
    }

    return {
        "station_id": station_id, "month": month, "day": day,
        "divination": {
            "ben": ben, "zhi": zhi, "cuo": cuo, "zong": zong, "hu": hu,
            "changing_positions": cast["changing_positions"],
            "line_values": line_values,
            "narrative": narrative,
            "var_yao_ci": var_yao_ci,
        },
    }
