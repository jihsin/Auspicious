// frontend/src/components/LunarCard.tsx
"use client";

import { LunarDateInfo, YiJiInfo } from "@/lib/types";

interface LunarCardProps {
  lunarDate: LunarDateInfo;
  yiJi: YiJiInfo;
  jieqi?: string | null;
}

export default function LunarCard({ lunarDate, yiJi, jieqi }: LunarCardProps) {
  return (
    <div className="bg-gradient-to-br from-red-50 to-amber-50 rounded-xl p-6 shadow-lg border border-red-100">
      {/* 農曆日期 */}
      <div className="text-center mb-6">
        <div className="text-3xl font-bold text-red-800 mb-1">
          {lunarDate.month_cn}{lunarDate.day_cn}
        </div>
        <div className="text-sm text-red-600">
          {lunarDate.year_cn} {lunarDate.生肖}年
        </div>
        <div className="text-xs text-amber-700 mt-1">
          {lunarDate.干支年}年 {lunarDate.干支月}月 {lunarDate.干支日}日
        </div>
      </div>

      {/* 節氣 */}
      {jieqi && (
        <div className="text-center mb-4 py-2 bg-amber-100 rounded-lg">
          <span className="text-amber-800 font-semibold">{jieqi}</span>
        </div>
      )}

      {/* 宜忌 */}
      <div className="grid grid-cols-2 gap-4">
        {/* 宜 */}
        <div className="bg-white/60 rounded-lg p-3">
          <div className="text-green-700 font-semibold mb-2 flex items-center gap-1">
            <span className="text-lg">&#x2713;</span> 宜
          </div>
          <div className="flex flex-wrap gap-1">
            {yiJi.yi.slice(0, 6).map((item, i) => (
              <span
                key={i}
                className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded"
              >
                {item}
              </span>
            ))}
          </div>
        </div>

        {/* 忌 */}
        <div className="bg-white/60 rounded-lg p-3">
          <div className="text-red-700 font-semibold mb-2 flex items-center gap-1">
            <span className="text-lg">&#x2717;</span> 忌
          </div>
          <div className="flex flex-wrap gap-1">
            {yiJi.ji.slice(0, 6).map((item, i) => (
              <span
                key={i}
                className="px-2 py-0.5 bg-red-100 text-red-700 text-xs rounded"
              >
                {item}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
