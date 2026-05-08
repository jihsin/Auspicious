"use client";

import { useEffect, useState } from "react";

import { fetchDayInterpretation } from "@/lib/api";
import type { DayInsight, DayInsightInterpretation } from "@/lib/types";

import { Layer1Headline } from "./Layer1Headline";
import { Layer2Visual } from "./Layer2Visual";
import { Layer3Academic } from "./Layer3Academic";

interface Props {
  insight: DayInsight;
}

export function DivinationDrawer({ insight }: Props) {
  const [data, setData] = useState<DayInsightInterpretation | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDayInterpretation(insight.station_id, insight.month, insight.day)
      .then(setData)
      .catch((e: Error) => setError(e.message));
  }, [insight.station_id, insight.month, insight.day]);

  if (error) {
    return (
      <div className="text-sm text-rose-600 px-4 py-3 bg-rose-50 rounded">
        詮釋載入失敗：{error}
      </div>
    );
  }
  if (!data) return <DrawerSkeleton />;

  const d = data.divination;
  // 之卦 line values: invert changing positions only.
  const zhiLineValues = d.line_values.map((v, i) =>
    d.changing_positions.includes(i + 1)
      ? v === 9 ? 8 : v === 6 ? 7 : v
      : v
  );

  const hasChange = d.changing_positions.length > 0;

  return (
    <div className="rounded-2xl border border-slate-200 overflow-hidden bg-white shadow-sm">
      <Layer1Headline insight={insight} narrative={d.narrative} ben={d.ben} hasChange={hasChange} />
      <Layer2Visual divination={d} zhiLineValues={zhiLineValues} />
      <Layer3Academic divination={d} />
    </div>
  );
}

function DrawerSkeleton() {
  return (
    <div className="rounded-2xl border border-slate-200 overflow-hidden bg-white shadow-sm">
      <div className="bg-amber-50 h-24 animate-pulse" />
      <div className="px-5 py-5 space-y-3">
        <div className="h-3 w-32 bg-slate-200 animate-pulse rounded" />
        <div className="flex gap-4">
          <div className="flex-1 h-32 bg-slate-100 animate-pulse rounded" />
          <div className="flex-1 h-32 bg-slate-100 animate-pulse rounded" />
        </div>
      </div>
      <div className="bg-stone-50 h-12 animate-pulse" />
    </div>
  );
}
