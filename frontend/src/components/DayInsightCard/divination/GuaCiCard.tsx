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
