#!/usr/bin/env python3
"""修正 NaN 聚合 bug 後，用既有 cleaned CSV 重新載入 + 重算統計。

不需重下載、不需重清洗。
用法:
    python3 data-pipeline/rerun_after_fix.py            # 全部站
    python3 data-pipeline/rerun_after_fix.py 466920     # 指定站
"""

import sys
from pathlib import Path

import pandas as pd

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

from app.analytics.engine import HistoricalWeatherAnalyzer  # noqa: E402

from load import load_and_aggregate_csv, load_to_database  # noqa: E402
from compute_snapshots import (  # noqa: E402
    compute_and_save_statistics,
    load_observation_data,
)


def rerun_station(station_id: str, processed_dir: Path, db_path: Path) -> dict:
    csv_path = processed_dir / f"{station_id}_cleaned.csv"
    if not csv_path.exists():
        return {"station_id": station_id, "skipped": True, "reason": "no cleaned CSV"}

    print(f"\n=== {station_id} ===")
    daily_df = load_and_aggregate_csv(csv_path, station_id)
    load_to_database(daily_df, db_path)

    obs_df = load_observation_data(db_path, station_id)
    obs_df["observed_date"] = pd.to_datetime(obs_df["observed_date"])
    start_year = int(obs_df["observed_date"].dt.year.min())
    end_year = int(obs_df["observed_date"].dt.year.max())

    analyzer = HistoricalWeatherAnalyzer(obs_df)
    saved = compute_and_save_statistics(db_path, station_id, analyzer, start_year, end_year)

    return {
        "station_id": station_id,
        "skipped": False,
        "daily_records": len(daily_df),
        "stats_saved": saved,
        "year_range": f"{start_year}-{end_year}",
    }


def main():
    processed_dir = project_root / "data" / "processed"
    db_path = project_root / "data" / "auspicious.db"

    if len(sys.argv) > 1:
        targets = [sys.argv[1]]
    else:
        targets = sorted({p.stem.split("_")[0] for p in processed_dir.glob("*_cleaned.csv")})

    print(f"Targets: {len(targets)} station(s)")
    results = []
    for sid in targets:
        try:
            results.append(rerun_station(sid, processed_dir, db_path))
        except Exception as e:
            print(f"  [error] {sid}: {e}")
            results.append({"station_id": sid, "skipped": True, "reason": str(e)})

    print("\n=== summary ===")
    for r in results:
        print(r)


if __name__ == "__main__":
    main()
