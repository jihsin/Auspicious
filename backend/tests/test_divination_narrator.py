from unittest.mock import patch

from app.services.divination.narrator import narrate


@patch("app.services.divination.narrator._call_gemini")
def test_narrate_returns_three_sections(mock_call):
    mock_call.return_value = """段一【氣候畫像】氣候畫像示範文字。
段二【特殊度】特殊度示範。
段三【想像層】想像層示範。
段四【標題】示範標題
段五【副標】示範副標說明今日氣候。
段六【標籤】偏暖,多雲,穩"""

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
    assert result["climate_portrait"].strip()
    assert result["anomaly_layer"].strip()
    assert result["imagination"].strip()
    assert result["headline"].strip()
    assert result["subtitle"].strip()
    assert len(result["tags"]) > 0


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
    assert result == {
        "climate_portrait": "",
        "anomaly_layer": "",
        "imagination": "",
        "headline": "",
        "subtitle": "",
        "tags": [],
    }


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
    assert result["climate_portrait"] == ""
    assert result["anomaly_layer"] == ""
    assert result["imagination"] == ""
    assert result["headline"] == ""
    assert result["subtitle"] == ""
    assert result["tags"] == []


def test_parse_sections_handles_six_segments():
    from app.services.divination.narrator import _parse_sections
    raw = """段一【氣候畫像】今日陽氣初升、地氣未動。
段二【特殊度】第二爻變動，午後可能轉折。
段三【想像層】半年後對位是地雷復，動極轉靜。
段四【標題】穩中帶變的一天
段五【副標】天涼略乾、雨機率持平 — 適合靜中蓄勢。
段六【標籤】偏涼,偏乾,二爻變"""
    out = _parse_sections(raw)
    assert out["climate_portrait"].startswith("今日陽氣")
    assert out["headline"] == "穩中帶變的一天"
    assert out["subtitle"].startswith("天涼略乾")
    assert out["tags"] == ["偏涼", "偏乾", "二爻變"]


def test_parse_sections_empty_input():
    from app.services.divination.narrator import _parse_sections
    out = _parse_sections(None)
    assert out == {
        "climate_portrait": "", "anomaly_layer": "", "imagination": "",
        "headline": "", "subtitle": "", "tags": [],
    }


def test_parse_sections_partial_input_keeps_defaults():
    from app.services.divination.narrator import _parse_sections
    raw = "段一【氣候畫像】只有第一段。"
    out = _parse_sections(raw)
    assert out["climate_portrait"].endswith("只有第一段。")
    assert out["headline"] == ""  # no 段四, default to empty
    assert out["tags"] == []


def test_parse_sections_strips_quotation_brackets():
    """If Gemini wraps tags in 「」, parser must strip them."""
    from app.services.divination.narrator import _parse_sections
    raw = "段六【標籤】「偏涼,偏乾,二爻變」"
    out = _parse_sections(raw)
    assert out["tags"] == ["偏涼", "偏乾", "二爻變"]
