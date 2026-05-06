import type { DayInsightCore } from "@/lib/types";

export function CoreMetric({ core }: { core: DayInsightCore }) {
  const pct = (core.value * 100).toFixed(0);
  const monthPct = (core.anomaly_month * 100).toFixed(1);
  const yearArrow = core.anomaly_year > 0.01 ? "↑" : core.anomaly_year < -0.01 ? "↓" : "";
  const yearColor = core.anomaly_year > 0.01 ? "text-rose-600"
                  : core.anomaly_year < -0.01 ? "text-sky-600" : "text-slate-500";

  return (
    <div>
      <div className="text-sm text-slate-500">降雨機率</div>
      <div className="text-4xl font-bold tabular-nums">{pct}%</div>
      <div className="mt-1 text-sm">
        <span className={yearColor}>
          {yearArrow}{Math.abs(core.anomaly_year * 100).toFixed(1)}% vs 年均
        </span>
        <span className="mx-2 text-slate-300">│</span>
        <span className="text-slate-600">
          {core.anomaly_month >= 0 ? "+" : ""}{monthPct}% vs 同月
        </span>
      </div>
    </div>
  );
}
