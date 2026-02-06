# backend/app/api/v1/line_webhook.py
"""LINE Webhook API

處理 LINE Bot 接收的訊息並回覆天氣資訊。
"""

import os
import hashlib
import hmac
import base64
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
import httpx

from app.database import get_db
from app.services.realtime_weather import fetch_realtime_weather
from app.services.lunar import get_lunar_info
from app.services.solar_term import get_current_solar_term
from app.models import DailyStatistics, Station
from app.services.decade_stats import get_extreme_records

router = APIRouter()

# LINE 設定
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"

# 站點對應（支援中文查詢）
STATION_MAPPING = {
    "台北": "466920",
    "臺北": "466920",
    "新北": "466920",
    "板橋": "466900",
    "桃園": "C0C700",
    "新竹": "C0D660",
    "台中": "467490",
    "臺中": "467490",
    "彰化": "C0F9A0",
    "嘉義": "467480",
    "台南": "467410",
    "臺南": "467410",
    "高雄": "467440",
    "屏東": "C0R150",
    "花蓮": "466990",
    "台東": "467660",
    "臺東": "467660",
    "宜蘭": "467080",
}


def verify_signature(body: bytes, signature: str) -> bool:
    """驗證 LINE 簽名"""
    if not LINE_CHANNEL_SECRET:
        return True  # 開發環境可跳過驗證

    hash_value = hmac.new(
        LINE_CHANNEL_SECRET.encode('utf-8'),
        body,
        hashlib.sha256
    ).digest()
    expected_signature = base64.b64encode(hash_value).decode('utf-8')
    return hmac.compare_digest(signature, expected_signature)


async def reply_message(reply_token: str, messages: list[dict]) -> bool:
    """回覆 LINE 訊息"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
    }

    payload = {
        "replyToken": reply_token,
        "messages": messages,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(LINE_REPLY_URL, headers=headers, json=payload)
            return response.status_code == 200
    except Exception as e:
        print(f"LINE 回覆錯誤: {e}")
        return False


def parse_user_query(text: str) -> dict:
    """解析用戶查詢意圖

    Returns:
        dict: {"type": "weather|help|unknown", "city": str|None}
    """
    text = text.strip().lower()

    # 幫助指令
    if text in ["help", "幫助", "說明", "?", "？"]:
        return {"type": "help", "city": None}

    # 查詢天氣（支援各種格式）
    # "台北天氣"、"天氣 台北"、"台北"、"查天氣"
    for city, station_id in STATION_MAPPING.items():
        if city in text:
            return {"type": "weather", "city": city, "station_id": station_id}

    # 預設查台北
    if any(keyword in text for keyword in ["天氣", "氣溫", "溫度", "會下雨", "下雨", "今天"]):
        return {"type": "weather", "city": "台北", "station_id": "466920"}

    return {"type": "unknown", "city": None}


async def generate_weather_reply(station_id: str, city: str, db: Session) -> str:
    """生成天氣回覆訊息"""
    today = datetime.now()
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

    # 取得極值
    extreme_records = get_extreme_records(db, station_id, month_day)

    if realtime:
        temp = realtime.temp
        weather = realtime.weather or "未知"
        humidity = realtime.humidity
        precipitation = realtime.precipitation or 0
        temp_max = realtime.temp_max
        temp_min = realtime.temp_min
        obs_time = realtime.obs_time.strftime("%H:%M") if realtime.obs_time else ""
    else:
        return f"抱歉，無法取得 {city} 的即時天氣資料。請稍後再試。"

    # 歷史比較
    hist_avg = round(stats.temp_avg_mean, 1) if stats and stats.temp_avg_mean else None
    if hist_avg and temp:
        diff = round(temp - hist_avg, 1)
        diff_str = f"+{diff}" if diff > 0 else str(diff)
    else:
        diff_str = "N/A"

    # 降雨機率
    if stats and stats.precip_probability is not None:
        rain_prob = round(stats.precip_probability * 100)
        if rain_prob >= 60:
            rain_advice = "☔ 高機率降雨，記得帶傘！"
        elif rain_prob >= 30:
            rain_advice = "🌂 可能下雨，建議備傘"
        else:
            rain_advice = "☀️ 降雨機率低"
    else:
        rain_prob = None
        rain_advice = ""

    # 農曆
    lunar_str = f"{lunar_date.get('month_cn', '')}{lunar_date.get('day_cn', '')}"

    message = f"""🌤 {city}天氣（{obs_time}）

• 天氣：{weather}
• 氣溫：{temp}°C
• 高低溫：{temp_min}°C ~ {temp_max}°C
• 濕度：{round(humidity) if humidity else 'N/A'}%

📊 歷史比較（36年）
• 平均：{hist_avg if hist_avg else 'N/A'}°C
• 今日差異：{diff_str}°C

🌧 降雨
• 累積雨量：{precipitation}mm
• 歷史機率：{rain_prob if rain_prob else 'N/A'}%
{rain_advice}

📅 {today.strftime('%m/%d')}（農曆{lunar_str}）"""

    return message


def get_help_message() -> str:
    """回傳說明訊息"""
    return """🌤 好日子天氣機器人

📍 查詢天氣：
直接輸入城市名稱即可！
例如：台北、高雄、花蓮

支援城市：
台北、板橋、桃園、新竹
台中、彰化、嘉義
台南、高雄、屏東
花蓮、台東、宜蘭

💡 小技巧：
• 輸入「天氣」查台北
• 輸入「高雄天氣」查高雄
• 輸入「會下雨嗎」查台北降雨

🔗 完整功能：
https://auspicious-zeta.vercel.app"""


@router.post("/webhook")
async def line_webhook(request: Request, db: Session = Depends(get_db)):
    """LINE Webhook 端點"""
    # 取得請求內容
    body = await request.body()
    signature = request.headers.get("X-Line-Signature", "")

    # 驗證簽名
    if not verify_signature(body, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    # 解析事件
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    events = data.get("events", [])

    for event in events:
        event_type = event.get("type")
        reply_token = event.get("replyToken")

        if not reply_token:
            continue

        # 處理訊息事件
        if event_type == "message":
            message = event.get("message", {})
            message_type = message.get("type")

            if message_type == "text":
                user_text = message.get("text", "")
                query = parse_user_query(user_text)

                if query["type"] == "help":
                    reply_text = get_help_message()
                elif query["type"] == "weather":
                    reply_text = await generate_weather_reply(
                        query["station_id"],
                        query["city"],
                        db
                    )
                else:
                    reply_text = f"""🤔 不太確定你的意思

試試這些指令：
• 輸入城市名（如「台北」「高雄」）
• 輸入「天氣」查看台北天氣
• 輸入「幫助」查看完整說明"""

                await reply_message(reply_token, [{"type": "text", "text": reply_text}])

        # 處理加好友事件
        elif event_type == "follow":
            welcome = """👋 歡迎使用好日子天氣機器人！

直接輸入城市名稱即可查詢天氣
例如：台北、高雄、花蓮

輸入「幫助」查看完整說明 🌤"""
            await reply_message(reply_token, [{"type": "text", "text": welcome}])

    return {"status": "ok"}


@router.get("/webhook")
async def verify_webhook():
    """LINE Webhook 驗證端點（GET 請求）"""
    return {"status": "ok", "message": "Webhook is ready"}
