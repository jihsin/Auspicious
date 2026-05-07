// frontend/src/components/DayInsightCard/divination/NarrativeBlock.tsx
import type { DivinationNarrative } from "@/lib/types";

/** Three short paragraphs (氣候畫像 / 異常之處 / 給今天的話).
 *  Hidden entirely when all three are empty. */
export function NarrativeBlock({ narrative }: { narrative: DivinationNarrative }) {
  const empty =
    !narrative.climate_portrait &&
    !narrative.anomaly_layer &&
    !narrative.imagination;
  if (empty) return null;

  return (
    <div className="mt-5 pt-4 border-t border-dashed border-slate-200 space-y-3 text-[13.5px] leading-relaxed text-slate-700">
      {narrative.climate_portrait && (
        <Section heading="氣候畫像" body={narrative.climate_portrait} />
      )}
      {narrative.anomaly_layer && (
        <Section heading="異常之處" body={narrative.anomaly_layer} />
      )}
      {narrative.imagination && (
        <Section heading="給今天的話" body={narrative.imagination} />
      )}
    </div>
  );
}

function Section({ heading, body }: { heading: string; body: string }) {
  return (
    <div>
      <h4 className="text-[11px] uppercase tracking-wider text-slate-500 font-medium mb-1.5">
        {heading}
      </h4>
      <p className="m-0">{body}</p>
    </div>
  );
}
