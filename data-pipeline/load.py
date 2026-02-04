#!/usr/bin/env python3
"""資料載入腳本

將清洗後的小時級 CSV 資料聚合為日級資料，
並載入到 SQLite 資料庫中。

使用方式:
    poetry run python data-pipeline/load.py
"""

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# 將 backend/app 加入 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

from app.models import Base, RawObservation


def load_and_aggregate_csv(csv_path: Path, station_id: str) -> pd.DataFrame:
    """讀取小時級 CSV 並聚合為日級資料

    Args:
        csv_path: CSV 檔案路徑
        station_id: 氣象站代碼

    Returns:
        日級彙總的 DataFrame
    """
    print(f"正在讀取 CSV: {csv_path}")

    # 讀取 CSV
    df = pd.read_csv(csv_path, parse_dates=["observed_datetime"])

    print(f"原始資料筆數: {len(df):,} 筆小時資料")

    # 提取日期欄位
    df["observed_date"] = df["observed_datetime"].dt.date

    # 按日期分組並計算聚合統計
    print("正在聚合為日級資料...")

    daily_agg = df.groupby("observed_date").agg(
        temperature_avg=("temperature", "mean"),
        temperature_max=("temperature", "max"),
        temperature_min=("temperature", "min"),
        precipitation=("precipitation", "sum"),
        humidity_avg=("humidity", "mean"),
        wind_speed_avg=("wind_speed", "mean"),
        wind_speed_max=("wind_speed", "max"),
        sunshine_hours=("sunshine_hours", "sum"),
        global_radiation_sum=("global_radiation", "sum"),
        station_pressure_avg=("station_pressure", "mean"),
    ).reset_index()

    # 加入站點 ID
    daily_agg["station_id"] = station_id

    # 四捨五入到合理精度
    float_columns = [
        "temperature_avg", "temperature_max", "temperature_min",
        "precipitation", "humidity_avg", "wind_speed_avg", "wind_speed_max",
        "sunshine_hours", "global_radiation_sum", "station_pressure_avg"
    ]
    for col in float_columns:
        if col in daily_agg.columns:
            daily_agg[col] = daily_agg[col].round(2)

    print(f"聚合後資料筆數: {len(daily_agg):,} 筆日級資料")

    return daily_agg


def load_to_database(df: pd.DataFrame, db_path: Path) -> int:
    """將 DataFrame 載入到 SQLite 資料庫

    Args:
        df: 日級彙總的 DataFrame
        db_path: 資料庫檔案路徑

    Returns:
        成功載入的記錄數
    """
    # 確保資料目錄存在
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # 建立資料庫引擎
    engine = create_engine(f"sqlite:///{db_path}", echo=False)

    # 建立所有資料表
    print(f"正在建立資料庫: {db_path}")
    Base.metadata.create_all(engine)

    # 載入資料
    print("正在載入資料到資料庫...")
    loaded_count = 0
    skipped_count = 0

    # 準備批次插入的資料
    records = []
    for _, row in df.iterrows():
        record = {
            "station_id": row["station_id"],
            "observed_date": row["observed_date"],
            "temperature_avg": row["temperature_avg"] if pd.notna(row["temperature_avg"]) else None,
            "temperature_max": row["temperature_max"] if pd.notna(row["temperature_max"]) else None,
            "temperature_min": row["temperature_min"] if pd.notna(row["temperature_min"]) else None,
            "precipitation": row["precipitation"] if pd.notna(row["precipitation"]) else None,
            "humidity_avg": row["humidity_avg"] if pd.notna(row["humidity_avg"]) else None,
            "wind_speed_avg": row["wind_speed_avg"] if pd.notna(row["wind_speed_avg"]) else None,
            "wind_speed_max": row["wind_speed_max"] if pd.notna(row["wind_speed_max"]) else None,
            "sunshine_hours": row["sunshine_hours"] if pd.notna(row["sunshine_hours"]) else None,
            "global_radiation_sum": row["global_radiation_sum"] if pd.notna(row["global_radiation_sum"]) else None,
            "station_pressure_avg": row["station_pressure_avg"] if pd.notna(row["station_pressure_avg"]) else None,
        }
        records.append(record)

    # 使用批次插入（先刪除該站點的現有資料，再插入新資料）
    with Session(engine) as session:
        # 取得此批次的站點 ID
        station_ids = df["station_id"].unique()

        for station_id in station_ids:
            # 刪除該站點的現有資料
            deleted = session.query(RawObservation).filter(
                RawObservation.station_id == station_id
            ).delete()
            if deleted > 0:
                print(f"  已刪除站點 {station_id} 的 {deleted:,} 筆舊資料")

        session.commit()

        # 批次插入新資料
        batch_size = 1000
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            session.execute(
                RawObservation.__table__.insert(),
                batch
            )
            loaded_count += len(batch)
            print(f"  已插入 {loaded_count:,} / {len(records):,} 筆...")

        session.commit()

    print(f"載入完成: {loaded_count:,} 筆記錄")
    return loaded_count


def verify_database(db_path: Path) -> None:
    """驗證資料庫內容

    Args:
        db_path: 資料庫檔案路徑
    """
    engine = create_engine(f"sqlite:///{db_path}", echo=False)

    with Session(engine) as session:
        # 統計記錄數
        total_count = session.query(RawObservation).count()
        print(f"\n=== 資料庫驗證 ===")
        print(f"總記錄數: {total_count:,}")

        # 取得日期範圍
        from sqlalchemy import func
        result = session.query(
            func.min(RawObservation.observed_date),
            func.max(RawObservation.observed_date)
        ).first()

        if result and result[0]:
            print(f"日期範圍: {result[0]} ~ {result[1]}")

        # 取得各站點統計
        stations = session.query(
            RawObservation.station_id,
            func.count(RawObservation.id)
        ).group_by(RawObservation.station_id).all()

        print(f"站點數: {len(stations)}")
        for station_id, count in stations:
            print(f"  - {station_id}: {count:,} 筆")

        # 抽樣顯示幾筆資料
        print("\n最近 5 筆資料:")
        samples = session.query(RawObservation).order_by(
            RawObservation.observed_date.desc()
        ).limit(5).all()

        for obs in samples:
            print(f"  {obs.observed_date}: 溫度={obs.temperature_avg}°C, "
                  f"降水={obs.precipitation}mm, 濕度={obs.humidity_avg}%")


def main():
    """主程式進入點"""
    # 設定路徑
    project_root = Path(__file__).parent.parent
    csv_path = project_root / "data" / "processed" / "466920_cleaned.csv"
    db_path = project_root / "data" / "auspicious.db"

    # 台北站代碼
    station_id = "466920"

    # 檢查 CSV 是否存在
    if not csv_path.exists():
        print(f"錯誤: 找不到 CSV 檔案: {csv_path}")
        sys.exit(1)

    print("=" * 50)
    print("好日子資料載入程式")
    print("=" * 50)
    print(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 載入並聚合資料
    daily_df = load_and_aggregate_csv(csv_path, station_id)

    # 載入到資料庫
    load_to_database(daily_df, db_path)

    # 驗證結果
    verify_database(db_path)

    print("\n載入程式執行完成!")


if __name__ == "__main__":
    main()
