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
            role="img"
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
