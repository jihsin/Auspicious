"""從 GitHub 下載歷史氣象數據"""

from __future__ import annotations

import httpx
from pathlib import Path
import time
from typing import Optional


GITHUB_BASE_URL = "https://raw.githubusercontent.com/Raingel/historical_weather/master/data"


def build_csv_url(station_id: str, year: int) -> str:
    """
    建構 CSV 檔案的 GitHub raw URL

    Args:
        station_id: 觀測站代碼，如 '466920'
        year: 年份，如 2023

    Returns:
        完整的 CSV 下載 URL
    """
    return f"{GITHUB_BASE_URL}/{station_id}/{station_id}_{year}.csv"


def download_csv(station_id: str, year: int, output_dir: Path) -> Optional[Path]:
    """
    下載單一年份的 CSV 檔案

    Args:
        station_id: 觀測站代碼
        year: 年份
        output_dir: 輸出目錄

    Returns:
        下載後的檔案路徑，失敗時返回 None
    """
    url = build_csv_url(station_id, year)
    output_path = output_dir / f"{station_id}_{year}.csv"

    try:
        response = httpx.get(url, timeout=30.0)
        response.raise_for_status()

        output_path.write_bytes(response.content)
        print(f"✓ Downloaded: {station_id}_{year}.csv")
        return output_path

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            print(f"✗ Not found: {station_id}_{year}.csv")
        else:
            print(f"✗ Error downloading {year}: {e}")
        return None


def download_station_data(
    station_id: str,
    start_year: int,
    end_year: int,
    output_dir: Path,
    delay: float = 0.5
) -> list[Path]:
    """
    下載指定站號的多年數據

    Args:
        station_id: 觀測站代碼
        start_year: 起始年份
        end_year: 結束年份（包含）
        output_dir: 輸出目錄
        delay: 每次下載間隔秒數（避免被限流）

    Returns:
        成功下載的檔案路徑列表
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    downloaded = []

    for year in range(start_year, end_year + 1):
        path = download_csv(station_id, year, output_dir)
        if path:
            downloaded.append(path)
        time.sleep(delay)

    print(f"\n總計下載 {len(downloaded)} 個檔案")
    return downloaded


if __name__ == "__main__":
    # 下載台北站 1991-2025 的數據（約 35 年）
    station_id = "466920"
    output_dir = Path("../data/raw")

    download_station_data(
        station_id=station_id,
        start_year=1991,
        end_year=2025,
        output_dir=output_dir
    )
