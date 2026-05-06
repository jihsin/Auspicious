import type { DayInsightExtremes } from "@/lib/types";

export function ExtremesAnchor({ extremes }: { extremes: DayInsightExtremes }) {
  if (!extremes.wettest && !extremes.driest) return null;
  return (
    <div className="text-xs text-slate-500 space-y-0.5">
      {extremes.wettest && (
        <div>最濕：{extremes.wettest.year} / {extremes.wettest.value.toFixed(1)} mm</div>
      )}
      {extremes.driest && (
        <div>最乾：{extremes.driest.year} / {extremes.driest.value.toFixed(1)} mm</div>
      )}
    </div>
  );
}
