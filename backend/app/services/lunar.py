# backend/app/services/lunar.py
"""農曆服務

使用 cnlunar 庫提供農曆相關功能：
- 農曆日期轉換
- 每日宜忌
- 二十四節氣
- 干支紀年
"""

from datetime import datetime, date
from typing import Optional
import cnlunar


class LunarService:
    """農曆服務"""

    def __init__(self, dt: datetime):
        """初始化農曆服務

        Args:
            dt: 要查詢的日期時間
        """
        self.dt = dt
        self._lunar = cnlunar.Lunar(dt)

    def get_lunar_date(self) -> dict:
        """取得農曆日期

        Returns:
            農曆日期資訊
        """
        return {
            "year": self._lunar.lunarYear,
            "month": self._lunar.lunarMonth,
            "day": self._lunar.lunarDay,
            "year_cn": self._lunar.lunarYearCn,
            "month_cn": self._lunar.lunarMonthCn,
            "day_cn": self._lunar.lunarDayCn,
            "干支年": self._lunar.year8Char,
            "干支月": self._lunar.month8Char,
            "干支日": self._lunar.day8Char,
            "生肖": self._lunar.chineseYearZodiac,
            "is_leap": self._lunar.isLunarLeapMonth,
        }

    def get_yi_ji(self) -> dict:
        """取得每日宜忌

        Returns:
            宜忌資訊 {"yi": [...], "ji": [...]}
        """
        return {
            "yi": list(self._lunar.goodThing) if self._lunar.goodThing else [],
            "ji": list(self._lunar.badThing) if self._lunar.badThing else [],
        }

    def get_jieqi(self) -> Optional[str]:
        """取得當日節氣（如果有的話）

        Returns:
            節氣名稱，如果當天不是節氣則返回 None
        """
        jieqi = self._lunar.todaySolarTerms
        return jieqi if jieqi and jieqi != "無" else None

    def get_ganzhi(self) -> dict:
        """取得完整干支資訊

        Returns:
            年月日干支
        """
        return {
            "年柱": self._lunar.year8Char,
            "月柱": self._lunar.month8Char,
            "日柱": self._lunar.day8Char,
        }


def get_lunar_info(dt: date) -> dict:
    """取得完整農曆資訊（便捷函式）

    Args:
        dt: 日期

    Returns:
        完整農曆資訊
    """
    # 轉換為 datetime
    dt_full = datetime(dt.year, dt.month, dt.day, 12, 0)
    service = LunarService(dt_full)

    return {
        "lunar_date": service.get_lunar_date(),
        "yi_ji": service.get_yi_ji(),
        "jieqi": service.get_jieqi(),
        "ganzhi": service.get_ganzhi(),
    }
