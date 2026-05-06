import type { DayInsightSideBadge } from "@/lib/types";

export function SideBadges({ badges }: { badges: DayInsightSideBadge[] }) {
  if (badges.length === 0) return null;
  return (
    <div className="mt-2 flex flex-wrap gap-2">
      {badges.map((b) => (
        <span
          key={b.metric}
          className={`inline-flex items-center rounded px-2 py-0.5 text-xs ${
            b.direction === "above" ? "bg-rose-50 text-rose-700" : "bg-sky-50 text-sky-700"
          }`}
        >
          ⚠️ {b.label}
        </span>
      ))}
    </div>
  );
}
