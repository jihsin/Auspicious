"""應用程式設定模組

使用 pydantic-settings 管理應用程式配置，
支援從環境變數和 .env 檔案載入設定。
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


# 專案根目錄（backend 的上一層）
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"


class Settings(BaseSettings):
    """應用程式設定類別

    Attributes:
        app_name: 應用程式名稱
        debug: 是否啟用除錯模式
        database_url: SQLite 資料庫連接字串
        data_dir: 資料目錄路徑
    """

    app_name: str = "好日子 API"
    debug: bool = True
    database_url: str = f"sqlite:///{DATA_DIR / 'auspicious.db'}"
    data_dir: Path = DATA_DIR

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# 全域設定實例
settings = Settings()
