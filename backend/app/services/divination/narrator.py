"""Three-section narrative for the divination drawer.

Uses Gemini via the existing ai_engine client. Falls back to empty
strings if the AI is unavailable or errors — UI displays "詮釋暫時無法產生".
"""

from google.genai import types

from app.services.ai_engine import GENERATION_CONFIG, MODEL_NAME, get_client


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
段六【標籤】3 個 ≤4 字的關鍵字，用半形逗號分隔 — 範例：偏涼,偏乾,二爻變

風格：段一至段三古典文學語感、可入詩；段四至段六完全白話、現代生活語感。
"""


def _call_gemini(prompt: str) -> str | None:
    """Indirection so tests can patch this single call."""
    client = get_client()
    if client is None:
        return None
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=GENERATION_CONFIG["temperature"],
            top_p=GENERATION_CONFIG["top_p"],
            top_k=GENERATION_CONFIG["top_k"],
            max_output_tokens=GENERATION_CONFIG["max_output_tokens"],
        ),
    )
    return response.text or None


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
                    out[k] = [t.strip("「」 ") for t in content.split(",") if t.strip("「」 ")]
                else:
                    out[k] = content
                break
    return out


def narrate(*, station_name, month, day, ben, zhi, cuo, zong, hu,
            changing_positions, anomalies, solar_term) -> dict:
    """Generate a 6-section narrative. Returns dict with empty strings on failure."""
    prompt = PROMPT_TEMPLATE.format(
        station_name=station_name, month=month, day=day, solar_term=solar_term or "—",
        ben_num=ben["num"], ben_name=ben["name"],
        zhi_num=zhi["num"], zhi_name=zhi["name"],
        cuo_num=cuo["num"], cuo_name=cuo["name"],
        zong_num=zong["num"], zong_name=zong["name"],
        hu_num=hu["num"], hu_name=hu["name"],
        changing_positions=changing_positions if changing_positions else "無",
        t_anom=anomalies.get("temp_diff", 0),
        h_anom=anomalies.get("humidity_diff", 0),
        p_anom=anomalies.get("precip_diff_pct", 0),
    )
    try:
        raw = _call_gemini(prompt)
    except Exception:
        return {"climate_portrait": "", "anomaly_layer": "", "imagination": "",
                "headline": "", "subtitle": "", "tags": []}

    return _parse_sections(raw)
