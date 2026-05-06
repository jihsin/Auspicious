import pytest

from app.services.divination.four_methods import cast_hexagram


def test_six_static_yins_returns_kun():
    """6 少陰 (all 8) → 本卦=2 坤為地, 之卦=同, no changing."""
    result = cast_hexagram([8] * 6)
    assert result["ben_num"] == 2
    assert result["zhi_num"] == 2
    assert result["changing_positions"] == []


def test_six_static_yangs_returns_qian():
    """6 少陽 (all 7) → 本卦=1 乾為天."""
    result = cast_hexagram([7] * 6)
    assert result["ben_num"] == 1
    assert result["zhi_num"] == 1
    assert result["changing_positions"] == []


def test_changing_line_changes_zhi():
    """5 少陰 + 1 老陽 at line 1 → 本卦不同於之卦."""
    result = cast_hexagram([9, 8, 8, 8, 8, 8])
    assert result["ben_num"] != result["zhi_num"]
    assert result["changing_positions"] == [1]


def test_cuo_zong_hu_present_and_in_range():
    result = cast_hexagram([7, 8, 7, 8, 7, 8])
    for k in ("cuo_num", "zong_num", "hu_num", "ben_num", "zhi_num"):
        assert 1 <= result[k] <= 64, f"{k} out of range: {result[k]}"


def test_invalid_value_raises():
    with pytest.raises(ValueError):
        cast_hexagram([5, 7, 8, 9, 7, 8])  # 5 is not a valid line value


def test_wrong_count_raises():
    with pytest.raises(AssertionError):
        cast_hexagram([7, 8, 9])
