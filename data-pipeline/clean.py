"""數據清洗模組

處理中央氣象局觀測資料的清洗工作：
- 移除缺失值標記（如 -99.8, -9999 等）
- 移除超出合理範圍的異常值
- 標準化日期格式
- 統一欄位命名
"""
from __future__ import annotations

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional


# 台灣合理的氣象數值範圍
VALID_RANGES = {
    "temperature": (-5, 45),      # 溫度 °C
    "precipitation": (0, 1000),   # 降水量 mm
    "humidity": (0, 100),         # 相對溼度 %
    "wind_speed": (0, 100),       # 風速 m/s
    "sunshine": (0, 14),          # 日照時數
    "pressure": (900, 1100),      # 氣壓 hPa
}

# 常見的缺失值標記（根據實際資料，-99.8 是主要標記）
MISSING_MARKERS = [-9999, -9999.0, -99, -99.0, -99.8, 9999, 9999.0, "", "NA", "N/A", "null", "..."]


def clean_temperature_column(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """
    清洗溫度欄位：移除缺失值標記和異常值
    
    Args:
        df: 輸入 DataFrame
        column: 要清洗的欄位名稱
        
    Returns:
        清洗後的 DataFrame（副本）
    """
    result = df.copy()
    min_val, max_val = VALID_RANGES["temperature"]

    # 轉換為數值型態
    result[column] = pd.to_numeric(result[column], errors="coerce")

    # 替換缺失值標記
    for marker in MISSING_MARKERS:
        if isinstance(marker, (int, float)):
            result.loc[result[column] == marker, column] = np.nan

    # 移除超出範圍的異常值
    result.loc[(result[column] < min_val) | (result[column] > max_val), column] = np.nan

    return result


def standardize_date_column(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """
    標準化日期欄位格式
    
    Args:
        df: 輸入 DataFrame
        column: 日期欄位名稱
        
    Returns:
        日期欄位已轉換為 datetime64 的 DataFrame
    """
    result = df.copy()
    result[column] = pd.to_datetime(result[column], format="mixed", errors="coerce")
    return result


def clean_precipitation_column(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """清洗降水量欄位"""
    result = df.copy()
    min_val, max_val = VALID_RANGES["precipitation"]

    result[column] = pd.to_numeric(result[column], errors="coerce")

    for marker in MISSING_MARKERS:
        if isinstance(marker, (int, float)):
            result.loc[result[column] == marker, column] = np.nan

    result.loc[(result[column] < min_val) | (result[column] > max_val), column] = np.nan

    return result


def clean_humidity_column(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """清洗相對溼度欄位"""
    result = df.copy()
    min_val, max_val = VALID_RANGES["humidity"]

    result[column] = pd.to_numeric(result[column], errors="coerce")

    for marker in MISSING_MARKERS:
        if isinstance(marker, (int, float)):
            result.loc[result[column] == marker, column] = np.nan

    result.loc[(result[column] < min_val) | (result[column] > max_val), column] = np.nan

    return result


def clean_csv_file(filepath: Path) -> pd.DataFrame:
    """
    清洗單一 CSV 檔案
    
    根據中央氣象局 CODIS 資料格式處理：
    - 第一欄（Unnamed: 0）是觀測時間
    - Tx: 溫度
    - RH: 相對溼度
    - Precp: 降水量
    - 缺失值標記為 -99.8
    
    Args:
        filepath: CSV 檔案路徑
        
    Returns:
        清洗後的 DataFrame
    """
    # 讀取 CSV
    df = pd.read_csv(filepath, encoding="utf-8")

    # 標準化欄位名稱（根據實際 CODIS CSV 欄位）
    column_mapping = {
        "Unnamed: 0": "observed_datetime",  # 觀測時間
        "StnPres": "station_pressure",       # 測站氣壓
        "SeaPres": "sea_pressure",           # 海平面氣壓
        "Tx": "temperature",                 # 溫度
        "Td": "dew_point",                   # 露點溫度
        "RH": "humidity",                    # 相對溼度
        "WS": "wind_speed",                  # 風速
        "WD": "wind_direction",              # 風向
        "WSGust": "wind_gust_speed",         # 最大陣風速
        "WDGust": "wind_gust_direction",     # 最大陣風向
        "Precp": "precipitation",            # 降水量
        "PrecpHour": "precipitation_hours",  # 降水時數
        "SunShine": "sunshine_hours",        # 日照時數
        "GloblRad": "global_radiation",      # 全天空日射量
        "Visb": "visibility",                # 能見度
        "UVI": "uv_index",                   # 紫外線指數
        "Cloud Amount": "cloud_amount",      # 雲量
        "VaporPressure": "vapor_pressure",   # 水氣壓
    }

    existing_mapping = {k: v for k, v in column_mapping.items() if k in df.columns}
    df = df.rename(columns=existing_mapping)

    # 日期標準化
    if "observed_datetime" in df.columns:
        df = standardize_date_column(df, "observed_datetime")

    # 清洗溫度欄位
    temp_columns = ["temperature", "dew_point"]
    for col in temp_columns:
        if col in df.columns:
            df = clean_temperature_column(df, col)

    # 清洗降水量
    if "precipitation" in df.columns:
        df = clean_precipitation_column(df, "precipitation")

    # 清洗溼度
    if "humidity" in df.columns:
        df = clean_humidity_column(df, "humidity")

    return df


def merge_and_clean_all(
    input_dir: Path,
    station_id: str,
    output_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    合併並清洗指定站號的所有 CSV 檔案
    
    Args:
        input_dir: 包含 CSV 檔案的目錄
        station_id: 氣象站編號（如 466920）
        output_path: 輸出檔案路徑（可選）
        
    Returns:
        合併並清洗後的 DataFrame
    """
    csv_files = sorted(input_dir.glob(f"{station_id}_*.csv"))

    if not csv_files:
        raise FileNotFoundError(f"No CSV files found for station {station_id}")

    all_dfs = []
    for filepath in csv_files:
        print(f"Processing: {filepath.name}")
        try:
            df = clean_csv_file(filepath)
            if len(df) > 0:
                all_dfs.append(df)
        except Exception as e:
            print(f"  Error processing {filepath.name}: {e}")

    if not all_dfs:
        raise ValueError("No valid data found")

    merged = pd.concat(all_dfs, ignore_index=True)

    # 按日期排序並去重
    if "observed_datetime" in merged.columns:
        merged = merged.sort_values("observed_datetime")
        merged = merged.drop_duplicates(subset=["observed_datetime"], keep="last")

    print(f"\n總計 {len(merged)} 筆記錄")
    if "observed_datetime" in merged.columns and len(merged) > 0:
        valid_dates = merged["observed_datetime"].dropna()
        if len(valid_dates) > 0:
            print(f"日期範圍: {valid_dates.min()} ~ {valid_dates.max()}")

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        merged.to_csv(output_path, index=False)
        print(f"已儲存至: {output_path}")

    return merged


def get_data_quality_report(df: pd.DataFrame) -> dict:
    """
    產生資料品質報告
    
    Args:
        df: 清洗後的 DataFrame
        
    Returns:
        包含各欄位缺失率等統計的字典
    """
    report = {
        "total_rows": len(df),
        "columns": {},
    }
    
    for col in df.columns:
        missing_count = df[col].isna().sum()
        missing_pct = (missing_count / len(df)) * 100 if len(df) > 0 else 0
        report["columns"][col] = {
            "missing_count": int(missing_count),
            "missing_percentage": round(missing_pct, 2),
            "dtype": str(df[col].dtype),
        }
    
    return report


if __name__ == "__main__":
    input_dir = Path(__file__).parent.parent / "data" / "raw"
    output_path = Path(__file__).parent.parent / "data" / "processed" / "466920_cleaned.csv"

    df = merge_and_clean_all(input_dir, "466920", output_path)
    
    # 顯示資料品質報告
    report = get_data_quality_report(df)
    print(f"\n資料品質報告:")
    print(f"總筆數: {report['total_rows']}")
    key_columns = ["temperature", "humidity", "precipitation", "sunshine_hours"]
    for col in key_columns:
        if col in report["columns"]:
            info = report["columns"][col]
            print(f"  {col}: 缺失 {info['missing_percentage']}%")
