import type { HexagramRef } from "@/lib/types";

const lineGlyph = (value: number, isChanging: boolean): string => {
  // value: 6=老陰, 7=少陽, 8=少陰, 9=老陽
  const yang = value === 7 || value === 9;
  const base = yang ? "─────" : "── ──";
  return isChanging ? `${base}  ★` : base;
};

interface Props {
  hex: HexagramRef;
  lineValues: number[];
  changingPositions: number[];
  caption?: string;
}

export function HexagramDisplay({ hex, lineValues, changingPositions, caption }: Props) {
  // Render top-to-bottom (line 6 first)
  const rows = [...lineValues].reverse();
  const positions = [6, 5, 4, 3, 2, 1];

  return (
    <div>
      <div className="mb-1 text-base font-semibold">
        第 {hex.num} 卦《{hex.name}》
        {hex.upper_trigram && hex.lower_trigram && (
          <span className="ml-2 text-sm text-slate-500">
            {hex.upper_trigram}上 {hex.lower_trigram}下
          </span>
        )}
      </div>
      <pre className="font-mono text-sm leading-tight text-slate-700">
        {rows.map((v, i) => {
          const pos = positions[i];
          const changing = changingPositions.includes(pos);
          return <div key={pos}>{lineGlyph(v, changing)}</div>;
        })}
      </pre>
      {hex.judgement && <div className="mt-1 text-xs text-slate-600">卦辭：{hex.judgement}</div>}
      {caption && <div className="mt-1 text-xs text-slate-400">{caption}</div>}
    </div>
  );
}
