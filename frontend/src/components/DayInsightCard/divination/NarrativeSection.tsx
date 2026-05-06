import type { DivinationNarrative } from "@/lib/types";

export function NarrativeSection({ narrative }: { narrative: DivinationNarrative }) {
  const empty =
    !narrative.climate_portrait &&
    !narrative.anomaly_layer &&
    !narrative.imagination;
  if (empty) {
    return (
      <div className="text-sm text-slate-400 italic">
        詮釋暫時無法產生，請稍後再試。
      </div>
    );
  }
  return (
    <div className="space-y-2 text-sm leading-relaxed text-slate-700">
      {narrative.climate_portrait && <p>{narrative.climate_portrait}</p>}
      {narrative.anomaly_layer && <p>{narrative.anomaly_layer}</p>}
      {narrative.imagination && <p>{narrative.imagination}</p>}
    </div>
  );
}
