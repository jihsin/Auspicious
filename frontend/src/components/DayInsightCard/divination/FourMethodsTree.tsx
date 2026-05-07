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
