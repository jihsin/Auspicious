# backend/app/services/proverb_verify.py
"""諺語驗證服務

使用 36 年歷史氣象數據驗證諺語準確率。
"""

from datetime import date, timedelta
from typing import Optional
from dataclasses import dataclass
import statistics
import math

from sqlalchemy import func, extract, and_, or_
from sqlalchemy.orm import Session

from app.models import RawObservation, DailyStatistics
from app.services.proverb import (
    Proverb,
    ProverbVerification,
    get_proverb_by_id,
    get_verifiable_proverbs,
)


@dataclass
class VerificationResult:
    """驗證結果"""
    proverb_id: str
    proverb_text: str
    verification: ProverbVerification
    scientific_explanation: str
    confidence_level: str  # 高/中/低
    data_quality: str      # 資料品質說明


def _get_station_with_most_data(db: Session) -> str:
    """取得資料最完整的站點（通常是臺北站）"""
    result = db.query(
        RawObservation.station_id,
        func.count(RawObservation.id).label('count')
    ).group_by(RawObservation.station_id).order_by(func.count(RawObservation.id).desc()).first()
    return result[0] if result else "466920"


def _get_solar_term_date(year: int, term_name: str) -> Optional[date]:
    """取得某年特定節氣的大約日期

    注：這是根據典型日期的近似值，實際節氣日期可能有 1-2 天誤差
    """
    # 節氣典型日期對照表
    term_dates = {
        "立春": (2, 4), "雨水": (2, 19), "驚蟄": (3, 6), "春分": (3, 21),
        "清明": (4, 5), "穀雨": (4, 20), "立夏": (5, 6), "小滿": (5, 21),
        "芒種": (6, 6), "夏至": (6, 21), "小暑": (7, 7), "大暑": (7, 23),
        "立秋": (8, 8), "處暑": (8, 23), "白露": (9, 8), "秋分": (9, 23),
        "寒露": (10, 8), "霜降": (10, 24), "立冬": (11, 8), "小雪": (11, 22),
        "大雪": (12, 7), "冬至": (12, 22), "小寒": (1, 6), "大寒": (1, 20),
    }

    if term_name not in term_dates:
        return None

    month, day = term_dates[term_name]
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _has_precipitation(precip: Optional[float], threshold: float = 0.1) -> bool:
    """判斷是否有降水"""
    return precip is not None and precip >= threshold


def _interpret_accuracy(rate: float) -> str:
    """解讀準確率"""
    if rate >= 0.8:
        return "非常準確，歷史數據強烈支持此諺語"
    elif rate >= 0.65:
        return "準確度高，歷史數據支持此諺語"
    elif rate >= 0.5:
        return "有一定參考價值，但並非絕對準確"
    elif rate >= 0.35:
        return "準確度有限，僅供參考"
    else:
        return "歷史數據不支持此諺語，可能因氣候或地理差異"


def _confidence_level(sample_count: int, rate: float) -> str:
    """判斷信心水準"""
    if sample_count >= 30 and rate not in [0.0, 1.0]:
        return "高"
    elif sample_count >= 15:
        return "中"
    else:
        return "低"


# ============================================
# 個別諺語驗證函數
# ============================================

def verify_lichun_rain(db: Session, station_id: str) -> VerificationResult:
    """驗證「立春落雨透清明」

    邏輯：立春日有雨的年份，檢查立春到清明期間的降雨天數是否高於平均
    """
    proverb = get_proverb_by_id("lichun_rain")

    # 取得所有年份的資料範圍
    years_query = db.query(
        extract('year', RawObservation.observed_date).label('year')
    ).filter(
        RawObservation.station_id == station_id
    ).distinct().all()

    years = [int(y[0]) for y in years_query]

    total_cases = 0  # 立春有雨的年數
    positive_cases = 0  # 立春有雨且清明前多雨的年數
    sample_years = []

    for year in years:
        lichun_date = _get_solar_term_date(year, "立春")
        qingming_date = _get_solar_term_date(year, "清明")

        if not lichun_date or not qingming_date:
            continue

        # 檢查立春當天是否有雨
        lichun_obs = db.query(RawObservation).filter(
            RawObservation.station_id == station_id,
            RawObservation.observed_date == lichun_date
        ).first()

        if not lichun_obs or not _has_precipitation(lichun_obs.precipitation):
            continue

        # 立春有雨
        total_cases += 1
        sample_years.append(year)

        # 計算立春到清明期間的降雨天數
        rainy_days = db.query(func.count(RawObservation.id)).filter(
            RawObservation.station_id == station_id,
            RawObservation.observed_date > lichun_date,
            RawObservation.observed_date <= qingming_date,
            RawObservation.precipitation >= 0.1
        ).scalar() or 0

        # 計算總天數
        total_days = (qingming_date - lichun_date).days
        rain_ratio = rainy_days / total_days if total_days > 0 else 0

        # 如果降雨天數超過 40%，視為「透清明」
        if rain_ratio >= 0.4:
            positive_cases += 1

    accuracy = positive_cases / total_cases if total_cases > 0 else 0

    return VerificationResult(
        proverb_id=proverb.id,
        proverb_text=proverb.text,
        verification=ProverbVerification(
            total_cases=total_cases,
            positive_cases=positive_cases,
            accuracy_rate=round(accuracy, 3),
            interpretation=_interpret_accuracy(accuracy),
            sample_years=sample_years[-10:],  # 只顯示最近 10 年
            methodology="檢查立春有雨的年份中，立春至清明期間降雨天數佔比是否超過 40%",
        ),
        scientific_explanation=proverb.scientific_explanation,
        confidence_level=_confidence_level(total_cases, accuracy),
        data_quality=f"分析了 {len(years)} 年資料，其中 {total_cases} 年立春有雨",
    )


def verify_qingming_rain(db: Session, station_id: str) -> VerificationResult:
    """驗證「清明時節雨紛紛」

    邏輯：計算清明節前後一週的歷史降雨機率
    """
    proverb = get_proverb_by_id("qingming_rain")

    years_query = db.query(
        extract('year', RawObservation.observed_date).label('year')
    ).filter(
        RawObservation.station_id == station_id
    ).distinct().all()

    years = [int(y[0]) for y in years_query]

    total_cases = 0
    positive_cases = 0
    sample_years = []

    for year in years:
        qingming_date = _get_solar_term_date(year, "清明")
        if not qingming_date:
            continue

        # 清明前後一週（共 15 天）
        start_date = qingming_date - timedelta(days=7)
        end_date = qingming_date + timedelta(days=7)

        # 計算這期間的降雨天數
        rainy_days = db.query(func.count(RawObservation.id)).filter(
            RawObservation.station_id == station_id,
            RawObservation.observed_date >= start_date,
            RawObservation.observed_date <= end_date,
            RawObservation.precipitation >= 0.1
        ).scalar() or 0

        total_days = db.query(func.count(RawObservation.id)).filter(
            RawObservation.station_id == station_id,
            RawObservation.observed_date >= start_date,
            RawObservation.observed_date <= end_date
        ).scalar() or 0

        if total_days >= 10:  # 至少要有 10 天資料
            total_cases += 1
            sample_years.append(year)
            # 如果超過 50% 天數有雨，視為「雨紛紛」
            if rainy_days / total_days >= 0.5:
                positive_cases += 1

    accuracy = positive_cases / total_cases if total_cases > 0 else 0

    return VerificationResult(
        proverb_id=proverb.id,
        proverb_text=proverb.text,
        verification=ProverbVerification(
            total_cases=total_cases,
            positive_cases=positive_cases,
            accuracy_rate=round(accuracy, 3),
            interpretation=_interpret_accuracy(accuracy),
            sample_years=sample_years[-10:],
            methodology="計算清明節前後一週（15 天）中降雨天數是否超過 50%",
        ),
        scientific_explanation=proverb.scientific_explanation,
        confidence_level=_confidence_level(total_cases, accuracy),
        data_quality=f"分析了 {total_cases} 年資料",
    )


def verify_xiazhi_heat(db: Session, station_id: str) -> VerificationResult:
    """驗證「夏至不過不熱」

    邏輯：比較夏至前後各 30 天的平均最高溫
    """
    proverb = get_proverb_by_id("xiazhi_heat")

    years_query = db.query(
        extract('year', RawObservation.observed_date).label('year')
    ).filter(
        RawObservation.station_id == station_id
    ).distinct().all()

    years = [int(y[0]) for y in years_query]

    total_cases = 0
    positive_cases = 0
    sample_years = []
    temp_diffs = []

    for year in years:
        xiazhi_date = _get_solar_term_date(year, "夏至")
        if not xiazhi_date:
            continue

        # 夏至前 30 天平均最高溫
        before_temps = db.query(func.avg(RawObservation.temperature_max)).filter(
            RawObservation.station_id == station_id,
            RawObservation.observed_date >= xiazhi_date - timedelta(days=30),
            RawObservation.observed_date < xiazhi_date,
            RawObservation.temperature_max.isnot(None)
        ).scalar()

        # 夏至後 30 天平均最高溫
        after_temps = db.query(func.avg(RawObservation.temperature_max)).filter(
            RawObservation.station_id == station_id,
            RawObservation.observed_date > xiazhi_date,
            RawObservation.observed_date <= xiazhi_date + timedelta(days=30),
            RawObservation.temperature_max.isnot(None)
        ).scalar()

        if before_temps and after_temps:
            total_cases += 1
            sample_years.append(year)
            temp_diffs.append(after_temps - before_temps)

            # 夏至後溫度更高，視為驗證成功
            if after_temps > before_temps:
                positive_cases += 1

    accuracy = positive_cases / total_cases if total_cases > 0 else 0
    avg_diff = sum(temp_diffs) / len(temp_diffs) if temp_diffs else 0

    return VerificationResult(
        proverb_id=proverb.id,
        proverb_text=proverb.text,
        verification=ProverbVerification(
            total_cases=total_cases,
            positive_cases=positive_cases,
            accuracy_rate=round(accuracy, 3),
            interpretation=f"{_interpret_accuracy(accuracy)}。夏至後平均比夏至前高 {avg_diff:.1f}°C",
            sample_years=sample_years[-10:],
            methodology="比較夏至前後各 30 天的平均最高溫",
        ),
        scientific_explanation=proverb.scientific_explanation,
        confidence_level=_confidence_level(total_cases, accuracy),
        data_quality=f"分析了 {total_cases} 年資料",
    )


def verify_dongzhi_cold(db: Session, station_id: str) -> VerificationResult:
    """驗證「冬至不過不寒」

    邏輯：比較冬至前後各 30 天的平均最低溫
    """
    proverb = get_proverb_by_id("dongzhi_cold")

    years_query = db.query(
        extract('year', RawObservation.observed_date).label('year')
    ).filter(
        RawObservation.station_id == station_id
    ).distinct().all()

    years = [int(y[0]) for y in years_query]

    total_cases = 0
    positive_cases = 0
    sample_years = []
    temp_diffs = []

    for year in years:
        dongzhi_date = _get_solar_term_date(year, "冬至")
        if not dongzhi_date:
            continue

        # 冬至前 30 天平均最低溫
        before_temps = db.query(func.avg(RawObservation.temperature_min)).filter(
            RawObservation.station_id == station_id,
            RawObservation.observed_date >= dongzhi_date - timedelta(days=30),
            RawObservation.observed_date < dongzhi_date,
            RawObservation.temperature_min.isnot(None)
        ).scalar()

        # 冬至後 30 天平均最低溫
        after_temps = db.query(func.avg(RawObservation.temperature_min)).filter(
            RawObservation.station_id == station_id,
            RawObservation.observed_date > dongzhi_date,
            RawObservation.observed_date <= dongzhi_date + timedelta(days=30),
            RawObservation.temperature_min.isnot(None)
        ).scalar()

        if before_temps and after_temps:
            total_cases += 1
            sample_years.append(year)
            temp_diffs.append(before_temps - after_temps)  # 冬至後應該更冷

            # 冬至後溫度更低，視為驗證成功
            if after_temps < before_temps:
                positive_cases += 1

    accuracy = positive_cases / total_cases if total_cases > 0 else 0
    avg_diff = sum(temp_diffs) / len(temp_diffs) if temp_diffs else 0

    return VerificationResult(
        proverb_id=proverb.id,
        proverb_text=proverb.text,
        verification=ProverbVerification(
            total_cases=total_cases,
            positive_cases=positive_cases,
            accuracy_rate=round(accuracy, 3),
            interpretation=f"{_interpret_accuracy(accuracy)}。冬至後平均比冬至前低 {avg_diff:.1f}°C",
            sample_years=sample_years[-10:],
            methodology="比較冬至前後各 30 天的平均最低溫",
        ),
        scientific_explanation=proverb.scientific_explanation,
        confidence_level=_confidence_level(total_cases, accuracy),
        data_quality=f"分析了 {total_cases} 年資料",
    )


def verify_spring_mother_face(db: Session, station_id: str) -> VerificationResult:
    """驗證「春天後母面」

    邏輯：計算春季（3-5月）每日溫差的變異程度
    """
    proverb = get_proverb_by_id("spring_mother_face")

    # 計算春季（3-5月）每日最高最低溫差
    spring_diffs = db.query(
        (RawObservation.temperature_max - RawObservation.temperature_min).label('diff')
    ).filter(
        RawObservation.station_id == station_id,
        extract('month', RawObservation.observed_date).in_([3, 4, 5]),
        RawObservation.temperature_max.isnot(None),
        RawObservation.temperature_min.isnot(None)
    ).all()

    # 計算夏季（6-8月）每日溫差作為對照
    summer_diffs = db.query(
        (RawObservation.temperature_max - RawObservation.temperature_min).label('diff')
    ).filter(
        RawObservation.station_id == station_id,
        extract('month', RawObservation.observed_date).in_([6, 7, 8]),
        RawObservation.temperature_max.isnot(None),
        RawObservation.temperature_min.isnot(None)
    ).all()

    spring_values = [d[0] for d in spring_diffs if d[0] is not None]
    summer_values = [d[0] for d in summer_diffs if d[0] is not None]

    if len(spring_values) < 100 or len(summer_values) < 100:
        return VerificationResult(
            proverb_id=proverb.id,
            proverb_text=proverb.text,
            verification=ProverbVerification(
                total_cases=0,
                positive_cases=0,
                accuracy_rate=0,
                interpretation="資料不足，無法驗證",
                sample_years=[],
                methodology="比較春季與夏季的日溫差變異程度",
            ),
            scientific_explanation=proverb.scientific_explanation,
            confidence_level="低",
            data_quality="資料不足",
        )

    spring_std = statistics.stdev(spring_values)
    summer_std = statistics.stdev(summer_values)
    spring_mean = statistics.mean(spring_values)
    summer_mean = statistics.mean(summer_values)

    # 如果春季溫差變異比夏季大，驗證成功
    is_verified = spring_std > summer_std
    accuracy = 1.0 if is_verified else 0.0

    return VerificationResult(
        proverb_id=proverb.id,
        proverb_text=proverb.text,
        verification=ProverbVerification(
            total_cases=len(spring_values),
            positive_cases=len(spring_values) if is_verified else 0,
            accuracy_rate=accuracy,
            interpretation=f"春季日溫差標準差 {spring_std:.1f}°C，夏季 {summer_std:.1f}°C。{'春季確實變化較大' if is_verified else '夏季變化更大'}",
            sample_years=[],
            methodology="比較春季（3-5月）與夏季（6-8月）每日溫差的標準差",
        ),
        scientific_explanation=proverb.scientific_explanation,
        confidence_level="高" if len(spring_values) > 1000 else "中",
        data_quality=f"春季 {len(spring_values)} 筆，夏季 {len(summer_values)} 筆資料",
    )


def verify_three_fu_days(db: Session, station_id: str) -> VerificationResult:
    """驗證「小暑大暑，上蒸下煮」

    邏輯：計算七月的平均最高溫和超過 35°C 的天數比例
    """
    proverb = get_proverb_by_id("three_fu_days")

    # 計算七月的統計
    july_stats = db.query(
        func.avg(RawObservation.temperature_max).label('avg_max'),
        func.count(RawObservation.id).label('total_days'),
    ).filter(
        RawObservation.station_id == station_id,
        extract('month', RawObservation.observed_date) == 7,
        RawObservation.temperature_max.isnot(None)
    ).first()

    # 計算超過 35°C 的天數
    hot_days = db.query(func.count(RawObservation.id)).filter(
        RawObservation.station_id == station_id,
        extract('month', RawObservation.observed_date) == 7,
        RawObservation.temperature_max >= 35
    ).scalar() or 0

    # 計算其他月份平均最高溫作為對照
    other_months_avg = db.query(
        func.avg(RawObservation.temperature_max)
    ).filter(
        RawObservation.station_id == station_id,
        extract('month', RawObservation.observed_date).notin_([6, 7, 8]),
        RawObservation.temperature_max.isnot(None)
    ).scalar() or 25

    if not july_stats or july_stats.total_days < 100:
        return VerificationResult(
            proverb_id=proverb.id,
            proverb_text=proverb.text,
            verification=ProverbVerification(
                total_cases=0,
                positive_cases=0,
                accuracy_rate=0,
                interpretation="資料不足，無法驗證",
                sample_years=[],
                methodology="計算七月平均最高溫和高溫天數比例",
            ),
            scientific_explanation=proverb.scientific_explanation,
            confidence_level="低",
            data_quality="資料不足",
        )

    hot_ratio = hot_days / july_stats.total_days
    temp_diff = july_stats.avg_max - other_months_avg

    # 如果七月比其他月份平均高 5°C 以上，且高溫天數超過 20%，視為驗證成功
    is_verified = temp_diff >= 5 and hot_ratio >= 0.1

    return VerificationResult(
        proverb_id=proverb.id,
        proverb_text=proverb.text,
        verification=ProverbVerification(
            total_cases=july_stats.total_days,
            positive_cases=hot_days,
            accuracy_rate=round(hot_ratio, 3),
            interpretation=f"七月平均最高溫 {july_stats.avg_max:.1f}°C，超過 35°C 的天數佔 {hot_ratio*100:.1f}%。{'確實是一年最熱時期' if is_verified else '驗證結果不明顯'}",
            sample_years=[],
            methodology="計算七月平均最高溫和超過 35°C 的天數比例",
        ),
        scientific_explanation=proverb.scientific_explanation,
        confidence_level="高" if july_stats.total_days > 500 else "中",
        data_quality=f"分析了 {july_stats.total_days} 天七月資料",
    )


def verify_cold_in_nine(db: Session, station_id: str) -> VerificationResult:
    """驗證「小寒大寒，凍成冰團」

    邏輯：計算一月的平均最低溫和低於 10°C 的天數比例
    """
    proverb = get_proverb_by_id("cold_in_nine")

    # 計算一月的統計
    jan_stats = db.query(
        func.avg(RawObservation.temperature_min).label('avg_min'),
        func.count(RawObservation.id).label('total_days'),
    ).filter(
        RawObservation.station_id == station_id,
        extract('month', RawObservation.observed_date) == 1,
        RawObservation.temperature_min.isnot(None)
    ).first()

    # 計算低於 10°C 的天數
    cold_days = db.query(func.count(RawObservation.id)).filter(
        RawObservation.station_id == station_id,
        extract('month', RawObservation.observed_date) == 1,
        RawObservation.temperature_min < 10
    ).scalar() or 0

    # 計算其他月份平均最低溫作為對照
    other_months_avg = db.query(
        func.avg(RawObservation.temperature_min)
    ).filter(
        RawObservation.station_id == station_id,
        extract('month', RawObservation.observed_date).notin_([12, 1, 2]),
        RawObservation.temperature_min.isnot(None)
    ).scalar() or 20

    if not jan_stats or jan_stats.total_days < 100:
        return VerificationResult(
            proverb_id=proverb.id,
            proverb_text=proverb.text,
            verification=ProverbVerification(
                total_cases=0,
                positive_cases=0,
                accuracy_rate=0,
                interpretation="資料不足，無法驗證",
                sample_years=[],
                methodology="計算一月平均最低溫和低溫天數比例",
            ),
            scientific_explanation=proverb.scientific_explanation,
            confidence_level="低",
            data_quality="資料不足",
        )

    cold_ratio = cold_days / jan_stats.total_days
    temp_diff = other_months_avg - jan_stats.avg_min

    # 如果一月比其他月份平均低 5°C 以上，視為驗證成功
    is_verified = temp_diff >= 5

    return VerificationResult(
        proverb_id=proverb.id,
        proverb_text=proverb.text,
        verification=ProverbVerification(
            total_cases=jan_stats.total_days,
            positive_cases=cold_days,
            accuracy_rate=round(cold_ratio, 3),
            interpretation=f"一月平均最低溫 {jan_stats.avg_min:.1f}°C，低於 10°C 的天數佔 {cold_ratio*100:.1f}%。{'確實是一年最冷時期' if is_verified else '驗證結果不明顯'}",
            sample_years=[],
            methodology="計算一月平均最低溫和低於 10°C 的天數比例",
        ),
        scientific_explanation=proverb.scientific_explanation,
        confidence_level="高" if jan_stats.total_days > 500 else "中",
        data_quality=f"分析了 {jan_stats.total_days} 天一月資料",
    )


def verify_plum_rain(db: Session, station_id: str) -> VerificationResult:
    """驗證「小滿大滿江河滿」

    邏輯：計算五月下旬至六月中旬的累積降雨量
    """
    proverb = get_proverb_by_id("plum_rain")

    years_query = db.query(
        extract('year', RawObservation.observed_date).label('year')
    ).filter(
        RawObservation.station_id == station_id
    ).distinct().all()

    years = [int(y[0]) for y in years_query]

    plum_rain_totals = []
    other_period_totals = []
    sample_years = []

    for year in years:
        # 梅雨季期間（5/20 - 6/20）
        plum_rain = db.query(func.sum(RawObservation.precipitation)).filter(
            RawObservation.station_id == station_id,
            RawObservation.observed_date >= date(year, 5, 20),
            RawObservation.observed_date <= date(year, 6, 20),
            RawObservation.precipitation.isnot(None)
        ).scalar() or 0

        # 對照期間（同樣長度的 4/1 - 5/1）
        other_period = db.query(func.sum(RawObservation.precipitation)).filter(
            RawObservation.station_id == station_id,
            RawObservation.observed_date >= date(year, 4, 1),
            RawObservation.observed_date <= date(year, 5, 1),
            RawObservation.precipitation.isnot(None)
        ).scalar() or 0

        if plum_rain > 0 or other_period > 0:
            plum_rain_totals.append(plum_rain)
            other_period_totals.append(other_period)
            sample_years.append(year)

    if len(plum_rain_totals) < 10:
        return VerificationResult(
            proverb_id=proverb.id,
            proverb_text=proverb.text,
            verification=ProverbVerification(
                total_cases=0,
                positive_cases=0,
                accuracy_rate=0,
                interpretation="資料不足，無法驗證",
                sample_years=[],
                methodology="比較梅雨季期間與其他期間的降雨量",
            ),
            scientific_explanation=proverb.scientific_explanation,
            confidence_level="低",
            data_quality="資料不足",
        )

    avg_plum = sum(plum_rain_totals) / len(plum_rain_totals)
    avg_other = sum(other_period_totals) / len(other_period_totals)

    # 梅雨季降雨量超過對照期間的年數
    positive_cases = sum(1 for p, o in zip(plum_rain_totals, other_period_totals) if p > o)
    accuracy = positive_cases / len(plum_rain_totals)

    return VerificationResult(
        proverb_id=proverb.id,
        proverb_text=proverb.text,
        verification=ProverbVerification(
            total_cases=len(plum_rain_totals),
            positive_cases=positive_cases,
            accuracy_rate=round(accuracy, 3),
            interpretation=f"梅雨季（5/20-6/20）平均降雨 {avg_plum:.1f}mm，對照期間 {avg_other:.1f}mm。{accuracy*100:.0f}% 的年份梅雨季雨量更多",
            sample_years=sample_years[-10:],
            methodology="比較五月下旬至六月中旬與四月的累積降雨量",
        ),
        scientific_explanation=proverb.scientific_explanation,
        confidence_level=_confidence_level(len(plum_rain_totals), accuracy),
        data_quality=f"分析了 {len(plum_rain_totals)} 年資料",
    )


def verify_autumn_tiger(db: Session, station_id: str) -> VerificationResult:
    """驗證「處暑天還暑，好似秋老虎」

    邏輯：計算八月下旬至九月上旬的高溫天數
    """
    proverb = get_proverb_by_id("autumn_tiger")

    # 處暑前後期間（8/20 - 9/10）的高溫統計
    stats = db.query(
        func.avg(RawObservation.temperature_max).label('avg_max'),
        func.count(RawObservation.id).label('total_days'),
    ).filter(
        RawObservation.station_id == station_id,
        or_(
            and_(
                extract('month', RawObservation.observed_date) == 8,
                extract('day', RawObservation.observed_date) >= 20
            ),
            and_(
                extract('month', RawObservation.observed_date) == 9,
                extract('day', RawObservation.observed_date) <= 10
            )
        ),
        RawObservation.temperature_max.isnot(None)
    ).first()

    # 高於 32°C 的天數
    hot_days = db.query(func.count(RawObservation.id)).filter(
        RawObservation.station_id == station_id,
        or_(
            and_(
                extract('month', RawObservation.observed_date) == 8,
                extract('day', RawObservation.observed_date) >= 20
            ),
            and_(
                extract('month', RawObservation.observed_date) == 9,
                extract('day', RawObservation.observed_date) <= 10
            )
        ),
        RawObservation.temperature_max >= 32
    ).scalar() or 0

    if not stats or stats.total_days < 50:
        return VerificationResult(
            proverb_id=proverb.id,
            proverb_text=proverb.text,
            verification=ProverbVerification(
                total_cases=0,
                positive_cases=0,
                accuracy_rate=0,
                interpretation="資料不足，無法驗證",
                sample_years=[],
                methodology="計算處暑前後的高溫天數比例",
            ),
            scientific_explanation=proverb.scientific_explanation,
            confidence_level="低",
            data_quality="資料不足",
        )

    hot_ratio = hot_days / stats.total_days

    return VerificationResult(
        proverb_id=proverb.id,
        proverb_text=proverb.text,
        verification=ProverbVerification(
            total_cases=stats.total_days,
            positive_cases=hot_days,
            accuracy_rate=round(hot_ratio, 3),
            interpretation=f"處暑前後（8/20-9/10）平均最高溫 {stats.avg_max:.1f}°C，{hot_ratio*100:.1f}% 天數超過 32°C。{'秋老虎現象明顯' if hot_ratio > 0.5 else '秋老虎現象不明顯'}",
            sample_years=[],
            methodology="計算八月下旬至九月上旬超過 32°C 的天數比例",
        ),
        scientific_explanation=proverb.scientific_explanation,
        confidence_level="高" if stats.total_days > 300 else "中",
        data_quality=f"分析了 {stats.total_days} 天資料",
    )


# ============================================
# 主要驗證函數
# ============================================

# 諺語 ID 到驗證函數的映射
VERIFICATION_FUNCTIONS = {
    "lichun_rain": verify_lichun_rain,
    "qingming_rain": verify_qingming_rain,
    "xiazhi_heat": verify_xiazhi_heat,
    "dongzhi_cold": verify_dongzhi_cold,
    "spring_mother_face": verify_spring_mother_face,
    "three_fu_days": verify_three_fu_days,
    "cold_in_nine": verify_cold_in_nine,
    "plum_rain": verify_plum_rain,
    "autumn_tiger": verify_autumn_tiger,
}


def verify_proverb(db: Session, proverb_id: str, station_id: Optional[str] = None) -> Optional[VerificationResult]:
    """驗證單一諺語

    Args:
        db: 資料庫 session
        proverb_id: 諺語 ID
        station_id: 站點 ID（可選，預設使用資料最完整的站點）

    Returns:
        驗證結果，或 None（如果諺語不存在或不可驗證）
    """
    if proverb_id not in VERIFICATION_FUNCTIONS:
        proverb = get_proverb_by_id(proverb_id)
        if proverb and not proverb.verifiable:
            return VerificationResult(
                proverb_id=proverb_id,
                proverb_text=proverb.text if proverb else "",
                verification=ProverbVerification(
                    total_cases=0,
                    positive_cases=0,
                    accuracy_rate=0,
                    interpretation="此諺語需要額外資料（如農產量、雷擊紀錄等）才能驗證",
                    sample_years=[],
                    methodology=proverb.verification_method if proverb else "",
                ),
                scientific_explanation=proverb.scientific_explanation if proverb else "",
                confidence_level="無法驗證",
                data_quality="缺少必要資料",
            )
        return None

    if not station_id:
        station_id = _get_station_with_most_data(db)

    verify_func = VERIFICATION_FUNCTIONS[proverb_id]
    return verify_func(db, station_id)


def verify_all_proverbs(db: Session, station_id: Optional[str] = None) -> list[VerificationResult]:
    """驗證所有可驗證的諺語

    Args:
        db: 資料庫 session
        station_id: 站點 ID（可選）

    Returns:
        所有諺語的驗證結果列表
    """
    if not station_id:
        station_id = _get_station_with_most_data(db)

    results = []
    for proverb_id, verify_func in VERIFICATION_FUNCTIONS.items():
        try:
            result = verify_func(db, station_id)
            results.append(result)
        except Exception as e:
            # 記錄錯誤但繼續驗證其他諺語
            proverb = get_proverb_by_id(proverb_id)
            results.append(VerificationResult(
                proverb_id=proverb_id,
                proverb_text=proverb.text if proverb else "",
                verification=ProverbVerification(
                    total_cases=0,
                    positive_cases=0,
                    accuracy_rate=0,
                    interpretation=f"驗證時發生錯誤：{str(e)}",
                    sample_years=[],
                    methodology="",
                ),
                scientific_explanation=proverb.scientific_explanation if proverb else "",
                confidence_level="錯誤",
                data_quality="驗證失敗",
            ))

    return results


def get_proverb_stats_summary(db: Session, station_id: Optional[str] = None) -> dict:
    """取得諺語驗證統計摘要

    Returns:
        {
            "total_proverbs": 諺語總數,
            "verifiable_count": 可驗證數量,
            "verified_count": 已驗證數量,
            "avg_accuracy": 平均準確率,
            "high_accuracy_count": 高準確率（>65%）數量,
        }
    """
    from app.services.proverb import get_all_proverbs, get_verifiable_proverbs

    all_proverbs = get_all_proverbs()
    verifiable = get_verifiable_proverbs()

    results = verify_all_proverbs(db, station_id)
    valid_results = [r for r in results if r.verification.total_cases > 0]

    accuracies = [r.verification.accuracy_rate for r in valid_results]

    return {
        "total_proverbs": len(all_proverbs),
        "verifiable_count": len(verifiable),
        "verified_count": len(valid_results),
        "avg_accuracy": round(sum(accuracies) / len(accuracies), 3) if accuracies else 0,
        "high_accuracy_count": sum(1 for a in accuracies if a >= 0.65),
    }
