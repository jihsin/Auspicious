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
