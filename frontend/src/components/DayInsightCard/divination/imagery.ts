// 8 trigram natural-imagery assets.
// Maps each trigram (天/地/水/風/雷/火/澤/山) to:
//   - A static image path under /hexagram/
//   - A CSS gradient fallback (used while image loads or if it 404s)

interface TrigramImagery {
  /** Path served from frontend/public/hexagram/ */
  src: string;
  /** Tailwind gradient class string used as fallback background */
  gradient: string;
  /** Short English alt for the photo */
  alt: string;
}

const IMAGERY: Record<string, TrigramImagery> = {
  乾: { src: "/hexagram/heaven.svg",   gradient: "from-sky-200 to-sky-400",         alt: "Open sky" },
  坤: { src: "/hexagram/earth.svg",    gradient: "from-stone-300 to-stone-500",     alt: "Open earth" },
  坎: { src: "/hexagram/water.svg",    gradient: "from-blue-300 to-blue-600",       alt: "Flowing water" },
  巽: { src: "/hexagram/wind.svg",     gradient: "from-emerald-200 to-teal-400",    alt: "Wind through grass" },
  震: { src: "/hexagram/thunder.svg",  gradient: "from-indigo-400 to-purple-700",   alt: "Thunder cloud" },
  離: { src: "/hexagram/fire.svg",     gradient: "from-orange-300 to-rose-500",     alt: "Bright fire" },
  兌: { src: "/hexagram/lake.svg",     gradient: "from-cyan-200 to-cyan-500",       alt: "Still lake" },
  艮: { src: "/hexagram/mountain.svg", gradient: "from-stone-400 to-stone-700",     alt: "Quiet mountain" },
};

const FALLBACK: TrigramImagery = {
  src: "",
  gradient: "from-slate-200 to-slate-400",
  alt: "",
};

/** Get imagery keyed by trigram name (e.g., "乾"). Falls back to neutral gray
 *  when the trigram is unknown or undefined. */
export function getImagery(trigram: string | null | undefined): TrigramImagery {
  if (!trigram) return FALLBACK;
  return IMAGERY[trigram] ?? FALLBACK;
}

export type { TrigramImagery };
