# backend/app/database.py
"""資料庫連線管理"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.config import settings
from app.models import Base


engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}  # SQLite 專用
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """初始化資料庫表"""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """取得資料庫 session（FastAPI 依賴注入用）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
