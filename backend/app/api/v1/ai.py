# backend/app/api/v1/ai.py
"""AI 智慧引擎 API 路由"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query, Path, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.weather import ApiResponse
from app.services.ai_engine import (
    is_ai_available,
    generate_solar_term_insight,
    generate_proverb_insight,
    generate_activity_suggestion,
    generate_daily_insight,
    parse_json_response,
)
from app.services.solar_term import get_solar_term_info, get_current_solar_term, get_nearest_solar_term
from app.api.v1.line_webhook import process_with_function_calling
from app.services.proverb import get_proverb_by_id
from app.services.proverb_verify import verify_proverb
from app.services.lunar import get_lunar_info
from app.models import DailyStatistics

router = APIRouter()


# ============================================
# Response Schemas
# ============================================

class AIStatusResponse(BaseModel):
    """AI 狀態回應"""
    available: bool = Field(..., description="AI 服務是否可用")
    model: str = Field(..., description="使用的模型")
    provider: str = Field(default="Vertex AI", description="AI 提供者")
    message: str = Field(..., description="狀態訊息")


class SolarTermInsightResponse(BaseModel):
    """節氣 AI 解讀回應"""
    term_name: str = Field(..., description="節氣名稱")
    meaning: Optional[str] = Field(None, description="節氣意涵")
    taiwan_perspective: Optional[str] = Field(None, description="臺灣觀點")
    life_tips: Optional[str] = Field(None, description="生活建議")
    fun_fact: Optional[str] = Field(None, description="有趣小知識")
    raw_response: Optional[str] = Field(None, description="原始回應（JSON 解析失敗時）")
    model: str = Field(..., description="使用的模型")


class ProverbInsightResponse(BaseModel):
    """諺語 AI 解讀回應"""
    proverb_text: str = Field(..., description="諺語原文")
    translation: Optional[str] = Field(None, description="白話翻譯")
    scientific_analysis: Optional[str] = Field(None, description="科學解釋")
    modern_use: Optional[str] = Field(None, description="現代應用")
    reliability: Optional[str] = Field(None, description="可信度評估")
    raw_response: Optional[str] = Field(None, description="原始回應")
    model: str = Field(..., description="使用的模型")


class ActivitySuggestionResponse(BaseModel):
    """活動建議回應"""
    activity_type: str = Field(..., description="活動類型")
    location: str = Field(..., description="地點")
    target_date: str = Field(..., description="目標日期")
    score: Optional[int] = Field(None, description="適合度評分 (1-10)")
    weather_expectation: Optional[str] = Field(None, description="天氣預期")
    suggestions: Optional[str] = Field(None, description="建議")
    cautions: Optional[str] = Field(None, description="注意事項")
    raw_response: Optional[str] = Field(None, description="原始回應")
    model: str = Field(..., description="使用的模型")


class DailyInsightResponse(BaseModel):
    """每日洞察回應"""
    date: str = Field(..., description="日期")
    lunar_date: str = Field(..., description="農曆日期")
    solar_term: Optional[str] = Field(None, description="節氣")
    insight: str = Field(..., description="洞察內容")
    model: str = Field(..., description="使用的模型")


class ChatRequest(BaseModel):
    """聊天請求"""
    message: str = Field(..., description="用戶訊息", min_length=1, max_length=500)


class ChatResponse(BaseModel):
    """聊天回應"""
    message: str = Field(..., description="AI 回應")
    data_source: str = Field(default="中央氣象署36年歷史統計(1991-2026)", description="資料來源")


# ============================================
# API Endpoints
# ============================================

@router.get(
    "/status",
    response_model=ApiResponse[AIStatusResponse],
    summary="檢查 AI 服務狀態",
    description="檢查 AI 智慧引擎是否可用"
)
async def check_status():
    """檢查 AI 服務狀態"""
    available = is_ai_available()
    return ApiResponse(
        success=True,
        data=AIStatusResponse(
            available=available,
            model="gemini-2.0-flash" if available else "N/A",
            provider="Google AI Studio",
            message="AI 服務正常運作" if available else "AI 服務不可用（未設定 GEMINI_API_KEY 或配額已用完）"
        )
    )


@router.get(
    "/solar-term/{term_name}",
    response_model=ApiResponse[SolarTermInsightResponse],
    summary="生成節氣 AI 解讀",
    description="使用 AI 生成指定節氣的深度解讀"
)
async def get_solar_term_insight(
    term_name: str = Path(..., description="節氣名稱（如：立春、雨水）"),
    db: Session = Depends(get_db)
):
    """生成節氣 AI 解讀"""
    # 檢查 AI 是否可用
    if not is_ai_available():
        return ApiResponse(
            success=False,
            error="AI 服務不可用"
        )

    # 取得節氣資訊
    term_info = get_solar_term_info(term_name)
    if not term_info:
        return ApiResponse(
            success=False,
            error=f"找不到節氣：{term_name}"
        )

    # 轉換為字典
    term_dict = {
        "name_en": term_info.name_en,
        "order": term_info.order,
        "season": term_info.season,
        "solar_longitude": term_info.solar_longitude,
        "typical_date": term_info.typical_date,
        "astronomy": term_info.astronomy,
        "agriculture": term_info.agriculture,
        "weather": term_info.weather,
        "phenology": term_info.phenology,
        "proverbs": term_info.proverbs,
        "health_tips": term_info.health_tips,
    }

    # 生成 AI 解讀
    response = generate_solar_term_insight(term_name, term_dict)

    if not response:
        return ApiResponse(
            success=False,
            error="AI 生成失敗"
        )

    # 解析 JSON 回應
    parsed = parse_json_response(response)

    if parsed:
        return ApiResponse(
            success=True,
            data=SolarTermInsightResponse(
                term_name=term_name,
                meaning=parsed.get("meaning"),
                taiwan_perspective=parsed.get("taiwan_perspective"),
                life_tips=parsed.get("life_tips"),
                fun_fact=parsed.get("fun_fact"),
                model=response.model,
            )
        )
    else:
        # JSON 解析失敗，返回原始內容
        return ApiResponse(
            success=True,
            data=SolarTermInsightResponse(
                term_name=term_name,
                raw_response=response.content,
                model=response.model,
            )
        )


@router.get(
    "/proverb/{proverb_id}",
    response_model=ApiResponse[ProverbInsightResponse],
    summary="生成諺語 AI 解讀",
    description="使用 AI 生成指定諺語的科學解讀"
)
async def get_proverb_insight(
    proverb_id: str = Path(..., description="諺語 ID"),
    include_verification: bool = Query(True, description="是否包含驗證結果"),
    db: Session = Depends(get_db)
):
    """生成諺語 AI 解讀"""
    if not is_ai_available():
        return ApiResponse(
            success=False,
            error="AI 服務不可用"
        )

    # 取得諺語資訊
    proverb = get_proverb_by_id(proverb_id)
    if not proverb:
        return ApiResponse(
            success=False,
            error=f"找不到諺語：{proverb_id}"
        )

    proverb_dict = {
        "meaning": proverb.meaning,
        "category": proverb.category.value,
        "region": proverb.region.value,
        "related_solar_term": proverb.related_solar_term,
        "applicable_months": proverb.applicable_months,
        "scientific_explanation": proverb.scientific_explanation,
    }

    # 取得驗證結果
    verification_dict = None
    if include_verification and proverb.verifiable:
        verification = verify_proverb(db, proverb_id)
        if verification:
            verification_dict = {
                "total_cases": verification.verification.total_cases,
                "accuracy_rate": verification.verification.accuracy_rate,
                "interpretation": verification.verification.interpretation,
            }

    # 生成 AI 解讀
    response = generate_proverb_insight(proverb.text, proverb_dict, verification_dict)

    if not response:
        return ApiResponse(
            success=False,
            error="AI 生成失敗"
        )

    parsed = parse_json_response(response)

    if parsed:
        return ApiResponse(
            success=True,
            data=ProverbInsightResponse(
                proverb_text=proverb.text,
                translation=parsed.get("translation"),
                scientific_analysis=parsed.get("scientific_analysis"),
                modern_use=parsed.get("modern_use"),
                reliability=parsed.get("reliability"),
                model=response.model,
            )
        )
    else:
        return ApiResponse(
            success=True,
            data=ProverbInsightResponse(
                proverb_text=proverb.text,
                raw_response=response.content,
                model=response.model,
            )
        )


@router.get(
    "/activity-suggestion",
    response_model=ApiResponse[ActivitySuggestionResponse],
    summary="生成活動建議",
    description="根據歷史天氣數據生成活動建議"
)
async def get_activity_suggestion(
    activity_type: str = Query(..., description="活動類型（如：婚禮、野餐、登山）"),
    location: str = Query(..., description="地點（如：臺北、高雄）"),
    target_date: str = Query(..., description="目標日期 (YYYY-MM-DD)"),
    station_id: Optional[str] = Query(None, description="站點 ID"),
    db: Session = Depends(get_db)
):
    """生成活動建議"""
    if not is_ai_available():
        return ApiResponse(
            success=False,
            error="AI 服務不可用"
        )

    # 解析日期
    try:
        target = date.fromisoformat(target_date)
    except ValueError:
        return ApiResponse(
            success=False,
            error="日期格式錯誤，請使用 YYYY-MM-DD"
        )

    # 取得歷史統計
    month_day = target.strftime("%m-%d")
    if not station_id:
        station_id = "466920"  # 預設臺北站

    stats = db.query(DailyStatistics).filter(
        DailyStatistics.station_id == station_id,
        DailyStatistics.month_day == month_day
    ).first()

    if not stats:
        return ApiResponse(
            success=False,
            error=f"找不到站點 {station_id} 在 {month_day} 的歷史統計"
        )

    stats_dict = {
        "temp_avg_mean": stats.temp_avg_mean,
        "precip_probability": stats.precip_probability,
        "tendency_sunny": stats.tendency_sunny,
    }

    # 生成建議
    response = generate_activity_suggestion(
        activity_type, location, target, {}, stats_dict
    )

    if not response:
        return ApiResponse(
            success=False,
            error="AI 生成失敗"
        )

    parsed = parse_json_response(response)

    if parsed:
        score = parsed.get("score")
        if isinstance(score, str):
            try:
                score = int(score)
            except ValueError:
                score = None

        return ApiResponse(
            success=True,
            data=ActivitySuggestionResponse(
                activity_type=activity_type,
                location=location,
                target_date=target_date,
                score=score,
                weather_expectation=parsed.get("weather_expectation"),
                suggestions=parsed.get("suggestions"),
                cautions=parsed.get("cautions"),
                model=response.model,
            )
        )
    else:
        return ApiResponse(
            success=True,
            data=ActivitySuggestionResponse(
                activity_type=activity_type,
                location=location,
                target_date=target_date,
                raw_response=response.content,
                model=response.model,
            )
        )


@router.get(
    "/daily-insight",
    response_model=ApiResponse[DailyInsightResponse],
    summary="生成每日洞察",
    description="生成指定日期的天氣洞察"
)
async def get_daily_insight(
    target_date: Optional[str] = Query(None, description="目標日期 (YYYY-MM-DD)，預設今天"),
    station_id: Optional[str] = Query(None, description="站點 ID"),
    db: Session = Depends(get_db)
):
    """生成每日洞察"""
    if not is_ai_available():
        return ApiResponse(
            success=False,
            error="AI 服務不可用"
        )

    # 解析日期
    if target_date:
        try:
            target = date.fromisoformat(target_date)
        except ValueError:
            return ApiResponse(
                success=False,
                error="日期格式錯誤，請使用 YYYY-MM-DD"
            )
    else:
        target = date.today()

    # 取得農曆資訊
    lunar_info = get_lunar_info(target)
    lunar_dict = {
        "lunar_date": f"{lunar_info.lunar_month}月{lunar_info.lunar_day}"
    }

    # 取得節氣資訊
    solar_term = get_current_solar_term(target)
    solar_term_dict = None
    if solar_term:
        term_info = get_solar_term_info(solar_term)
        if term_info:
            solar_term_dict = {"name": term_info.name}

    # 取得歷史統計
    month_day = target.strftime("%m-%d")
    if not station_id:
        station_id = "466920"

    stats = db.query(DailyStatistics).filter(
        DailyStatistics.station_id == station_id,
        DailyStatistics.month_day == month_day
    ).first()

    stats_dict = {}
    if stats:
        stats_dict = {
            "temp_avg_mean": stats.temp_avg_mean,
            "precip_probability": stats.precip_probability,
            "tendency_sunny": stats.tendency_sunny,
        }

    # 生成洞察
    response = generate_daily_insight(target, lunar_dict, solar_term_dict, stats_dict)

    if not response:
        return ApiResponse(
            success=False,
            error="AI 生成失敗"
        )

    return ApiResponse(
        success=True,
        data=DailyInsightResponse(
            date=target.isoformat(),
            lunar_date=lunar_dict["lunar_date"],
            solar_term=solar_term,
            insight=response.content.strip(),
            model=response.model,
        )
    )


@router.post(
    "/chat",
    response_model=ApiResponse[ChatResponse],
    summary="AI 天氣助手對話",
    description="使用 Function Calling 查詢歷史資料庫，回答任何天氣相關問題"
)
async def chat_with_ai(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    好日子 AI 天氣助手

    可以問的問題類型：
    - 即時天氣：「台北現在天氣」
    - 未來預估：「10天後高雄天氣」
    - 最熱日子：「台北全年最熱哪天」
    - 最冷日子：「今年最冷是什麼時候」
    - 最少雨日：「五月哪天最適合出遊」
    - 月份比較：「7月和8月哪個比較熱」

    所有回答都基於中央氣象署 36 年歷史統計資料。
    """
    try:
        response = await process_with_function_calling(request.message, db)
        return ApiResponse(
            success=True,
            data=ChatResponse(
                message=response,
                data_source="中央氣象署36年歷史統計(1991-2026)"
            )
        )
    except Exception as e:
        print(f"AI 對話失敗: {e}")
        import traceback
        traceback.print_exc()
        return ApiResponse(
            success=False,
            data=None,
            error="AI 服務暫時無法使用，請稍後再試"
        )
