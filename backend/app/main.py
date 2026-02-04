"""FastAPI 應用程式入口"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="好日子 API",
    description="歷史氣象統計與節氣分析 API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {"status": "ok", "version": "0.1.0"}
