"""氣象觀測資料模型

定義日級彙總的氣象觀測資料 ORM 模型。
"""

from datetime import date
from typing import Optional

from sqlalchemy import Date, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class RawObservation(Base):
    """日級氣象觀測資料模型

    儲存從中央氣象局取得的歷史氣象資料，
    已從小時級資料彙總為日級統計資料。

    Attributes:
        id: 主鍵
        station_id: 氣象站代碼（如 466920 為台北站）
        observed_date: 觀測日期
        temperature_avg: 日平均溫度 (°C)
        temperature_max: 日最高溫度 (°C)
        temperature_min: 日最低溫度 (°C)
        precipitation: 日降水量總和 (mm)
        humidity_avg: 日平均相對濕度 (%)
        wind_speed_avg: 日平均風速 (m/s)
        wind_speed_max: 日最大風速 (m/s)
        sunshine_hours: 日照時數總和 (hr)
        station_pressure_avg: 日平均測站氣壓 (hPa)
        global_radiation_sum: 日全天空日射量總和 (MJ/m²)
    """

    __tablename__ = "raw_observations"

    # 使用複合唯一約束防止同一站點同一天有重複資料
    __table_args__ = (
        UniqueConstraint("station_id", "observed_date", name="uq_station_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    station_id: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    observed_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # 溫度相關欄位
    temperature_avg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    temperature_max: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    temperature_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # 降水與濕度
    precipitation: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    humidity_avg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # 風速
    wind_speed_avg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    wind_speed_max: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # 日照與輻射
    sunshine_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    global_radiation_sum: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # 氣壓
    station_pressure_avg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    def __repr__(self) -> str:
        return (
            f"RawObservation(station_id={self.station_id!r}, "
            f"observed_date={self.observed_date!r}, "
            f"temp_avg={self.temperature_avg})"
        )
