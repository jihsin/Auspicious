from unittest.mock import patch

from app.services.divination.narrator import narrate


@patch("app.services.divination.narrator._call_gemini")
def test_narrate_returns_three_sections(mock_call):
    mock_call.return_value = """段一：氣候畫像示範文字。
段二：特殊度示範。
段三：想像層示範。"""

    result = narrate(
        station_name="台北", month=6, day=15,
        ben={"num": 35, "name": "火地晉"},
        zhi={"num": 8,  "name": "水地比"},
        cuo={"num": 5,  "name": "水天需"},
        zong={"num": 36, "name": "地火明夷"},
        hu={"num": 39,  "name": "水山蹇"},
        changing_positions=[6],
        anomalies={"temp_diff": 2.0, "humidity_diff": 5.0, "precip_diff_pct": 8.0},
        solar_term="芒種",
    )
    assert "climate_portrait" in result
    assert "anomaly_layer" in result
    assert "imagination" in result
    assert all(v.strip() for v in result.values())


@patch("app.services.divination.narrator._call_gemini")
def test_narrate_returns_fallback_on_exception(mock_call):
    mock_call.side_effect = RuntimeError("quota exceeded")
    result = narrate(
        station_name="台北", month=6, day=15,
        ben={"num": 1, "name": "乾為天"}, zhi={"num": 1, "name": "乾為天"},
        cuo={"num": 2, "name": "坤為地"}, zong={"num": 1, "name": "乾為天"},
        hu={"num": 1, "name": "乾為天"},
        changing_positions=[], anomalies={}, solar_term="夏至",
    )
    assert result["climate_portrait"] == ""
    assert result["anomaly_layer"] == ""
    assert result["imagination"] == ""


@patch("app.services.divination.narrator._call_gemini")
def test_narrate_returns_fallback_when_gemini_returns_none(mock_call):
    mock_call.return_value = None
    result = narrate(
        station_name="台北", month=6, day=15,
        ben={"num": 1, "name": "乾為天"}, zhi={"num": 1, "name": "乾為天"},
        cuo={"num": 2, "name": "坤為地"}, zong={"num": 1, "name": "乾為天"},
        hu={"num": 1, "name": "乾為天"},
        changing_positions=[], anomalies={}, solar_term="夏至",
    )
    assert all(v == "" for v in result.values())
