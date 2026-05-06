"""Four-methods (本/錯/綜/互/之) calculation.

Adapted from pi-mono iching_divination.py @ 271c9e3 (MIT License).
Original used random three-coin tossing; here the line values are
supplied by the caller, computed deterministically from weather data.
"""

from app.services.divination.hexagram_table import TABLE
from app.services.divination.line_mapping import lines_to_trigram


def _is_yang(value: int) -> bool:
    return value in (7, 9)


def _is_changing(value: int) -> bool:
    return value in (6, 9)


def cast_hexagram(values: list[int]) -> dict:
    """Compute 本/錯/綜/互/之 hexagrams from 6 line values (line 1 first)."""
    assert len(values) == 6, f"need 6 line values, got {len(values)}"
    for v in values:
        if v not in (6, 7, 8, 9):
            raise ValueError(f"invalid line value: {v}")

    lower_bits = lines_to_trigram(values[0:3])
    upper_bits = lines_to_trigram(values[3:6])
    ben_num = TABLE[lower_bits][upper_bits]

    # 之卦：變爻取反 (老陰→少陽, 老陽→少陰)
    changed = [(8 if _is_yang(v) else 7) if _is_changing(v) else v for v in values]
    zhi_num = TABLE[lines_to_trigram(changed[0:3])][lines_to_trigram(changed[3:6])]

    changing_positions = [i + 1 for i, v in enumerate(values) if _is_changing(v)]

    # 錯卦：陰陽全翻
    cuo_num = TABLE[lower_bits ^ 7][upper_bits ^ 7]

    # 綜卦：六爻倒序
    rev = values[::-1]
    zong_num = TABLE[lines_to_trigram(rev[0:3])][lines_to_trigram(rev[3:6])]

    # 互卦：lines[1:4] 為下卦, lines[2:5] 為上卦
    hu_num = TABLE[lines_to_trigram(values[1:4])][lines_to_trigram(values[2:5])]

    return {
        "values": values,
        "ben_num": ben_num,
        "zhi_num": zhi_num,
        "cuo_num": cuo_num,
        "zong_num": zong_num,
        "hu_num": hu_num,
        "changing_positions": changing_positions,
        "lower_bits": lower_bits,
        "upper_bits": upper_bits,
    }
