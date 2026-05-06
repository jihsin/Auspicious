from app.services.day_insight.label_rules import match_label


def _ctx(**kwargs):
    base = {
        "month": 6, "day": 15,
        "precip_probability": 0.40,    # was 0.52; must be < 0.50 so meiyu rule does NOT trigger
        "anomaly_year": 0.08, "anomaly_month": 0.02,
        "temp_z": 0.5, "precip_z_in_month": 0.5,
        "is_solar_term_day": False,
        "is_north_station": False,
    }
    base.update(kwargs)
    return base


def test_typical_meiyu():
    label = match_label(_ctx(month=6, day=15, precip_probability=0.55))
    assert label["text"] == "典型梅雨日"
    assert label["category"] == "seasonal"


def test_anomaly_dry():
    label = match_label(_ctx(anomaly_month=-0.20))
    assert label["text"] == "異常乾旱期"
    assert label["category"] == "anomaly"


def test_no_match_returns_null():
    label = match_label(_ctx())
    assert label["text"] is None
    assert label["category"] is None


def test_record_overrides_anomaly():
    # 紀錄級多雨優先於 異常多雨期
    label = match_label(_ctx(anomaly_month=+0.20, precip_z_in_month=2.5))
    assert label["text"] == "紀錄級多雨"
