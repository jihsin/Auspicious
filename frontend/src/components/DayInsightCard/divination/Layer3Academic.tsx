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
