# 好日子 (Auspicious) -- 專案指南

## 概述

「好日子」是一款歷史氣象統計與節氣分析應用，幫助使用者根據歷史天氣數據、農曆節氣、
諺語驗證等資訊來挑選適合的日期（如婚禮、活動規劃）。
採用前後端分離架構，搭配資料管線進行氣象數據的擷取與統計。

## 技術棧

- **後端**: Python 3.11 / FastAPI / SQLAlchemy / SQLite / Poetry
- **前端**: Next.js 16 / React 19 / TypeScript / Tailwind CSS 4 / Zustand / pnpm
- **AI 整合**: Google Gemini (google-genai) / Vertex AI
- **部署**: Docker Compose / Google Cloud Build / Vercel (前端)
- **通知**: LINE Webhook

## 專案結構

```
├── backend/                 # FastAPI 後端服務
│   ├── app/
│   │   ├── main.py          # 應用程式入口，路由註冊
│   │   ├── api/v1/          # REST API 端點（weather, lunar, ai, planner 等）
│   │   ├── services/        # 業務邏輯（ai_engine, cwa_sync, planner 等）
│   │   ├── models/          # SQLAlchemy ORM 模型
│   │   ├── schemas/         # Pydantic 資料驗證
│   │   ├── config.py        # 環境變數與設定
│   │   └── database.py      # 資料庫初始化
│   ├── tests/               # 後端測試
│   └── pyproject.toml       # Python 依賴管理
├── frontend/                # Next.js 前端
│   ├── src/app/             # App Router 頁面（chat, compare, planner 等）
│   ├── src/components/      # 共用元件
│   ├── src/hooks/           # 自訂 Hooks
│   └── package.json         # Node 依賴管理
├── data-pipeline/           # 資料管線腳本
│   ├── fetch_github.py      # 從 GitHub 擷取原始資料
│   ├── load.py              # 載入資料至資料庫
│   ├── compute_snapshots.py # 計算統計快照
│   └── batch_process.py     # 批次處理
├── docker-compose.yml       # 本地開發環境
├── docker-compose.prod.yml  # 正式環境
└── scripts/deploy-backend.sh
```

## 關鍵檔案

| 檔案 | 用途 |
|------|------|
| `backend/app/main.py` | FastAPI 入口，所有路由註冊於此 |
| `backend/app/services/ai_engine.py` | Gemini AI 整合核心邏輯 |
| `backend/app/services/planner.py` | 活動日期規劃引擎 |
| `frontend/src/app/page.tsx` | 前端首頁入口 |
| `docker-compose.yml` | 本地開發環境定義 |

## 開發指令

### 後端
```bash
cd backend
poetry install                          # 安裝依賴
poetry run uvicorn app.main:app --reload # 啟動開發伺服器 (port 8000)
poetry run pytest                        # 執行測試
poetry run ruff check .                  # Lint 檢查
```

### 前端
```bash
cd frontend
pnpm install          # 安裝依賴
pnpm dev              # 啟動開發伺服器 (port 3000)
pnpm build            # 正式建置
pnpm lint             # ESLint 檢查
```

### Docker
```bash
docker compose up     # 啟動完整本地環境（後端 + 前端）
```

## API 路由總覽

所有 API 前綴為 `/api/v1/`：
`weather` | `stations` | `lunar` | `solar-term` | `proverb` | `ai` | `planner` | `daily-report` | `line`

## 注意事項

- 後端使用 SQLite，資料庫檔案位於 `data/` 目錄，請勿將 `.db` 檔案提交至版控
- Ruff lint 規則：line-length=100，target Python 3.11
- 前端環境變數 `NEXT_PUBLIC_API_URL` 指向後端位址
- AI 功能依賴 Google Cloud 憑證，本地開發需設定相關環境變數
- 修改 API 路由後，確認 `main.py` 中的 `include_router` 已更新
- 資料管線腳本為獨立執行，不屬於 FastAPI 應用程式的一部分
