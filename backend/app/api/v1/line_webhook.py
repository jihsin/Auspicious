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
from app.services.ai_engine import generate_daily_insight

router = APIRouter()

# LINE 設定
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"

# 站點對應（只使用有 36 年歷史資料的站點）
STATION_MAPPING = {
    "台北": "466920",
    "臺北": "466920",
    "新北": "466920",
    "板橋": "466920",  # 使用台北站
    "桃園": "467571",  # 使用新竹站（最近）
    "新竹": "467571",
    "台中": "467490",
    "臺中": "467490",
    "彰化": "467490",  # 使用台中站
    "南投": "467650",  # 日月潭
    "嘉義": "467480",
    "阿里山": "467530",
    "台南": "467410",
    "臺南": "467410",
    "高雄": "467440",
    "屏東": "467590",  # 恆春
    "恆春": "467590",
    "花蓮": "466990",
    "台東": "467660",
    "臺東": "467660",
    "宜蘭": "466920",  # 使用台北站（最近）
    "基隆": "466940",
    "澎湖": "467350",
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


async def parse_user_query_with_ai(text: str) -> dict:
    """使用 AI 解析用戶查詢意圖

    Returns:
        dict: {"type": "weather|recommend|help|chat", ...}
    """
    import google.generativeai as genai
    from app.config import settings

    text = text.strip()

    # 幫助指令（快速處理）
    if text.lower() in ["help", "幫助", "說明", "?", "？", "指令"]:
        return {"type": "help", "city": None, "original_query": text}

    # 使用 AI 解析意圖
    try:
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")

        prompt = f"""你是一個天氣查詢助手。分析用戶的訊息，判斷他們想要什麼。

用戶訊息：「{text}」

請用 JSON 格式回答（只回傳 JSON，不要其他文字）：
{{
  "intent": "weather" 或 "recommend" 或 "chat" 或 "help",
  "city": "城市名" 或 null,
  "month": 月份數字(1-12) 或 null,
  "preference": "sunny" 或 "cool" 或 "dry" 或 null,
  "days": 連續天數 或 null,
  "needs_ai_response": true 或 false
}}

規則：
- "weather"：查詢即時天氣、今天會不會下雨等
- "recommend"：推薦好日子、找特定條件的日期（如：連續晴天、適合出遊的日子、幾月幾號適合辦活動）
- "chat"：閒聊、打招呼、非天氣問題
- "help"：詢問功能、怎麼使用

- city 只能是：台北、新北、桃園、新竹、台中、彰化、南投、嘉義、台南、高雄、屏東、花蓮、台東、宜蘭、基隆、澎湖
- 如果沒提到城市，city 設為 null（會用台北）
- preference：晴天/出遊/戶外=sunny，涼爽/舒適=cool，乾燥/不下雨=dry
- days：如果用戶說「連續三天」就是 3"""

        response = model.generate_content(prompt)
        response_text = response.text.strip()

        # 解析 JSON
        import json
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        response_text = response_text.strip()

        result = json.loads(response_text)

        intent = result.get("intent", "chat")
        city = result.get("city") or "台北"
        month = result.get("month")
        preference = result.get("preference") or "sunny"
        days = result.get("days")
        needs_ai = result.get("needs_ai_response", False)

        # 確認城市有對應的站點
        station_id = STATION_MAPPING.get(city, "466920")

        if intent == "weather":
            return {
                "type": "weather",
                "city": city,
                "station_id": station_id,
                "original_query": text,
                "needs_ai": needs_ai
            }
        elif intent == "recommend":
            return {
                "type": "recommend",
                "city": city,
                "station_id": station_id,
                "month": month,
                "preference": preference,
                "days": days,
                "original_query": text
            }
        elif intent == "help":
            return {"type": "help", "city": None, "original_query": text}
        else:
            return {"type": "chat", "city": None, "original_query": text, "needs_ai": True}

    except Exception as e:
        print(f"AI 解析失敗: {e}")
        return parse_user_query_fallback(text)


def parse_user_query_fallback(text: str) -> dict:
    """備用：關鍵字匹配（當 AI 失敗時）"""
    text_lower = text.strip().lower()

    for city, station_id in STATION_MAPPING.items():
        if city in text_lower:
            return {"type": "weather", "city": city, "station_id": station_id, "original_query": text}

    if any(kw in text_lower for kw in ["天氣", "氣溫", "溫度", "下雨", "出門", "熱", "冷"]):
        return {"type": "weather", "city": "台北", "station_id": "466920", "original_query": text}

    return {"type": "chat", "city": None, "original_query": text, "needs_ai": True}


async def generate_ai_chat_response(user_query: str, weather_context: dict = None) -> str:
    """使用 AI 生成智慧對話回覆"""
    import google.generativeai as genai
    from app.config import settings

    try:
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")

        context = """你是「好日子」天氣機器人，一個親切、專業的台灣天氣助手。

你的特色：
1. 結合 36 年歷史氣象數據，能告訴用戶今天跟往年比較如何
2. 融合農曆、節氣等傳統智慧
3. 回答要簡潔、有溫度、實用

回答風格：
- 用繁體中文
- 適度使用 emoji
- 像朋友聊天一樣自然
- 控制在 200 字以內"""

        if weather_context:
            context += f"""

目前天氣資料：
- 地點：{weather_context.get('city', '台北')}
- 即時天氣：{weather_context.get('weather', '未知')}
- 氣溫：{weather_context.get('temp', 'N/A')}°C
- 歷史平均：{weather_context.get('hist_avg', 'N/A')}°C
- 今日差異：{weather_context.get('diff', 'N/A')}°C
- 降雨機率：{weather_context.get('rain_prob', 'N/A')}%
- 農曆：{weather_context.get('lunar', '')}"""

        prompt = f"{context}\n\n用戶問：「{user_query}」\n\n請回答："

        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        print(f"AI 對話失敗: {e}")
        return "抱歉，我現在有點忙，請稍後再問我天氣問題！"


async def generate_weather_reply(station_id: str, city: str, db: Session, user_query: str = None, needs_ai: bool = False) -> str:
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
        diff = None

    # 降雨機率
    if stats and stats.precip_probability is not None:
        rain_prob = round(stats.precip_probability * 100)
    else:
        rain_prob = None

    # 農曆
    lunar_str = f"{lunar_date.get('month_cn', '')}{lunar_date.get('day_cn', '')}"

    # 如果需要 AI 智慧回覆（用戶問了特定問題）
    if needs_ai and user_query:
        weather_context = {
            "city": city,
            "weather": weather,
            "temp": temp,
            "temp_max": temp_max,
            "temp_min": temp_min,
            "humidity": humidity,
            "hist_avg": hist_avg,
            "diff": diff_str,
            "rain_prob": rain_prob,
            "lunar": lunar_str,
        }
        return await generate_ai_chat_response(user_query, weather_context)

    # 標準天氣報告
    if rain_prob is not None:
        if rain_prob >= 60:
            rain_advice = "☔ 高機率降雨，記得帶傘！"
        elif rain_prob >= 30:
            rain_advice = "🌂 可能下雨，建議備傘"
        else:
            rain_advice = "☀️ 降雨機率低"
    else:
        rain_advice = ""

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


async def generate_recommend_reply(query: dict, db: Session) -> str:
    """生成日期推薦回覆"""
    import google.generativeai as genai
    from app.config import settings

    station_id = query.get("station_id", "466920")
    city = query.get("city", "台北")
    month = query.get("month")
    preference = query.get("preference", "sunny")
    days = query.get("days")
    original_query = query.get("original_query", "")

    # 取得推薦日期
    from app.models import DailyStatistics

    # 查詢該月份的統計資料
    if month:
        month_prefix = f"{month:02d}-"
        stats_list = db.query(DailyStatistics).filter(
            DailyStatistics.station_id == station_id,
            DailyStatistics.month_day.like(f"{month_prefix}%")
        ).all()
    else:
        # 未指定月份，查詢未來 3 個月
        from datetime import datetime
        current_month = datetime.now().month
        months = [(current_month + i - 1) % 12 + 1 for i in range(3)]
        stats_list = db.query(DailyStatistics).filter(
            DailyStatistics.station_id == station_id
        ).all()
        stats_list = [s for s in stats_list if int(s.month_day.split("-")[0]) in months]

    if not stats_list:
        return f"抱歉，找不到 {city} 的歷史資料來推薦日期。"

    # 根據偏好排序
    def score_day(stat):
        score = 0
        if preference == "sunny":
            # 晴天偏好：低降雨機率
            if stat.precip_probability:
                score -= stat.precip_probability * 100
        elif preference == "cool":
            # 涼爽偏好：溫度接近 22-25 度
            if stat.temp_avg_mean:
                score -= abs(stat.temp_avg_mean - 23) * 5
        elif preference == "dry":
            # 乾燥偏好：低降雨機率
            if stat.precip_probability:
                score -= stat.precip_probability * 100
        return score

    sorted_stats = sorted(stats_list, key=score_day, reverse=True)

    # 如果要連續天數
    if days and days > 1:
        best_sequences = []
        for i in range(len(sorted_stats) - days + 1):
            # 檢查是否連續
            seq = sorted_stats[i:i+days]
            # 簡化：只取前幾名組合
            avg_score = sum(score_day(s) for s in seq) / days
            best_sequences.append((seq, avg_score))
        best_sequences.sort(key=lambda x: x[1], reverse=True)
        top_dates = best_sequences[0][0] if best_sequences else sorted_stats[:days]
    else:
        top_dates = sorted_stats[:5]

    # 使用 AI 生成友善回覆
    try:
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")

        dates_info = []
        for stat in top_dates[:5]:
            rain_prob = round(stat.precip_probability * 100) if stat.precip_probability else "N/A"
            temp = round(stat.temp_avg_mean, 1) if stat.temp_avg_mean else "N/A"
            dates_info.append(f"- {stat.month_day}：平均 {temp}°C，降雨機率 {rain_prob}%")

        dates_str = "\n".join(dates_info)

        prompt = f"""用戶問：「{original_query}」

根據 {city} 36年歷史資料，推薦的日期如下：
{dates_str}

請用親切的方式回答用戶，說明推薦原因。
- 簡潔有力，不超過 150 字
- 適度用 emoji
- 如果用戶問連續天數，說明這幾天的特點"""

        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        print(f"AI 推薦回覆失敗: {e}")
        # 降級回覆
        dates_str = ", ".join([s.month_day for s in top_dates[:5]])
        return f"🌤 根據 {city} 36年歷史，推薦日期：{dates_str}\n這些日子天氣較穩定！"


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

                # 使用 AI 解析意圖
                query = await parse_user_query_with_ai(user_text)

                if query["type"] == "help":
                    reply_text = get_help_message()
                elif query["type"] == "weather":
                    reply_text = await generate_weather_reply(
                        query["station_id"],
                        query["city"],
                        db,
                        user_query=query.get("original_query"),
                        needs_ai=query.get("needs_ai", False)
                    )
                elif query["type"] == "recommend":
                    reply_text = await generate_recommend_reply(query, db)
                elif query["type"] == "chat":
                    # 純聊天，用 AI 回覆
                    reply_text = await generate_ai_chat_response(user_text)
                else:
                    reply_text = await generate_ai_chat_response(user_text)

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
