// frontend/src/components/DayInsightCard/divination/Layer1Headline.tsx
import type { DayInsight, DivinationNarrative } from "@/lib/types";

interface Props {
  insight: DayInsight;
  narrative: DivinationNarrative;
  hasChange: boolean;
}

/** Top amber-tinted layer. Hides headline/subtitle when AI failed; tags
 *  fall back to deterministic anomaly-direction snippets. */
export function Layer1Headline({ insight, narrative, hasChange }: Props) {
  const fallbackTags = getFallbackTags(insight, hasChange);
  // Defensive: backend may transitionally serve old JSON without `tags`
  // during a Vercel-vs-Cloud-Run deploy gap. `?? []` guards the .length call.
  const aiTags = narrative.tags ?? [];
  const tags = aiTags.length > 0 ? aiTags : fallbackTags;

  return (
    <div className="bg-gradient-to-br from-amber-50 to-amber-100 border-b border-amber-200 px-5 py-5">
      <div className="flex justify-between items-start mb-2 text-[11px] uppercase tracking-wider text-amber-700">
        <span>{insight.month}月{insight.day}日 · {insight.meta.years_analyzed}年統計</span>
        {hasChange && <span>本卦 ▸ 之卦</span>}
      </div>
      {narrative.headline && (
        <h3 className="text-2xl font-bold text-amber-900 mb-1">
          {narrative.headline}
        </h3>
      )}
      {narrative.subtitle && (
        <p className="text-sm text-amber-800 mb-3 leading-relaxed">
          {narrative.subtitle}
        </p>
      )}
      <div className="flex flex-wrap gap-1.5">
        {tags.map((t, i) => (
          <span
            key={`${t}-${i}`}
            className="bg-amber-900/10 text-amber-900 px-2.5 py-1 rounded-full text-xs font-medium"
          >
            {t}
          </span>
        ))}
      </div>
    </div>
  );
}

function getFallbackTags(insight: DayInsight, hasChange: boolean): string[] {
  // Deterministic anomaly-direction snippets when AI tags missing.
  const tags: string[] = [];
  for (const b of insight.side_badges.slice(0, 2)) {
    const noun = b.metric === "temp_avg" ? "氣溫" : "濕度";
    const dir = b.direction === "above" ? "偏高" : "偏低";
    tags.push(`${noun}${dir}`);
  }
  tags.push(hasChange ? "有變動" : "六爻皆靜");
  return tags;
}
