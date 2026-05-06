# backend/app/schemas/common.py
"""Shared Pydantic schema primitives reused across multiple schema modules."""

from pydantic import BaseModel, Field


class ExtremeRecord(BaseModel):
    """極值紀錄（含年份）— used by both weather and day_insight schemas."""

    value: float = Field(..., description="極值數值")
    year: int = Field(..., description="發生年份")
