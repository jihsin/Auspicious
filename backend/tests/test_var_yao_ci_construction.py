"""Verify the var_yao_ci dict is built correctly from changing positions.

Self-contained — does not exercise the DB-dependent build_interpretation
function. The full integration is verified post-deploy via the curl smoke
test in Task 11 step 4.
"""

import pytest

from app.services.divination.yao_ci import get_yao_ci


def _build_var_yao_ci(ben_num: int, changing_positions: list[int]) -> dict:
    """Mirrors the production logic in service.build_interpretation."""
    return {
        pos: get_yao_ci(ben_num, pos).model_dump()
        for pos in changing_positions
    }


def test_two_changing_positions_yields_two_entries():
    out = _build_var_yao_ci(ben_num=1, changing_positions=[2, 5])
    assert set(out.keys()) == {2, 5}
    for pos in (2, 5):
        assert out[pos]["original"]
        assert out[pos]["vernacular"]


def test_zero_changing_positions_yields_empty_dict():
    out = _build_var_yao_ci(ben_num=1, changing_positions=[])
    assert out == {}


def test_invalid_hex_raises_keyerror():
    with pytest.raises(KeyError):
        _build_var_yao_ci(ben_num=99, changing_positions=[1])
