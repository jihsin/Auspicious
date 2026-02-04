"""統計分析引擎測試

使用 TDD 方法，先定義測試案例，再實作功能。
"""

import pytest
import pandas as pd
import numpy as np
from datetime import date


class TestComputeBasicStats:
    """測試基本統計計算"""

    def test_compute_basic_stats_normal_data(self):
        """測試正常數據的基本統計"""
        from app.analytics.engine import compute_basic_stats

        data = pd.Series([10.0, 15.0, 20.0, 25.0, 30.0])
        stats = compute_basic_stats(data)

        assert stats["mean"] == 20.0
        assert stats["median"] == 20.0
        assert "std_dev" in stats
        assert "percentile_25" in stats
        assert "percentile_75" in stats
        assert stats["percentile_25"] == 15.0
        assert stats["percentile_75"] == 25.0

    def test_compute_basic_stats_with_nan(self):
        """測試含有 NaN 值的數據"""
        from app.analytics.engine import compute_basic_stats

        data = pd.Series([10.0, np.nan, 20.0, np.nan, 30.0])
        stats = compute_basic_stats(data)

        # 應該忽略 NaN 值
        assert stats["mean"] == 20.0
        assert stats["count"] == 3

    def test_compute_basic_stats_empty_series(self):
        """測試空數據"""
        from app.analytics.engine import compute_basic_stats

        data = pd.Series([], dtype=float)
        stats = compute_basic_stats(data)

        assert np.isnan(stats["mean"])
        assert stats["count"] == 0


class TestComputePrecipitationStats:
    """測試降水統計計算"""

    def test_compute_precipitation_stats_normal(self):
        """測試正常降水數據"""
        from app.analytics.engine import compute_precipitation_stats

        # 10 天中有 3 天下雨（>0.1mm 視為有雨）
        precip = pd.Series([0, 0, 5.0, 0, 0, 10.0, 0, 0, 0, 60.0])
        stats = compute_precipitation_stats(precip)

        assert stats["probability"] == 0.3  # 3/10
        assert stats["heavy_rain_probability"] == 0.1  # 1/10 (>50mm)
        assert stats["max_recorded_mm"] == 60.0

    def test_compute_precipitation_stats_no_rain(self):
        """測試完全無雨的數據"""
        from app.analytics.engine import compute_precipitation_stats

        precip = pd.Series([0, 0, 0, 0, 0])
        stats = compute_precipitation_stats(precip)

        assert stats["probability"] == 0.0
        assert stats["heavy_rain_probability"] == 0.0
        assert stats["max_recorded_mm"] == 0.0

    def test_compute_precipitation_stats_light_rain(self):
        """測試微量降雨（<0.1mm 不計入）"""
        from app.analytics.engine import compute_precipitation_stats

        # 0.05mm 應該不算有雨
        precip = pd.Series([0.05, 0.08, 0.1, 0.5, 1.0])
        stats = compute_precipitation_stats(precip)

        # 只有 0.1, 0.5, 1.0 算有雨 => 3/5 = 0.6
        assert stats["probability"] == 0.6


class TestComputeWeatherTendency:
    """測試天氣傾向計算"""

    def test_compute_weather_tendency_sunny(self):
        """測試晴天主導的數據"""
        from app.analytics.engine import compute_weather_tendency

        # 模擬數據：5 天晴、3 天陰、2 天雨
        # 晴天: 降水 < 0.1mm 且日照 > 3hr
        # 雨天: 降水 >= 1mm
        # 陰天: 其他
        precip = pd.Series([0, 0, 0, 0, 0, 0.5, 0.5, 0.5, 5.0, 10.0])
        sunshine = pd.Series([8, 7, 9, 6, 8, 1, 2, 1, 0, 0])

        tendency = compute_weather_tendency(precip, sunshine)

        assert "sunny" in tendency
        assert "cloudy" in tendency
        assert "rainy" in tendency
        assert tendency["dominant"] in ["sunny", "cloudy", "rainy"]
        assert tendency["sunny"] == 0.5  # 5/10
        assert tendency["rainy"] == 0.2  # 2/10 (>=1mm)
        assert tendency["cloudy"] == 0.3  # 3/10

    def test_compute_weather_tendency_rainy(self):
        """測試雨天主導的數據"""
        from app.analytics.engine import compute_weather_tendency

        precip = pd.Series([5.0, 10.0, 15.0, 20.0, 1.0])
        sunshine = pd.Series([0, 0, 0, 0, 0])

        tendency = compute_weather_tendency(precip, sunshine)

        assert tendency["dominant"] == "rainy"
        assert tendency["rainy"] == 1.0

    def test_compute_weather_tendency_with_nan(self):
        """測試含有 NaN 值的天氣傾向"""
        from app.analytics.engine import compute_weather_tendency

        precip = pd.Series([0, np.nan, 5.0])
        sunshine = pd.Series([8, np.nan, 0])

        tendency = compute_weather_tendency(precip, sunshine)

        # 有效數據只有 2 天
        assert tendency["total_valid_days"] == 2


class TestHistoricalWeatherAnalyzer:
    """測試歷史天氣分析器"""

    @pytest.fixture
    def sample_df(self):
        """建立測試用的 DataFrame"""
        dates = pd.date_range(start="2020-01-01", periods=365, freq="D")
        np.random.seed(42)

        return pd.DataFrame({
            "observed_date": dates,
            "temperature_avg": np.random.normal(25, 5, 365),
            "temperature_max": np.random.normal(30, 5, 365),
            "temperature_min": np.random.normal(20, 5, 365),
            "precipitation": np.random.exponential(5, 365),
            "sunshine_hours": np.random.uniform(0, 12, 365),
            "humidity_avg": np.random.uniform(50, 90, 365),
        })

    def test_analyzer_initialization(self, sample_df):
        """測試分析器初始化"""
        from app.analytics.engine import HistoricalWeatherAnalyzer

        analyzer = HistoricalWeatherAnalyzer(sample_df)
        assert analyzer.data is not None
        assert len(analyzer.data) == 365

    def test_get_date_range_stats(self, sample_df):
        """測試指定日期範圍的統計"""
        from app.analytics.engine import HistoricalWeatherAnalyzer

        analyzer = HistoricalWeatherAnalyzer(sample_df)

        # 查詢 1 月 15 日的歷史統計（±3 天視窗）
        stats = analyzer.get_date_range_stats(
            month=1, day=15, window_days=3
        )

        assert "temperature" in stats
        assert "precipitation" in stats
        assert "weather_tendency" in stats

    def test_get_date_range_stats_year_boundary(self, sample_df):
        """測試跨年邊界的統計（如 1 月 1 日±3 天）"""
        from app.analytics.engine import HistoricalWeatherAnalyzer

        # 需要多年資料才能正確測試
        dates = pd.date_range(start="2019-01-01", end="2021-12-31", freq="D")
        np.random.seed(42)

        multi_year_df = pd.DataFrame({
            "observed_date": dates,
            "temperature_avg": np.random.normal(25, 5, len(dates)),
            "precipitation": np.random.exponential(5, len(dates)),
            "sunshine_hours": np.random.uniform(0, 12, len(dates)),
        })

        analyzer = HistoricalWeatherAnalyzer(multi_year_df)

        # 查詢 1 月 1 日（應該也要包含 12 月底的資料）
        stats = analyzer.get_date_range_stats(
            month=1, day=1, window_days=3
        )

        # 應該有來自多年的資料
        assert stats["sample_size"] > 7  # 至少 3 年 * 7 天 = 21 天資料

    def test_get_monthly_summary(self, sample_df):
        """測試月份摘要統計"""
        from app.analytics.engine import HistoricalWeatherAnalyzer

        analyzer = HistoricalWeatherAnalyzer(sample_df)

        summary = analyzer.get_monthly_summary(month=1)

        assert "avg_temperature" in summary
        assert "rain_days" in summary
        assert "avg_sunshine_hours" in summary
