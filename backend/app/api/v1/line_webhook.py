# backend/app/api/v1/line_webhook.py
"""LINE Webhook API - AI 智能版"""

import os
import hashlib
import hmac
import base64
import json
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
import httpx
import google.generativeai as genai

from app.database import get_db
from app.services.realtime_weather import fetch_realtime_weather
from app.services.lunar import get_lunar_info
from app.models import DailyStatistics

router = APIRouter()

# 設定
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# 即時天氣站點
REALTIME_STATIONS = {
    "台北": "466920", "臺北": "466920", "新北": "466881",
    "桃園": "467571", "新竹": "467571",
    "台中": "467490", "臺中": "467490",
    "嘉義": "467480", "台南": "467410", "臺南": "467410",
    "高雄": "467441", "屏東": "467590",
    "花蓮": "466990", "台東": "467660", "臺東": "467660",
    "宜蘭": "467080", "基隆": "466940", "澎湖": "467350",
}

# 歷史統計站點
STATS_STATIONS = {
    "台北": "466920", "臺北": "466920", "新北": "466920",
    "桃園": "467571", "新竹": "467571",
    "台中": "467490", "臺中": "467490",
    "嘉義": "467480", "台南": "467410", "臺南": "467410",
    "高雄": "467440", "屏東": "467590",
    "花蓮": "466990", "台東": "467660", "臺東": "467660",
    "宜蘭": "466920", "基隆": "466940", "澎湖": "467350",
}


def verify_signature(body: bytes, signature: str) -> bool:
    if not LINE_CHANNEL_SECRET:
        return True
    hash_value = hmac.new(LINE_CHANNEL_SECRET.encode(), body, hashlib.sha256).digest()
    return hmac.compare_digest(signature, base64.b64encode(hash_value).decode())


async def reply_line(reply_token: str, text: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://api.line.me/v2/bot/message/reply",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
                },
                json={"replyToken": reply_token, "messages": [{"type": "text", "text": text}]}
            )
            return response.status_code == 200
    except Exception as e:
        print(f"LINE 回覆錯誤: {e}")
        return False


async def ai_process_query(user_message: str, db: Session) -> str:
    """用 AI 處理所有用戶查詢"""

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash")

    today = datetime.now()

    # 第一步：讓 AI 理解用戶意圖
    intent_prompt = f"""你是天氣助手。分析用戶訊息，回傳 JSON（只要 JSON，不要其他文字）。

用戶：「{user_message}」
今天：{today.strftime('%Y-%m-%d')}（星期{['一','二','三','四','五','六','日'][today.weekday()]}）

回傳格式：
{{
  "intent": "realtime_weather" 或 "future_weather" 或 "recommend_dates" 或 "chat",
  "city": "城市名" 或 "台北",
  "target_date": "MM-DD" 或 null,
  "days_from_today": 數字 或 0,
  "month": 月份數字 或 null,
  "preference": "sunny/rainy/cool" 或 null,
  "original_question": "用戶原始問題的重點"
}}

規則：
- 問現在/今天天氣 → realtime_weather, days_from_today=0
- 問明天/後天/X天後/下週X/特定日期 → future_weather, 算出 days_from_today
- 推薦好日子/找日期 → recommend_dates
- 閒聊/其他 → chat
- city 只能是：台北、新北、桃園、新竹、台中、嘉義、台南、高雄、屏東、花蓮、台東、宜蘭、基隆、澎湖"""

    try:
        response = model.generate_content(intent_prompt)
        response_text = response.text.strip()

        # 清理 JSON
        if "```" in response_text:
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        response_text = response_text.strip()

        intent = json.loads(response_text)
        print(f"AI 解析結果: {intent}")

    except Exception as e:
        print(f"AI 解析失敗: {e}")
        # 降級處理
        intent = {"intent": "realtime_weather", "city": "台北", "days_from_today": 0}

    city = intent.get("city", "台北")
    days_offset = intent.get("days_from_today", 0)
    intent_type = intent.get("intent", "realtime_weather")

    # 第二步：根據意圖取得資料
    if intent_type == "realtime_weather":
        return await get_realtime_weather_response(city, user_message, db, model)

    elif intent_type == "future_weather":
        return await get_future_weather_response(city, days_offset, user_message, db, model)

    elif intent_type == "recommend_dates":
        month = intent.get("month")
        preference = intent.get("preference", "sunny")
        return await get_recommend_response(city, month, preference, user_message, db, model)

    else:  # chat
        return await get_chat_response(user_message, model)


async def get_realtime_weather_response(city: str, question: str, db: Session, model) -> str:
    """即時天氣回覆"""
    today = datetime.now()
    month_day = today.strftime("%m-%d")

    realtime_station = REALTIME_STATIONS.get(city, "466920")
    stats_station = STATS_STATIONS.get(city, "466920")

    realtime = await fetch_realtime_weather(realtime_station)
    stats = db.query(DailyStatistics).filter(
        DailyStatistics.station_id == stats_station,
        DailyStatistics.month_day == month_day
    ).first()

    lunar_info = get_lunar_info(today.date())
    lunar_date = lunar_info.get("lunar_date", {})

    if not realtime:
        return f"抱歉，無法取得 {city} 的即時天氣資料。"

    # 組合資料給 AI
    weather_data = f"""
{city} 即時天氣（{realtime.obs_time.strftime('%H:%M') if realtime.obs_time else ''}）：
- 天氣：{realtime.weather or '未知'}
- 氣溫：{realtime.temp}°C
- 最高/最低：{realtime.temp_max}°C / {realtime.temp_min}°C
- 濕度：{realtime.humidity}%

歷史統計（36年）：
- 平均溫度：{round(stats.temp_avg_mean, 1) if stats and stats.temp_avg_mean else 'N/A'}°C
- 降雨機率：{round(stats.precip_probability * 100) if stats and stats.precip_probability else 'N/A'}%

農曆：{lunar_date.get('month_cn', '')}{lunar_date.get('day_cn', '')}
"""

    # 讓 AI 生成回覆
    reply_prompt = f"""根據以下天氣資料，回答用戶問題。

{weather_data}

用戶問：「{question}」

要求：
- 直接回答用戶的問題
- 簡潔有溫度，100字內
- 可以給出建議（如：帶傘、穿外套）
- 適度用 emoji"""

    response = model.generate_content(reply_prompt)
    return response.text.strip()


async def get_future_weather_response(city: str, days_offset: int, question: str, db: Session, model) -> str:
    """未來天氣回覆（用歷史統計）"""
    target_date = datetime.now() + timedelta(days=days_offset)
    month_day = target_date.strftime("%m-%d")

    stats_station = STATS_STATIONS.get(city, "466920")
    stats = db.query(DailyStatistics).filter(
        DailyStatistics.station_id == stats_station,
        DailyStatistics.month_day == month_day
    ).first()

    if not stats:
        return f"抱歉，找不到 {city} 在 {month_day} 的歷史資料。"

    weather_data = f"""
{city} {target_date.strftime('%m/%d')}（{days_offset}天後）歷史統計（36年資料）：
- 平均溫度：{round(stats.temp_avg_mean, 1) if stats.temp_avg_mean else 'N/A'}°C
- 平均最高溫：{round(stats.temp_max_mean, 1) if stats.temp_max_mean else 'N/A'}°C
- 平均最低溫：{round(stats.temp_min_mean, 1) if stats.temp_min_mean else 'N/A'}°C
- 降雨機率：{round(stats.precip_probability * 100) if stats.precip_probability else 'N/A'}%
"""

    reply_prompt = f"""根據歷史統計資料，回答用戶關於未來天氣的問題。

{weather_data}

用戶問：「{question}」

要求：
- 說明這是根據 36 年歷史資料的統計預估
- 給出實用建議
- 簡潔，100字內
- 適度用 emoji"""

    response = model.generate_content(reply_prompt)
    return response.text.strip()


async def get_recommend_response(city: str, month: int, preference: str, question: str, db: Session, model) -> str:
    """日期推薦回覆"""
    stats_station = STATS_STATIONS.get(city, "466920")

    if month:
        stats_list = db.query(DailyStatistics).filter(
            DailyStatistics.station_id == stats_station,
            DailyStatistics.month_day.like(f"{month:02d}-%")
        ).all()
    else:
        # 未來 3 個月
        current_month = datetime.now().month
        months = [(current_month + i - 1) % 12 + 1 for i in range(3)]
        stats_list = db.query(DailyStatistics).filter(
            DailyStatistics.station_id == stats_station
        ).all()
        stats_list = [s for s in stats_list if int(s.month_day.split("-")[0]) in months]

    if not stats_list:
        return f"抱歉，找不到 {city} 的歷史資料。"

    # 按偏好排序
    if preference == "sunny" or preference == "dry":
        sorted_stats = sorted(stats_list, key=lambda s: s.precip_probability or 1)
    elif preference == "cool":
        sorted_stats = sorted(stats_list, key=lambda s: abs((s.temp_avg_mean or 25) - 23))
    else:
        sorted_stats = sorted(stats_list, key=lambda s: s.precip_probability or 1)

    top5 = sorted_stats[:5]
    dates_info = "\n".join([
        f"- {s.month_day}：平均 {round(s.temp_avg_mean, 1) if s.temp_avg_mean else 'N/A'}°C，降雨機率 {round(s.precip_probability * 100) if s.precip_probability else 'N/A'}%"
        for s in top5
    ])

    reply_prompt = f"""根據 {city} 36年歷史資料，推薦日期如下：

{dates_info}

用戶問：「{question}」

要求：
- 說明推薦原因
- 簡潔實用，100字內
- 適度用 emoji"""

    response = model.generate_content(reply_prompt)
    return response.text.strip()


async def get_chat_response(question: str, model) -> str:
    """閒聊回覆"""
    prompt = f"""你是「好日子」天氣機器人，親切友善。

用戶說：「{question}」

回答要求：
- 如果是打招呼，友善回應並介紹自己能查天氣
- 如果是問功能，說明可以查即時天氣、未來天氣預估、推薦好日子
- 簡潔，50字內
- 適度用 emoji"""

    response = model.generate_content(prompt)
    return response.text.strip()


@router.post("/webhook")
async def line_webhook(request: Request, db: Session = Depends(get_db)):
    body = await request.body()
    signature = request.headers.get("X-Line-Signature", "")

    if not verify_signature(body, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    try:
        data = await request.json()
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    for event in data.get("events", []):
        reply_token = event.get("replyToken")
        if not reply_token:
            continue

        if event.get("type") == "message":
            msg = event.get("message", {})
            if msg.get("type") == "text":
                user_text = msg.get("text", "")

                try:
                    reply = await ai_process_query(user_text, db)
                except Exception as e:
                    print(f"處理失敗: {e}")
                    reply = "抱歉，系統忙碌中，請稍後再試。"

                await reply_line(reply_token, reply)

        elif event.get("type") == "follow":
            await reply_line(reply_token, "👋 嗨！我是好日子天氣機器人\n\n直接問我天氣問題吧！\n例如：台北天氣、明天會下雨嗎、推薦五月好日子")

    return {"status": "ok"}


@router.get("/webhook")
async def verify_webhook():
    return {"status": "ok"}
