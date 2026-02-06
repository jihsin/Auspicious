# 好日子 (Auspicious) 維護手冊

> 最後更新：2026-02-06

## 專案概述

「好日子」是一個結合 36 年歷史氣象數據與傳統曆法智慧的天氣分析應用。

### 技術架構

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   前端 (Vercel) │────▶│  後端 (Cloud Run)│────▶│   外部 API      │
│   Next.js 16    │     │   FastAPI       │     │   CWA / Gemini  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │  SQLite 資料庫   │
                        │  36年歷史資料    │
                        └─────────────────┘
```

---

## 部署資訊

### 前端 (Vercel)

| 項目 | 值 |
|------|-----|
| URL | https://auspicious-zeta.vercel.app |
| 平台 | Vercel |
| 框架 | Next.js 16 |
| 根目錄 | `frontend/` |
| 建置指令 | `pnpm build` |

**環境變數：**
```
NEXT_PUBLIC_API_URL=https://auspicious-api-331213739902.asia-east1.run.app
```

### 後端 (Google Cloud Run)

| 項目 | 值 |
|------|-----|
| URL | https://auspicious-api-331213739902.asia-east1.run.app |
| 專案 | ready-market-crm |
| 區域 | asia-east1 |
| 服務名稱 | auspicious-api |

**環境變數：**
```bash
CWA_API_KEY=CWA-1187BDB4-7163-43CE-8AF0-5F235A9ABBCB
GEMINI_API_KEY=AIzaSyAMtkU2oc-ceC1v7H9MCF_jQzRP76Ey27A
LINE_CHANNEL_ACCESS_TOKEN=ajmo4iZaBrv8VjvS9gARbffUoNWl7NoamRPq+TEPfZkG6DRhbo/1Zjhb25MV0FePJJ/7X5CC7qtkXhV4HUGv5GSVXP5jClLnR6XRqflxs5oS4qn5cSdmMf+2IbNWPOWPhMeZ/kzXFJK3dGv1CFk5RgdB04t89/1O/w1cDnyilFU=
LINE_USER_ID=Uce98fb15cb3c174281f2c8e973e4c039
```

### GitHub Repository

| 項目 | 值 |
|------|-----|
| URL | https://github.com/jihsin/Auspicious |
| 帳號 | jihsin |

---

## 外部服務與 API

### 1. CWA 中央氣象署 OpenData API

| 項目 | 值 |
|------|-----|
| 管理後台 | https://opendata.cwa.gov.tw/user/authkey |
| 帳號 | jihsin@gmail.com |
| 用途 | 即時天氣觀測資料 |
| API 文件 | https://opendata.cwa.gov.tw/dist/opendata-swagger.html |

**使用的資料集：**
| 代碼 | 名稱 | 用途 |
|------|------|------|
| O-A0003-001 | 自動氣象站觀測資料 | 即時天氣 |

**密鑰更新步驟：**
1. 登入 https://opendata.cwa.gov.tw/user/authkey
2. 點擊「取得授權碼」或「重新產生」
3. 複製新的 API Key
4. 更新 Cloud Run 環境變數（見下方部署指令）

### 2. Google Gemini AI

| 項目 | 值 |
|------|-----|
| 管理後台 | https://aistudio.google.com/apikey |
| 模型 | gemini-2.0-flash |
| 用途 | AI 智慧解讀生成 |

**密鑰更新步驟：**
1. 登入 https://aistudio.google.com/apikey
2. 建立或複製 API Key
3. 更新 Cloud Run 環境變數

### 3. LINE Messaging API

| 項目 | 值 |
|------|-----|
| 管理後台 | https://developers.line.biz/console/ |
| Channel ID | 2009062719 |
| Channel 名稱 | JihsinWang |
| 用途 | API 失效通知 |

**相關資訊：**
- Channel Secret: `ea75cb05929c699e5349c49d2e873af9`
- User ID: `Uce98fb15cb3c174281f2c8e973e4c039`

---

## 常用維護指令

### 部署後端

```bash
cd /Users/tomwang/Codes/Auspicious/backend

# 完整部署（含環境變數）
gcloud run deploy auspicious-api \
  --source . \
  --region asia-east1 \
  --allow-unauthenticated \
  --set-env-vars="CWA_API_KEY=<新密鑰>,GEMINI_API_KEY=<新密鑰>,LINE_CHANNEL_ACCESS_TOKEN=<TOKEN>,LINE_USER_ID=<USER_ID>"
```

### 部署前端

```bash
cd /Users/tomwang/Codes/Auspicious/frontend

# 方法 1：推送到 GitHub（Vercel 自動部署）
git push origin main

# 方法 2：Vercel CLI
vercel --prod
```

### 查看 Cloud Run 日誌

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=auspicious-api" --limit=50
```

### 查看目前環境變數

```bash
gcloud run services describe auspicious-api \
  --region=asia-east1 \
  --format="yaml(spec.template.spec.containers[0].env)"
```

### 更新單一環境變數

```bash
gcloud run services update auspicious-api \
  --region=asia-east1 \
  --update-env-vars="CWA_API_KEY=<新密鑰>"
```

---

## API 端點清單

### 天氣 API (`/api/v1/weather`)

| 端點 | 方法 | 說明 |
|------|------|------|
| `/daily/{station_id}/{month_day}` | GET | 指定日期歷史統計 |
| `/today/{station_id}` | GET | 今日歷史統計 |
| `/historical/{station_id}` | GET | 即時天氣 vs 歷史比較 |
| `/range/{station_id}` | GET | 日期範圍統計 |
| `/recommend/{station_id}` | GET | 最佳日期推薦 |
| `/compare` | GET | 多站點比較 |

### 站點 API (`/api/v1/stations`)

| 端點 | 方法 | 說明 |
|------|------|------|
| `/` | GET | 所有站點列表 |
| `/{station_id}` | GET | 單一站點資訊 |
| `/nearest` | GET | 最近站點（GPS） |

### 節氣 API (`/api/v1/solar-term`)

| 端點 | 方法 | 說明 |
|------|------|------|
| `/all` | GET | 24 節氣列表 |
| `/{term_name}` | GET | 單一節氣詳情 |
| `/current` | GET | 當前/最近節氣 |

### 諺語 API (`/api/v1/proverb`)

| 端點 | 方法 | 說明 |
|------|------|------|
| `/all` | GET | 所有諺語 |
| `/by-id/{id}` | GET | 單一諺語 |
| `/verify/{id}` | GET | 諺語驗證結果 |
| `/stats` | GET | 驗證統計 |

### 活動規劃 API (`/api/v1/planner`)

| 端點 | 方法 | 說明 |
|------|------|------|
| `/activity-types` | GET | 16 種活動類型 |
| `/plan` | GET | 完整規劃（指定日期） |
| `/quick-plan` | GET | 快速規劃（30天） |

### AI API (`/api/v1/ai`)

| 端點 | 方法 | 說明 |
|------|------|------|
| `/status` | GET | AI 服務狀態 |
| `/solar-term/{name}` | GET | 節氣 AI 解讀 |
| `/proverb/{id}` | GET | 諺語 AI 解讀 |
| `/activity-suggestion` | GET | 活動建議 |
| `/daily-insight` | GET | 每日洞察 |

---

## 通知系統

### 觸發條件

| 情況 | 通知內容 |
|------|---------|
| CWA API 返回 401 | API 密鑰失效警報 |
| Gemini API 配額用盡 | API 密鑰失效警報 |

### 冷卻機制

- 同類型通知間隔：1 小時
- 避免重複轟炸

### 測試通知

```bash
curl -X POST https://api.line.me/v2/bot/message/push \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <LINE_CHANNEL_ACCESS_TOKEN>' \
  -d '{
    "to": "<LINE_USER_ID>",
    "messages": [{"type": "text", "text": "測試訊息"}]
  }'
```

---

## 資料庫

### 位置

- 本地：`/Users/tomwang/Codes/Auspicious/data/auspicious.db`
- Cloud Run：打包在 Docker image 中

### 主要表格

| 表格 | 說明 | 記錄數 |
|------|------|--------|
| stations | 氣象站資訊 | ~700 |
| raw_observations | 原始觀測資料 | ~180 萬 |
| daily_statistics | 每日統計摘要 | ~5,000 |

### 資料範圍

- 年份：1991-2026（36 年）
- 站點：14 個主要站（有完整統計）

---

## 已知限制

1. **Gemini API 配額**：免費方案有每日限制，超過會返回 429
2. **CWA API 密鑰**：需定期更新（約 1 年有效）
3. **即時天氣**：僅支援有 CWA 資料的站點
4. **歷史資料**：僅有 14 個主要站有完整 36 年統計

---

## 故障排除

### 即時天氣顯示 null

1. 檢查 CWA API 密鑰是否有效
2. 檢查 Cloud Run 日誌
3. 手動測試 CWA API：
   ```bash
   curl "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001?Authorization=<API_KEY>&StationId=466920"
   ```

### AI 功能不可用

1. 檢查 Gemini API 配額
2. 檢查 `/api/v1/ai/status` 端點
3. 查看 Cloud Run 日誌中的錯誤

### 沒收到 LINE 通知

1. 確認已加 Bot 為好友
2. 檢查 LINE_CHANNEL_ACCESS_TOKEN 是否正確
3. 測試發送訊息（見上方測試指令）

---

## 版本歷史

| 版本 | 日期 | 重點功能 |
|------|------|---------|
| Phase 3.5 | 2026-02-06 | 前端頁面升級、LINE 通知 |
| Phase 3.4.1 | 2026-02-06 | 智慧活動規劃 API |
| Phase 3.3 | 2026-02-05 | AI 智慧引擎 (Gemini) |
| Phase 3.2 | 2026-02-05 | 節氣資料庫、諺語驗證 |
| Phase 3.1 | 2026-02-05 | 年代分層統計、氣候趨勢 |

---

## 聯絡資訊

- GitHub: https://github.com/jihsin/Auspicious
- Email: jihsin@gmail.com
