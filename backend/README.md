# 好日子 App 後端服務

歷史氣象統計與節氣分析 API 服務，整合 AI 智慧天氣助手。

## 技術棧

- **Python 3.11+**
- **FastAPI** - Web 框架
- **SQLAlchemy** - ORM
- **Pandas/NumPy** - 數據處理
- **Google Gemini 2.0 Flash** - AI 引擎（Function Calling）
- **LINE Messaging API** - 聊天機器人
- **Cloud Run** - GCP 部署

## 功能特色

### AI 天氣助手
- 基於中央氣象署 **36 年歷史統計資料 (1991-2026)**
- 使用 Gemini Function Calling 確保數據來自資料庫，不會編造
- 支援多輪對話（10 分鐘記憶）
- LINE Bot 與 Web API 雙入口

### 支援的查詢類型
| 問題類型 | 範例 |
|---------|------|
| 即時天氣 | 「台北現在天氣」 |
| 未來預估 | 「10天後高雄天氣」 |
| 最熱日子 | 「台北全年最熱哪天」 |
| 最冷日子 | 「今年最冷是什麼時候」 |
| 最少雨日 | 「五月哪天最適合出遊」 |
| 月份比較 | 「7月和8月哪個比較熱」 |
| 溫度閾值 | 「哪些天超過33度」「低於10度的日子」 |
| 降雨機率 | 「2/7 會下雨嗎」 |

### 支援城市
台北市、新北市、基隆市、桃園市、新竹市、苗栗縣、台中市、彰化縣、南投縣、雲林縣、嘉義市、台南市、高雄市、屏東縣、宜蘭縣、花蓮縣、台東縣、澎湖縣

## 開發

```bash
# 安裝依賴
poetry install

# 啟動開發伺服器
poetry run uvicorn app.main:app --reload --port 8000

# 執行測試
poetry run pytest
```

## 環境變數

```bash
# 必要
DATABASE_URL=sqlite:///./data/weather.db
GEMINI_API_KEY=your_gemini_api_key

# LINE Bot（可選）
LINE_CHANNEL_ACCESS_TOKEN=your_line_token
LINE_CHANNEL_SECRET=your_line_secret
```

## API 端點

### 核心服務
| 端點 | 說明 |
|------|------|
| `GET /health` | 健康檢查 |
| `GET /api/v1/weather/daily/{station_id}/{date}` | 查詢每日天氣統計 |
| `GET /api/v1/stations` | 取得所有氣象站 |
| `GET /api/v1/lunar/{date}` | 農曆資訊 |
| `GET /api/v1/solar-term/current` | 當前節氣 |
| `GET /api/v1/proverb/today` | 今日諺語 |

### AI 智慧引擎
| 端點 | 說明 |
|------|------|
| `GET /api/v1/ai/status` | AI 服務狀態 |
| `POST /api/v1/ai/chat` | AI 天氣助手對話 |
| `GET /api/v1/ai/solar-term/{term}` | 節氣 AI 解讀 |
| `GET /api/v1/ai/proverb/{id}` | 諺語 AI 解讀 |
| `GET /api/v1/ai/activity-suggestion` | 活動建議 |
| `GET /api/v1/ai/daily-insight` | 每日洞察 |

### LINE Webhook
| 端點 | 說明 |
|------|------|
| `POST /api/v1/line/webhook` | LINE Bot 訊息接收 |

## 部署

### Cloud Run
```bash
gcloud run deploy auspicious-api \
  --source . \
  --region asia-east1 \
  --allow-unauthenticated
```

### 當前版本
- **Revision:** `auspicious-api-00039-jvp`
- **URL:** https://auspicious-api-331213739902.asia-east1.run.app

## 資料來源

- 中央氣象署開放資料平台
- 36 年歷史統計 (1991-2026)
- 每日自動同步更新

## 授權

MIT License
