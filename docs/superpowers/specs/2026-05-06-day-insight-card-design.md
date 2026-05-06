# DayInsightCard：差異化日資訊卡片設計

**日期**：2026-05-06
**狀態**：設計已批准，待寫實作計畫
**作者**：Tom Wang + Claude

---

## 1. 背景與問題

「好日子」app 的核心使用情境是婚禮選日 / 活動規劃，使用者會查詢未來日期的歷史氣象。

目前的展示問題：

- 主視覺顯示「降雨機率 44%」這類絕對數字
- 北部站點（特別是台北）全年降雨機率本來就在 40-50% 之間
- 使用者打開查不同日子，看到的數字幾乎都是 50% 上下，**完全無法判斷「這天到底特別不特別」**

調查時亦發現一個獨立 bug：`data-pipeline/load.py` 的 NaN 聚合導致 1997 年 243 天「假 0mm」。已單獨修復（見 commit 待提交）。但修完後分布幾乎不變 — 證明扁平問題的根因是**展示層缺乏差異化指標**，不是資料層 bug。

## 2. 目標

把「這天到底特別不特別」做成一眼可見的視覺資訊，讓使用者在 planner / compare / weather 任何頁面都能快速判讀某日的氣候特性與相對位置。

## 3. 非目標（NON-GOALS）

階段一**不做**以下事項，避免 scope creep：

- 「今日實時氣象 vs 歷史」對比（即實時觀測值疊加在卡片上）— 留待階段二
- 起卦 / 易經卦象視覺化 — 獨立功能，留待差異化指標完成後再處理
- 預報資料整合（CWA forecast）— 階段二
- 規則標籤的完整定稿 — 草稿即可，實作時可調

## 4. 設計決策摘要

| 維度 | 決策 |
|---|---|
| 卡片位置 | 並列在現有 WeatherCard / SolarTermCard 旁邊 |
| 元件 | 新增獨立 `DayInsightCard.tsx`，不融入既有 WeatherCard |
| 結構 | 三層（標籤 / 核心數字+異常度 / 雙極值錨點）+ 點擊展開 AI 詮釋 |
| 標籤產生 | 規則式查表（~20 個標籤） |
| 異常度基準 | 雙基準（vs 年平均、vs 同月平均） |
| 多維度處理 | 主：降雨機率；副：其他維度若 |Z| ≥ 1 顯示 badge |
| 歷史錨點 | 雙極值（最濕年/mm + 最乾年/mm） |
| AI 詮釋 | 點擊展開時 lazy load 呼叫 Gemini |
| 適用情境 | 階段一：純歷史統計版（planner / compare / weather 共用同一張卡） |

## 5. UI 設計

### 卡片版面

```
┌─────────────────────────────────────────┐
│ 🌧️ 典型梅雨日                              │ ← 頂部：規則標籤（可能為空）
├─────────────────────────────────────────┤
│ 降雨機率                                    │
│   52%                                       │ ← 中段：核心數字（大字）
│   ↑+8% vs 年均  │  +2% vs 同月              │ ← 雙基準異常度
│                                             │
│ ⚠️ 氣溫比同月偏低 -2°C                      │ ← 副 badge（其他維度若異常）
├─────────────────────────────────────────┤
│ 最濕：2009 / 85 mm                          │
│ 最乾：2002 / 0 mm                           │ ← 底部：雙極值錨點
├─────────────────────────────────────────┤
│ [點擊看詳細詮釋 ▾]                         │ ← 展開：AI 個性化敘事
└─────────────────────────────────────────┘
```

### 視覺規則

- 標籤色彩按類型分組：季節典型（綠）/ 異常（橙）/ 紀錄級（紅）/ 節氣（藍）
- 異常度上箭頭紅、下箭頭藍，0 ±1% 不顯示箭頭
- 副 badge 僅在 |Z| ≥ 1 時出現，避免噪音
- 「無標籤」時頂部留空（不放 placeholder 文字），中段直接上移

## 6. 後端設計

### 6.1 新 endpoint

```
GET /api/v1/day-insight/{station_id}/{month}/{day}
```

回應 schema：

```typescript
{
  station_id: string,
  month: number,        // 1-12
  day: number,          // 1-31
  label: {
    text: string | null,  // "典型梅雨日"，無匹配為 null
    category: "seasonal" | "anomaly" | "record" | "solar_term" | null,
  },
  core: {
    metric: "precip_probability",
    value: number,                   // 0.52
    anomaly_year: number,            // +0.08 (vs 年均)
    anomaly_month: number,           // +0.02 (vs 同月均)
  },
  side_badges: Array<{
    metric: "temp_avg" | "humidity_avg",
    label: string,                   // "氣溫比同月偏低 -2°C"
    direction: "above" | "below",
    z_score: number,                 // 用於前端排序
  }>,
  extremes: {
    wettest: { year: number, value: number },
    driest:  { year: number, value: number },
  },
  meta: {
    years_analyzed: number,
    start_year: number,
    end_year: number,
  }
}
```

### 6.2 計算邏輯

```python
# Pseudo-code

def get_day_insight(station_id, month, day):
    # 1. 取該站該日的統計
    day_stat = db.query(DailyStatistics).filter_by(
        station_id=station_id, month_day=f"{month:02d}-{day:02d}"
    ).first()

    # 2. 計算年平均、同月平均（針對該站）
    year_mean_precip = db.query(AVG(DailyStatistics.precip_probability)) \
                          .filter_by(station_id=station_id).scalar()
    month_mean_precip = db.query(AVG(DailyStatistics.precip_probability)) \
                           .filter_by(station_id=station_id) \
                           .filter(DailyStatistics.month_day.like(f"{month:02d}-%")) \
                           .scalar()

    # 3. 異常度
    anomaly_year  = day_stat.precip_probability - year_mean_precip
    anomaly_month = day_stat.precip_probability - month_mean_precip

    # 4. 雙極值（反查 raw_observations）
    extremes = compute_extremes(station_id, month, day)

    # 5. 多維度副 badge（temp / humidity）
    side_badges = compute_side_badges(station_id, day_stat, month)

    # 6. 規則標籤
    label = match_label(day_stat, anomaly_year, anomaly_month, side_badges, month, day)

    return DayInsight(...)
```

### 6.3 雙極值反查

`daily_statistics` 沒有「最濕年份」這欄，需從 `raw_observations` 取。為避免每次查詢掃整年資料，可考慮：

- **方案 a（先做）**：直接查（站點 X × 月日 Y 約 36 筆，cost 低）
- **方案 b（如有效能問題）**：在 `daily_statistics` 加 `wettest_year`, `wettest_value`, `driest_year`, `driest_value` 欄位，由 `compute_snapshots.py` 順便計算

階段一採方案 a。若量級擴大再 migrate。

### 6.4 規則標籤庫

存放位置：`backend/app/services/day_label_rules.py`

草稿（實作時可調）：

| 類型 | 觸發條件 | 標籤 |
|---|---|---|
| 季節典型 | month 5-6 + precip_probability ≥ 0.50 | 典型梅雨日 |
|  | month 7-8 + precip_probability ≥ 0.45 + temp_z ≥ +1 | 盛夏雷雨日 |
|  | month in (12,1,2) + temp_z ≤ -1 | 冬季冷氣團 |
|  | month in (9,10) + precip_z ≤ -1 | 秋高氣爽 |
|  | month in (10,11) + 北部站（466900/466920/466940/466910/466930） | 東北季風前緣 |
| 異常 | anomaly_month ≥ +0.15 | 異常多雨期 |
|  | anomaly_month ≤ -0.15 | 異常乾旱期 |
|  | temp_z ≥ +1.5 | 異常高溫 |
|  | temp_z ≤ -1.5 | 寒流警報 |
| 紀錄級 | precip_probability 在同月 366 天中前 5% | 紀錄級多雨 |
|  | temp_avg_mean 在同月中前 5% | 紀錄級高溫 |
| 節氣相關 | 該日為 24 節氣轉換日（查 solar_term 服務） | 節氣轉換點 |
| 預設 | 無匹配 | null |

優先順序：紀錄級 > 異常 > 節氣轉換點 > 季節典型。任一規則命中即返回，不疊加。

### 6.5 多維度副 badge 邏輯

```python
def compute_side_badges(station_id, day_stat, month):
    badges = []

    # 溫度
    month_temps = ... # 該站當月所有 day 的 temp_avg_mean
    temp_mean   = mean(month_temps)
    temp_stddev = stddev(month_temps)

    if temp_stddev > 0:
        z = (day_stat.temp_avg_mean - temp_mean) / temp_stddev
        if abs(z) >= 1.0:  # 門檻：±1 標準差
            direction = "above" if z > 0 else "below"
            delta = day_stat.temp_avg_mean - temp_mean
            badges.append({
                "metric": "temp_avg",
                "label": f"氣溫比同月{'偏高' if z > 0 else '偏低'} {delta:+.1f}°C",
                "direction": direction,
                "z_score": z,
            })

    # 濕度（類似邏輯）
    ...

    # 排序：|z_score| 大的排前面，最多 2 個
    badges.sort(key=lambda b: -abs(b["z_score"]))
    return badges[:2]
```

### 6.6 AI 詮釋（lazy load）

獨立 endpoint：

```
GET /api/v1/day-insight/{station_id}/{month}/{day}/interpretation
```

呼叫既有 `ai_engine.py` 的新 method `generate_day_interpretation()`，傳入 day_insight payload，prompt 模板包含：
- 該日所有指標
- 標籤、異常度、極值
- 節氣資訊（呼叫 solar_term service）
- （可選）保留「起卦」精神：請 Gemini 用易經/節氣語境寫一段詮釋

回應使用 Gemini 既有快取機制（如已實作）；若無，加 in-memory LRU（key = station_id + month-day，TTL 7 天）避免重複呼叫。

## 7. 前端設計

### 7.1 元件結構

```
frontend/src/components/DayInsightCard.tsx        # 主元件
frontend/src/components/DayInsightCard/
  ├── LabelBadge.tsx                              # 頂部標籤
  ├── CoreMetric.tsx                              # 中段核心數字
  ├── SideBadges.tsx                              # 多維度副 badge
  ├── ExtremesAnchor.tsx                          # 底部雙極值
  └── InterpretationDrawer.tsx                    # 點擊展開的 AI 詮釋
```

### 7.2 整合位置

| 頁面 | 整合方式 |
|---|---|
| `/planner` | 候選日期列表中每日掛一張 |
| `/compare` | 每候選站點各一張 |
| `/range` (現有) | 區間查詢結果中每日一張 |
| 首頁 | 與 WeatherCard / SolarTermCard 並列 |

### 7.3 API client

擴充 `frontend/src/lib/api.ts`：

```typescript
export const fetchDayInsight = (
  stationId: string, month: number, day: number
): Promise<DayInsight> => ...

export const fetchDayInterpretation = (
  stationId: string, month: number, day: number
): Promise<string> => ...
```

## 8. 資料流

```
使用者開啟頁面（如 /planner）
    ↓
前端針對每候選日期呼叫 GET /day-insight/{station}/{month}/{day}
    ↓
後端：
  1. 查 daily_statistics 該日資料
  2. 算年/月平均（可在 process 內 cache）
  3. 算雙極值（查 raw_observations）
  4. 算副 badge（z_score）
  5. 套規則標籤
  6. 回傳完整 payload
    ↓
前端渲染 DayInsightCard（不含 AI 詮釋）
    ↓
使用者點「看詳細詮釋」 → lazy fetch interpretation endpoint
    ↓
後端呼叫 Gemini，回傳一段文字
```

## 9. 邊界與錯誤處理

| 情境 | 處理 |
|---|---|
| `daily_statistics` 該日無資料 | 回傳 404；前端顯示「該站該日無歷史資料」 |
| `precip_probability` 為 NULL（資料缺失） | 異常度不計算；core 顯示「資料不足」 |
| 月平均/年平均計算失敗 | 該值返回 null；前端對應欄位不顯示 |
| 雙極值 raw_observations 全為 NULL | extremes 返回 null；底部那行不顯示 |
| AI 詮釋 timeout / 配額耗盡 | 前端 fallback：「詮釋暫時無法產生，請稍後再試」 |
| 站點 ID 不存在 | 400 |

## 10. 測試策略

- **後端**：
  - `test_day_label_rules.py`：規則表逐條 unit test
  - `test_day_insight_api.py`：API 整合測試（用 fixture 站點 466920）
  - 邊界 case：閏年 2/29、跨月、有 NULL 的日子
- **前端**：
  - `DayInsightCard.test.tsx`：snapshot + 互動（點擊展開）
  - 視覺 regression：在 Storybook 加入幾組典型 day_insight payload

## 11. 實作階段

| Phase | 內容 |
|---|---|
| **P1** | 後端 endpoint + 規則表（不含 AI） |
| **P2** | 前端元件 + 整合到 /planner |
| **P3** | AI 詮釋 endpoint + 點擊展開 |
| **P4** | 整合其他頁面（/compare, /range, 首頁） |
| **P5（選做）** | 實時氣象對比層（NON-GOAL 移除狀態） |

## 12. 開放問題（可在實作期間決定）

1. AI 詮釋的 prompt 風格 — 是否保留「起卦」精神（用易經語境）？
2. 規則標籤是否需要支援 i18n（中/英）？階段一只做繁中。
3. 雙極值「最乾」當很多年都是 0mm 時如何選代表年份？
   - 提案：`MIN(precipitation), tiebreak by year DESC`（取最近一次完全乾旱的年份）

---

## 附錄 A：與起卦功能的關係

起卦功能（先前討論的「上卦=今日 / 下卦=歷史」反差設計）獨立成另一個設計階段。本卡片完成後，可考慮：

- 將起卦結果作為第四層加在 DayInsightCard 中（或獨立卡片）
- AI 詮釋 prompt 可預留「卦象」語境，讓詮釋本身帶古典美學

但這些都是後續迭代，不在本 spec scope 內。

## 附錄 B：相關 bug 修復

本設計獨立於下列 bug 修復，可分頭進行：

- `data-pipeline/load.py` NaN 聚合 bug 修復（已完成，待 commit）
- `data-pipeline/rerun_after_fix.py` 重跑工具（已完成，待 commit）
