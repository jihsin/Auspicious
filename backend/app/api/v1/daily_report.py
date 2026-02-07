# backend/app/api/v1/daily_report.py
"""每日報告 API

用於 Cloud Scheduler 觸發的每日 LINE 報告。
"""

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query

# 台灣時區 (UTC+8)
TW_TIMEZONE = timezone(timedelta(hours=8))
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.weather import ApiResponse
from app.services.notification import send_line_message
from app.services.realtime_weather import fetch_realtime_weather
from app.services.lunar import get_lunar_info
from app.services.solar_term import get_current_solar_term
from app.models import DailyStatistics
from app.services.decade_stats import get_extreme_records

router = APIRouter()


async def generate_daily_report(station_id: str, db: Session) -> str:
    """生成每日報告內容"""
    today = datetime.now(TW_TIMEZONE)
    month_day = today.strftime("%m-%d")

    # 取得即時天氣
    realtime = await fetch_realtime_weather(station_id)

    # 取得歷史統計
    stats = db.query(DailyStatistics).filter(
        DailyStatistics.station_id == station_id,
        DailyStatistics.month_day == month_day
    ).first()

    # 取得農曆
    lunar_info = get_lunar_info(today.date())
    lunar_date = lunar_info.get("lunar_date", {})

    # 取得節氣
    solar_term = get_current_solar_term(today.date())

    # 取得極值
    extreme_records = get_extreme_records(db, station_id, month_day)

    # 即時天氣資訊
    if realtime:
        temp = realtime.temp
        temp_max = realtime.temp_max
        temp_min = realtime.temp_min
        weather = realtime.weather or "未知"
        obs_time = realtime.obs_time.strftime("%H:%M") if realtime.obs_time else ""
        humidity = realtime.humidity
        # 處理無效降雨量（CWA API 用負數表示缺失資料）
        raw_precip = realtime.precipitation
        precipitation = raw_precip if raw_precip is not None and raw_precip >= 0 else None
    else:
        temp = temp_max = temp_min = "N/A"
        weather = "無法取得"
        obs_time = ""
        humidity = None
        precipitation = None

    # 歷史統計
    hist_avg = round(stats.temp_avg_mean, 1) if stats and stats.temp_avg_mean else "N/A"

    # 差異計算
    if realtime and realtime.temp and stats and stats.temp_avg_mean:
        diff = round(realtime.temp - stats.temp_avg_mean, 1)
        diff_str = f"+{diff}" if diff > 0 else str(diff)
    else:
        diff_str = "N/A"

    # 農曆資訊
    lunar_str = f"{lunar_date.get('month_cn', '')}{lunar_date.get('day_cn', '')}"
    zodiac = lunar_date.get('生肖', '')
    ganzhi_day = lunar_date.get('干支日', '')

    # 極值
    max_temp_rec = extreme_records.get('max_temp', {}) if extreme_records else {}
    min_temp_rec = extreme_records.get('min_temp', {}) if extreme_records else {}
    max_precip_rec = extreme_records.get('max_precip', {}) if extreme_records else {}

    # 節氣
    jieqi_str = solar_term if solar_term and solar_term != "无" else "無特定節氣"

    # 降雨機率與歷史
    if stats and stats.precip_probability is not None:
        rain_prob = round(stats.precip_probability * 100)
        rain_prob_str = f"{rain_prob}%"
    else:
        rain_prob_str = "N/A"
        rain_prob = None

    # 降雨評估
    if precipitation and precipitation > 0:
        rain_status = f"☔ 已有降雨 {precipitation}mm"
    elif rain_prob is not None:
        if rain_prob >= 60:
            rain_status = "☔ 高機率降雨，建議攜帶雨具"
        elif rain_prob >= 30:
            rain_status = "🌂 可能降雨，建議備傘"
        else:
            rain_status = "☀️ 降雨機率低"
    else:
        rain_status = "資料不足"

    # 濕度
    humidity_str = f"{round(humidity)}%" if humidity else "N/A"

    # 累積雨量顯示
    precip_str = f"{precipitation}mm" if precipitation is not None else "--"

    # 組合訊息
    message = f"""🌤 好日子 - 每日天氣報告

📅 {today.strftime('%Y年%m月%d日')}（農曆{lunar_str}）
🐍 {zodiac}年 {ganzhi_day}日

━━━━━━━━━━━━━━━━
🌡 臺北即時天氣（{obs_time}）
━━━━━━━━━━━━━━━━
• 天氣：{weather}
• 氣溫：{temp}°C
• 今日高低：{temp_min}°C ~ {temp_max}°C
• 濕度：{humidity_str}
• 累積雨量：{precip_str}

━━━━━━━━━━━━━━━━
🌧 降雨參考
━━━━━━━━━━━━━━━━
• 歷史降雨機率：{rain_prob_str}
• 歷史最大雨量：{max_precip_rec.get('value', 'N/A')}mm ({max_precip_rec.get('year', '')})
• 今日建議：{rain_status}

━━━━━━━━━━━━━━━━
📊 氣溫歷史比較（36年）
━━━━━━━━━━━━━━━━
• 歷史平均：{hist_avg}°C
• 今日差異：{diff_str}°C
• 歷史最高：{max_temp_rec.get('value', 'N/A')}°C ({max_temp_rec.get('year', '')})
• 歷史最低：{min_temp_rec.get('value', 'N/A')}°C ({min_temp_rec.get('year', '')})

🌿 節氣：{jieqi_str}

🔗 https://auspicious-zeta.vercel.app"""

    return message


@router.post(
    "/send",
    response_model=ApiResponse[dict],
    summary="發送每日報告",
    description="發送每日天氣報告到 LINE（供 Cloud Scheduler 呼叫）"
)
async def send_daily_report(
    station_id: str = Query("466920", description="氣象站 ID"),
    db: Session = Depends(get_db)
):
    """發送每日報告到 LINE"""
    try:
        message = await generate_daily_report(station_id, db)
        success = await send_line_message(message)

        return ApiResponse(
            success=success,
            data={
                "sent": success,
                "station_id": station_id,
                "timestamp": datetime.now(TW_TIMEZONE).isoformat()
            },
            error=None if success else "LINE 訊息發送失敗"
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            data=None,
            error=str(e)
        )


@router.get(
    "/preview",
    response_model=ApiResponse[dict],
    summary="預覽每日報告",
    description="預覽每日報告內容（不發送）"
)
async def preview_daily_report(
    station_id: str = Query("466920", description="氣象站 ID"),
    db: Session = Depends(get_db)
):
    """預覽每日報告內容"""
    try:
        message = await generate_daily_report(station_id, db)
        return ApiResponse(
            success=True,
            data={
                "message": message,
                "station_id": station_id,
                "timestamp": datetime.now(TW_TIMEZONE).isoformat()
            }
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            data=None,
            error=str(e)
        )
