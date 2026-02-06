# backend/app/api/v1/line_webhook.py
"""LINE Webhook API - Function Calling 版本

所有天氣回答都基於資料庫查詢，不允許 AI 編造數據。
"""

import os
import hashlib
import hmac
import base64
import json
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
import httpx
from google import genai
from google.genai import types

from app.database import get_db
from app.services.realtime_weather import fetch_realtime_weather
from app.services.lunar import get_lunar_info
from app.models import DailyStatistics

router = APIRouter()

# 設定
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# 城市對應站點
REALTIME_STATIONS = {
    "台北": "466920", "臺北": "466920", "新北": "466881",
    "桃園": "467571", "新竹": "467571",
    "台中": "467490", "臺中": "467490",
    "嘉義": "467480", "台南": "467410", "臺南": "467410",
    "高雄": "467441", "屏東": "467590",
    "花蓮": "466990", "台東": "467660", "臺東": "467660",
    "宜蘭": "467080", "基隆": "466940", "澎湖": "467350",
}

STATS_STATIONS = {
    "台北": "466920", "臺北": "466920", "新北": "466920",
    "桃園": "467571", "新竹": "467571",
    "台中": "467490", "臺中": "467490",
    "嘉義": "467480", "台南": "467410", "臺南": "467410",
    "高雄": "467440", "屏東": "467590",
    "花蓮": "466990", "台東": "467660", "臺東": "467660",
    "宜蘭": "466920", "基隆": "466940", "澎湖": "467350",
}

SUPPORTED_CITIES = list(set(REALTIME_STATIONS.keys()))


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


# ============ 資料庫查詢工具函數 ============

class WeatherTools:
    """天氣資料庫查詢工具集"""

    def __init__(self, db: Session):
        self.db = db

    async def get_realtime_weather(self, city: str) -> dict:
        """取得即時天氣資料"""
        station_id = REALTIME_STATIONS.get(city, "466920")
        realtime = await fetch_realtime_weather(station_id)

        if not realtime:
            return {"error": f"無法取得 {city} 的即時天氣資料"}

        today = datetime.now()
        month_day = today.strftime("%m-%d")
        stats_station = STATS_STATIONS.get(city, "466920")
        stats = self.db.query(DailyStatistics).filter(
            DailyStatistics.station_id == stats_station,
            DailyStatistics.month_day == month_day
        ).first()

        lunar_info = get_lunar_info(today.date())
        lunar_date = lunar_info.get("lunar_date", {})

        return {
            "city": city,
            "obs_time": realtime.obs_time.strftime('%Y-%m-%d %H:%M') if realtime.obs_time else "",
            "weather": realtime.weather or "未知",
            "temp": realtime.temp,
            "temp_max": realtime.temp_max,
            "temp_min": realtime.temp_min,
            "humidity": realtime.humidity,
            "precipitation": realtime.precipitation or 0,
            "historical_avg_temp": round(stats.temp_avg_mean, 1) if stats and stats.temp_avg_mean else None,
            "historical_rain_prob": round(stats.precip_probability * 100) if stats and stats.precip_probability else None,
            "lunar_date": f"{lunar_date.get('month_cn', '')}{lunar_date.get('day_cn', '')}",
            "data_source": "中央氣象署即時觀測 + 36年歷史統計"
        }

    def get_date_statistics(self, city: str, month_day: str) -> dict:
        """取得特定日期的歷史統計資料"""
        station_id = STATS_STATIONS.get(city, "466920")
        stats = self.db.query(DailyStatistics).filter(
            DailyStatistics.station_id == station_id,
            DailyStatistics.month_day == month_day
        ).first()

        if not stats:
            return {"error": f"找不到 {city} 在 {month_day} 的歷史資料"}

        return {
            "city": city,
            "date": month_day,
            "temp_avg": round(stats.temp_avg_mean, 1) if stats.temp_avg_mean else None,
            "temp_max_avg": round(stats.temp_max_mean, 1) if stats.temp_max_mean else None,
            "temp_min_avg": round(stats.temp_min_mean, 1) if stats.temp_min_mean else None,
            "rain_probability": round(stats.precip_probability * 100) if stats.precip_probability else None,
            "data_years": 36,
            "data_source": "中央氣象署36年歷史統計(1991-2026)"
        }

    def get_hottest_days(self, city: str, month: Optional[int] = None, top_n: int = 5) -> dict:
        """查詢最熱的日子"""
        station_id = STATS_STATIONS.get(city, "466920")
        query = self.db.query(DailyStatistics).filter(
            DailyStatistics.station_id == station_id,
            DailyStatistics.temp_max_mean.isnot(None)
        )

        if month:
            query = query.filter(DailyStatistics.month_day.like(f"{month:02d}-%"))

        results = query.order_by(DailyStatistics.temp_max_mean.desc()).limit(top_n).all()

        if not results:
            return {"error": f"找不到 {city} 的歷史資料"}

        return {
            "city": city,
            "month": month,
            "hottest_days": [
                {
                    "date": r.month_day,
                    "avg_max_temp": round(r.temp_max_mean, 1),
                    "avg_temp": round(r.temp_avg_mean, 1) if r.temp_avg_mean else None
                }
                for r in results
            ],
            "data_source": "中央氣象署36年歷史統計(1991-2026)"
        }

    def get_coldest_days(self, city: str, month: Optional[int] = None, top_n: int = 5) -> dict:
        """查詢最冷的日子"""
        station_id = STATS_STATIONS.get(city, "466920")
        query = self.db.query(DailyStatistics).filter(
            DailyStatistics.station_id == station_id,
            DailyStatistics.temp_min_mean.isnot(None)
        )

        if month:
            query = query.filter(DailyStatistics.month_day.like(f"{month:02d}-%"))

        results = query.order_by(DailyStatistics.temp_min_mean.asc()).limit(top_n).all()

        if not results:
            return {"error": f"找不到 {city} 的歷史資料"}

        return {
            "city": city,
            "month": month,
            "coldest_days": [
                {
                    "date": r.month_day,
                    "avg_min_temp": round(r.temp_min_mean, 1),
                    "avg_temp": round(r.temp_avg_mean, 1) if r.temp_avg_mean else None
                }
                for r in results
            ],
            "data_source": "中央氣象署36年歷史統計(1991-2026)"
        }

    def get_driest_days(self, city: str, month: Optional[int] = None, top_n: int = 5) -> dict:
        """查詢降雨機率最低的日子（最適合出遊）"""
        station_id = STATS_STATIONS.get(city, "466920")
        query = self.db.query(DailyStatistics).filter(
            DailyStatistics.station_id == station_id,
            DailyStatistics.precip_probability.isnot(None)
        )

        if month:
            query = query.filter(DailyStatistics.month_day.like(f"{month:02d}-%"))

        results = query.order_by(DailyStatistics.precip_probability.asc()).limit(top_n).all()

        if not results:
            return {"error": f"找不到 {city} 的歷史資料"}

        return {
            "city": city,
            "month": month,
            "driest_days": [
                {
                    "date": r.month_day,
                    "rain_probability": round(r.precip_probability * 100),
                    "avg_temp": round(r.temp_avg_mean, 1) if r.temp_avg_mean else None
                }
                for r in results
            ],
            "data_source": "中央氣象署36年歷史統計(1991-2026)"
        }

    def get_rainiest_days(self, city: str, month: Optional[int] = None, top_n: int = 5) -> dict:
        """查詢降雨機率最高的日子"""
        station_id = STATS_STATIONS.get(city, "466920")
        query = self.db.query(DailyStatistics).filter(
            DailyStatistics.station_id == station_id,
            DailyStatistics.precip_probability.isnot(None)
        )

        if month:
            query = query.filter(DailyStatistics.month_day.like(f"{month:02d}-%"))

        results = query.order_by(DailyStatistics.precip_probability.desc()).limit(top_n).all()

        if not results:
            return {"error": f"找不到 {city} 的歷史資料"}

        return {
            "city": city,
            "month": month,
            "rainiest_days": [
                {
                    "date": r.month_day,
                    "rain_probability": round(r.precip_probability * 100),
                    "avg_temp": round(r.temp_avg_mean, 1) if r.temp_avg_mean else None
                }
                for r in results
            ],
            "data_source": "中央氣象署36年歷史統計(1991-2026)"
        }

    def compare_months(self, city: str, month1: int, month2: int) -> dict:
        """比較兩個月份的天氣"""
        station_id = STATS_STATIONS.get(city, "466920")

        def get_month_stats(month: int):
            stats = self.db.query(
                func.avg(DailyStatistics.temp_avg_mean).label('avg_temp'),
                func.avg(DailyStatistics.temp_max_mean).label('avg_max'),
                func.avg(DailyStatistics.temp_min_mean).label('avg_min'),
                func.avg(DailyStatistics.precip_probability).label('rain_prob')
            ).filter(
                DailyStatistics.station_id == station_id,
                DailyStatistics.month_day.like(f"{month:02d}-%")
            ).first()

            return {
                "month": month,
                "avg_temp": round(stats.avg_temp, 1) if stats.avg_temp else None,
                "avg_max_temp": round(stats.avg_max, 1) if stats.avg_max else None,
                "avg_min_temp": round(stats.avg_min, 1) if stats.avg_min else None,
                "avg_rain_probability": round(stats.rain_prob * 100) if stats.rain_prob else None
            }

        return {
            "city": city,
            "month1_stats": get_month_stats(month1),
            "month2_stats": get_month_stats(month2),
            "data_source": "中央氣象署36年歷史統計(1991-2026)"
        }

    def get_future_date_stats(self, city: str, days_from_today: int) -> dict:
        """取得未來某天的歷史統計預估"""
        target_date = datetime.now() + timedelta(days=days_from_today)
        month_day = target_date.strftime("%m-%d")

        result = self.get_date_statistics(city, month_day)
        if "error" not in result:
            result["target_date"] = target_date.strftime("%Y-%m-%d")
            result["days_from_today"] = days_from_today

        return result


# ============ Function Calling 定義 ============

WEATHER_TOOLS = [
    types.FunctionDeclaration(
        name="get_realtime_weather",
        description="取得指定城市的即時天氣資料，包含當前氣溫、天氣狀況、濕度等，以及與歷史平均的比較",
        parameters_json_schema={
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": f"城市名稱，支援：{', '.join(SUPPORTED_CITIES)}"
                }
            },
            "required": ["city"]
        }
    ),
    types.FunctionDeclaration(
        name="get_date_statistics",
        description="取得特定日期的36年歷史天氣統計資料，包含平均溫度、最高最低溫、降雨機率",
        parameters_json_schema={
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名稱"},
                "month_day": {"type": "string", "description": "日期，格式為 MM-DD，例如 07-15"}
            },
            "required": ["city", "month_day"]
        }
    ),
    types.FunctionDeclaration(
        name="get_future_date_stats",
        description="取得未來某天的歷史統計預估，例如「10天後的天氣」",
        parameters_json_schema={
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名稱"},
                "days_from_today": {"type": "integer", "description": "從今天算起的天數，例如 1=明天, 7=一週後, 30=一個月後"}
            },
            "required": ["city", "days_from_today"]
        }
    ),
    types.FunctionDeclaration(
        name="get_hottest_days",
        description="查詢一年中或特定月份最熱的日子（依平均最高溫排序）",
        parameters_json_schema={
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名稱"},
                "month": {"type": "integer", "description": "月份(1-12)，不指定則查全年"},
                "top_n": {"type": "integer", "description": "返回前幾名，預設5"}
            },
            "required": ["city"]
        }
    ),
    types.FunctionDeclaration(
        name="get_coldest_days",
        description="查詢一年中或特定月份最冷的日子（依平均最低溫排序）",
        parameters_json_schema={
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名稱"},
                "month": {"type": "integer", "description": "月份(1-12)，不指定則查全年"},
                "top_n": {"type": "integer", "description": "返回前幾名，預設5"}
            },
            "required": ["city"]
        }
    ),
    types.FunctionDeclaration(
        name="get_driest_days",
        description="查詢降雨機率最低的日子，最適合安排戶外活動或出遊",
        parameters_json_schema={
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名稱"},
                "month": {"type": "integer", "description": "月份(1-12)，不指定則查全年"},
                "top_n": {"type": "integer", "description": "返回前幾名，預設5"}
            },
            "required": ["city"]
        }
    ),
    types.FunctionDeclaration(
        name="get_rainiest_days",
        description="查詢降雨機率最高的日子",
        parameters_json_schema={
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名稱"},
                "month": {"type": "integer", "description": "月份(1-12)，不指定則查全年"},
                "top_n": {"type": "integer", "description": "返回前幾名，預設5"}
            },
            "required": ["city"]
        }
    ),
    types.FunctionDeclaration(
        name="compare_months",
        description="比較兩個月份的天氣差異，例如「7月和8月哪個比較熱」",
        parameters_json_schema={
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名稱"},
                "month1": {"type": "integer", "description": "第一個月份(1-12)"},
                "month2": {"type": "integer", "description": "第二個月份(1-12)"}
            },
            "required": ["city", "month1", "month2"]
        }
    ),
]


async def process_with_function_calling(user_message: str, db: Session) -> str:
    """使用 Function Calling 處理用戶查詢"""

    client = genai.Client(api_key=GEMINI_API_KEY)
    tools = WeatherTools(db)

    today = datetime.now()
    system_instruction = f"""你是「好日子」天氣助手。今天是 {today.strftime('%Y-%m-%d')}（星期{['一','二','三','四','五','六','日'][today.weekday()]}）。

核心理念：
我們使用中央氣象署 36 年歷史統計資料來「預估」未來天氣。當用戶問「2026年最熱哪天」或「明年最冷什麼時候」，我們用歷史上該日期的平均值來預估。

重要規則：
1. 你只能使用提供的工具函數來查詢天氣資料
2. 絕對不可以編造任何數據，所有數字都必須來自工具查詢結果
3. 回答要簡潔（100字內）、友善、適度使用 emoji
4. 提到數據時，說明這是「36年歷史統計預估」

問題對應工具：
- 「2026年/今年/明年最熱哪天」→ 用 get_hottest_days 查歷史最熱日期
- 「2026年/今年/明年最冷哪天」→ 用 get_coldest_days 查歷史最冷日期
- 「五月最適合出遊」→ 用 get_driest_days 查降雨機率最低
- 「X天後天氣」→ 用 get_future_date_stats 查該日期歷史統計

支援的城市：{', '.join(SUPPORTED_CITIES)}"""

    tool_config = types.Tool(function_declarations=WEATHER_TOOLS)

    # 第一次請求：讓 AI 決定要調用什麼工具
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=user_message,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=[tool_config],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
        )
    )

    # 檢查是否有 function call
    if not response.function_calls:
        # 沒有 function call，可能是閒聊
        if response.text:
            return response.text
        return "您好！我是好日子天氣助手，可以幫您查詢即時天氣、歷史統計、推薦好日子等。請問有什麼我可以幫您的？"

    # 執行所有 function calls
    function_responses = []
    for fc in response.function_calls:
        func_name = fc.name
        func_args = dict(fc.args) if fc.args else {}

        print(f"調用工具: {func_name}({func_args})")

        # 執行對應的工具函數
        if func_name == "get_realtime_weather":
            result = await tools.get_realtime_weather(**func_args)
        elif func_name == "get_date_statistics":
            result = tools.get_date_statistics(**func_args)
        elif func_name == "get_future_date_stats":
            result = tools.get_future_date_stats(**func_args)
        elif func_name == "get_hottest_days":
            result = tools.get_hottest_days(**func_args)
        elif func_name == "get_coldest_days":
            result = tools.get_coldest_days(**func_args)
        elif func_name == "get_driest_days":
            result = tools.get_driest_days(**func_args)
        elif func_name == "get_rainiest_days":
            result = tools.get_rainiest_days(**func_args)
        elif func_name == "compare_months":
            result = tools.compare_months(**func_args)
        else:
            result = {"error": f"未知的工具: {func_name}"}

        print(f"工具結果: {result}")

        function_responses.append(
            types.Part.from_function_response(
                name=func_name,
                response={"result": result}
            )
        )

    # 第二次請求：讓 AI 根據工具結果生成回覆
    final_response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            types.Content(role="user", parts=[types.Part.from_text(text=user_message)]),
            response.candidates[0].content,  # AI 的 function call
            types.Content(role="tool", parts=function_responses)  # 工具結果
        ],
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=[tool_config]
        )
    )

    return final_response.text.strip() if final_response.text else "抱歉，無法生成回覆。"


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
                    reply = await process_with_function_calling(user_text, db)
                except Exception as e:
                    print(f"處理失敗: {e}")
                    import traceback
                    traceback.print_exc()
                    reply = "抱歉，系統忙碌中，請稍後再試。"

                await reply_line(reply_token, reply)

        elif event.get("type") == "follow":
            welcome = """👋 嗨！我是「好日子」天氣助手

我可以幫您：
🌡 查即時天氣：「台北現在天氣」
📅 查未來天氣：「10天後高雄天氣」
🔥 找最熱日子：「台北全年最熱哪天」
☀️ 推薦好日子：「五月哪幾天最適合出遊」
📊 比較月份：「7月和8月哪個比較熱」

所有資料來自中央氣象署 36 年歷史統計！"""
            await reply_line(reply_token, welcome)

    return {"status": "ok"}


@router.get("/webhook")
async def verify_webhook():
    return {"status": "ok"}
