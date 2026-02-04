"""數據清洗功能測試"""

import pytest
import pandas as pd
from io import StringIO


def test_clean_temperature_removes_missing_markers():
    """測試清洗溫度欄位的缺失值標記"""
    from clean import clean_temperature_column

    # -9999 是常見的缺失值標記
    df = pd.DataFrame({"temperature_avg": [25.5, -9999, 18.3, -9999.0]})
    result = clean_temperature_column(df, "temperature_avg")

    assert pd.isna(result["temperature_avg"].iloc[1])
    assert pd.isna(result["temperature_avg"].iloc[3])
    assert result["temperature_avg"].iloc[0] == 25.5


def test_clean_temperature_removes_outliers():
    """測試清洗溫度異常值（超過合理範圍）"""
    from clean import clean_temperature_column

    df = pd.DataFrame({"temperature_avg": [25.5, 55.0, -25.0, 18.3]})
    result = clean_temperature_column(df, "temperature_avg")

    # 台灣溫度不可能超過 45°C 或低於 -5°C
    assert pd.isna(result["temperature_avg"].iloc[1])  # 55.0 -> NaN
    assert pd.isna(result["temperature_avg"].iloc[2])  # -25.0 -> NaN


def test_standardize_date_column():
    """測試日期格式標準化"""
    from clean import standardize_date_column

    df = pd.DataFrame({"date": ["2023-02-04", "2023/02/05", "20230206"]})
    result = standardize_date_column(df, "date")

    assert result["date"].dtype == "datetime64[ns]"
    assert len(result) == 3
