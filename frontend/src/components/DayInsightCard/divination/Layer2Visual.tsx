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
