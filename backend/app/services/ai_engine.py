# backend/app/services/ai_engine.py
"""AI 智慧引擎服務

整合 Google Gemini 生成智慧解讀：
- 節氣深度解讀
- 諺語科學解釋
- 天氣建議
- 活動規劃建議
"""

import os
from datetime import date
from typing import Optional
from dataclasses import dataclass
from functools import lru_cache
import json

import google.generativeai as genai
from google.generativeai.types import GenerateContentResponse

from app.config import settings


# ============================================
# 配置
# ============================================

# 從環境變數取得 API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# 模型配置
MODEL_NAME = "gemini-2.0-flash"  # 使用最新的 Flash 模型（快速且便宜）

# 生成配置
GENERATION_CONFIG = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 1024,
}

# 安全設定（調整為較寬鬆）
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
]


@dataclass
class AIResponse:
    """AI 回應結構"""
    content: str
    model: str
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    cached: bool = False


def _init_model() -> Optional[genai.GenerativeModel]:
    """初始化 Gemini 模型"""
    if not GEMINI_API_KEY:
        return None

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            generation_config=GENERATION_CONFIG,
            safety_settings=SAFETY_SETTINGS,
        )
        return model
    except Exception as e:
        print(f"初始化 Gemini 失敗: {e}")
        return None


# 延遲初始化模型
_model: Optional[genai.GenerativeModel] = None


def get_model() -> Optional[genai.GenerativeModel]:
    """取得模型實例（延遲初始化）"""
    global _model
    if _model is None:
        _model = _init_model()
    return _model


def is_ai_available() -> bool:
    """檢查 AI 服務是否可用"""
    return bool(GEMINI_API_KEY) and get_model() is not None


# ============================================
# Prompt 模板
# ============================================

SYSTEM_CONTEXT = """你是「好日子」天氣 App 的 AI 助手，專門提供臺灣氣象知識解讀。

你的專業領域包括：
1. 二十四節氣的天文、農業、氣象意義
2. 臺灣在地氣象諺語的科學解釋
3. 臺灣各地微氣候特徵
4. 基於歷史氣象數據的分析解讀
5. 活動規劃的天氣建議

回應風格：
- 使用繁體中文
- 簡潔有力，避免冗長
- 結合科學知識與生活應用
- 適當加入臺灣在地觀點
- 如有不確定處，誠實說明

限制：
- 不提供精確的天氣預報（那是氣象局的工作）
- 只提供歷史統計和一般性建議
- 不做投資或重大決策的建議
"""


def _create_solar_term_prompt(
    term_name: str,
    term_info: dict,
    current_weather: Optional[dict] = None,
    historical_avg: Optional[dict] = None,
) -> str:
    """建立節氣解讀的 Prompt"""
    prompt = f"""請為節氣「{term_name}」提供深度解讀。

節氣資訊：
- 英文：{term_info.get('name_en', '')}
- 序號：第 {term_info.get('order', '')} 個節氣
- 季節：{term_info.get('season', '')}
- 太陽黃經：{term_info.get('solar_longitude', '')} 度
- 典型日期：{term_info.get('typical_date', '')}
- 天文意義：{term_info.get('astronomy', '')}
- 農業意義：{term_info.get('agriculture', '')}
- 臺灣氣象特徵：{term_info.get('weather', '')}
- 物候（三候）：{', '.join(term_info.get('phenology', []))}
- 相關諺語：{', '.join(term_info.get('proverbs', [])[:3])}
- 養生建議：{term_info.get('health_tips', '')}
"""

    if current_weather:
        prompt += f"""
今日天氣（供參考）：
- 溫度：{current_weather.get('temperature', 'N/A')}°C
- 天氣狀況：{current_weather.get('weather', 'N/A')}
"""

    if historical_avg:
        prompt += f"""
歷史平均（供比較）：
- 歷史平均溫度：{historical_avg.get('temp_avg', 'N/A')}°C
"""

    prompt += """
請提供：
1. **節氣意涵**（50字內）：用白話解釋這個節氣的核心意義
2. **臺灣觀點**（80字內）：這個節氣在臺灣的特殊意義或現象
3. **生活建議**（50字內）：這段時間的生活、飲食、活動建議
4. **有趣小知識**（50字內）：一個與這節氣相關的有趣事實

請用 JSON 格式回應，包含 meaning、taiwan_perspective、life_tips、fun_fact 四個欄位。
"""
    return prompt


def _create_proverb_prompt(
    proverb_text: str,
    proverb_info: dict,
    verification_result: Optional[dict] = None,
) -> str:
    """建立諺語解讀的 Prompt"""
    prompt = f"""請解讀臺灣氣象諺語：「{proverb_text}」

諺語資訊：
- 白話意思：{proverb_info.get('meaning', '')}
- 分類：{proverb_info.get('category', '')}
- 來源地區：{proverb_info.get('region', '')}
- 相關節氣：{proverb_info.get('related_solar_term', '無')}
- 適用月份：{proverb_info.get('applicable_months', [])}
- 科學解釋：{proverb_info.get('scientific_explanation', '')}
"""

    if verification_result:
        prompt += f"""
歷史驗證結果：
- 驗證樣本數：{verification_result.get('total_cases', 0)}
- 準確率：{verification_result.get('accuracy_rate', 0) * 100:.1f}%
- 驗證解讀：{verification_result.get('interpretation', '')}
"""

    prompt += """
請提供：
1. **白話翻譯**（30字內）：用現代語言解釋這句諺語
2. **科學解釋**（100字內）：從氣象學角度解釋為何這諺語有道理（或沒道理）
3. **現代應用**（50字內）：這句諺語對現代人的實用價值
4. **可信度評估**（20字內）：根據驗證結果，給出可信度評語

請用 JSON 格式回應，包含 translation、scientific_analysis、modern_use、reliability 四個欄位。
"""
    return prompt


def _create_activity_suggestion_prompt(
    activity_type: str,
    location: str,
    date_str: str,
    weather_info: dict,
    historical_stats: dict,
) -> str:
    """建立活動建議的 Prompt"""
    prompt = f"""請為以下活動提供天氣建議：

活動資訊：
- 類型：{activity_type}
- 地點：{location}
- 日期：{date_str}

天氣資訊：
- 歷史平均溫度：{historical_stats.get('temp_avg_mean', 'N/A')}°C
- 歷史降雨機率：{historical_stats.get('precip_probability', 0) * 100:.0f}%
- 歷史晴天比例：{historical_stats.get('tendency_sunny', 0) * 100:.0f}%

請提供：
1. **適合度評分**（1-10）：這天適合該活動的程度
2. **天氣預期**（50字內）：根據歷史數據，這天可能的天氣狀況
3. **建議**（100字內）：具體的活動建議，包含備案
4. **注意事項**（50字內）：特別需要注意的天氣因素

請用 JSON 格式回應，包含 score、weather_expectation、suggestions、cautions 四個欄位。
"""
    return prompt


def _create_daily_insight_prompt(
    date_str: str,
    lunar_info: dict,
    solar_term_info: Optional[dict],
    weather_stats: dict,
    climate_trend: Optional[dict],
) -> str:
    """建立每日洞察的 Prompt"""
    prompt = f"""請為 {date_str} 提供天氣洞察。

日期資訊：
- 農曆：{lunar_info.get('lunar_date', '')}
- 節氣：{solar_term_info.get('name', '無') if solar_term_info else '無'}

歷史天氣統計：
- 平均溫度：{weather_stats.get('temp_avg_mean', 'N/A')}°C
- 降雨機率：{weather_stats.get('precip_probability', 0) * 100:.0f}%
- 晴天比例：{weather_stats.get('tendency_sunny', 0) * 100:.0f}%
"""

    if climate_trend:
        prompt += f"""
氣候趨勢：
- 近 10 年溫度變化：{climate_trend.get('trend_per_decade', 0):.2f}°C/10年
- 趨勢解讀：{climate_trend.get('interpretation', '')}
"""

    prompt += """
請提供一段 50-80 字的每日洞察，包含：
1. 這天的歷史天氣特徵
2. 與氣候變遷的關聯（如有）
3. 一句生活建議

直接回傳洞察文字，不需要 JSON 格式。
"""
    return prompt


# ============================================
# AI 生成函數
# ============================================

def generate_solar_term_insight(
    term_name: str,
    term_info: dict,
    current_weather: Optional[dict] = None,
    historical_avg: Optional[dict] = None,
) -> Optional[AIResponse]:
    """生成節氣深度解讀

    Args:
        term_name: 節氣名稱
        term_info: 節氣資訊字典
        current_weather: 當前天氣（可選）
        historical_avg: 歷史平均（可選）

    Returns:
        AIResponse 或 None（如果 AI 不可用）
    """
    model = get_model()
    if not model:
        return None

    prompt = _create_solar_term_prompt(term_name, term_info, current_weather, historical_avg)

    try:
        response = model.generate_content(
            [SYSTEM_CONTEXT, prompt],
        )

        if response.text:
            return AIResponse(
                content=response.text,
                model=MODEL_NAME,
            )
    except Exception as e:
        print(f"生成節氣解讀失敗: {e}")

    return None


def generate_proverb_insight(
    proverb_text: str,
    proverb_info: dict,
    verification_result: Optional[dict] = None,
) -> Optional[AIResponse]:
    """生成諺語科學解讀

    Args:
        proverb_text: 諺語原文
        proverb_info: 諺語資訊字典
        verification_result: 驗證結果（可選）

    Returns:
        AIResponse 或 None
    """
    model = get_model()
    if not model:
        return None

    prompt = _create_proverb_prompt(proverb_text, proverb_info, verification_result)

    try:
        response = model.generate_content(
            [SYSTEM_CONTEXT, prompt],
        )

        if response.text:
            return AIResponse(
                content=response.text,
                model=MODEL_NAME,
            )
    except Exception as e:
        print(f"生成諺語解讀失敗: {e}")

    return None


def generate_activity_suggestion(
    activity_type: str,
    location: str,
    target_date: date,
    weather_info: dict,
    historical_stats: dict,
) -> Optional[AIResponse]:
    """生成活動建議

    Args:
        activity_type: 活動類型（如：婚禮、野餐、登山）
        location: 地點
        target_date: 目標日期
        weather_info: 天氣資訊
        historical_stats: 歷史統計

    Returns:
        AIResponse 或 None
    """
    model = get_model()
    if not model:
        return None

    date_str = target_date.strftime("%Y年%m月%d日")
    prompt = _create_activity_suggestion_prompt(
        activity_type, location, date_str, weather_info, historical_stats
    )

    try:
        response = model.generate_content(
            [SYSTEM_CONTEXT, prompt],
        )

        if response.text:
            return AIResponse(
                content=response.text,
                model=MODEL_NAME,
            )
    except Exception as e:
        print(f"生成活動建議失敗: {e}")

    return None


def generate_daily_insight(
    target_date: date,
    lunar_info: dict,
    solar_term_info: Optional[dict],
    weather_stats: dict,
    climate_trend: Optional[dict] = None,
) -> Optional[AIResponse]:
    """生成每日洞察

    Args:
        target_date: 目標日期
        lunar_info: 農曆資訊
        solar_term_info: 節氣資訊（可選）
        weather_stats: 天氣統計
        climate_trend: 氣候趨勢（可選）

    Returns:
        AIResponse 或 None
    """
    model = get_model()
    if not model:
        return None

    date_str = target_date.strftime("%Y年%m月%d日")
    prompt = _create_daily_insight_prompt(
        date_str, lunar_info, solar_term_info, weather_stats, climate_trend
    )

    try:
        response = model.generate_content(
            [SYSTEM_CONTEXT, prompt],
        )

        if response.text:
            return AIResponse(
                content=response.text,
                model=MODEL_NAME,
            )
    except Exception as e:
        print(f"生成每日洞察失敗: {e}")

    return None


def parse_json_response(response: AIResponse) -> Optional[dict]:
    """解析 JSON 格式的 AI 回應

    Args:
        response: AI 回應

    Returns:
        解析後的字典，或 None（解析失敗時）
    """
    if not response or not response.content:
        return None

    content = response.content.strip()

    # 嘗試移除 markdown 代碼塊標記
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]

    content = content.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # 嘗試修復常見問題
        try:
            # 有時 AI 會回傳多行 JSON
            lines = [line for line in content.split('\n') if line.strip()]
            for i, line in enumerate(lines):
                if line.strip().startswith('{'):
                    json_str = '\n'.join(lines[i:])
                    # 找到 } 結尾
                    brace_count = 0
                    end_idx = 0
                    for j, char in enumerate(json_str):
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                end_idx = j + 1
                                break
                    return json.loads(json_str[:end_idx])
        except Exception:
            pass

        print(f"JSON 解析失敗: {content[:200]}")
        return None
