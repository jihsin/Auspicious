"""數據下載功能測試"""

import pytest
from pathlib import Path


def test_build_csv_url():
    """測試 CSV URL 建構"""
    from fetch_github import build_csv_url

    url = build_csv_url("466920", 2023)
    expected = "https://raw.githubusercontent.com/Raingel/historical_weather/master/data/466920/466920-2023.csv"
    assert url == expected


def test_build_csv_url_with_different_station():
    """測試不同站號的 URL"""
    from fetch_github import build_csv_url

    url = build_csv_url("467490", 2020)
    assert "467490" in url
    assert "2020" in url
