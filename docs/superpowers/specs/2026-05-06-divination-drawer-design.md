# Divination Drawer：DayInsightCard 中的易經詮釋抽屜

**日期**：2026-05-06
**狀態**：設計已批准，待寫實作計畫
**作者**：Tom Wang + Claude
**前置**：[2026-05-06-day-insight-card-design.md](./2026-05-06-day-insight-card-design.md) 必須先完成

---

## 1. 背景

DayInsightCard spec 在 §附錄 A 預留了起卦整合點。本 spec 把該整合點具體化：使用易經卦象作為 DayInsightCard 「點擊看詳細詮釋」抽屜的展開內容，提供具備古典美學的差異化詮釋層。

直接受兩件事啟發：
- 使用者一句話：「用當天天氣資訊起卦」
- pi-mono `271c9e3` commit 的 `iching_divination.py`：提供完整 64 卦查表 + 四法計算（本/錯/綜/互/之），MIT License

## 2. 目標

- 為 DayInsightCard 的差異化指標提供詩意的詮釋層
- 透過卦象結構自然編碼「該日 vs 該月 vs 全年」的氣候差異
- 把 pi-mono 的隨機三錢法改造為決定性的氣象映射，讓「同一天起出同一卦」的可重現性
- 利用四法（錯卦/綜卦/互卦/之卦）擴充詮釋深度

## 3. 非目標

- 不做隨機三錢法（每次重整一定不同）— 我們要決定性結果
- 不做變爻爻辭逐爻詳解（先做卦辭層即可）
- 不取代 DayInsightCard 主視覺；只擴充其抽屜
- 不獨立成 `/divination` 頁面

## 4. 設計決策摘要

| 維度 | 決策 |
|---|---|
| 整合方式 | DayInsightCard 「看詳細詮釋」抽屜內容 |
| 6 爻來源 | 上卦=該日 vs 該月、下卦=該月 vs 年均 |
| Trigram 三維度 | [溫差, 濕差, 雨差]，>0=陽 ≤0=陰 |
| 變爻門檻 | \|z_score\| ≥ 1（與 DayInsightCard side badges 同步） |
| 四法顯示 | 本卦+之卦顯眼，錯/綜/互 一行小字速覽 |
| AI 詮釋 | 三層敘事（氣候畫像 / 特殊度 / 想像層），規則查卦名+卦辭、AI 寫敘事 |
| 演算法來源 | pi-mono `iching_divination.py`（MIT），保留 attribution |

## 5. 6 爻生成邏輯

### 5.1 結構

```
上卦 = 該日 vs 該月平均（特異度）
  第 6 爻：日雨機率 vs 月均雨機率   （>0=陽，z≥1=變）
  第 5 爻：日均濕度 vs 月均濕度
  第 4 爻：日均溫   vs 月均溫

下卦 = 該月 vs 年均（季節背景）
  第 3 爻：月均雨機率 vs 年均
  第 2 爻：月均濕度   vs 年均
  第 1 爻：月均溫     vs 年均
```

「上卦下卦相同 → 重卦/近似卦 → 典型日」、「上下卦差異大 → 混合卦 → 特殊日」自然編碼差異化。

### 5.2 爻值對照（呼應三錢法 6/7/8/9 系統）

```python
# 偏離方向 + 強度 → 爻值
def line_value(deviation: float, z_score: float) -> int:
    yang = deviation > 0
    changing = abs(z_score) >= 1.0
    if yang and changing:    return 9   # 老陽
    if yang and not changing: return 7  # 少陽
    if not yang and changing: return 6  # 老陰
    return 8                            # 少陰
```

### 5.3 為何選 [溫, 濕, 雨] 三維

- 對應傳統八卦中最典型的氣象意象（離=火/熱、坎=水/雨、巽=風/溼/呼吸）
- 三維 8 種組合剛好填滿 trigram 空間（2^3 = 8）
- 是 daily_statistics 中最完整、最少 NULL 的三個欄位

未來可考慮加入日照/風為第二組 trigram（變成 12 爻多卦系統），但屬 NON-GOAL。

## 6. 四法計算

完全採用 pi-mono `iching_divination.py:271c9e3` 的演算法（MIT License）。

| 卦 | 公式 | Auspicious 語義 |
|---|---|---|
| 本卦 | `TABLE[lower][upper]` | **氣候畫像**（這天的氣候本相） |
| 之卦 | 變爻取反後重算 | **趨勢**（異常維度回歸常態後的卦） |
| 錯卦 | `lower XOR 7`, `upper XOR 7` | **想像對立**（反季節想像） |
| 綜卦 | 六爻倒序 | **季節對位**（半年後的卦） |
| 互卦 | `lines[1:4]` 為下、`lines[2:5]` 為上 | **內在核心**（不變的氣候本質） |

> 註：「綜卦＝半年後」是 Auspicious 的延伸詮釋；傳統易經並無此對應，但因綜卦的「視角倒轉」性質與「半年/半轉日」概念相通，作為敘事輔助。AI prompt 中應註明這是「氣象延伸詮釋」而非傳統爻辭。

## 7. 卦象資料庫

### 7.1 資料

`backend/app/data/hexagrams.py`（或 JSON）：

```python
HEXAGRAMS = [
    {"num": 1,  "name": "乾為天", "judgement": "元亨利貞", "image_meaning": "天行健，君子以自強不息"},
    {"num": 2,  "name": "坤為地", "judgement": "元亨利牝馬之貞", "image_meaning": "地勢坤，君子以厚德載物"},
    # ...
    {"num": 64, "name": "火水未濟", "judgement": "亨小狐汔濟", "image_meaning": "火在水上，未濟；君子以慎辨物居方"},
]
```

每筆 ~30-50 字，全 64 卦 ~3000 字，一次性人工編寫（可參考公版易經如朱熹《周易本義》、王弼注）或委由 AI 初稿後人工校稿。

### 7.2 八卦名與符號（直接從 pi-mono 複製）

```python
TRIGRAM_NAMES   = ["坤","艮","坎","巽","震","離","兌","乾"]
TRIGRAM_SYMBOLS = ["☷","☶","☵","☴","☳","☲","☱","☰"]
TRIGRAM_NATURE  = ["地","山","水","風","雷","火","澤","天"]
```

### 7.3 64 卦 TABLE

從 pi-mono `iching_divination.py:84-95` 直接複製。檔案頂部加註：

```python
# 64-卦對應表來源：moregatest/pi-mono iching_divination.py @ 271c9e3 (MIT License)
# 8x8 二維查表確保 64 卦完整無重複（pi-mono 已驗證 _validate_table()）
```

## 8. AI 詮釋設計

### 8.1 三層敘事結構

prompt 模板（送 Gemini）：

```
你是「好日子」app 的氣象詮釋師。請依下列卦象結果，用三段式繁體中文寫一份氣候洞察。

【日期】{station_name} {month}/{day}（節氣：{solar_term}）
【本卦】{ben_num}-{ben_name}（{upper_name}上 {lower_name}下）
【互卦】{hu_num}-{hu_name}
【之卦】{zhi_num}-{zhi_name}（變爻：{changing_positions}）
【錯卦】{cuo_num}-{cuo_name}
【綜卦】{zong_num}-{zong_name}
【氣候資料】溫差={t_anom}°C 濕差={h_anom}% 雨機率差={p_anom}%

請寫成三段，每段 30-50 字：
段一【氣候畫像】合論本卦+互卦，描寫這天的氣候本相
段二【特殊度】從變爻和之卦切入，描述異常維度與可能轉變
段三【想像層】用錯卦和綜卦延伸，給出反季節對立或半年後的對位想像

風格：古典文學語感、可入詩，但不要硬塞卦辭原文。
```

### 8.2 規則層（不靠 AI）

下列資料 100% 從查表/計算取得，不依賴 AI：

- 5 卦各自的卦號 + 卦名 + 八卦組合（顯示用）
- 卦辭（從 HEXAGRAMS 表取，可選顯示）
- 變爻位置 + 爻值
- 該日氣象差異數值

AI 只負責「三段敘事」這層創作。即使 AI 失敗，使用者仍可看到完整的卦象結構與卦辭。

### 8.3 Cache 策略

- key = `{station_id}-{month:02d}-{day:02d}`
- TTL = 7 天（卦象本身決定性，但 AI 可能微調 prompt 後重生）
- 後端用 in-memory LRU（單實例 Cloud Run 即可，跨 revision 重生 cost OK）

## 9. UI 設計

### 9.1 抽屜結構

```
┌─────────────────────────────────────────────────────┐
│ DayInsightCard 主視覺（標籤/數字/極值）                │
│ ─────────────────────────────                       │
│ [點擊看詳細詮釋 ▾]                                   │
└─────────────────────────────────────────────────────┘
       ↓ 點擊展開後
┌─────────────────────────────────────────────────────┐
│ 【本卦】☲離上 ☷坤下　火地晉                          │
│   ───── ★ (老陽 第六爻為變爻：日雨機率異常)         │
│   ─────                                             │
│   ─────                                             │
│   -- -                                              │
│   -- -                                              │
│   -- -                                              │
│   卦辭：晉，康侯用錫馬蕃庶                           │
│                                                       │
│ 【之卦】☵坎上 ☷坤下　水地比                          │
│   （日雨機率回歸常態後的趨勢）                       │
│                                                       │
│ ─────────────────────────────                        │
│ 四法速覽                                              │
│ 錯：水天需 ｜ 綜：山地剝 ｜ 互：水山蹇                │
│ （點各卦展開詳細）                                    │
│                                                       │
│ ─────────────────────────────                        │
│ AI 詮釋（Gemini 三層敘事，~120 字）：                 │
│ 段一：火地晉，明出地上...                             │
│ 段二：第六爻動，水地比之變...                         │
│ 段三：錯卦水天需，倒看半年...                         │
└─────────────────────────────────────────────────────┘
```

### 9.2 元件結構

```
frontend/src/components/DayInsightCard/
  ├── InterpretationDrawer.tsx        # 抽屜容器
  └── divination/
      ├── HexagramDisplay.tsx         # 卦象 + 6 爻線繪製
      ├── FourMethodsSummary.tsx      # 錯/綜/互 一行速覽
      └── NarrativeSection.tsx        # 三層敘事 prose
```

### 9.3 爻線視覺

採用 pi-mono 的 ASCII 風格在 web 中以 monospace 字體呈現：

- 少陽：`─────`
- 老陽：`──★──`（金黃色或用「★」變爻 marker）
- 少陰：`── ──`
- 老陰：`──×──`（變爻 marker）

或用 SVG 繪製更精緻；先 ASCII，視效果迭代。

## 10. 後端 API 變更

擴充 DayInsightCard spec 已定義的 interpretation endpoint：

```
GET /api/v1/day-insight/{station_id}/{month}/{day}/interpretation
```

回應 schema 擴充（在 DayInsightCard spec §6.1 schema 基礎上加）：

```typescript
{
  // ... DayInsightCard interpretation 既有欄位
  divination: {
    ben:  { num, name, upper_trigram, lower_trigram, lines: [...], judgement },
    zhi:  { num, name, upper_trigram, lower_trigram, judgement, changing_positions },
    cuo:  { num, name, judgement },
    zong: { num, name, judgement },
    hu:   { num, name, judgement },
    narrative: {
      climate_portrait: string,   // 段一：氣候畫像（本+互）
      anomaly_layer:    string,   // 段二：特殊度（變爻+之卦）
      imagination:      string,   // 段三：想像層（錯+綜）
    }
  }
}
```

### 10.1 模組結構

```
backend/app/services/divination/
  ├── __init__.py
  ├── hexagram_table.py    # TABLE + TRIGRAM 常數（pi-mono 致謝）
  ├── hexagrams.py          # 64 卦資料（卦名+卦辭+大象傳）
  ├── line_mapping.py       # 氣象 → 爻值（5.2 邏輯）
  ├── four_methods.py       # 錯/綜/互/之計算
  └── narrator.py           # AI 三層敘事 prompt + Gemini 呼叫
```

`narrator.py` 重用既有 `app/services/ai_engine.py` 的 client，避免重新建立 Gemini 連線。

## 11. 邊界與錯誤處理

| 情境 | 處理 |
|---|---|
| 該日某維度資料 NULL | 該爻 fallback 為「少陰」（陰、不變），narrative 中註明資料缺失 |
| 6 爻全靜（無變爻） | 之卦 = 本卦，UI 顯示「六爻皆靜」並提示「典型氣候日」 |
| AI 三層敘事失敗 | 顯示卦象結構 + 卦辭，narrative 區塊顯示「詮釋暫時無法產生」 |
| TABLE 索引異常 | 應由 pi-mono 的 `_validate_table()` 在啟動時保證；發生即拋 500 |
| 卦辭資料庫缺漏 | judgement 顯示空字串，不影響卦象顯示 |

## 12. 測試策略

- `test_line_mapping.py`：氣象偏離/z_score 各區間 → 爻值正確映射
- `test_four_methods.py`：對 pi-mono 已知測試案例（如本卦=1乾、變爻位置 1 → 之卦=44天風姤）逐條 unit test
- `test_table_consistency.py`：執行 `_validate_table()` 確保 64 卦完整
- `test_divination_api.py`：API 整合測試，驗證 schema + cache
- 前端 snapshot：典型日（六爻靜）、特殊日（多變爻）、極端日（六爻全變）三組 fixture

## 13. 實作階段

接續 DayInsightCard spec 的 P3：

| Phase | 內容 |
|---|---|
| **P3.1** | 後端 divination 模組 + TABLE + 64 卦資料庫 |
| **P3.2** | 6 爻映射邏輯 + 四法計算 + 單元測試 |
| **P3.3** | AI narrator + interpretation endpoint 整合 |
| **P3.4** | 前端 InterpretationDrawer + HexagramDisplay 元件 |
| **P3.5** | 整合測試 + 視覺微調 |

## 14. 開放問題（實作期間決定）

1. **64 卦卦辭資料**：自編 vs 借用古籍版本（公版周易《彖傳》《大象》）— 需查無版權版本
2. **變爻門檻動態化**：是否提供使用者調整（目前固定 \|z\|≥1）
3. **歷史對照模式**：是否支援「比對歷史某年同日」的卦象（例如「2009 艾莉颱風日 vs 今天」）— 暫列為 P4 後迭代
4. **多語言**：暫只繁中。若英文版啟用需要重新設計卦辭翻譯

## 15. 致謝與授權

- 64 卦對應表 + 四法計算邏輯參考自 [moregatest/pi-mono](https://github.com/moregatest/pi-mono) `scripts/iching_divination.py` (commit 271c9e3, MIT License)
- 八卦/64 卦本身為公開歷史知識，無版權限制
- 卦辭參考公版《周易本義》（朱熹注，元代以前公版）
