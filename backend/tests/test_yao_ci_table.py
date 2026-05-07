"""Validate the 384-row 爻辭 lookup table.

Mirrors the boot-time guard pattern from hexagram_table.py.
"""

from app.services.divination.yao_ci import YAO_CI, get_yao_ci, validate_yao_ci_table


def test_table_has_all_384_entries():
    validate_yao_ci_table()  # raises if incomplete


def test_each_hex_has_six_lines():
    for hex_num in range(1, 65):
        for pos in range(1, 7):
            assert (hex_num, pos) in YAO_CI, f"missing 卦{hex_num} 爻{pos}"


def test_get_yao_ci_returns_entry():
    entry = get_yao_ci(1, 1)  # 乾 初九
    assert entry.original
    assert entry.vernacular


def test_get_yao_ci_bad_hex_raises():
    import pytest
    with pytest.raises(KeyError):
        get_yao_ci(99, 1)


def test_qian_yi_initial_line_classical():
    """Spot-check 乾 初九 爻辭 matches classical text."""
    entry = get_yao_ci(1, 1)
    assert "潛龍勿用" in entry.original
