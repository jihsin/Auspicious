"use client";

import { useEffect, useState } from "react";

import { fetchDayInsight, fetchDayInterpretation } from "@/lib/api";
import type { DayInsight } from "@/lib/types";
import type { DayInsightInterpretation } from "@/lib/types";

import { LabelBadge } from "./DayInsightCard/LabelBadge";
import { CoreMetric } from "./DayInsightCard/CoreMetric";
import { SideBadges } from "./DayInsightCard/SideBadges";
import { ExtremesAnchor } from "./DayInsightCard/ExtremesAnchor";
import { HexagramDisplay } from "./DayInsightCard/divination/HexagramDisplay";
import { FourMethodsSummary } from "./DayInsightCard/divination/FourMethodsSummary";
import { NarrativeSection } from "./DayInsightCard/divination/NarrativeSection";

interface Props {
  stationId: string;
  month: number;
  day: number;
}

function DivinationDrawer({ stationId, month, day }: Props) {
  const [data, setData] = useState<DayInsightInterpretation | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDayInterpretation(stationId, month, day)
      .then(setData)
      .catch((e: Error) => setError(e.message));
  }, [stationId, month, day]);

  if (error) {
    return (
      <div className="text-sm text-rose-600">詮釋載入失敗：{error}</div>
    );
  }
  if (!data) {
    return <div className="text-sm text-slate-400">詮釋計算中…</div>;
  }

  const d = data.divination;

  // 之卦的 line values：把變爻反向
  // 老陰(6)→少陽(7), 老陽(9)→少陰(8); 不變爻保留
  const zhiLineValues = d.line_values.map((v, i) => {
    if (!d.changing_positions.includes(i + 1)) return v;
    if (v === 9) return 8;
    if (v === 6) return 7;
    return v;
  });

  return (
    <div className="space-y-4 rounded bg-slate-50 p-3">
      <HexagramDisplay
        hex={d.ben}
        lineValues={d.line_values}
        changingPositions={d.changing_positions}
        caption="本卦：氣候畫像"
      />
      {d.changing_positions.length > 0 && (
        <HexagramDisplay
          hex={d.zhi}
          lineValues={zhiLineValues}
          changingPositions={[]}
          caption="之卦：趨勢"
        />
      )}
      <FourMethodsSummary cuo={d.cuo} zong={d.zong} hu={d.hu} />
      <NarrativeSection narrative={d.narrative} />
    </div>
  );
}

export function DayInsightCard({ stationId, month, day }: Props) {
  const [data, setData] = useState<DayInsight | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  useEffect(() => {
    fetchDayInsight(stationId, month, day)
      .then(setData)
      .catch((e: Error) => setError(e.message));
  }, [stationId, month, day]);

  if (error) {
    return <div className="rounded border p-4 text-sm text-rose-600">無歷史資料</div>;
  }
  if (!data) {
    return <div className="rounded border p-4 text-sm text-slate-400">載入中…</div>;
  }

  return (
    <div className="rounded-lg border bg-white p-4 shadow-sm space-y-3">
      <LabelBadge label={data.label} />
      <CoreMetric core={data.core} />
      <SideBadges badges={data.side_badges} />
      <ExtremesAnchor extremes={data.extremes} />
      <button
        onClick={() => setDrawerOpen((o) => !o)}
        className="w-full rounded bg-slate-50 py-2 text-sm text-slate-600 hover:bg-slate-100"
      >
        {drawerOpen ? "收起詮釋 ▴" : "看詳細詮釋 ▾"}
      </button>
      {drawerOpen && (
        <DivinationDrawer stationId={stationId} month={month} day={day} />
      )}
    </div>
  );
}
