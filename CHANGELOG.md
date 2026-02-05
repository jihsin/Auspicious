# 好日子 (Auspicious) 開發日誌

## [Unreleased]

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

### Phase 3: 進階功能（待開發）

- [ ] 週期性天氣查詢（選擇日期範圍）
- [ ] 歷史同期比較
- [ ] 天氣推薦最佳日期
- [ ] 更多站點資料擴展

### 部署

- [ ] 後端部署至 Cloud Run
- [ ] 前端部署至 Vercel
- [ ] 設定 CI/CD 流程
