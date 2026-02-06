# backend/app/main.py
"""FastAPI 應用程式入口"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.api.v1 import weather, stations, lunar, solar_term, proverb, ai, planner

app = FastAPI(
    title="好日子 API",
    description="歷史氣象統計與節氣分析 API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://auspicious-zeta.vercel.app",
        "https://auspicious-auspicious1.vercel.app",
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    """應用程式啟動時初始化資料庫"""
    init_db()


@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {"status": "ok", "version": "0.1.0"}


# 註冊 API 路由
app.include_router(
    weather.router,
    prefix="/api/v1/weather",
    tags=["weather"]
)
app.include_router(
    stations.router,
    prefix="/api/v1/stations",
    tags=["stations"]
)
app.include_router(
    lunar.router,
    prefix="/api/v1/lunar",
    tags=["lunar"]
)
app.include_router(
    solar_term.router,
    prefix="/api/v1/solar-term",
    tags=["solar-term"]
)
app.include_router(
    proverb.router,
    prefix="/api/v1/proverb",
    tags=["proverb"]
)
app.include_router(
    ai.router,
    prefix="/api/v1/ai",
    tags=["ai"]
)
app.include_router(
    planner.router,
    prefix="/api/v1/planner",
    tags=["planner"]
)
