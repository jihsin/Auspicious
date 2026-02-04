"""資料模型模組

包含 SQLAlchemy ORM 模型定義。
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy 宣告式基底類別"""
    pass


# 匯出所有模型
from app.models.observation import RawObservation

__all__ = ["Base", "RawObservation"]
