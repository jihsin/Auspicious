#!/usr/bin/env python3
"""統計快照計算腳本

為全年 366 天（含閏年 2/29）生成預計算統計資料，
並儲存到 daily_statistics 表中。

使用方式:
    cd data-pipeline && python3 compute_snapshots.py

注意：此腳本會清除現有的統計資料後重新計算。
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

from app.models import Base, RawObservation, DailyStatistics
from app.analytics.engine import HistoricalWeatherAnalyzer


def load_observation_data(db_path: Path, station_id: str) -> pd.DataFrame:
    """從資料庫載入觀測資料

    Args:
        db_path: 資料庫檔案路徑
        station_id: 氣象站代碼

    Returns:
        包含觀測資料的 DataFrame
    """
    engine = create_engine(f"sqlite:///{db_path}", echo=False)

    with Session(engine) as session:
        # 查詢該站點的所有觀測資料
        observations = session.query(RawObservation).filter(
            RawObservation.station_id == station_id
        ).all()

        # 轉換為 DataFrame
        data = []
        for obs in observations:
            data.append({
                "observed_date": obs.observed_date,
                "temperature_avg": obs.temperature_avg,
                "temperature_max": obs.temperature_max,
                "temperature_min": obs.temperature_min,
                "precipitation": obs.precipitation,
                "humidity_avg": obs.humidity_avg,
                "sunshine_hours": obs.sunshine_hours,
            })

        df = pd.DataFrame(data)
        print(f"載入 {len(df):,} 筆觀測資料")
        return df


def generate_366_days() -> list[tuple[int, int]]:
    """生成全年 366 天的月日組合

    Returns:
        [(month, day), ...] 的列表，包含 1/1 到 12/31 以及 2/29
    """
    days = []

    # 使用閏年來生成所有可能的日期
    # 2024 是閏年
    for month in range(1, 13):
        if month in [1, 3, 5, 7, 8, 10, 12]:
            max_day = 31
        elif month in [4, 6, 9, 11]:
            max_day = 30
        else:  # 2 月
            max_day = 29  # 包含閏年

        for day in range(1, max_day + 1):
            days.append((month, day))

    return days


def compute_and_save_statistics(
    db_path: Path,
    station_id: str,
    analyzer: HistoricalWeatherAnalyzer,
    start_year: int,
    end_year: int,
) -> int:
    """計算並儲存統計資料

    Args:
        db_path: 資料庫檔案路徑
        station_id: 氣象站代碼
        analyzer: 已初始化的分析器
        start_year: 資料起始年份
        end_year: 資料結束年份

    Returns:
        成功儲存的記錄數
    """
    engine = create_engine(f"sqlite:///{db_path}", echo=False)

    # 確保資料表存在
    Base.metadata.create_all(engine)

    # 生成 366 天
    all_days = generate_366_days()
    print(f"將計算 {len(all_days)} 天的統計資料...")

    # 計算每天的統計
    statistics_records = []

    for i, (month, day) in enumerate(all_days):
        # 取得該日期的統計（使用 ±3 天的滑動視窗）
        stats = analyzer.get_date_range_stats(month, day, window_days=3)

        # 建立記錄
        record = DailyStatistics(
            station_id=station_id,
            month_day=f"{month:02d}-{day:02d}",
            years_analyzed=end_year - start_year + 1,
            start_year=start_year,
            end_year=end_year,
        )

        # 溫度統計
        if "temperature" in stats:
            temp = stats["temperature"]
            record.temp_avg_mean = temp.get("mean")
            record.temp_avg_median = temp.get("median")
            record.temp_avg_stddev = temp.get("std_dev")

            # 最高溫統計
            if "max_stats" in temp:
                record.temp_max_mean = temp["max_stats"].get("mean")
                record.temp_max_record = temp["max_stats"].get("max")

            # 最低溫統計
            if "min_stats" in temp:
                record.temp_min_mean = temp["min_stats"].get("mean")
                record.temp_min_record = temp["min_stats"].get("min")

        # 降水統計
        if "precipitation" in stats:
            precip = stats["precipitation"]
            record.precip_probability = precip.get("probability")
            record.precip_avg_when_rain = precip.get("mean_rain_day_mm")
            record.precip_heavy_prob = precip.get("heavy_rain_probability")
            record.precip_max_record = precip.get("max_recorded_mm")

        # 天氣傾向
        if "weather_tendency" in stats:
            tendency = stats["weather_tendency"]
            record.tendency_sunny = tendency.get("sunny")
            record.tendency_cloudy = tendency.get("cloudy")
            record.tendency_rainy = tendency.get("rainy")

        statistics_records.append(record)

        # 進度顯示
        if (i + 1) % 50 == 0 or i == len(all_days) - 1:
            print(f"  已計算 {i + 1}/{len(all_days)} 天...")

    # 儲存到資料庫
    print("\n正在儲存到資料庫...")

    with Session(engine) as session:
        # 先刪除該站點的現有統計資料
        deleted = session.query(DailyStatistics).filter(
            DailyStatistics.station_id == station_id
        ).delete()

        if deleted > 0:
            print(f"  已刪除 {deleted:,} 筆舊統計資料")

        session.commit()

        # 批次插入新資料
        session.add_all(statistics_records)
        session.commit()

        print(f"  已插入 {len(statistics_records):,} 筆新統計資料")

    return len(statistics_records)


def verify_statistics(db_path: Path, station_id: str) -> None:
    """驗證統計資料

    Args:
        db_path: 資料庫檔案路徑
        station_id: 氣象站代碼
    """
    engine = create_engine(f"sqlite:///{db_path}", echo=False)

    with Session(engine) as session:
        # 統計記錄數
        total_count = session.query(DailyStatistics).filter(
            DailyStatistics.station_id == station_id
        ).count()

        print(f"\n=== 統計資料驗證 ===")
        print(f"站點 {station_id} 共有 {total_count:,} 筆統計資料")

        # 檢查是否有 366 天
        if total_count == 366:
            print("  [OK] 366 天統計完整")
        else:
            print(f"  [警告] 預期 366 筆，實際 {total_count} 筆")

        # 抽樣顯示幾筆資料
        print("\n抽樣資料:")

        # 顯示幾個代表性日期
        sample_dates = ["01-01", "02-29", "07-15", "12-31"]
        for month_day in sample_dates:
            stat = session.query(DailyStatistics).filter(
                DailyStatistics.station_id == station_id,
                DailyStatistics.month_day == month_day
            ).first()

            if stat:
                print(f"  {month_day}: 平均溫度={stat.temp_avg_mean:.1f}°C, "
                      f"降雨機率={stat.precip_probability:.1%}, "
                      f"晴天={stat.tendency_sunny:.1%}")
            else:
                print(f"  {month_day}: 無資料")


def main():
    """主程式進入點"""
    # 設定路徑
    project_root = Path(__file__).parent.parent
    db_path = project_root / "data" / "auspicious.db"

    # 台北站代碼
    station_id = "466920"

    # 檢查資料庫是否存在
    if not db_path.exists():
        print(f"錯誤: 找不到資料庫檔案: {db_path}")
        sys.exit(1)

    print("=" * 60)
    print("好日子統計快照計算程式")
    print("=" * 60)
    print(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"資料庫: {db_path}")
    print(f"站點: {station_id}")
    print()

    # 載入觀測資料
    print("步驟 1/3: 載入觀測資料...")
    df = load_observation_data(db_path, station_id)

    if len(df) == 0:
        print("錯誤: 無觀測資料")
        sys.exit(1)

    # 取得資料年份範圍
    df["observed_date"] = pd.to_datetime(df["observed_date"])
    start_year = df["observed_date"].dt.year.min()
    end_year = df["observed_date"].dt.year.max()
    print(f"資料範圍: {start_year} ~ {end_year} ({end_year - start_year + 1} 年)")

    # 初始化分析器
    print("\n步驟 2/3: 計算統計資料...")
    analyzer = HistoricalWeatherAnalyzer(df)

    # 計算並儲存統計
    saved_count = compute_and_save_statistics(
        db_path, station_id, analyzer, start_year, end_year
    )

    # 驗證結果
    print("\n步驟 3/3: 驗證結果...")
    verify_statistics(db_path, station_id)

    print("\n" + "=" * 60)
    print("統計快照計算完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
