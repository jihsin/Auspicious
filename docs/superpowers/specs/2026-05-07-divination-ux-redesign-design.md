# DivinationDrawer UX 重構：三層摺疊式詮釋

**日期**：2026-05-07
**狀態**：設計已批准，待寫實作計畫
**作者**：Tom Wang + Claude
**前置**：[2026-05-06-divination-drawer-design.md](./2026-05-06-divination-drawer-design.md)（已實作上線，本 spec 是其後續 UX 重構）

---

## 1. 背景

2026-05-06 上線的 DivinationDrawer（85 行 React）對非易經讀者過於艱澀：

- 純 ASCII 陰陽爻線（`─────` / `── ──`）
- 卦辭只有古文（如「乾：元亨利貞」）
- 四法縮成一行字（「錯：第 X 卦《Y》（對立面）」）
- 沒有為「不懂易經的人」設計的入口層

使用者要求：「pi-mono 的起卦及卦象有不少方式，更容易圖像或更接近生活，現在的版本不懂讀卦的較難懂。」

研究 pi-mono `iching_divination.py @ 271c9e3` 與《圖解易經智慧寶典：精解64卦384爻》（唐頤／華威國際／2014）後，本 spec 採用該書的「主題標題 → 圖解 → 古文」三層結構。

## 2. 目標

- 不懂易經的人讀完 **Layer 1（標題層）** 就理解今日氣候性質
- 想多了解的人在 **Layer 2（視覺層）** 看見圖像化卦象與 AI 敘事
- 易經迷在 **Layer 3（學術層）** 取得卦辭、爻辭、四法樹完整資訊
- 不增加 Gemini quota 消耗（headline + subtitle + tags 與既有三段敘事**同一次 call** 取回）
- 維持現有 `@lru_cache` 與 fallback 行為

## 3. 非目標

- 不重新設計 DayInsightCard 主卡（CoreMetric / SideBadges / ExtremesAnchor 不動）
- 不改變起卦演算法（line_mapping.py 不動）
- 不改變後端 API 路徑（`/api/v1/day-insight/{station}/{month}/{day}/interpretation` 不動）
- 不引入新的前端依賴（仍用 Tailwind 4）

## 4. 設計決策摘要

| 維度 | 決策 |
|---|---|
| 結構 | 三層垂直摺疊：Layer 1 標題 / Layer 2 視覺 / Layer 3 古文 |
| 預設展開 | Layer 1 + Layer 2；Layer 3 預設關（`<details>` 原生互動） |
| 配色 | Layer 1 米黃漸層（`amber-50→100`）；Layer 2 純白；Layer 3 米色（`stone-50`） |
| AI 新欄位 | `headline` / `subtitle` / `tags`（同一次 Gemini call 多回） |
| 爻辭 | 新增 384 條爻辭表（AI 一次性生成 + 人工校對） |
| 變爻視覺 | CSS `@keyframes pulse` 金色光暈，無 JS 動畫 |
| 本→之轉場 | 並排顯示，無動畫；< 480px 改為直向 + ↓ 箭頭 |
| 無變爻情況 | Layer 1 tag 顯「六爻皆靜」；Layer 2 只顯本卦；Layer 3 隱藏 YaoCiCard |
| AI 失敗 fallback | Layer 1 headline/subtitle 隱藏（tags 改用 side_badges direction 推導）；Layer 2 NarrativeBlock 隱藏；Layer 2 HexagramPair 與 Layer 3 完整保留（皆非 AI-dependent） |

## 5. 後端改動

### 5.1 Schema 擴充（`schemas/day_insight.py`）

```python
class DivinationNarrative(BaseModel):
    climate_portrait: str
    anomaly_layer: str
    imagination: str
    headline: str          # NEW · ≤12 字大標
    subtitle: str          # NEW · ≤30 字副標
    tags: list[str]        # NEW · 3 個，每個 ≤4 字

class YaoCiEntry(BaseModel):
    original: str          # 古文爻辭
    vernacular: str        # 白話翻譯

class Divination(BaseModel):
    # ... 既有欄位 ...
    var_yao_ci: dict[int, YaoCiEntry]  # NEW · key 為爻位 1-6，只填 changing_positions
```

### 5.2 新增模組

- `backend/app/services/divination/yao_ci.py` — 64 卦 × 6 爻 = **384 條爻辭表**
  - 結構：`YAO_CI: dict[tuple[int, int], YaoCiEntry]`，key 是 `(卦號, 爻位)`
  - boot-time `validate_yao_ci_table()` 確保 384 條完整
  - 來源：原文 from `pi-mono iching_divination.py` 引用之經典版本（MIT 標註保留）；白話 by AI 一次性生成 → 人工校對
- `backend/tests/test_yao_ci_table.py` — completeness + 抽樣正確性

### 5.3 Narrator prompt 改造（`narrator.py`）

現有 `narrate()` 回傳 `{climate_portrait, anomaly_layer, imagination}`。改為一次 call 回傳 6 個 key：

```
{climate_portrait, anomaly_layer, imagination, headline, subtitle, tags}
```

- prompt 中明確指定 `headline ≤ 12 字、subtitle ≤ 30 字、tags 為 list of 3 strings each ≤ 4 字`
- parse 失敗時：對應 key 設為空字串 / 空陣列；既有三段敘事的 fallback 行為不變

### 5.4 Service 改動（`service.py`）

`build_interpretation()` 在組裝回傳時：
- 從 `yao_ci.YAO_CI` 抽出 `changing_positions` 對應的爻辭，填入 `var_yao_ci`
- 無變爻時 `var_yao_ci = {}`

## 6. 前端改動

### 6.1 檔案結構

```
frontend/src/components/
  DayInsightCard.tsx                              ← 改：移除 inline DivinationDrawer
  DayInsightCard/divination/
    DivinationDrawer.tsx              ← 改寫     組裝三層
    Layer1Headline.tsx                ← 新       米黃頂層 + 標題副標 + tag
    Layer2Visual.tsx                  ← 新       本→之 + AI 敘事
      HexagramPair.tsx                ← 新       本→之 並排或直向 + 箭頭
      HexagramVisual.tsx              ← 重寫     8 卦符號 + 6 條真陰陽爻
      NarrativeBlock.tsx              ← 改名     從 NarrativeSection 演進
    Layer3Academic.tsx                ← 新       <details> 摺疊
      GuaCiCard.tsx                   ← 新       卦辭 + 白話對照
      YaoCiCard.tsx                   ← 新       變爻爻辭 + 白話
      FourMethodsTree.tsx             ← 取代     替代 FourMethodsSummary
    glyphs.ts                         ← 新       TRIGRAM_SYMBOLS, NATURE_NAMES 常數
```

### 6.2 要刪除的檔案

- `divination/HexagramDisplay.tsx`（被 `HexagramVisual` 取代，UI 完全重畫）
- `divination/FourMethodsSummary.tsx`（被 `FourMethodsTree` 取代）
- `DayInsightCard.tsx` 內部的 `function DivinationDrawer` 內聯定義

### 6.3 互動細節

| 議題 | 行為 |
|---|---|
| RWD 斷點 | `< 480px`：HexagramPair 直向（本卦 → ↓ → 之卦）；其他 layer 高度 auto |
| Loading | Skeleton 對應三層輪廓（米黃方塊 + 雙列灰塊 + 摺疊條） |
| AI 失敗 | 各層獨立 fallback：<br>· Layer 1：headline/subtitle 隱藏；tags 改從 `data.side_badges` direction 推導<br>· Layer 2 HexagramPair：照常顯示（純 deterministic 資料）<br>· Layer 2 NarrativeBlock：整段隱藏<br>· Layer 3：照常顯示（卦辭/爻辭/四法皆非 AI 來源） |
| 變爻光暈 | CSS `@keyframes pulse 2s ease-in-out infinite` 金色 box-shadow |
| Layer 3 摺疊 | `<details><summary>` 原生（無 JS） |
| A11y | 陰陽爻線 `role="img" aria-label="陽爻"` / `"陰爻（變）"`；headline 用 `<h3>` |

### 6.4 測試

- `__tests__/HexagramVisual.test.tsx` — snapshot：6 線 yang/yin 排列、變爻光暈 class
- `__tests__/Layer1Headline.test.tsx` — fallback：headline 為空時隱藏文字段、保留 tag
- `__tests__/FourMethodsTree.test.tsx` — 5 行皆現、白話標籤正確
- 不為純 layout 元件（Layer1/Layer2/Layer3 容器）寫測試

## 7. 實作順序建議

1. 先做 `yao_ci.py` 表 + 測試（純資料，可獨立驗證）
2. 改 `narrator.py` prompt + schema 新欄位（後端 API 先能回新格式）
3. 寫 `glyphs.ts` 常數
4. 重寫 `HexagramVisual` + 寫 `HexagramPair`（Layer 2 視覺核心）
5. 寫 `Layer1Headline`、`NarrativeBlock`、`Layer3Academic`（外殼）
6. 寫 `GuaCiCard`、`YaoCiCard`、`FourMethodsTree`（Layer 3 內容）
7. 改寫 `DivinationDrawer.tsx` 組裝三層
8. 改 `DayInsightCard.tsx` 移除 inline drawer
9. 刪除舊 `HexagramDisplay.tsx`、`FourMethodsSummary.tsx`
10. 部署 + 視覺驗證（依 deployment-verification-protocol：先確認 Vercel 跑的是最新 SHA）

## 8. 開放問題

- **384 條爻辭白話翻譯品質**：AI 一次性生成後，人工校對工作量約半天到一天。是否要分批校對（例如先做 12 個 demo 卦）？
- **`tags` emoji**：要不要在 Gemini prompt 裡明確要求每個 tag 帶 emoji（如「☀ 偏涼」），還是 frontend 用 anomaly direction 自行推導？

決定可在實作階段微調。
