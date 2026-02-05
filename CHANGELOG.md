# 好日子 (Auspicious) 開發日誌

## [Unreleased]

### Phase 3: 進階功能開發 (2026-02-05 ~ 進行中)

#### 新增功能

**後端 (Backend)**
- 日期範圍查詢 API (`GET /api/v1/weather/range/{station_id}`)
  - 支援查詢指定日期範圍的歷史統計（最多 31 天）
  - 返回每日摘要與範圍統計
  - 自動計算最佳/最差日期
- 最佳日期推薦 API (`GET /api/v1/weather/recommend/{station_id}`)
  - 5 種偏好類型：sunny(晴天), mild(溫和), cool(涼爽), outdoor(戶外), wedding(婚禮)
  - 基於天氣統計計算推薦分數 (0-100)
  - 返回推薦理由與農曆資訊
- 多站點比較 API (`GET /api/v1/weather/compare`)
  - 支援 2-5 個站點同時比較
  - 依晴天率自動排名
  - 返回最佳站點推薦

**前端 (Frontend)**
- 日期推薦頁面 (`/recommend`)
  - 月份選擇、偏好類型選擇
  - `RecommendationCard` 組件展示推薦結果
- 多站點比較頁面 (`/compare`)
  - 日期選擇、多站點勾選 (2-5 個)
  - `ComparisonCard` 組件展示比較結果
  - 排名視覺化（金銀銅牌）
- 日期範圍分析頁面 (`/range`)
  - 日期範圍選擇器
  - 溫度趨勢折線圖
  - 降雨與晴天機率柱狀圖
  - 範圍統計摘要
- 天氣圖表組件 (`WeatherChart.tsx`)
  - `TemperatureChart`: 溫度趨勢折線圖
  - `PrecipChart`: 降雨與晴天機率柱狀圖
  - `TendencyPieChart`: 天氣傾向圓餅圖
  - `StationCompareChart`: 多站點比較柱狀圖
- `DateRangePicker` 日期範圍選擇器組件
- 首頁功能入口連結（3 個功能頁面）

---

### Phase 2: GPS 定位 + 多站點擴展 (2026-02-04 ~ 2026-02-05)

#### 新增功能

**後端 (Backend)**
- `Station` 資料模型，支援經緯度座標儲存
- CWA API 同步服務，可同步全台 835 個觀測站
- Haversine 距離計算工具 (`app/utils/geo.py`)
- 最近站點 API (`GET /api/v1/stations/nearest`)
- 農曆服務 (`app/services/lunar.py`)，基於 cnlunar 套件
- 農曆 API 端點 (`GET /api/v1/lunar/`)
- 天氣 API 整合農曆資訊（宜忌、節氣、干支）

**前端 (Frontend)**
- GPS 定位 Hook (`useGeolocation`)
- 站點選擇器組件 (`StationSelector`)
- 農曆卡片組件 (`LunarCard`)
- 首頁整合 GPS 自動定位功能

**資料處理 (Data Pipeline)**
- 批量處理腳本 (`batch_process.py`)
- 14 站點歷史統計資料（32-36 年）

#### 修復

- 修復 Weather API hardcoded 站點問題，改為動態查詢資料庫
- 修復 CWA 站點同步重複問題
- 處理高雄站點遷移問題（467441 → 467440）
- 修正臺南站名稱顯示問題

#### 站點覆蓋

| 地區 | 站點 |
|------|------|
| 北部 | 臺北、基隆、新竹 |
| 中部 | 臺中、嘉義、日月潭、阿里山、玉山 |
| 南部 | 臺南、高雄、恆春 |
| 東部 | 花蓮、臺東 |
| 離島 | 澎湖 |

#### 技術細節

- 資料來源：GitHub (Raingel/historical_weather) CWA CODIS 資料
- 統計方法：±3 天滑動窗口平滑，支援 366 天（含閏年 2/29）
- API 設計：RESTful，支援 GPS 定位查詢最近站點

---

### Phase 1: MVP 基礎建設 (2026-02-04)

#### 新增功能

- 後端 FastAPI 框架建立
- SQLAlchemy ORM 資料模型
- 歷史天氣統計 API
- 前端 Next.js 14 專案
- 天氣卡片組件
- 基礎 UI 設計

#### 資料模型

- `RawObservation`: 原始觀測資料
- `DailyStatistics`: 每日統計快照
- `Station`: 站點資訊

---

## 開發規範

### Git Commit 格式

```
<type>(<scope>): <subject>

feat: 新功能
fix: 修復 bug
docs: 文件
refactor: 重構
test: 測試
chore: 雜務
```

### 部署前檢查清單

- [ ] `git status` 確認所有變更已 commit
- [ ] `git log -3` 確認最近的 commit 正確
- [ ] 測試 API 端點正常
- [ ] 測試前端功能正常

---

## 後續規劃

### Phase 3: 進階功能

- [x] 日期範圍查詢 API
- [x] 最佳日期推薦 API
- [x] 多站點比較功能
- [x] 天氣圖表視覺化 (recharts)
- [ ] PWA 離線支援
- [ ] 更多站點資料擴展

### 部署

- [ ] 後端部署至 Cloud Run
- [ ] 前端部署至 Vercel
- [ ] 設定 CI/CD 流程
