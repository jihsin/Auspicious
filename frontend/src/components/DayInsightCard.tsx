"use client";

import { useEffect, useState } from "react";

import { fetchDayInsight } from "@/lib/api";
import type { DayInsight } from "@/lib/types";

import { LabelBadge } from "./DayInsightCard/LabelBadge";
import { CoreMetric } from "./DayInsightCard/CoreMetric";
import { SideBadges } from "./DayInsightCard/SideBadges";
import { ExtremesAnchor } from "./DayInsightCard/ExtremesAnchor";
import { DivinationDrawer } from "./DayInsightCard/divination/DivinationDrawer";

interface Props {
  stationId: string;
  month: number;
  day: number;
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
      {drawerOpen && <DivinationDrawer insight={data} />}
    </div>
  );
}
