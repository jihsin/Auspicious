import type { DayInsightLabel } from "@/lib/types";

const COLOR: Record<NonNullable<DayInsightLabel["category"]>, string> = {
  seasonal: "bg-emerald-100 text-emerald-800",
  anomaly: "bg-amber-100 text-amber-800",
  record: "bg-rose-100 text-rose-800",
  solar_term: "bg-sky-100 text-sky-800",
};

export function LabelBadge({ label }: { label: DayInsightLabel }) {
  if (!label.text || !label.category) return null;
  return (
    <div className={`inline-block rounded-full px-3 py-1 text-sm font-medium ${COLOR[label.category]}`}>
      {label.text}
    </div>
  );
}
