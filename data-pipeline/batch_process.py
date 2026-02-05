#!/usr/bin/env python3
"""批量處理多站點歷史資料

為多個氣象站點執行完整的 ETL 流程：
1. 從 GitHub 下載 CSV 資料
2. 清洗資料
3. 載入到資料庫
4. 計算統計快照
5. 更新 has_statistics 標記

使用方式:
    cd data-pipeline && python3 batch_process.py

注意：此程序會耗費較長時間（每站約 5-10 分鐘）
"""

import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# 將 backend/app 加入 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

from app.models import Base, RawObservation, DailyStatistics, Station
from app.analytics.engine import HistoricalWeatherAnalyzer

# 引入現有的模組
from fetch_github import download_station_data
from clean import merge_and_clean_all, get_data_quality_report
from load import load_and_aggregate_csv, load_to_database
from compute_snapshots import (
    load_observation_data,
    generate_366_days,
    compute_and_save_statistics,
    verify_statistics,
)


# 主要氣象站列表（有較完整的歷史資料）
# 來源: 中央氣象局主要觀測站
MAIN_STATIONS = [
    # (station_id, name, start_year)
    ("466920", "臺北", 1991),      # 已完成
    ("466940", "基隆", 1991),
    ("467490", "臺中", 1991),
    ("467441", "高雄", 1991),
    ("467350", "澎湖", 1991),
    ("467480", "嘉義", 1991),
    ("466990", "花蓮", 1991),
    ("467660", "臺東", 1991),
    ("467571", "新竹", 1991),
    ("467590", "恆春", 1991),
    ("467650", "日月潭", 1991),
    ("467530", "阿里山", 1991),
    ("467550", "玉山", 1991),
]

# 設定
END_YEAR = 2025
MIN_YEARS_REQUIRED = 10  # 至少需要 10 年資料才計算統計


def process_single_station(
    station_id: str,
    station_name: str,
    start_year: int,
    raw_dir: Path,
    processed_dir: Path,
    db_path: Path,
    skip_download: bool = False,
) -> dict:
    """處理單一站點的完整 ETL 流程

    Args:
        station_id: 站點代碼
        station_name: 站點名稱
        start_year: 資料起始年份
        raw_dir: 原始資料目錄
        processed_dir: 清洗後資料目錄
        db_path: 資料庫路徑
        skip_download: 是否跳過下載（如果已有資料）

    Returns:
        處理結果統計
    """
    result = {
        "station_id": station_id,
        "station_name": station_name,
        "success": False,
        "error": None,
        "downloaded_files": 0,
        "raw_records": 0,
        "daily_records": 0,
        "statistics_records": 0,
    }

    print(f"\n{'=' * 60}")
    print(f"處理站點: {station_name} ({station_id})")
    print(f"{'=' * 60}")

    try:
        # Step 1: 下載資料
        if not skip_download:
            print(f"\n[1/4] 下載資料 ({start_year}-{END_YEAR})...")
            downloaded = download_station_data(
                station_id=station_id,
                start_year=start_year,
                end_year=END_YEAR,
                output_dir=raw_dir,
                delay=0.3,  # 稍微降低延遲
            )
            result["downloaded_files"] = len(downloaded)

            if len(downloaded) < MIN_YEARS_REQUIRED:
                result["error"] = f"資料不足: 只下載到 {len(downloaded)} 個檔案"
                print(f"  [警告] {result['error']}")
                return result
        else:
            # 檢查現有檔案數量
            existing_files = list(raw_dir.glob(f"{station_id}_*.csv"))
            result["downloaded_files"] = len(existing_files)
            print(f"\n[1/4] 跳過下載，使用現有 {len(existing_files)} 個檔案")

        # Step 2: 清洗資料
        print(f"\n[2/4] 清洗資料...")
        output_csv = processed_dir / f"{station_id}_cleaned.csv"

        try:
            df = merge_and_clean_all(raw_dir, station_id, output_csv)
            result["raw_records"] = len(df)

            # 顯示資料品質
            report = get_data_quality_report(df)
            key_columns = ["temperature", "precipitation", "humidity"]
            for col in key_columns:
                if col in report["columns"]:
                    info = report["columns"][col]
                    print(f"  {col}: 缺失 {info['missing_percentage']}%")

        except FileNotFoundError as e:
            result["error"] = f"無原始資料: {e}"
            print(f"  [錯誤] {result['error']}")
            return result
        except ValueError as e:
            result["error"] = f"資料處理失敗: {e}"
            print(f"  [錯誤] {result['error']}")
            return result

        # Step 3: 載入資料庫
        print(f"\n[3/4] 載入資料庫...")
        daily_df = load_and_aggregate_csv(output_csv, station_id)
        result["daily_records"] = len(daily_df)

        if len(daily_df) < 365 * MIN_YEARS_REQUIRED:
            result["error"] = f"日級資料不足: 只有 {len(daily_df)} 筆"
            print(f"  [警告] {result['error']}")
            # 仍然繼續載入，但可能統計品質較差

        load_to_database(daily_df, db_path)

        # Step 4: 計算統計快照
        print(f"\n[4/4] 計算統計快照...")

        # 載入剛寫入的觀測資料
        obs_df = load_observation_data(db_path, station_id)

        if len(obs_df) == 0:
            result["error"] = "無觀測資料可計算統計"
            return result

        # 取得年份範圍
        obs_df["observed_date"] = pd.to_datetime(obs_df["observed_date"])
        actual_start_year = obs_df["observed_date"].dt.year.min()
        actual_end_year = obs_df["observed_date"].dt.year.max()

        print(f"  實際資料範圍: {actual_start_year} ~ {actual_end_year}")

        # 初始化分析器
        analyzer = HistoricalWeatherAnalyzer(obs_df)

        # 計算統計
        saved_count = compute_and_save_statistics(
            db_path, station_id, analyzer, actual_start_year, actual_end_year
        )
        result["statistics_records"] = saved_count

        # 驗證
        verify_statistics(db_path, station_id)

        # Step 5: 更新 has_statistics 標記
        print(f"\n[5/5] 更新 has_statistics 標記...")
        update_station_statistics_flag(db_path, station_id, True)

        result["success"] = True
        print(f"\n[完成] 站點 {station_name} 處理成功!")

    except Exception as e:
        result["error"] = str(e)
        print(f"\n[錯誤] 處理站點 {station_name} 時發生錯誤: {e}")
        import traceback
        traceback.print_exc()

    return result


def update_station_statistics_flag(db_path: Path, station_id: str, has_statistics: bool):
    """更新站點的 has_statistics 標記

    Args:
        db_path: 資料庫路徑
        station_id: 站點代碼
        has_statistics: 是否有統計資料
    """
    engine = create_engine(f"sqlite:///{db_path}", echo=False)

    with Session(engine) as session:
        station = session.query(Station).filter(
            Station.station_id == station_id
        ).first()

        if station:
            station.has_statistics = has_statistics
            session.commit()
            print(f"  已更新站點 {station.name} ({station_id}): has_statistics = {has_statistics}")
        else:
            print(f"  [警告] 找不到站點 {station_id}")


def main():
    """主程式進入點"""
    # 設定路徑
    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"
    db_path = project_root / "data" / "auspicious.db"

    # 確保目錄存在
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("好日子批量資料處理程式")
    print("=" * 60)
    print(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"資料庫: {db_path}")
    print(f"待處理站點: {len(MAIN_STATIONS)} 個")
    print()

    # 詢問是否跳過已完成的站點
    skip_completed = True  # 預設跳過已完成的

    # 檢查哪些站點已經有統計資料
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    completed_stations = set()

    with Session(engine) as session:
        stations_with_stats = session.query(Station).filter(
            Station.has_statistics == True
        ).all()
        completed_stations = {s.station_id for s in stations_with_stats}

    print(f"已完成站點: {len(completed_stations)} 個")
    for station_id, name, _ in MAIN_STATIONS:
        status = "✓ 已完成" if station_id in completed_stations else "○ 待處理"
        print(f"  {status}: {name} ({station_id})")

    print()

    # 處理結果
    results = []
    start_time = time.time()

    for station_id, station_name, start_year in MAIN_STATIONS:
        # 跳過已完成的站點
        if skip_completed and station_id in completed_stations:
            print(f"\n跳過已完成站點: {station_name} ({station_id})")
            continue

        # 檢查是否已有下載的資料
        existing_files = list(raw_dir.glob(f"{station_id}_*.csv"))
        skip_download = len(existing_files) >= 10  # 如果已有 10 個以上檔案，跳過下載

        result = process_single_station(
            station_id=station_id,
            station_name=station_name,
            start_year=start_year,
            raw_dir=raw_dir,
            processed_dir=processed_dir,
            db_path=db_path,
            skip_download=skip_download,
        )
        results.append(result)

        # 每個站點處理完後休息一下
        time.sleep(1)

    # 總結
    elapsed = time.time() - start_time

    print("\n" + "=" * 60)
    print("批量處理完成!")
    print("=" * 60)
    print(f"總耗時: {elapsed / 60:.1f} 分鐘")
    print()

    # 統計結果
    success_count = sum(1 for r in results if r["success"])
    failed_count = len(results) - success_count

    print(f"成功: {success_count} 個站點")
    print(f"失敗: {failed_count} 個站點")
    print()

    # 詳細結果
    print("詳細結果:")
    for r in results:
        status = "✓" if r["success"] else "✗"
        print(f"  {status} {r['station_name']} ({r['station_id']})")
        if r["success"]:
            print(f"      下載: {r['downloaded_files']} 檔")
            print(f"      日級資料: {r['daily_records']:,} 筆")
            print(f"      統計: {r['statistics_records']} 天")
        else:
            print(f"      錯誤: {r['error']}")

    # 更新總覽
    print()
    print("站點統計狀態:")
    with Session(engine) as session:
        all_stations = session.query(Station).filter(
            Station.has_statistics == True
        ).all()

        for s in all_stations:
            print(f"  ✓ {s.name} ({s.station_id}) - {s.county}")


if __name__ == "__main__":
    main()
