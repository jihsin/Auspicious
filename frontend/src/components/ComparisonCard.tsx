// frontend/src/components/ComparisonCard.tsx
"use client";

import { StationWeatherComparison, LunarDateInfo } from "@/lib/types";

interface ComparisonCardProps {
  date: string;
  stations: StationWeatherComparison[];
  bestStation: string | null;
  lunarDate?: LunarDateInfo;
  jieqi?: string | null;
}

function getRankColor(rank: number | null): string {
  if (rank === 1) return "bg-yellow-100 border-yellow-400 text-yellow-800";
  if (rank === 2) return "bg-gray-100 border-gray-300 text-gray-700";
  if (rank === 3) return "bg-amber-50 border-amber-300 text-amber-700";
  return "bg-white border-gray-200 text-gray-600";
}

function getRankEmoji(rank: number | null): string {
  if (rank === 1) return "🥇";
  if (rank === 2) return "🥈";
  if (rank === 3) return "🥉";
  return `#${rank}`;
}

export function ComparisonCard({
  date,
  stations,
  bestStation,
  lunarDate,
  jieqi,
}: ComparisonCardProps) {
  if (stations.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-lg p-6 text-center text-gray-500">
        沒有找到站點資料
      </div>
    );
  }

  // 格式化日期顯示
  const [month, day] = date.split("-");
  const dateDisplay = `${parseInt(month)} 月 ${parseInt(day)} 日`;

  return (
    <div className="bg-white rounded-xl shadow-lg overflow-hidden">
      {/* 標題 */}
      <div className="bg-gradient-to-r from-green-500 to-teal-500 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-white font-semibold text-lg">
              {dateDisplay} 站點天氣比較
            </h3>
            {lunarDate && (
              <p className="text-green-100 text-sm">
                農曆 {lunarDate.month_cn}{lunarDate.day_cn}
                {jieqi && jieqi !== "無" && ` · ${jieqi}`}
              </p>
            )}
          </div>
          <div className="text-white text-sm">
            共 {stations.length} 站
          </div>
        </div>
      </div>

      {/* 比較列表 */}
      <div className="divide-y divide-gray-100">
        {stations.map((comp) => (
          <div
            key={comp.station.station_id}
            className={`px-6 py-4 border-l-4 ${getRankColor(comp.rank)}`}
          >
            <div className="flex items-start justify-between">
              {/* 左側：排名和站點資訊 */}
              <div className="flex items-center gap-4">
                <span className="text-2xl">
                  {getRankEmoji(comp.rank)}
                </span>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-lg font-semibold text-gray-800">
                      {comp.station.name}
                    </span>
                    <span className="text-sm text-gray-500">
                      {comp.station.city}
                    </span>
                    {comp.station.station_id === bestStation && (
                      <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full font-medium">
                        最佳
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-400 mt-1">
                    {comp.years_analyzed} 年歷史資料
                  </p>
                </div>
              </div>

              {/* 右側：晴天率 */}
              <div className="text-right">
                <div className="text-2xl font-bold text-yellow-600">
                  {comp.sunny_rate !== null
                    ? `${(comp.sunny_rate * 100).toFixed(0)}%`
                    : "N/A"}
                </div>
                <div className="text-xs text-gray-500">晴天率</div>
              </div>
            </div>

            {/* 天氣數據 */}
            <div className="flex items-center gap-6 mt-3 text-sm">
              {comp.temp_avg !== null && (
                <div className="flex items-center gap-1">
                  <span className="text-orange-500">🌡️</span>
                  <span className="text-gray-600">
                    {comp.temp_avg.toFixed(1)}°C
                  </span>
                  {comp.temp_max !== null && comp.temp_min !== null && (
                    <span className="text-gray-400 text-xs">
                      ({comp.temp_min.toFixed(0)}~{comp.temp_max.toFixed(0)})
                    </span>
                  )}
                </div>
              )}
              {comp.precip_prob !== null && (
                <div className="flex items-center gap-1">
                  <span className="text-blue-500">🌧️</span>
                  <span className="text-gray-600">
                    降雨 {(comp.precip_prob * 100).toFixed(0)}%
                  </span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* 底部提示 */}
      <div className="bg-gray-50 px-6 py-3 text-center text-xs text-gray-500">
        排名依據歷史晴天率，實際天氣可能有所不同
      </div>
    </div>
  );
}
