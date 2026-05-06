def test_day_insight_round_trip():
    from app.schemas.day_insight import (
        DayInsight, LabelInfo, CoreMetric, SideBadge, ExtremeRecord, Extremes, InsightMeta,
    )
    payload = DayInsight(
        station_id="466920", month=6, day=15,
        label=LabelInfo(text="典型梅雨日", category="seasonal"),
        core=CoreMetric(metric="precip_probability", value=0.52,
                        anomaly_year=0.08, anomaly_month=0.02),
        side_badges=[SideBadge(metric="temp_avg", label="氣溫比同月偏低 -2.0°C",
                               direction="below", z_score=-1.2)],
        extremes=Extremes(wettest=ExtremeRecord(year=2009, value=85.0),
                          driest=ExtremeRecord(year=2002, value=0.0)),
        meta=InsightMeta(years_analyzed=36, start_year=1991, end_year=2026),
    )
    assert payload.model_dump()["core"]["value"] == 0.52
