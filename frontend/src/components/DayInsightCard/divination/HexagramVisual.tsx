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
