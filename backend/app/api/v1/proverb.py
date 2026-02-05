# backend/app/api/v1/proverb.py
"""諺語 API 路由"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, Path
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.weather import ApiResponse
from app.services.proverb import (
    Proverb,
    ProverbCategory,
    ProverbRegion,
    get_all_proverbs,
    get_proverb_by_id,
    get_proverbs_by_category,
    get_proverbs_by_region,
    get_proverbs_by_solar_term,
    get_proverbs_by_month,
    get_verifiable_proverbs,
    search_proverbs,
)
from app.services.proverb_verify import (
    verify_proverb,
    verify_all_proverbs,
    get_proverb_stats_summary,
    VerificationResult,
)

router = APIRouter()


# ============================================
# Response Schemas
# ============================================

class ProverbResponse(BaseModel):
    """諺語回應"""
    id: str = Field(..., description="諺語 ID")
    text: str = Field(..., description="諺語原文")
    reading: Optional[str] = Field(None, description="臺語/客語讀音")
    meaning: str = Field(..., description="白話解釋")
    category: str = Field(..., description="分類")
    region: str = Field(..., description="來源地區")
    related_solar_term: Optional[str] = Field(None, description="相關節氣")
    scientific_explanation: str = Field(..., description="科學解釋")
    applicable_months: list[int] = Field(..., description="適用月份")
    keywords: list[str] = Field(..., description="關鍵字")
    verifiable: bool = Field(..., description="是否可用數據驗證")


class VerificationResponse(BaseModel):
    """驗證結果回應"""
    total_cases: int = Field(..., description="總驗證樣本數")
    positive_cases: int = Field(..., description="符合諺語的樣本數")
    accuracy_rate: float = Field(..., description="準確率 (0-1)")
    interpretation: str = Field(..., description="結果解讀")
    sample_years: list[int] = Field(..., description="使用的年份樣本")
    methodology: str = Field(..., description="驗證方法說明")


class ProverbVerificationResponse(BaseModel):
    """諺語驗證完整回應"""
    proverb_id: str = Field(..., description="諺語 ID")
    proverb_text: str = Field(..., description="諺語原文")
    verification: VerificationResponse = Field(..., description="驗證結果")
    scientific_explanation: str = Field(..., description="科學解釋")
    confidence_level: str = Field(..., description="信心水準（高/中/低）")
    data_quality: str = Field(..., description="資料品質說明")


class ProverbStatsSummary(BaseModel):
    """諺語統計摘要"""
    total_proverbs: int = Field(..., description="諺語總數")
    verifiable_count: int = Field(..., description="可驗證數量")
    verified_count: int = Field(..., description="已驗證數量")
    avg_accuracy: float = Field(..., description="平均準確率")
    high_accuracy_count: int = Field(..., description="高準確率（>65%）數量")


def _convert_proverb_to_response(proverb: Proverb) -> ProverbResponse:
    """將 Proverb 轉換為回應格式"""
    return ProverbResponse(
        id=proverb.id,
        text=proverb.text,
        reading=proverb.reading,
        meaning=proverb.meaning,
        category=proverb.category.value,
        region=proverb.region.value,
        related_solar_term=proverb.related_solar_term,
        scientific_explanation=proverb.scientific_explanation,
        applicable_months=proverb.applicable_months,
        keywords=proverb.keywords,
        verifiable=proverb.verifiable,
    )


def _convert_verification_to_response(result: VerificationResult) -> ProverbVerificationResponse:
    """將 VerificationResult 轉換為回應格式"""
    return ProverbVerificationResponse(
        proverb_id=result.proverb_id,
        proverb_text=result.proverb_text,
        verification=VerificationResponse(
            total_cases=result.verification.total_cases,
            positive_cases=result.verification.positive_cases,
            accuracy_rate=result.verification.accuracy_rate,
            interpretation=result.verification.interpretation,
            sample_years=result.verification.sample_years,
            methodology=result.verification.methodology,
        ),
        scientific_explanation=result.scientific_explanation,
        confidence_level=result.confidence_level,
        data_quality=result.data_quality,
    )


# ============================================
# API Endpoints
# ============================================

@router.get(
    "/all",
    response_model=ApiResponse[list[ProverbResponse]],
    summary="取得所有諺語",
    description="取得氣象諺語資料庫中的所有諺語"
)
async def get_all():
    """取得所有諺語"""
    proverbs = get_all_proverbs()
    return ApiResponse(
        success=True,
        data=[_convert_proverb_to_response(p) for p in proverbs]
    )


@router.get(
    "/by-id/{proverb_id}",
    response_model=ApiResponse[ProverbResponse],
    summary="依 ID 取得諺語",
    description="取得指定 ID 的諺語詳細資訊"
)
async def get_by_id(
    proverb_id: str = Path(..., description="諺語 ID")
):
    """依 ID 取得諺語"""
    proverb = get_proverb_by_id(proverb_id)
    if not proverb:
        return ApiResponse(
            success=False,
            error=f"找不到諺語：{proverb_id}"
        )

    return ApiResponse(
        success=True,
        data=_convert_proverb_to_response(proverb)
    )


@router.get(
    "/by-category/{category}",
    response_model=ApiResponse[list[ProverbResponse]],
    summary="依分類取得諺語",
    description="取得指定分類的所有諺語"
)
async def get_by_category(
    category: str = Path(..., description="分類（節氣/季節/降雨/溫度/農業/颱風/通用）")
):
    """依分類取得諺語"""
    try:
        cat = ProverbCategory(category)
    except ValueError:
        valid_categories = [c.value for c in ProverbCategory]
        return ApiResponse(
            success=False,
            error=f"無效的分類：{category}，有效選項：{', '.join(valid_categories)}"
        )

    proverbs = get_proverbs_by_category(cat)
    return ApiResponse(
        success=True,
        data=[_convert_proverb_to_response(p) for p in proverbs]
    )


@router.get(
    "/by-region/{region}",
    response_model=ApiResponse[list[ProverbResponse]],
    summary="依地區取得諺語",
    description="取得指定地區來源的所有諺語"
)
async def get_by_region(
    region: str = Path(..., description="地區（臺灣/華夏/客家/閩南）")
):
    """依地區取得諺語"""
    try:
        reg = ProverbRegion(region)
    except ValueError:
        valid_regions = [r.value for r in ProverbRegion]
        return ApiResponse(
            success=False,
            error=f"無效的地區：{region}，有效選項：{', '.join(valid_regions)}"
        )

    proverbs = get_proverbs_by_region(reg)
    return ApiResponse(
        success=True,
        data=[_convert_proverb_to_response(p) for p in proverbs]
    )


@router.get(
    "/by-solar-term/{solar_term}",
    response_model=ApiResponse[list[ProverbResponse]],
    summary="依節氣取得諺語",
    description="取得與指定節氣相關的所有諺語"
)
async def get_by_solar_term(
    solar_term: str = Path(..., description="節氣名稱（如：立春、清明）")
):
    """依節氣取得諺語"""
    proverbs = get_proverbs_by_solar_term(solar_term)
    return ApiResponse(
        success=True,
        data=[_convert_proverb_to_response(p) for p in proverbs]
    )


@router.get(
    "/by-month/{month}",
    response_model=ApiResponse[list[ProverbResponse]],
    summary="依月份取得諺語",
    description="取得指定月份適用的所有諺語"
)
async def get_by_month(
    month: int = Path(..., ge=1, le=12, description="月份 (1-12)")
):
    """依月份取得諺語"""
    proverbs = get_proverbs_by_month(month)
    return ApiResponse(
        success=True,
        data=[_convert_proverb_to_response(p) for p in proverbs]
    )


@router.get(
    "/verifiable",
    response_model=ApiResponse[list[ProverbResponse]],
    summary="取得可驗證的諺語",
    description="取得可用歷史數據驗證的諺語列表"
)
async def get_verifiable():
    """取得可驗證的諺語"""
    proverbs = get_verifiable_proverbs()
    return ApiResponse(
        success=True,
        data=[_convert_proverb_to_response(p) for p in proverbs]
    )


@router.get(
    "/search",
    response_model=ApiResponse[list[ProverbResponse]],
    summary="搜尋諺語",
    description="在諺語原文、解釋、關鍵字中搜尋"
)
async def search(
    q: str = Query(..., min_length=1, description="搜尋關鍵字")
):
    """搜尋諺語"""
    proverbs = search_proverbs(q)
    return ApiResponse(
        success=True,
        data=[_convert_proverb_to_response(p) for p in proverbs]
    )


# ============================================
# 驗證 API Endpoints
# ============================================

@router.get(
    "/verify/{proverb_id}",
    response_model=ApiResponse[ProverbVerificationResponse],
    summary="驗證單一諺語",
    description="使用歷史數據驗證指定諺語的準確率"
)
async def verify_single(
    proverb_id: str = Path(..., description="諺語 ID"),
    station_id: Optional[str] = Query(None, description="站點 ID（可選）"),
    db: Session = Depends(get_db)
):
    """驗證單一諺語"""
    proverb = get_proverb_by_id(proverb_id)
    if not proverb:
        return ApiResponse(
            success=False,
            error=f"找不到諺語：{proverb_id}"
        )

    result = verify_proverb(db, proverb_id, station_id)
    if not result:
        return ApiResponse(
            success=False,
            error=f"此諺語無法驗證：{proverb_id}"
        )

    return ApiResponse(
        success=True,
        data=_convert_verification_to_response(result)
    )


@router.get(
    "/verify-all",
    response_model=ApiResponse[list[ProverbVerificationResponse]],
    summary="驗證所有諺語",
    description="使用歷史數據驗證所有可驗證的諺語"
)
async def verify_all(
    station_id: Optional[str] = Query(None, description="站點 ID（可選）"),
    db: Session = Depends(get_db)
):
    """驗證所有諺語"""
    results = verify_all_proverbs(db, station_id)
    return ApiResponse(
        success=True,
        data=[_convert_verification_to_response(r) for r in results]
    )


@router.get(
    "/stats",
    response_model=ApiResponse[ProverbStatsSummary],
    summary="取得諺語統計摘要",
    description="取得諺語驗證的統計摘要"
)
async def get_stats(
    station_id: Optional[str] = Query(None, description="站點 ID（可選）"),
    db: Session = Depends(get_db)
):
    """取得諺語統計摘要"""
    summary = get_proverb_stats_summary(db, station_id)
    return ApiResponse(
        success=True,
        data=ProverbStatsSummary(**summary)
    )
