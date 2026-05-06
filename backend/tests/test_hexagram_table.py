import pytest

from app.services.divination.hexagram_table import TABLE, validate_table
from app.services.divination.hexagrams import HEXAGRAMS, get


def test_table_is_complete():
    validate_table()


def test_all_64_hexagrams_present():
    assert len(HEXAGRAMS) == 64
    for i, h in enumerate(HEXAGRAMS, start=1):
        assert h["num"] == i, f"index {i} has wrong num"
        assert h["name"], f"hex {i} missing name"
        assert "judgement" in h
        assert "image" in h


def test_get_returns_correct_entry():
    assert get(1)["name"] == "乾為天"
    assert get(64)["name"] == "火水未濟"


def test_get_rejects_out_of_range():
    with pytest.raises(ValueError):
        get(0)
    with pytest.raises(ValueError):
        get(65)
