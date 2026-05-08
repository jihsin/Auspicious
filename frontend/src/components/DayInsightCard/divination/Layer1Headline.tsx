// frontend/src/components/DayInsightCard/divination/Layer1Headline.tsx
"use client";

import { useState } from "react";
import type { DayInsight, DivinationNarrative, HexagramRef } from "@/lib/types";
import { getImagery } from "./imagery";

interface Props {
  insight: DayInsight;
  narrative: DivinationNarrative;
  ben: HexagramRef;
  hasChange: boolean;
}

/** Top amber-tinted layer.
 *  Layout: 80×80 trigram thumbnail (left) + content column (right).
 *
 *  Content column renders top-to-bottom:
 *  - Date row (always)
 *  - AI headline (only if narrative.headline non-empty)
 *  - AI subtitle (only if narrative.subtitle non-empty)
 *  - weather_persona (always if ben.weather_persona non-empty — deterministic fallback content)
 *  - Tags row (AI tags or side-badges-derived fallback)
 */
export function Layer1Headline({ insight, narrative, ben, hasChange }: Props) {
  const fallbackTags = getFallbackTags(insight, hasChange);
  // Defensive: backend may transitionally serve old JSON without `tags`
  // during a Vercel-vs-Cloud-Run deploy gap. `?? []` guards the .length call.
  const aiTags = narrative.tags ?? [];
  const tags = aiTags.length > 0 ? aiTags : fallbackTags;
  const imagery = getImagery(ben.upper_trigram);

  return (
    <div className="bg-gradient-to-br from-amber-50 to-amber-100 border-b border-amber-200 px-5 py-5">
      <div className="flex gap-4 items-start">
        <Thumbnail imagery={imagery} />
        <div className="flex-1 min-w-0">
          <div className="flex justify-between items-start mb-2 text-[11px] uppercase tracking-wider text-amber-700">
            <span>{insight.month}月{insight.day}日 · {insight.meta.years_analyzed}年統計</span>
            {hasChange && <span>本卦 ▸ 之卦</span>}
          </div>
          {narrative.headline && (
            <h3 className="text-2xl font-bold text-amber-900 mb-1 leading-tight">
              {narrative.headline}
            </h3>
          )}
          {narrative.subtitle && (
            <p className="text-sm text-amber-800 mb-2 leading-relaxed">
              {narrative.subtitle}
            </p>
          )}
          {ben.weather_persona && (
            <p className="text-[13px] text-amber-900 mb-3 leading-relaxed">
              {ben.weather_persona}
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
      </div>
    </div>
  );
}

function Thumbnail({ imagery }: { imagery: ReturnType<typeof getImagery> }) {
  const [imgFailed, setImgFailed] = useState(false);
  const baseClass = "w-20 h-20 rounded-lg flex-shrink-0 overflow-hidden shadow-sm ring-1 ring-amber-200/40";

  if (!imagery.src || imgFailed) {
    return (
      <div
        className={`${baseClass} bg-gradient-to-br ${imagery.gradient}`}
        role="img"
        aria-label={imagery.alt || "卦象意象"}
      />
    );
  }
  return (
    <img
      src={imagery.src}
      alt={imagery.alt}
      className={`${baseClass} object-cover`}
      onError={() => setImgFailed(true)}
    />
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
