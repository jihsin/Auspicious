import type { HexagramRef } from "@/lib/types";

interface Props {
  cuo: HexagramRef;
  zong: HexagramRef;
  hu: HexagramRef;
}

export function FourMethodsSummary({ cuo, zong, hu }: Props) {
  return (
    <div className="text-xs text-slate-600">
      <span className="text-slate-400">四法速覽：</span>
      錯：第 {cuo.num} 卦《{cuo.name}》（對立面）
      <span className="mx-1 text-slate-300">｜</span>
      綜：第 {zong.num} 卦《{zong.name}》（半年對位）
      <span className="mx-1 text-slate-300">｜</span>
      互：第 {hu.num} 卦《{hu.name}》（內在核心）
    </div>
  );
}
