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
