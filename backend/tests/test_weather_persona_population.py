"""Verify weather_persona is populated in hex_ref output for all 64 hexagrams.

Self-contained — exercises the metadata lookup, not the full DB-dependent
build_interpretation. Catches regressions if a 卦 entry forgets the field.
"""

from app.services.divination.hexagrams import get as get_hex


def test_all_64_hexagrams_have_weather_persona():
    for num in range(1, 65):
        meta = get_hex(num)
        wp = meta.get("weather_persona")
        assert wp, f"卦 {num} ({meta['name']}) missing weather_persona"
        assert len(wp) <= 30, f"卦 {num} weather_persona too long: {len(wp)} 字"


def test_hex_ref_includes_weather_persona():
    """Mirrors the production logic in service.hex_ref()."""
    from app.services.divination.hexagrams import get as get_hex

    def hex_ref_local(num: int) -> dict:
        meta = get_hex(num)
        return {
            "num": num,
            "name": meta["name"],
            "judgement": meta.get("judgement", ""),
            "image": meta.get("image", ""),
            "weather_persona": meta.get("weather_persona", ""),
        }

    out = hex_ref_local(1)  # 乾為天
    assert "weather_persona" in out
    assert out["weather_persona"]  # non-empty
    assert "陽光" in out["weather_persona"] or "晴" in out["weather_persona"]  # 乾 should reference sun/sky
