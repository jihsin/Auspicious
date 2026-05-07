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
