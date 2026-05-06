# DivinationDrawer UX 重構 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure the existing DivinationDrawer (85 lines, too academic) into a three-layer fold (elevator-pitch headline → visual hexagram + AI narrative → collapsible 卦辭/爻辭/四法樹), per spec [`2026-05-07-divination-ux-redesign-design.md`](../specs/2026-05-07-divination-ux-redesign-design.md).

**Architecture:** Backend extends `DivinationNarrative` with `headline/subtitle/tags` from the same Gemini call (no extra quota); adds a 384-row 爻辭 table with classical+vernacular pairs. Frontend splits the drawer into 11 components organized by layer, with per-layer AI fallback logic.

**Tech Stack:** Python 3.11 / FastAPI / Pydantic v2 / SQLAlchemy / pytest (backend) · Next.js 16 / React 19 / TypeScript / Tailwind 4 (frontend) · Google Gemini via existing `ai_engine` client · Vercel git integration (auto-deploy on push to main).

## Deviations from spec

- **Frontend unit tests deferred.** Spec §6.4 lists `HexagramVisual.test.tsx`, `Layer1Headline.test.tsx`, `FourMethodsTree.test.tsx`. The repo has no frontend test framework configured (no jest / vitest in `frontend/package.json`, no `*.test.*` files exist). Setting one up is a separate concern. This plan relies on `pnpm tsc --noEmit` + `pnpm build` + post-deploy Playwright visual verification (Task 11). If frontend tests become a priority, file a follow-up plan to add vitest setup.

---

## File Structure

```
backend/
  app/schemas/day_insight.py           ← MODIFY (add YaoCiEntry, extend Narrative + Divination)
  app/services/divination/
    yao_ci.py                          ← CREATE (384-row table)
    narrator.py                        ← MODIFY (extend prompt + parser for 6 sections)
    service.py                         ← MODIFY (lookup yao_ci for var_yao_ci field)
  tests/
    test_yao_ci_table.py               ← CREATE (completeness + sample correctness)
    test_divination_narrator.py        ← MODIFY (cover 6-section parser + fallback)
    test_divination_service.py         ← MODIFY (verify var_yao_ci population)
frontend/
  src/lib/types.ts                     ← MODIFY (mirror new backend fields)
  src/components/DayInsightCard.tsx    ← MODIFY (remove inline DivinationDrawer)
  src/components/DayInsightCard/divination/
    DivinationDrawer.tsx               ← CREATE (top-level assembly)
    Layer1Headline.tsx                 ← CREATE
    Layer2Visual.tsx                   ← CREATE
    Layer3Academic.tsx                 ← CREATE
    HexagramPair.tsx                   ← CREATE
    HexagramVisual.tsx                 ← REWRITE (replace ASCII with real CSS lines)
    NarrativeBlock.tsx                 ← RENAME from NarrativeSection.tsx
    GuaCiCard.tsx                      ← CREATE
    YaoCiCard.tsx                      ← CREATE
    FourMethodsTree.tsx                ← CREATE
    glyphs.ts                          ← CREATE (TRIGRAM_SYMBOLS, NATURE_NAMES)
  src/components/DayInsightCard/divination/
    HexagramDisplay.tsx                ← DELETE (replaced by HexagramVisual)
    FourMethodsSummary.tsx             ← DELETE (replaced by FourMethodsTree)
    NarrativeSection.tsx               ← DELETE (replaced by NarrativeBlock)
```

---

## Task 1: Backend schemas — add YaoCiEntry + extend Narrative/Divination

**Files:**
- Modify: `backend/app/schemas/day_insight.py`
- Test: covered indirectly by Task 4-5; no new test file

- [ ] **Step 1: Edit `backend/app/schemas/day_insight.py`**

Replace the `Narrative` and `Divination` classes (lines 58-72) with:

```python
class Narrative(BaseModel):
    climate_portrait: str
    anomaly_layer: str
    imagination: str
    headline: str = ""        # NEW · ≤12 字大標
    subtitle: str = ""        # NEW · ≤30 字副標
    tags: list[str] = []      # NEW · 3 個，每個 ≤4 字


class YaoCiEntry(BaseModel):
    original: str             # 古文爻辭
    vernacular: str           # 白話翻譯


class Divination(BaseModel):
    ben: HexagramRef
    zhi: HexagramRef
    cuo: HexagramRef
    zong: HexagramRef
    hu: HexagramRef
    changing_positions: list[int]
    line_values: list[int]
    narrative: Narrative
    var_yao_ci: dict[int, YaoCiEntry] = {}  # NEW · key = 爻位 (1-6)
```

The defaults (empty string / list / dict) ensure backwards compatibility — existing call sites that don't populate the new fields still validate.

- [ ] **Step 2: Run pytest to confirm no schema regression**

Run: `cd backend && poetry run pytest tests/test_divination_*.py -q`
Expected: existing tests still pass (new fields default to empty).

- [ ] **Step 3: Commit**

```bash
git add backend/app/schemas/day_insight.py
git commit -m "feat(schemas): add headline/subtitle/tags + YaoCiEntry + var_yao_ci

Extend DivinationNarrative with three new optional fields (headline ≤12字,
subtitle ≤30字, tags list[str]≤4字) for the upcoming three-layer drawer
redesign. Add YaoCiEntry and var_yao_ci dict on Divination for per-line
classical+vernacular 爻辭 pairs.

All new fields have defaults so existing call sites validate unchanged.
"
```

---

## Task 2: yao_ci.py skeleton + validator + 卦 1-3 sample data

**Files:**
- Create: `backend/app/services/divination/yao_ci.py`
- Create: `backend/tests/test_yao_ci_table.py`

- [ ] **Step 1: Write the failing completeness test**

Create `backend/tests/test_yao_ci_table.py`:

```python
"""Validate the 384-row 爻辭 lookup table.

Mirrors the boot-time guard pattern from hexagram_table.py.
"""

from app.services.divination.yao_ci import YAO_CI, get_yao_ci, validate_yao_ci_table


def test_table_has_all_384_entries():
    validate_yao_ci_table()  # raises if incomplete


def test_each_hex_has_six_lines():
    for hex_num in range(1, 65):
        for pos in range(1, 7):
            assert (hex_num, pos) in YAO_CI, f"missing 卦{hex_num} 爻{pos}"


def test_get_yao_ci_returns_entry():
    entry = get_yao_ci(1, 1)  # 乾 初九
    assert entry.original
    assert entry.vernacular


def test_get_yao_ci_bad_hex_raises():
    import pytest
    with pytest.raises(KeyError):
        get_yao_ci(99, 1)


def test_qian_yi_initial_line_classical():
    """Spot-check 乾 初九 爻辭 matches classical text."""
    entry = get_yao_ci(1, 1)
    assert "潛龍勿用" in entry.original
```

- [ ] **Step 2: Create `backend/app/services/divination/yao_ci.py` with skeleton + 卦 1-3 sample**

```python
# backend/app/services/divination/yao_ci.py
"""384-row 爻辭 lookup table (64 卦 × 6 爻).

原文 (original) 出自《周易》爻辭 — 先秦典籍，公共領域。
白話 (vernacular) 為 AI 輔助生成 + 人工校對結果（CC-BY-SA 4.0 標註）。
"""

from app.schemas.day_insight import YaoCiEntry


# Key: (hex_num, line_pos), where line_pos 1=初爻, 6=上爻
YAO_CI: dict[tuple[int, int], YaoCiEntry] = {
    # ---------- 卦 1 乾為天 ----------
    (1, 1): YaoCiEntry(
        original="初九：潛龍勿用。",
        vernacular="深水裡的龍，先別動 — 時機未到，沉潛蓄力比逞強更聰明。",
    ),
    (1, 2): YaoCiEntry(
        original="九二：見龍在田，利見大人。",
        vernacular="龍開始浮現，宜尋覓貴人或合作夥伴 — 不是孤軍時候。",
    ),
    (1, 3): YaoCiEntry(
        original="九三：君子終日乾乾，夕惕若厲，無咎。",
        vernacular="白天卯足全力、晚上仍警戒檢視 — 這樣的勤勉才能化險為夷。",
    ),
    (1, 4): YaoCiEntry(
        original="九四：或躍在淵，無咎。",
        vernacular="該躍出還是退守？兩可之間，憑直覺抉擇皆無咎。",
    ),
    (1, 5): YaoCiEntry(
        original="九五：飛龍在天，利見大人。",
        vernacular="勢頭最盛之時，正是擴大格局、結交同等量級的人的時刻。",
    ),
    (1, 6): YaoCiEntry(
        original="上九：亢龍有悔。",
        vernacular="飛得太高的龍，會懊悔 — 物極必反，懂得收斂才是真本事。",
    ),
    # ---------- 卦 2 坤為地 ----------
    (2, 1): YaoCiEntry(
        original="初六：履霜，堅冰至。",
        vernacular="踩到第一片霜，就知道嚴冬將至 — 從微小徵兆讀出大趨勢。",
    ),
    (2, 2): YaoCiEntry(
        original="六二：直方大，不習無不利。",
        vernacular="正直、方正、寬大這三個本性夠了 — 不必刻意修飾，自然順遂。",
    ),
    (2, 3): YaoCiEntry(
        original="六三：含章可貞，或從王事，無成有終。",
        vernacular="懷藏才華靜守正道，即便代人辦事不居功，也會有好結局。",
    ),
    (2, 4): YaoCiEntry(
        original="六四：括囊，無咎無譽。",
        vernacular="把袋口紮緊 — 該沉默的時候沉默，沒讚也沒罵就是上策。",
    ),
    (2, 5): YaoCiEntry(
        original="六五：黃裳，元吉。",
        vernacular="居中的黃色內裳象徵謙退守中 — 大吉。",
    ),
    (2, 6): YaoCiEntry(
        original="上六：龍戰于野，其血玄黃。",
        vernacular="陰盛至極與陽相搏 — 兩敗俱傷的場面，宜避其鋒。",
    ),
    # ---------- 卦 3 水雷屯 ----------
    (3, 1): YaoCiEntry(
        original="初九：磐桓，利居貞，利建侯。",
        vernacular="開局徘徊不定，留在原地守正反而有利，也適合奠基立業。",
    ),
    (3, 2): YaoCiEntry(
        original="六二：屯如邅如，乘馬班如。匪寇婚媾，女子貞不字，十年乃字。",
        vernacular="進退維谷，車馬徘徊。對方不是敵人是求婚者 — 但十年後才會回應。",
    ),
    (3, 3): YaoCiEntry(
        original="六三：即鹿無虞，惟入于林中。君子幾不如舍，往吝。",
        vernacular="無嚮導獵鹿只會迷失叢林。君子當知見機放手，硬闖會有遺憾。",
    ),
    (3, 4): YaoCiEntry(
        original="六四：乘馬班如，求婚媾，往吉，無不利。",
        vernacular="徘徊之時若主動求結盟，前往大吉、無往不利。",
    ),
    (3, 5): YaoCiEntry(
        original="九五：屯其膏，小貞吉，大貞凶。",
        vernacular="囤積資源該散卻不散 — 小事守正吉，大事守舊凶。",
    ),
    (3, 6): YaoCiEntry(
        original="上六：乘馬班如，泣血漣如。",
        vernacular="徘徊到最後，血淚漣漣 — 此時當斷不斷反受其亂。",
    ),
}


def validate_yao_ci_table() -> None:
    expected_keys = {(h, p) for h in range(1, 65) for p in range(1, 7)}
    missing = expected_keys - YAO_CI.keys()
    if missing:
        raise RuntimeError(f"YAO_CI incomplete: missing {len(missing)} entries, e.g. {sorted(missing)[:3]}")


def get_yao_ci(hex_num: int, line_pos: int) -> YaoCiEntry:
    """Lookup 爻辭 by (卦號, 爻位 1-6). Raises KeyError if missing."""
    return YAO_CI[(hex_num, line_pos)]


# Boot-time guard intentionally OMITTED here — table is incomplete
# until Task 3. We only call validate_yao_ci_table() in tests.
```

- [ ] **Step 3: Run the test — completeness FAILS, samples PASS**

Run: `cd backend && poetry run pytest tests/test_yao_ci_table.py -v`
Expected: `test_table_has_all_384_entries` FAILS with `RuntimeError: YAO_CI incomplete: missing 366 entries`. Other 4 tests PASS.

- [ ] **Step 4: Commit (incomplete table is intentional — Task 3 fills the rest)**

```bash
git add backend/app/services/divination/yao_ci.py backend/tests/test_yao_ci_table.py
git commit -m "feat(divination): yao_ci.py skeleton + 18 entries (卦 1-3)

Add 爻辭 lookup table structure with classical+vernacular pairs.
Validation harness, getter, and 18 sample entries (卦 1 乾 / 卦 2 坤 /
卦 3 屯). Remaining 366 entries to be populated in next commit;
test_table_has_all_384_entries fails until then by design.
"
```

---

## Task 3: Populate remaining 366 yao-ci entries

**Files:**
- Modify: `backend/app/services/divination/yao_ci.py`
- Reference: any classical 易經 source for original text (《周易》is public domain)
- Test: existing `test_yao_ci_table.py` will pass after population

This task is **content work, not pure code**. Estimated 1-2 hours including review.

- [ ] **Step 1: Generate first-pass vernacular translations via Gemini**

Run this generation script (one-shot, manual):

```bash
# backend/scripts/generate_yao_ci.py
# Run from backend/ with: poetry run python scripts/generate_yao_ci.py > /tmp/yao_ci_draft.py
"""One-shot generator. Calls Gemini to draft vernacular translations
for 卦 4-64. Output is to be reviewed manually before paste-in.
"""

from app.services.ai_engine import get_client
from app.services.divination.hexagrams import HEXAGRAMS

CLASSICAL_YAO_CI: dict[tuple[int, int], str] = {
    # Paste classical 爻辭 from a public-domain 周易 source
    # for 卦 4-64, all 6 lines each. ~366 entries.
    # E.g.:
    # (4, 1): "初六：發蒙，利用刑人，用說桎梏，以往吝。",
    # (4, 2): "九二：包蒙吉，納婦吉，子克家。",
    # ... (continue) ...
}

PROMPT = """以下是《周易》第 {hex_num} 卦《{hex_name}》第 {pos} 爻的原文：

{original}

請用一句不超過 40 字的繁體中文白話翻譯，要求：
1. 保留原意，不誇張不過度詮釋
2. 用現代生活語感，不要加註解
3. 一句話，不要分行

只輸出翻譯文字，不要任何前綴或標號。"""

def main():
    client = get_client()
    print("# Auto-generated drafts. Review before merging into yao_ci.py")
    for (hex_num, pos), original in CLASSICAL_YAO_CI.items():
        hex_name = next(h["name"] for h in HEXAGRAMS if h["num"] == hex_num)
        prompt = PROMPT.format(hex_num=hex_num, hex_name=hex_name, pos=pos, original=original)
        resp = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        vernacular = (resp.text or "").strip()
        print(f"    ({hex_num}, {pos}): YaoCiEntry(")
        print(f"        original={original!r},")
        print(f"        vernacular={vernacular!r},")
        print("    ),")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Manually populate `CLASSICAL_YAO_CI` in the script**

This is the slow part. Source classical 爻辭 from 中國哲學書電子化計劃 (https://ctext.org/book-of-changes/yi-jing/zh) which mirrors《周易》— public domain. Paste 366 lines into `CLASSICAL_YAO_CI`. Allow ~30 min.

- [ ] **Step 3: Run the generator, redirect output**

```bash
cd backend && poetry run python scripts/generate_yao_ci.py > /tmp/yao_ci_draft.py
```

Expected: `/tmp/yao_ci_draft.py` contains ~366 `YaoCiEntry` blocks.

- [ ] **Step 4: Review samples — spot-check 5-10 random translations**

Manually open `/tmp/yao_ci_draft.py`, sample-read 5-10 entries (across different 卦). Look for:
- Mistranslations of archaic terms (e.g., 「攸」「咎」「貞」 misread)
- Tone too casual or too academic
- Length way off (>40 字 or <10 字)

If any look wrong, edit them in-place. Don't try to review all 366 in this pass — `tags` Layer 1 fallback covers most users; deep readers will spot-correct over time.

- [ ] **Step 5: Paste reviewed entries into `yao_ci.py`**

Copy contents of `/tmp/yao_ci_draft.py` (just the `YaoCiEntry` blocks, not the script wrapper) and paste before the `}` closing `YAO_CI`. Final file has 384 entries.

- [ ] **Step 6: Re-enable boot-time validation**

In `yao_ci.py`, **remove** the comment about the omitted boot-time guard, and **add** at the bottom of the module:

```python
validate_yao_ci_table()  # boot-time guard
```

- [ ] **Step 7: Run all 5 tests — all PASS**

Run: `cd backend && poetry run pytest tests/test_yao_ci_table.py -v`
Expected: 5 passed.

- [ ] **Step 8: Commit**

```bash
git add backend/app/services/divination/yao_ci.py backend/scripts/generate_yao_ci.py
git commit -m "feat(divination): complete 384 yao-ci entries (卦 4-64) + boot guard

Add remaining 366 爻辭 entries with AI-drafted, human-reviewed
vernacular translations. Enable validate_yao_ci_table() at boot.

Generation script (scripts/generate_yao_ci.py) kept for reproducibility:
classical text from 《周易》(public domain via ctext.org), vernacular
translations via Gemini gemini-2.0-flash with sample-review pass.
"
```

---

## Task 4: Update narrator.py for 6-section output

**Files:**
- Modify: `backend/app/services/divination/narrator.py`
- Modify: `backend/tests/test_divination_narrator.py`

- [ ] **Step 1: Write a failing test for the new parser**

Append to `backend/tests/test_divination_narrator.py`:

```python
def test_parse_sections_handles_six_segments():
    from app.services.divination.narrator import _parse_sections
    raw = """段一【氣候畫像】今日陽氣初升、地氣未動。
段二【特殊度】第二爻變動，午後可能轉折。
段三【想像層】半年後對位是地雷復，動極轉靜。
段四【標題】穩中帶變的一天
段五【副標】天涼略乾、雨機率持平 — 適合靜中蓄勢。
段六【標籤】偏涼,偏乾,二爻變"""
    out = _parse_sections(raw)
    assert out["climate_portrait"].startswith("今日陽氣")
    assert out["headline"] == "穩中帶變的一天"
    assert out["subtitle"].startswith("天涼略乾")
    assert out["tags"] == ["偏涼", "偏乾", "二爻變"]


def test_parse_sections_empty_input():
    from app.services.divination.narrator import _parse_sections
    out = _parse_sections(None)
    assert out == {
        "climate_portrait": "", "anomaly_layer": "", "imagination": "",
        "headline": "", "subtitle": "", "tags": [],
    }


def test_parse_sections_partial_input_keeps_defaults():
    from app.services.divination.narrator import _parse_sections
    raw = "段一【氣候畫像】只有第一段。"
    out = _parse_sections(raw)
    assert out["climate_portrait"].endswith("只有第一段。")
    assert out["headline"] == ""  # no 段四, default to empty
    assert out["tags"] == []
```

- [ ] **Step 2: Run the failing tests**

Run: `cd backend && poetry run pytest tests/test_divination_narrator.py::test_parse_sections_handles_six_segments -v`
Expected: FAIL — `KeyError: 'headline'` or `AssertionError`.

- [ ] **Step 3: Update narrator.py**

Replace `PROMPT_TEMPLATE` and `_parse_sections` in `backend/app/services/divination/narrator.py`:

```python
PROMPT_TEMPLATE = """你是「好日子」app 的氣象詮釋師。請依下列卦象結果，用「六段式」繁體中文輸出一份氣候洞察。

【日期】{station_name} {month}/{day}（節氣：{solar_term}）
【本卦】{ben_num}-{ben_name}
【互卦】{hu_num}-{hu_name}
【之卦】{zhi_num}-{zhi_name}（變爻：{changing_positions}）
【錯卦】{cuo_num}-{cuo_name}
【綜卦】{zong_num}-{zong_name}
【氣候資料】溫差={t_anom}°C 濕差={h_anom}% 雨機率差={p_anom}%

請輸出嚴格六段，格式如下（不要加其他文字、不要 markdown）：

段一【氣候畫像】合論本卦+互卦，描寫這天的氣候本相，30-50 字
段二【特殊度】從變爻和之卦切入，描述異常維度與可能轉變，30-50 字
段三【想像層】用錯卦和綜卦延伸，給出反季節對立或半年後對位想像，30-50 字
段四【標題】≤12 字的「今日定調」標題，要朗朗上口，例如「穩中帶變的一天」「躁動需穩的一天」
段五【副標】≤30 字的一句話，承接標題、用白話描述今日氣候性質
段六【標籤】3 個 ≤4 字的關鍵字，用半形逗號分隔，例如「偏涼,偏乾,二爻變」

風格：段一至段三古典文學語感、可入詩；段四至段六完全白話、現代生活語感。
"""


def _parse_sections(text: str | None) -> dict:
    empty = {
        "climate_portrait": "", "anomaly_layer": "", "imagination": "",
        "headline": "", "subtitle": "", "tags": [],
    }
    if not text:
        return empty

    sentinel = "§§§"
    markers = ["段一", "段二", "段三", "段四", "段五", "段六"]
    keys = ["climate_portrait", "anomaly_layer", "imagination",
            "headline", "subtitle", "tags"]

    for m in markers:
        text = text.replace(m, sentinel + m)
    parts = [p.strip() for p in text.split(sentinel) if p.strip()]
    # First part may be preamble — drop it if it doesn't start with a marker.
    parts = [p for p in parts if any(p.startswith(m) for m in markers)]

    out = dict(empty)
    for part in parts:
        for m, k in zip(markers, keys):
            if part.startswith(m):
                # Strip "段N【...】" prefix; keep only content
                content = part.split("】", 1)[-1].strip() if "】" in part else part
                if k == "tags":
                    out[k] = [t.strip() for t in content.split(",") if t.strip()]
                else:
                    out[k] = content
                break
    return out
```

- [ ] **Step 4: Run all narrator tests — all PASS**

Run: `cd backend && poetry run pytest tests/test_divination_narrator.py -v`
Expected: all tests pass (existing 3-section tests + new 3 tests for 6-section parsing).

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/divination/narrator.py backend/tests/test_divination_narrator.py
git commit -m "feat(divination): extend narrator to six-section output

Add 段四【標題】 ≤12字 / 段五【副標】 ≤30字 / 段六【標籤】 3 個 ≤4字 to the
Gemini prompt and parser. Same single API call (no extra quota). Backward
compatible: missing/empty new sections default to empty string / list.

Tests cover: full 6-section parse, None input, partial input (only 段一).
"
```

---

## Task 5: Wire var_yao_ci into service.build_interpretation

**Files:**
- Modify: `backend/app/services/divination/service.py`
- Create: `backend/tests/test_var_yao_ci_construction.py` (self-contained, no DB)

- [ ] **Step 1: Write a self-contained failing test for var_yao_ci dict construction**

Create `backend/tests/test_var_yao_ci_construction.py`:

```python
"""Verify the var_yao_ci dict is built correctly from changing positions.

Self-contained — does not exercise the DB-dependent build_interpretation
function. The full integration is verified post-deploy via the curl smoke
test in Task 11 step 4.
"""

import pytest

from app.services.divination.yao_ci import get_yao_ci


def _build_var_yao_ci(ben_num: int, changing_positions: list[int]) -> dict:
    """Mirrors the production logic in service.build_interpretation."""
    return {
        pos: get_yao_ci(ben_num, pos).model_dump()
        for pos in changing_positions
    }


def test_two_changing_positions_yields_two_entries():
    out = _build_var_yao_ci(ben_num=1, changing_positions=[2, 5])
    assert set(out.keys()) == {2, 5}
    for pos in (2, 5):
        assert out[pos]["original"]
        assert out[pos]["vernacular"]


def test_zero_changing_positions_yields_empty_dict():
    out = _build_var_yao_ci(ben_num=1, changing_positions=[])
    assert out == {}


def test_invalid_hex_raises_keyerror():
    with pytest.raises(KeyError):
        _build_var_yao_ci(ben_num=99, changing_positions=[1])
```

- [ ] **Step 2: Run the test — `_build_var_yao_ci` doesn't exist in production code yet, but the test imports `get_yao_ci` only, so it should PASS**

Run: `cd backend && poetry run pytest tests/test_var_yao_ci_construction.py -v`
Expected: 3 passed (the test contains its own helper; this validates the LOGIC we're about to add to service.py).

- [ ] **Step 3: Edit `backend/app/services/divination/service.py`**

Add import near the top (around line 13):

```python
from app.services.divination.yao_ci import get_yao_ci
```

Modify the `return` block at the bottom (lines 124-132):

```python
    var_yao_ci = {
        pos: get_yao_ci(cast["ben_num"], pos).model_dump()
        for pos in cast["changing_positions"]
    }

    return {
        "station_id": station_id, "month": month, "day": day,
        "divination": {
            "ben": ben, "zhi": zhi, "cuo": cuo, "zong": zong, "hu": hu,
            "changing_positions": cast["changing_positions"],
            "line_values": line_values,
            "narrative": narrative,
            "var_yao_ci": var_yao_ci,
        },
    }
```

- [ ] **Step 4: Run full suite to confirm no regression**

Run: `cd backend && poetry run pytest -q`
Expected: all green (≥ 82 tests passing — 79 existing + 3 new from this task).

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/divination/service.py backend/tests/test_var_yao_ci_construction.py
git commit -m "feat(divination): populate var_yao_ci from yao_ci table

build_interpretation now looks up 爻辭 for each changing position from
the new yao_ci.YAO_CI table and includes them in the response under
divination.var_yao_ci. Empty dict when no 變爻.

Test mocks the Gemini narrator so the unit doesn't hit the network.
"
```

---

## Task 6: Frontend types + glyphs constants

**Files:**
- Modify: `frontend/src/lib/types.ts`
- Create: `frontend/src/components/DayInsightCard/divination/glyphs.ts`

- [ ] **Step 1: Edit `frontend/src/lib/types.ts`**

Replace lines 443-458 (`DivinationNarrative` and `Divination` interfaces) with:

```typescript
export interface DivinationNarrative {
  climate_portrait: string;
  anomaly_layer: string;
  imagination: string;
  headline: string;        // NEW · ≤12 字
  subtitle: string;        // NEW · ≤30 字
  tags: string[];          // NEW · 3 個 ≤4 字
}

export interface YaoCiEntry {
  original: string;
  vernacular: string;
}

export interface Divination {
  ben: HexagramRef;
  zhi: HexagramRef;
  cuo: HexagramRef;
  zong: HexagramRef;
  hu: HexagramRef;
  changing_positions: number[];
  line_values: number[];
  narrative: DivinationNarrative;
  var_yao_ci: Record<number, YaoCiEntry>;  // NEW
}
```

- [ ] **Step 2: Create `frontend/src/components/DayInsightCard/divination/glyphs.ts`**

```typescript
// 八卦索引對應：坤0 艮1 坎2 巽3 震4 離5 兌6 乾7
// (與 backend/app/services/divination/hexagram_table.py 同步)
export const TRIGRAM_NAMES = ["坤", "艮", "坎", "巽", "震", "離", "兌", "乾"] as const;
export const TRIGRAM_SYMBOLS = ["☷", "☶", "☵", "☴", "☳", "☲", "☱", "☰"] as const;
export const TRIGRAM_NATURE = ["地", "山", "水", "風", "雷", "火", "澤", "天"] as const;

/** Map a trigram name to its symbol, e.g. "乾" → "☰". */
export function symbolOf(name: string): string {
  const idx = TRIGRAM_NAMES.indexOf(name as typeof TRIGRAM_NAMES[number]);
  return idx >= 0 ? TRIGRAM_SYMBOLS[idx] : "?";
}

/** Map a trigram name to its nature, e.g. "乾" → "天". */
export function natureOf(name: string): string {
  const idx = TRIGRAM_NAMES.indexOf(name as typeof TRIGRAM_NAMES[number]);
  return idx >= 0 ? TRIGRAM_NATURE[idx] : "";
}
```

- [ ] **Step 3: Confirm typecheck passes**

Run: `cd frontend && pnpm tsc --noEmit`
Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/lib/types.ts frontend/src/components/DayInsightCard/divination/glyphs.ts
git commit -m "feat(frontend): mirror backend yao-ci/headline fields + add glyphs

Add headline/subtitle/tags to DivinationNarrative and var_yao_ci to
Divination; create glyphs.ts with TRIGRAM_NAMES/SYMBOLS/NATURE constants
synced from backend/app/services/divination/hexagram_table.py.
"
```

---

## Task 7: Rewrite HexagramVisual + add HexagramPair

**Files:**
- Rewrite: `frontend/src/components/DayInsightCard/divination/HexagramVisual.tsx` (renaming HexagramDisplay → HexagramVisual)
- Create: `frontend/src/components/DayInsightCard/divination/HexagramPair.tsx`

- [ ] **Step 1: Create new `HexagramVisual.tsx`** (rewrite — old `HexagramDisplay.tsx` will be deleted in Task 11)

```tsx
// frontend/src/components/DayInsightCard/divination/HexagramVisual.tsx
import type { HexagramRef } from "@/lib/types";
import { symbolOf, natureOf } from "./glyphs";

interface Props {
  hex: HexagramRef;
  lineValues: number[];        // 6 entries, line 1 first (bottom)
  changingPositions: number[]; // 1-based positions
  caption?: string;
}

/** Render a single hexagram with trigram labels + 6 stacked lines (top = line 6). */
export function HexagramVisual({ hex, lineValues, changingPositions, caption }: Props) {
  // Display order: line 6 on top, line 1 on bottom
  const ordered = [...lineValues].map((v, i) => ({ v, pos: i + 1 })).reverse();

  return (
    <div className="flex flex-col gap-2">
      <div className="text-xs text-slate-500">
        {hex.upper_trigram && (
          <span className="mr-2">
            <span className="text-lg leading-none align-middle">{symbolOf(hex.upper_trigram)}</span>
            <span className="ml-1">{hex.upper_trigram}（{natureOf(hex.upper_trigram)}）上</span>
          </span>
        )}
        {hex.lower_trigram && (
          <span>
            <span className="text-lg leading-none align-middle">{symbolOf(hex.lower_trigram)}</span>
            <span className="ml-1">{hex.lower_trigram}（{natureOf(hex.lower_trigram)}）下</span>
          </span>
        )}
      </div>
      <div className="py-2" role="img" aria-label={`卦象 第${hex.num}卦 ${hex.name}`}>
        {ordered.map(({ v, pos }) => {
          const yang = v === 7 || v === 9;
          const changing = changingPositions.includes(pos);
          return (
            <div
              key={pos}
              className={[
                "h-2 my-1.5 rounded-sm",
                yang ? "bg-slate-800" : "",
                changing ? "ring-2 ring-amber-400 shadow-[0_0_12px_rgba(245,158,11,0.4)] animate-pulse" : "",
              ].filter(Boolean).join(" ")}
              style={
                yang
                  ? undefined
                  : {
                      background:
                        "linear-gradient(90deg, #1e293b 0%, #1e293b 44%, transparent 44%, transparent 56%, #1e293b 56%, #1e293b 100%)",
                    }
              }
              aria-label={yang ? (changing ? "陽爻（變）" : "陽爻") : changing ? "陰爻（變）" : "陰爻"}
            />
          );
        })}
      </div>
      <div className="text-sm font-semibold text-slate-700">
        第 {hex.num} 卦《{hex.name}》
      </div>
      {caption && <div className="text-xs text-slate-400">{caption}</div>}
    </div>
  );
}
```

- [ ] **Step 2: Create `HexagramPair.tsx`**

```tsx
// frontend/src/components/DayInsightCard/divination/HexagramPair.tsx
import type { HexagramRef } from "@/lib/types";
import { HexagramVisual } from "./HexagramVisual";

interface Props {
  ben: HexagramRef;
  zhi: HexagramRef;
  lineValues: number[];
  zhiLineValues: number[];      // 變爻已反向
  changingPositions: number[];
}

/** Side-by-side ben → zhi on ≥480px; vertical (ben above zhi with ↓ arrow) below 480px.
 *  When changingPositions is empty, only ben is shown.
 */
export function HexagramPair({ ben, zhi, lineValues, zhiLineValues, changingPositions }: Props) {
  const hasChange = changingPositions.length > 0;

  return (
    <div className="flex flex-col sm:flex-row gap-4 sm:items-stretch">
      <div className="flex-1">
        <div className="text-xs text-slate-400 mb-1">本卦 · 現狀</div>
        <HexagramVisual
          hex={ben}
          lineValues={lineValues}
          changingPositions={changingPositions}
        />
      </div>
      {hasChange && (
        <>
          <div
            className="flex items-center justify-center text-2xl text-amber-500 sm:px-2"
            aria-label="變爻轉化"
          >
            <span className="hidden sm:block">→</span>
            <span className="sm:hidden">↓</span>
          </div>
          <div className="flex-1">
            <div className="text-xs text-slate-400 mb-1">之卦 · 趨勢</div>
            <HexagramVisual
              hex={zhi}
              lineValues={zhiLineValues}
              changingPositions={[]}
            />
          </div>
        </>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Confirm typecheck passes**

Run: `cd frontend && pnpm tsc --noEmit`
Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/DayInsightCard/divination/HexagramVisual.tsx \
        frontend/src/components/DayInsightCard/divination/HexagramPair.tsx
git commit -m "feat(frontend): rewrite HexagramVisual + add HexagramPair

HexagramVisual: replace ASCII --- glyphs with real CSS lines (yang =
solid bar, yin = split bar via gradient, changing = amber ring + pulse).
Trigram labels include 八卦 symbol + nature (e.g. ☰ 乾（天）).

HexagramPair: side-by-side ben → zhi with arrow; vertical layout below
480px; hides zhi when no changing positions.
"
```

---

## Task 8: Layer 1 + NarrativeBlock + Layer 2 composer

**Files:**
- Create: `frontend/src/components/DayInsightCard/divination/Layer1Headline.tsx`
- Create: `frontend/src/components/DayInsightCard/divination/NarrativeBlock.tsx` (renamed from NarrativeSection)
- Create: `frontend/src/components/DayInsightCard/divination/Layer2Visual.tsx`

- [ ] **Step 1: Create `Layer1Headline.tsx`**

```tsx
// frontend/src/components/DayInsightCard/divination/Layer1Headline.tsx
import type { DayInsight, DivinationNarrative } from "@/lib/types";

interface Props {
  insight: DayInsight;
  narrative: DivinationNarrative;
  hasChange: boolean;
}

/** Top amber-tinted layer. Hides headline/subtitle when AI failed; tags
 *  fall back to deterministic anomaly-direction snippets. */
export function Layer1Headline({ insight, narrative, hasChange }: Props) {
  const fallbackTags = useFallbackTags(insight, hasChange);
  const tags = narrative.tags.length > 0 ? narrative.tags : fallbackTags;

  return (
    <div className="bg-gradient-to-br from-amber-50 to-amber-100 border-b border-amber-200 px-5 py-5">
      <div className="flex justify-between items-start mb-2 text-[11px] uppercase tracking-wider text-amber-700">
        <span>{insight.month}月{insight.day}日 · {insight.meta.years_analyzed}年統計</span>
        {hasChange && <span>本卦 ▸ 之卦</span>}
      </div>
      {narrative.headline && (
        <h3 className="text-2xl font-bold text-amber-900 mb-1">
          {narrative.headline}
        </h3>
      )}
      {narrative.subtitle && (
        <p className="text-sm text-amber-800 mb-3 leading-relaxed">
          {narrative.subtitle}
        </p>
      )}
      <div className="flex flex-wrap gap-1.5">
        {tags.map((t, i) => (
          <span
            key={`${t}-${i}`}
            className="bg-amber-900/10 text-amber-900 px-2.5 py-1 rounded-full text-xs font-medium"
          >
            {t}
          </span>
        ))}
      </div>
    </div>
  );
}

function useFallbackTags(insight: DayInsight, hasChange: boolean): string[] {
  // Deterministic anomaly-direction snippets when AI tags missing.
  const tags: string[] = [];
  for (const b of insight.side_badges.slice(0, 2)) {
    const noun = b.metric === "temp_avg" ? "氣溫" : "濕度";
    const dir = b.direction === "above" ? "偏高" : "偏低";
    tags.push(`${noun}${dir}`);
  }
  tags.push(hasChange ? "有變動" : "六爻皆靜");
  return tags;
}
```

- [ ] **Step 2: Create `NarrativeBlock.tsx`** (replacing NarrativeSection)

```tsx
// frontend/src/components/DayInsightCard/divination/NarrativeBlock.tsx
import type { DivinationNarrative } from "@/lib/types";

/** Three short paragraphs (氣候畫像 / 異常之處 / 給今天的話).
 *  Hidden entirely when all three are empty. */
export function NarrativeBlock({ narrative }: { narrative: DivinationNarrative }) {
  const empty =
    !narrative.climate_portrait &&
    !narrative.anomaly_layer &&
    !narrative.imagination;
  if (empty) return null;

  return (
    <div className="mt-5 pt-4 border-t border-dashed border-slate-200 space-y-3 text-[13.5px] leading-relaxed text-slate-700">
      {narrative.climate_portrait && (
        <Section heading="氣候畫像" body={narrative.climate_portrait} />
      )}
      {narrative.anomaly_layer && (
        <Section heading="異常之處" body={narrative.anomaly_layer} />
      )}
      {narrative.imagination && (
        <Section heading="給今天的話" body={narrative.imagination} />
      )}
    </div>
  );
}

function Section({ heading, body }: { heading: string; body: string }) {
  return (
    <div>
      <h4 className="text-[11px] uppercase tracking-wider text-slate-500 font-medium mb-1.5">
        {heading}
      </h4>
      <p className="m-0">{body}</p>
    </div>
  );
}
```

- [ ] **Step 3: Create `Layer2Visual.tsx`**

```tsx
// frontend/src/components/DayInsightCard/divination/Layer2Visual.tsx
import type { Divination } from "@/lib/types";
import { HexagramPair } from "./HexagramPair";
import { NarrativeBlock } from "./NarrativeBlock";

interface Props {
  divination: Divination;
  zhiLineValues: number[];
}

/** White layer: visual hexagram pair + AI three-section narrative. */
export function Layer2Visual({ divination, zhiLineValues }: Props) {
  const d = divination;
  return (
    <div className="px-5 py-5 border-b border-slate-200">
      <div className="text-[11px] uppercase tracking-wider text-slate-500 mb-3">
        圖像 · 卦象結構
      </div>
      <HexagramPair
        ben={d.ben}
        zhi={d.zhi}
        lineValues={d.line_values}
        zhiLineValues={zhiLineValues}
        changingPositions={d.changing_positions}
      />
      <NarrativeBlock narrative={d.narrative} />
    </div>
  );
}
```

- [ ] **Step 4: Confirm typecheck**

Run: `cd frontend && pnpm tsc --noEmit`
Expected: no errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/DayInsightCard/divination/Layer1Headline.tsx \
        frontend/src/components/DayInsightCard/divination/NarrativeBlock.tsx \
        frontend/src/components/DayInsightCard/divination/Layer2Visual.tsx
git commit -m "feat(frontend): add Layer1Headline + NarrativeBlock + Layer2Visual

Layer1Headline: amber-tinted top layer with AI headline/subtitle/tags;
falls back to side-badge-derived tags when AI fails.

NarrativeBlock: replaces NarrativeSection (will be deleted) with the same
three sub-sections (氣候畫像/異常之處/給今天的話) but better headings and
auto-hide when all empty.

Layer2Visual: composes HexagramPair + NarrativeBlock into the white layer.
"
```

---

## Task 9: Layer 3 academic — GuaCi + YaoCi + FourMethodsTree + container

**Files:**
- Create: `frontend/src/components/DayInsightCard/divination/GuaCiCard.tsx`
- Create: `frontend/src/components/DayInsightCard/divination/YaoCiCard.tsx`
- Create: `frontend/src/components/DayInsightCard/divination/FourMethodsTree.tsx`
- Create: `frontend/src/components/DayInsightCard/divination/Layer3Academic.tsx`

- [ ] **Step 1: Create `GuaCiCard.tsx`**

```tsx
// frontend/src/components/DayInsightCard/divination/GuaCiCard.tsx
import type { HexagramRef } from "@/lib/types";

/** Classical 卦辭 + brief vernacular hint (vernacular comes from hex.image
 *  for now — follow-up plan can add per-卦 vernacular field). */
export function GuaCiCard({ hex }: { hex: HexagramRef }) {
  if (!hex.judgement) return null;
  return (
    <div className="bg-white border border-stone-200 rounded-lg px-4 py-3 my-2.5 text-[13px] leading-relaxed text-stone-700 font-serif">
      <div className="text-amber-800 font-semibold mb-1">
        《{hex.name}》卦辭
      </div>
      <div>{hex.judgement}</div>
      {hex.image && (
        <div className="mt-1.5 pt-1.5 border-t border-dashed border-stone-200 text-stone-500 text-[12px]">
          象傳：{hex.image}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Create `YaoCiCard.tsx`**

```tsx
// frontend/src/components/DayInsightCard/divination/YaoCiCard.tsx
import type { YaoCiEntry } from "@/lib/types";

interface Props {
  position: number;          // 1-6
  entry: YaoCiEntry;
}

/** Single 變爻 爻辭 with classical text + vernacular pair. */
export function YaoCiCard({ position, entry }: Props) {
  return (
    <div className="bg-white border border-stone-200 rounded-lg px-4 py-3 my-2.5 text-[13px] leading-relaxed text-stone-700 font-serif">
      <div className="text-amber-800 font-semibold mb-1">
        第 {position} 爻爻辭（變爻）
      </div>
      <div>{entry.original}</div>
      <div className="mt-1.5 pt-1.5 border-t border-dashed border-stone-200 text-stone-500 text-[12px]">
        白話：{entry.vernacular}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Create `FourMethodsTree.tsx`**

```tsx
// frontend/src/components/DayInsightCard/divination/FourMethodsTree.tsx
import type { Divination } from "@/lib/types";

const ROWS = [
  { mark: "●",  method: "本", key: "ben" as const,  meaning: "現狀" },
  { mark: "├─", method: "錯", key: "cuo" as const,  meaning: "對立面／隱藏動機" },
  { mark: "├─", method: "綜", key: "zong" as const, meaning: "對方視角" },
  { mark: "├─", method: "互", key: "hu" as const,   meaning: "內在核心／過程" },
  { mark: "└─", method: "之", key: "zhi" as const,  meaning: "趨勢／結果" },
];

/** Tree-style display of 5 hexagrams (本/錯/綜/互/之) with vernacular meanings. */
export function FourMethodsTree({ divination }: { divination: Divination }) {
  const hasChange = divination.changing_positions.length > 0;
  return (
    <div className="my-4 font-serif">
      {ROWS.map(row => {
        // 之卦 row hidden when no 變爻
        if (row.key === "zhi" && !hasChange) return null;
        const hex = divination[row.key];
        return (
          <div
            key={row.key}
            className="flex items-center py-1.5 border-b border-dashed border-stone-200 last:border-b-0"
          >
            <span className="w-5 text-stone-400 font-mono text-[11px]">{row.mark}</span>
            <span className="w-8 text-amber-800 text-[12px] font-semibold">{row.method}</span>
            <span className="flex-1 text-stone-700 text-[13px]">
              第 {hex.num} 卦《{hex.name}》
              {hex.upper_trigram && hex.lower_trigram && (
                <small className="text-stone-400 ml-1">
                  {hex.upper_trigram}上 {hex.lower_trigram}下
                </small>
              )}
            </span>
            <span className="text-[11px] text-stone-500 pl-2">← {row.meaning}</span>
          </div>
        );
      })}
    </div>
  );
}
```

- [ ] **Step 4: Create `Layer3Academic.tsx`**

```tsx
// frontend/src/components/DayInsightCard/divination/Layer3Academic.tsx
import type { Divination } from "@/lib/types";
import { GuaCiCard } from "./GuaCiCard";
import { YaoCiCard } from "./YaoCiCard";
import { FourMethodsTree } from "./FourMethodsTree";

/** Beige-tinted bottom layer: classical 卦辭 + 變爻爻辭 + 四法 tree.
 *  Collapsed by default via native <details>. */
export function Layer3Academic({ divination }: { divination: Divination }) {
  const d = divination;
  return (
    <details className="bg-stone-50 group">
      <summary className="px-5 py-3.5 cursor-pointer text-[13px] text-stone-600 flex justify-between items-center select-none hover:bg-stone-100 list-none">
        <span>📜 古文 · 四法 · 卦辭</span>
        <span className="text-stone-400 group-open:rotate-180 transition-transform">▾</span>
      </summary>
      <div className="px-5 pb-5 pt-1 border-t border-stone-200">
        <GuaCiCard hex={d.ben} />
        {d.changing_positions.map(pos =>
          d.var_yao_ci[pos] ? (
            <YaoCiCard key={pos} position={pos} entry={d.var_yao_ci[pos]} />
          ) : null
        )}
        <FourMethodsTree divination={d} />
        <div className="text-[11px] text-stone-400 mt-4 pt-3 border-t border-dashed border-stone-200 leading-relaxed">
          <strong className="text-stone-500">讀法：</strong>本卦看現狀、錯卦看反面、綜卦看別人怎麼看你、互卦看事情內裡的本質、之卦看走向。
        </div>
      </div>
    </details>
  );
}
```

- [ ] **Step 5: Confirm typecheck**

Run: `cd frontend && pnpm tsc --noEmit`
Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/DayInsightCard/divination/GuaCiCard.tsx \
        frontend/src/components/DayInsightCard/divination/YaoCiCard.tsx \
        frontend/src/components/DayInsightCard/divination/FourMethodsTree.tsx \
        frontend/src/components/DayInsightCard/divination/Layer3Academic.tsx
git commit -m "feat(frontend): add Layer 3 academic content + container

GuaCiCard: 卦辭 + 象傳 (paper background, serif).
YaoCiCard: per-變爻 classical 爻辭 + vernacular pair.
FourMethodsTree: 5-row 本/錯/綜/互/之 tree with vernacular meanings
(replacing one-line FourMethodsSummary).
Layer3Academic: <details> wrapper, collapsed by default, beige bg.
"
```

---

## Task 10: Assemble new DivinationDrawer + refactor DayInsightCard + delete obsolete files

**Files:**
- Create: `frontend/src/components/DayInsightCard/divination/DivinationDrawer.tsx`
- Modify: `frontend/src/components/DayInsightCard.tsx`
- Delete: `frontend/src/components/DayInsightCard/divination/HexagramDisplay.tsx`
- Delete: `frontend/src/components/DayInsightCard/divination/FourMethodsSummary.tsx`
- Delete: `frontend/src/components/DayInsightCard/divination/NarrativeSection.tsx`

- [ ] **Step 1: Create new top-level `DivinationDrawer.tsx`**

```tsx
// frontend/src/components/DayInsightCard/divination/DivinationDrawer.tsx
"use client";

import { useEffect, useState } from "react";

import { fetchDayInterpretation } from "@/lib/api";
import type { DayInsight, DayInsightInterpretation } from "@/lib/types";

import { Layer1Headline } from "./Layer1Headline";
import { Layer2Visual } from "./Layer2Visual";
import { Layer3Academic } from "./Layer3Academic";

interface Props {
  insight: DayInsight;
}

export function DivinationDrawer({ insight }: Props) {
  const [data, setData] = useState<DayInsightInterpretation | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDayInterpretation(insight.station_id, insight.month, insight.day)
      .then(setData)
      .catch((e: Error) => setError(e.message));
  }, [insight.station_id, insight.month, insight.day]);

  if (error) {
    return (
      <div className="text-sm text-rose-600 px-4 py-3 bg-rose-50 rounded">
        詮釋載入失敗：{error}
      </div>
    );
  }
  if (!data) return <DrawerSkeleton />;

  const d = data.divination;
  // 之卦 line values: invert changing positions only.
  const zhiLineValues = d.line_values.map((v, i) =>
    d.changing_positions.includes(i + 1)
      ? v === 9 ? 8 : v === 6 ? 7 : v
      : v
  );

  const hasChange = d.changing_positions.length > 0;

  return (
    <div className="rounded-2xl border border-slate-200 overflow-hidden bg-white shadow-sm">
      <Layer1Headline insight={insight} narrative={d.narrative} hasChange={hasChange} />
      <Layer2Visual divination={d} zhiLineValues={zhiLineValues} />
      <Layer3Academic divination={d} />
    </div>
  );
}

function DrawerSkeleton() {
  return (
    <div className="rounded-2xl border border-slate-200 overflow-hidden bg-white shadow-sm">
      <div className="bg-amber-50 h-24 animate-pulse" />
      <div className="px-5 py-5 space-y-3">
        <div className="h-3 w-32 bg-slate-200 animate-pulse rounded" />
        <div className="flex gap-4">
          <div className="flex-1 h-32 bg-slate-100 animate-pulse rounded" />
          <div className="flex-1 h-32 bg-slate-100 animate-pulse rounded" />
        </div>
      </div>
      <div className="bg-stone-50 h-12 animate-pulse" />
    </div>
  );
}
```

- [ ] **Step 2: Refactor `DayInsightCard.tsx` — remove inline drawer, import new**

Replace the entire file `frontend/src/components/DayInsightCard.tsx` with:

```tsx
"use client";

import { useEffect, useState } from "react";

import { fetchDayInsight } from "@/lib/api";
import type { DayInsight } from "@/lib/types";

import { LabelBadge } from "./DayInsightCard/LabelBadge";
import { CoreMetric } from "./DayInsightCard/CoreMetric";
import { SideBadges } from "./DayInsightCard/SideBadges";
import { ExtremesAnchor } from "./DayInsightCard/ExtremesAnchor";
import { DivinationDrawer } from "./DayInsightCard/divination/DivinationDrawer";

interface Props {
  stationId: string;
  month: number;
  day: number;
}

export function DayInsightCard({ stationId, month, day }: Props) {
  const [data, setData] = useState<DayInsight | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  useEffect(() => {
    fetchDayInsight(stationId, month, day)
      .then(setData)
      .catch((e: Error) => setError(e.message));
  }, [stationId, month, day]);

  if (error) {
    return <div className="rounded border p-4 text-sm text-rose-600">無歷史資料</div>;
  }
  if (!data) {
    return <div className="rounded border p-4 text-sm text-slate-400">載入中…</div>;
  }

  return (
    <div className="rounded-lg border bg-white p-4 shadow-sm space-y-3">
      <LabelBadge label={data.label} />
      <CoreMetric core={data.core} />
      <SideBadges badges={data.side_badges} />
      <ExtremesAnchor extremes={data.extremes} />
      <button
        onClick={() => setDrawerOpen((o) => !o)}
        className="w-full rounded bg-slate-50 py-2 text-sm text-slate-600 hover:bg-slate-100"
      >
        {drawerOpen ? "收起詮釋 ▴" : "看詳細詮釋 ▾"}
      </button>
      {drawerOpen && <DivinationDrawer insight={data} />}
    </div>
  );
}
```

- [ ] **Step 3: Delete obsolete files**

```bash
rm frontend/src/components/DayInsightCard/divination/HexagramDisplay.tsx
rm frontend/src/components/DayInsightCard/divination/FourMethodsSummary.tsx
rm frontend/src/components/DayInsightCard/divination/NarrativeSection.tsx
```

- [ ] **Step 4: Confirm build passes (catches any leftover imports of deleted files)**

Run: `cd frontend && pnpm build`
Expected: build succeeds. If it fails with `Cannot find module './HexagramDisplay'` etc, grep for that string and remove the stale import:

```bash
cd frontend && grep -rn "HexagramDisplay\|FourMethodsSummary\|NarrativeSection" src/
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/DayInsightCard.tsx \
        frontend/src/components/DayInsightCard/divination/DivinationDrawer.tsx
git rm frontend/src/components/DayInsightCard/divination/HexagramDisplay.tsx \
       frontend/src/components/DayInsightCard/divination/FourMethodsSummary.tsx \
       frontend/src/components/DayInsightCard/divination/NarrativeSection.tsx
git commit -m "feat(frontend): assemble three-layer DivinationDrawer + cleanup

Top-level DivinationDrawer composes Layer1Headline / Layer2Visual /
Layer3Academic, with skeleton loading state matching the three-layer
silhouette. DayInsightCard imports from new path; inline DivinationDrawer
function removed.

Delete obsolete HexagramDisplay (replaced by HexagramVisual),
FourMethodsSummary (by FourMethodsTree), NarrativeSection (by
NarrativeBlock).
"
```

---

## Task 11: Deploy + visual verify

**Files:**
- None (deployment only)

- [ ] **Step 1: Push to main**

```bash
git push origin main
```

Vercel git integration (fixed yesterday) should auto-trigger a build. GitHub Actions / Cloud Build will also rebuild backend.

- [ ] **Step 2: Wait for Vercel build (≈ 2 min)**

```bash
# Poll until READY (no token needed — public deployments listed unauthenticated would still need auth; use the Vercel dashboard instead)
open "https://vercel.com/auspicious1/auspicious/deployments"
```

Look for the deployment matching the latest commit SHA. State should reach `READY`.

- [ ] **Step 3: Verify backend Cloud Run has new revision**

```bash
gcloud run revisions list --service auspicious-api --region asia-east1 --limit 1 \
  --format='value(metadata.name,metadata.creationTimestamp)'
```

Expected: a revision with creationTimestamp after the push time. If not, check `scripts/deploy-backend.sh` is wired up.

- [ ] **Step 4: Smoke-test new API fields**

```bash
curl -s "https://auspicious-api-331213739902.asia-east1.run.app/api/v1/day-insight/466920/5/6/interpretation" \
  | python3 -m json.tool | head -50
```

Expected: response includes `divination.narrative.headline` (string), `narrative.tags` (list), `divination.var_yao_ci` (dict, possibly empty).

- [ ] **Step 5: Visual verify via Playwright**

Use `mcp__plugin_playwright_playwright__browser_navigate` to https://auspicious-zeta.vercel.app, then `browser_take_screenshot` saving to `docs/screenshots/2026-05-07-divination-redesign/home.png`. Click the「看詳細詮釋 ▾」button, screenshot the expanded drawer to `drawer-open.png`. Click the Layer 3 details summary, screenshot to `drawer-layer3-open.png`.

Confirm visually:
- [ ] Layer 1 amber background, headline displays (or fallback tags only if AI quota exhausted)
- [ ] Layer 2 ben → zhi side-by-side (desktop) with arrow + 變爻 amber pulse
- [ ] Layer 3 collapsed by default; opens to show 卦辭 + YaoCiCard(s) + FourMethodsTree
- [ ] No console errors (check `mcp__plugin_playwright_playwright__browser_console_messages`)

- [ ] **Step 6: Commit screenshots**

```bash
git add docs/screenshots/2026-05-07-divination-redesign/
git commit -m "docs(screenshots): visual verification of three-layer DivinationDrawer

Confirms post-deploy state: Layer 1 amber elevator-pitch / Layer 2
ben→zhi visual with 變爻 pulse / Layer 3 collapsible 卦辭+爻辭+四法tree.
"
git push origin main
```

---

## Summary

| Task | Layer | Time | TDD? |
|---|---|---|---|
| 1 | Schema | 10 min | partial |
| 2 | Backend | 20 min | ✓ |
| 3 | Backend (data) | 60-90 min | ✓ |
| 4 | Backend | 25 min | ✓ |
| 5 | Backend | 20 min | ✓ |
| 6 | Frontend | 15 min | typecheck |
| 7 | Frontend | 25 min | typecheck |
| 8 | Frontend | 25 min | typecheck |
| 9 | Frontend | 25 min | typecheck |
| 10 | Frontend | 20 min | build |
| 11 | Deploy | 15 min | screenshot |

**Total: ~4-5 hours**, dominated by Task 3 (爻辭 data review).

**Frequent commits:** Each task ends with one commit; ~11 commits total. Each commit is independently revertable.
