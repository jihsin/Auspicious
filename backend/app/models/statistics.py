"""統計快照資料模型

儲存預計算的每日統計資料，用於快速查詢歷史天氣模式。
每個站點的每一天（MM-DD）都有一筆統計記錄。
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Float, Integer, String, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models import Base


class DailyStatistics(Base):
    """每日統計快照表

    儲存基於歷史資料計算的統計數據，用於 API 快速回應。
    每個站點的 366 天（含閏年 2/29）各有一筆記錄。

    Attributes:
        id: 主鍵
        station_id: 氣象站代碼
        month_day: 日期標識，格式 'MM-DD'

        # 分析期間
        years_analyzed: 分析的年數
        start_year: 資料起始年份
        end_year: 資料結束年份

        # 溫度統計 (°C)
        temp_avg_mean: 平均溫度的平均值
        temp_avg_median: 平均溫度的中位數
        temp_avg_stddev: 平均溫度的標準差
        temp_max_mean: 最高溫的平均值
        temp_max_record: 歷史最高溫紀錄
        temp_min_mean: 最低溫的平均值
        temp_min_record: 歷史最低溫紀錄

        # 降水統計
        precip_probability: 降雨機率 (0-1)
        precip_avg_when_rain: 有雨日的平均降水量 (mm)
        precip_heavy_prob: 大雨機率 (>50mm) (0-1)
        precip_max_record: 歷史最大降水量紀錄 (mm)

        # 天氣傾向 (比例，0-1)
        tendency_sunny: 晴天比例
        tendency_cloudy: 陰天比例
        tendency_rainy: 雨天比例

        # 元數據
        computed_at: 統計計算時間
    """

    __tablename__ = "daily_statistics"

    __table_args__ = (
        UniqueConstraint("station_id", "month_day", name="uq_station_monthday"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    station_id: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    month_day: Mapped[str] = mapped_column(String(5), nullable=False)  # 'MM-DD' 格式

    # 分析期間
    years_analyzed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    start_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    end_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # 溫度統計
    temp_avg_mean: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    temp_avg_median: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    temp_avg_stddev: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    temp_max_mean: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    temp_max_record: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    temp_min_mean: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    temp_min_record: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # 降水統計
    precip_probability: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    precip_avg_when_rain: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    precip_heavy_prob: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    precip_max_record: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # 天氣傾向
    tendency_sunny: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tendency_cloudy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tendency_rainy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # 元數據
    computed_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"DailyStatistics(station_id={self.station_id!r}, "
            f"month_day={self.month_day!r}, "
            f"temp_avg_mean={self.temp_avg_mean})"
        )
