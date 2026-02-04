"""氣象站點資料模型

儲存全台觀測站的基本資訊與經緯度。
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models import Base


class Station(Base):
    """氣象站點資料表

    儲存全台 835 個觀測站的基本資訊與經緯度，
    支援基於位置的最近站點查詢。

    Attributes:
        id: 主鍵
        station_id: 氣象站代碼（如 466920）
        name: 站點名稱

        # 地理資訊
        county: 縣市名稱
        town: 鄉鎮市區名稱
        latitude: 緯度 (WGS84)
        longitude: 經度 (WGS84)
        altitude: 海拔高度 (公尺)

        # 狀態
        is_active: 是否啟用
        has_statistics: 是否有歷史統計資料

        # 元數據
        created_at: 建立時間
        updated_at: 更新時間
    """

    __tablename__ = "stations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    station_id: Mapped[str] = mapped_column(
        String(10), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)

    # 地理資訊
    county: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    town: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    altitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # 狀態
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    has_statistics: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # 元數據
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<Station {self.station_id}: {self.name}>"
