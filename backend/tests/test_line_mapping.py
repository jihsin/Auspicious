from app.services.divination.line_mapping import lines_from_weather, line_value, lines_to_trigram


def test_line_value_yang_changing():
    # deviation > 0 and |z| >= 1 → 老陽 = 9
    assert line_value(deviation=1.5, z_score=1.5) == 9


def test_line_value_yin_static():
    assert line_value(deviation=-0.1, z_score=-0.5) == 8


def test_line_value_yang_static():
    assert line_value(deviation=0.5, z_score=0.5) == 7


def test_line_value_yin_changing():
    assert line_value(deviation=-1.0, z_score=-1.5) == 6


def test_lines_from_weather_basic():
    """Day where every dimension is positive vs both baselines, with humidity exceeding |z|>=1."""
    ctx = {
        "day_temp_dev_vs_month": 0.5, "day_temp_z_vs_month": 0.5,
        "day_hum_dev_vs_month": 5,    "day_hum_z_vs_month": 1.5,
        "day_precip_dev_vs_month": 0.05, "day_precip_z_vs_month": 0.5,
        "month_temp_dev_vs_year": 2,  "month_temp_z_vs_year": 1.0,
        "month_hum_dev_vs_year": 3,   "month_hum_z_vs_year": 0.8,
        "month_precip_dev_vs_year": 0.05, "month_precip_z_vs_year": 0.6,
    }
    values = lines_from_weather(ctx)
    assert len(values) == 6
    assert values[3] == 7    # day_temp yang static
    assert values[4] == 9    # day_hum yang changing (z=1.5)
    assert values[0] == 9    # month_temp yang changing (z=1.0)


def test_lines_to_trigram_yang_yang_yang_is_qian():
    # 三個都陽（值=7或9）→ 二進位 111 = 7 = 乾
    assert lines_to_trigram([7, 7, 7]) == 7
    assert lines_to_trigram([9, 9, 9]) == 7


def test_lines_to_trigram_yin_yin_yin_is_kun():
    # 三個都陰（值=6或8）→ 二進位 000 = 0 = 坤
    assert lines_to_trigram([8, 8, 8]) == 0


def test_lines_to_trigram_bottom_yang_only_is_zhen():
    # 第一爻陽，其他陰 → bit 0 set → value 1 (艮)
    assert lines_to_trigram([7, 8, 8]) == 1   # bit 0 set → value 1
