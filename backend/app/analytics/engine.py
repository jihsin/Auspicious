"""統計分析引擎

提供氣象資料的統計計算功能，包括：
- 基本統計量計算（mean, median, std_dev, percentiles）
- 降水統計（probability, heavy_rain_probability, max）
- 天氣傾向分析（sunny/cloudy/rainy 比例）
- 歷史天氣分析器（支援滑動視窗查詢）

降水定義：
- 有雨：降水量 > 0.1mm
- 大雨：降水量 > 50mm
- 晴天：降水 < 0.1mm 且日照 > 3 小時
- 雨天：降水 >= 1mm
- 陰天：其他
"""

from typing import Any

import numpy as np
import pandas as pd


# ============================================================================
# 常數定義
# ============================================================================

# 降水閾值
RAIN_THRESHOLD = 0.1  # mm，超過此值視為有雨
HEAVY_RAIN_THRESHOLD = 50.0  # mm，超過此值視為大雨
RAINY_DAY_THRESHOLD = 1.0  # mm，用於天氣傾向判定

# 日照閾值
SUNNY_SUNSHINE_THRESHOLD = 3.0  # 小時，晴天的最低日照時數


# ============================================================================
# 基本統計函式
# ============================================================================


def compute_basic_stats(data: pd.Series) -> dict[str, Any]:
    """計算基本統計量

    Args:
        data: 數值型 pandas Series

    Returns:
        包含統計量的字典：
        - mean: 平均值
        - median: 中位數
        - std_dev: 標準差
        - min: 最小值
        - max: 最大值
        - percentile_25: 第 25 百分位數
        - percentile_75: 第 75 百分位數
        - count: 有效資料筆數（排除 NaN）
    """
    # 移除 NaN 值
    clean_data = data.dropna()

    if len(clean_data) == 0:
        return {
            "mean": np.nan,
            "median": np.nan,
            "std_dev": np.nan,
            "min": np.nan,
            "max": np.nan,
            "percentile_25": np.nan,
            "percentile_75": np.nan,
            "count": 0,
        }

    return {
        "mean": float(clean_data.mean()),
        "median": float(clean_data.median()),
        "std_dev": float(clean_data.std()),
        "min": float(clean_data.min()),
        "max": float(clean_data.max()),
        "percentile_25": float(clean_data.quantile(0.25)),
        "percentile_75": float(clean_data.quantile(0.75)),
        "count": len(clean_data),
    }


def compute_precipitation_stats(precip: pd.Series) -> dict[str, Any]:
    """計算降水統計

    Args:
        precip: 降水量 pandas Series (單位: mm)

    Returns:
        包含降水統計的字典：
        - probability: 降雨機率 (>0.1mm 的天數比例)
        - heavy_rain_probability: 大雨機率 (>50mm 的天數比例)
        - max_recorded_mm: 歷史最大降水量
        - mean_rain_day_mm: 有雨日的平均降水量
        - total_days: 總天數
        - rain_days: 有雨天數
    """
    clean_precip = precip.dropna()

    if len(clean_precip) == 0:
        return {
            "probability": 0.0,
            "heavy_rain_probability": 0.0,
            "max_recorded_mm": 0.0,
            "mean_rain_day_mm": 0.0,
            "total_days": 0,
            "rain_days": 0,
        }

    total_days = len(clean_precip)
    rain_days = (clean_precip >= RAIN_THRESHOLD).sum()
    heavy_rain_days = (clean_precip > HEAVY_RAIN_THRESHOLD).sum()

    # 有雨日的平均降水量
    rain_day_values = clean_precip[clean_precip >= RAIN_THRESHOLD]
    mean_rain_day = float(rain_day_values.mean()) if len(rain_day_values) > 0 else 0.0

    return {
        "probability": float(rain_days / total_days),
        "heavy_rain_probability": float(heavy_rain_days / total_days),
        "max_recorded_mm": float(clean_precip.max()),
        "mean_rain_day_mm": mean_rain_day,
        "total_days": total_days,
        "rain_days": int(rain_days),
    }


def compute_weather_tendency(
    precip: pd.Series, sunshine: pd.Series
) -> dict[str, Any]:
    """計算天氣傾向

    根據降水量和日照時數判定天氣類型：
    - 晴天 (sunny): 降水 < 0.1mm 且日照 > 3 小時
    - 雨天 (rainy): 降水 >= 1mm
    - 陰天 (cloudy): 其他情況

    Args:
        precip: 降水量 pandas Series (單位: mm)
        sunshine: 日照時數 pandas Series (單位: 小時)

    Returns:
        包含天氣傾向的字典：
        - sunny: 晴天比例
        - cloudy: 陰天比例
        - rainy: 雨天比例
        - dominant: 主要天氣類型
        - total_valid_days: 有效資料天數
    """
    # 對齊兩個 Series，只保留兩者都有值的日期
    combined = pd.DataFrame({"precip": precip, "sunshine": sunshine}).dropna()

    if len(combined) == 0:
        return {
            "sunny": 0.0,
            "cloudy": 0.0,
            "rainy": 0.0,
            "dominant": "unknown",
            "total_valid_days": 0,
        }

    total_days = len(combined)

    # 判定天氣類型
    is_rainy = combined["precip"] >= RAINY_DAY_THRESHOLD
    is_sunny = (combined["precip"] < RAIN_THRESHOLD) & (
        combined["sunshine"] > SUNNY_SUNSHINE_THRESHOLD
    )
    is_cloudy = ~is_rainy & ~is_sunny

    sunny_ratio = float(is_sunny.sum() / total_days)
    cloudy_ratio = float(is_cloudy.sum() / total_days)
    rainy_ratio = float(is_rainy.sum() / total_days)

    # 決定主要天氣類型
    max_ratio = max(sunny_ratio, cloudy_ratio, rainy_ratio)
    if max_ratio == sunny_ratio:
        dominant = "sunny"
    elif max_ratio == rainy_ratio:
        dominant = "rainy"
    else:
        dominant = "cloudy"

    return {
        "sunny": sunny_ratio,
        "cloudy": cloudy_ratio,
        "rainy": rainy_ratio,
        "dominant": dominant,
        "total_valid_days": total_days,
    }


# ============================================================================
# 歷史天氣分析器類別
# ============================================================================


class HistoricalWeatherAnalyzer:
    """歷史天氣分析器

    提供基於歷史資料的統計分析功能，支援：
    - 指定日期的滑動視窗統計
    - 月份摘要統計
    - 跨年邊界處理

    Attributes:
        data: 包含觀測資料的 DataFrame
    """

    def __init__(self, data: pd.DataFrame):
        """初始化分析器

        Args:
            data: 包含觀測資料的 DataFrame，必須包含 'observed_date' 欄位
        """
        self.data = data.copy()

        # 確保日期欄位為 datetime 類型
        if "observed_date" in self.data.columns:
            self.data["observed_date"] = pd.to_datetime(self.data["observed_date"])
            # 提取月和日，用於滑動視窗查詢
            self.data["month"] = self.data["observed_date"].dt.month
            self.data["day"] = self.data["observed_date"].dt.day
            # 建立「年中天數」(day of year)，用於跨年計算
            self.data["day_of_year"] = self.data["observed_date"].dt.dayofyear

    def get_date_range_stats(
        self, month: int, day: int, window_days: int = 3
    ) -> dict[str, Any]:
        """取得指定日期範圍的統計資料

        使用滑動視窗方法，收集歷史上同一時期的資料進行統計。
        例如查詢 1 月 15 日 ±3 天，會收集歷年 1/12 ~ 1/18 的資料。

        Args:
            month: 月份 (1-12)
            day: 日期 (1-31)
            window_days: 視窗半徑天數（預設 3 天，即 ±3 天共 7 天）

        Returns:
            包含統計資料的字典
        """
        # 計算目標日期的 day_of_year（使用非閏年）
        target_date = pd.Timestamp(year=2023, month=month, day=day)
        target_doy = target_date.dayofyear

        # 處理跨年邊界
        # 建立視窗範圍（考慮年首年尾）
        window_doys = []
        for offset in range(-window_days, window_days + 1):
            doy = target_doy + offset
            if doy < 1:
                doy += 365
            elif doy > 365:
                doy -= 365
            window_doys.append(doy)

        # 篩選視窗內的資料
        # 需要特別處理閏年（366 天）
        mask = self.data["day_of_year"].isin(window_doys) | (
            (self.data["day_of_year"] == 366)
            & (366 - 365 + target_doy in window_doys)
        )
        window_data = self.data[mask]

        # 計算各項統計
        result = {
            "target_date": f"{month:02d}-{day:02d}",
            "window_days": window_days,
            "sample_size": len(window_data),
        }

        # 溫度統計
        if "temperature_avg" in window_data.columns:
            result["temperature"] = compute_basic_stats(window_data["temperature_avg"])

            if "temperature_max" in window_data.columns:
                result["temperature"]["max_stats"] = compute_basic_stats(
                    window_data["temperature_max"]
                )
            if "temperature_min" in window_data.columns:
                result["temperature"]["min_stats"] = compute_basic_stats(
                    window_data["temperature_min"]
                )

        # 降水統計
        if "precipitation" in window_data.columns:
            result["precipitation"] = compute_precipitation_stats(
                window_data["precipitation"]
            )

        # 天氣傾向
        if (
            "precipitation" in window_data.columns
            and "sunshine_hours" in window_data.columns
        ):
            result["weather_tendency"] = compute_weather_tendency(
                window_data["precipitation"], window_data["sunshine_hours"]
            )

        # 濕度統計
        if "humidity_avg" in window_data.columns:
            result["humidity"] = compute_basic_stats(window_data["humidity_avg"])

        return result

    def get_monthly_summary(self, month: int) -> dict[str, Any]:
        """取得月份摘要統計

        Args:
            month: 月份 (1-12)

        Returns:
            包含月份摘要的字典
        """
        month_data = self.data[self.data["month"] == month]

        if len(month_data) == 0:
            return {
                "month": month,
                "sample_size": 0,
                "avg_temperature": np.nan,
                "rain_days": 0,
                "avg_sunshine_hours": np.nan,
            }

        result = {
            "month": month,
            "sample_size": len(month_data),
        }

        # 平均溫度
        if "temperature_avg" in month_data.columns:
            result["avg_temperature"] = float(month_data["temperature_avg"].mean())

        # 雨天數
        if "precipitation" in month_data.columns:
            result["rain_days"] = int(
                (month_data["precipitation"] >= RAIN_THRESHOLD).sum()
            )
            result["rain_days_ratio"] = float(
                result["rain_days"] / len(month_data)
            )

        # 平均日照時數
        if "sunshine_hours" in month_data.columns:
            result["avg_sunshine_hours"] = float(month_data["sunshine_hours"].mean())

        # 溫度範圍
        if "temperature_max" in month_data.columns:
            result["avg_high_temperature"] = float(month_data["temperature_max"].mean())
        if "temperature_min" in month_data.columns:
            result["avg_low_temperature"] = float(month_data["temperature_min"].mean())

        return result
