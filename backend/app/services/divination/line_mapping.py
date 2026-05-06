"""Weather → 6 hexagram lines.
Lower trigram (lines 1-3) = month vs year.
Upper trigram (lines 4-6) = day vs month.
Each trigram in order [溫, 濕, 雨].
"""

Z_THRESHOLD = 1.0


def line_value(deviation: float, z_score: float) -> int:
    """Map (deviation, z_score) to one of (6, 7, 8, 9):
       6 = 老陰 (yin changing), 7 = 少陽 (yang static),
       8 = 少陰 (yin static),    9 = 老陽 (yang changing).
    """
    yang = deviation > 0
    changing = abs(z_score) >= Z_THRESHOLD
    if yang and changing:
        return 9
    if yang and not changing:
        return 7
    if not yang and changing:
        return 6
    return 8


def lines_from_weather(ctx: dict) -> list[int]:
    """Return 6 line values, line 1 (bottom) to line 6 (top)."""
    return [
        line_value(ctx["month_temp_dev_vs_year"],   ctx["month_temp_z_vs_year"]),
        line_value(ctx["month_hum_dev_vs_year"],    ctx["month_hum_z_vs_year"]),
        line_value(ctx["month_precip_dev_vs_year"], ctx["month_precip_z_vs_year"]),
        line_value(ctx["day_temp_dev_vs_month"],    ctx["day_temp_z_vs_month"]),
        line_value(ctx["day_hum_dev_vs_month"],     ctx["day_hum_z_vs_month"]),
        line_value(ctx["day_precip_dev_vs_month"],  ctx["day_precip_z_vs_month"]),
    ]


def lines_to_trigram(three_values: list[int]) -> int:
    """3 line values → trigram bits (yang=1 yin=0, line 1 = bit 0).
    Returns 0..7 indexing into TRIGRAM_NAMES.
    """
    bits = 0
    for i, v in enumerate(three_values):
        if v in (7, 9):  # yang
            bits |= (1 << i)
    return bits
