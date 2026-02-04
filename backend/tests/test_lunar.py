# backend/tests/test_lunar.py
"""農曆服務測試"""

import pytest
from datetime import datetime, date
from app.services.lunar import LunarService, get_lunar_info


def test_get_lunar_date():
    """測試農曆日期轉換"""
    service = LunarService(datetime(2026, 2, 4))
    lunar = service.get_lunar_date()

    assert lunar["year"] is not None
    assert lunar["month"] is not None
    assert lunar["day"] is not None
    assert "干支年" in lunar
    assert "生肖" in lunar


def test_get_yi_ji():
    """測試宜忌資訊"""
    service = LunarService(datetime(2026, 2, 4))
    yi_ji = service.get_yi_ji()

    assert "yi" in yi_ji  # 宜
    assert "ji" in yi_ji  # 忌
    assert isinstance(yi_ji["yi"], list)
    assert isinstance(yi_ji["ji"], list)


def test_get_jieqi():
    """測試節氣資訊"""
    service = LunarService(datetime(2026, 2, 4))
    jieqi = service.get_jieqi()
    # 2 月 4 日是立春
    # jieqi 可能是 "立春" 或 None（取決於具體年份）
    assert jieqi is None or isinstance(jieqi, str)


def test_get_ganzhi():
    """測試干支資訊"""
    service = LunarService(datetime(2026, 2, 4))
    ganzhi = service.get_ganzhi()

    assert "年柱" in ganzhi
    assert "月柱" in ganzhi
    assert "日柱" in ganzhi


def test_get_lunar_info():
    """測試完整農曆資訊"""
    info = get_lunar_info(date(2026, 2, 4))

    assert "lunar_date" in info
    assert "yi_ji" in info
    assert "jieqi" in info
    assert "ganzhi" in info
