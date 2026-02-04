# backend/app/schemas/lunar.py
"""農曆 API Schema"""

from typing import Optional, List
from pydantic import BaseModel, Field


class LunarDateInfo(BaseModel):
    """農曆日期資訊"""
    year: int = Field(..., description="農曆年")
    month: int = Field(..., description="農曆月")
    day: int = Field(..., description="農曆日")
    year_cn: str = Field(..., description="農曆年中文")
    month_cn: str = Field(..., description="農曆月中文")
    day_cn: str = Field(..., description="農曆日中文")
    干支年: str = Field(..., description="年干支", alias="ganzhi_year")
    干支月: str = Field(..., description="月干支", alias="ganzhi_month")
    干支日: str = Field(..., description="日干支", alias="ganzhi_day")
    生肖: str = Field(..., description="生肖", alias="zodiac")
    is_leap: bool = Field(..., description="是否閏月")

    class Config:
        populate_by_name = True


class YiJiInfo(BaseModel):
    """宜忌資訊"""
    yi: List[str] = Field(default_factory=list, description="宜")
    ji: List[str] = Field(default_factory=list, description="忌")


class GanzhiInfo(BaseModel):
    """干支資訊"""
    年柱: str = Field(..., description="年柱", alias="year_pillar")
    月柱: str = Field(..., description="月柱", alias="month_pillar")
    日柱: str = Field(..., description="日柱", alias="day_pillar")

    class Config:
        populate_by_name = True


class LunarResponse(BaseModel):
    """農曆完整回應"""
    date: str = Field(..., description="公曆日期 (YYYY-MM-DD)")
    lunar_date: LunarDateInfo = Field(..., description="農曆日期資訊")
    yi_ji: YiJiInfo = Field(..., description="宜忌資訊")
    jieqi: Optional[str] = Field(None, description="當日節氣（如有）")
    ganzhi: GanzhiInfo = Field(..., description="干支資訊")

    class Config:
        json_schema_extra = {
            "example": {
                "date": "2026-02-04",
                "lunar_date": {
                    "year": 2025,
                    "month": 12,
                    "day": 17,
                    "year_cn": "二零二五年",
                    "month_cn": "十二月",
                    "day_cn": "十七",
                    "干支年": "乙巳",
                    "干支月": "己丑",
                    "干支日": "甲子",
                    "生肖": "蛇",
                    "is_leap": False
                },
                "yi_ji": {
                    "yi": ["祭祀", "祈福", "求嗣"],
                    "ji": ["動土", "破土", "安葬"]
                },
                "jieqi": "立春",
                "ganzhi": {
                    "年柱": "乙巳",
                    "月柱": "己丑",
                    "日柱": "甲子"
                }
            }
        }
