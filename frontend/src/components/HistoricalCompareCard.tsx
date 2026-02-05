// frontend/src/components/HistoricalCompareCard.tsx
"use client";

import {
  HistoricalComparison,
  RealtimeWeatherInfo,
  StationInfo,
  LunarDateInfo,
} from "@/lib/types";

interface HistoricalCompareCardProps {
  station: StationInfo;
  date: string;
  realtime: RealtimeWeatherInfo | null;
  comparisons: HistoricalComparison[];
  summary: string;
  lunarDate?: LunarDateInfo;
  jieqi?: string | null;
}

function getStatusColor(status: string): string {
  switch (status) {
    case "extreme":
      return "bg-red-100 text-red-700 border-red-300";
    case "above_normal":
      return "bg-orange-100 text-orange-700 border-orange-300";
    case "below_normal":
      return "bg-blue-100 text-blue-700 border-blue-300";
    default:
      return "bg-green-100 text-green-700 border-green-300";
  }
}

function getStatusLabel(status: string): string {
  switch (status) {
    case "extreme":
      return "異常";
    case "above_normal":
      return "偏高";
    case "below_normal":
      return "偏低";
    default:
      return "正常";
  }
}

function getDifferenceIcon(diff: number | null): string {
  if (diff === null) return "";
  if (diff > 0) return "↑";
  if (diff < 0) return "↓";
  return "→";
}

export function HistoricalCompareCard({
  station,
  date,
  realtime,
  comparisons,
  summary,
  lunarDate,
  jieqi,
}: HistoricalCompareCardProps) {
  // 格式化日期顯示
  const [month, day] = date.split("-");
  const dateDisplay = `${parseInt(month)} 月 ${parseInt(day)} 日`;

  return (
    <div className="bg-white rounded-xl shadow-lg overflow-hidden">
      {/* 標題 */}
      <div className="bg-gradient-to-r from-indigo-500 to-purple-500 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-white font-semibold text-lg">
              {station.name} · {dateDisplay}
            </h3>
            {lunarDate && (
              <p className="text-indigo-100 text-sm">
                農曆 {lunarDate.month_cn}{lunarDate.day_cn}
                {jieqi && jieqi !== "無" && ` · ${jieqi}`}
              </p>
            )}
          </div>
          <div className="text-white text-sm bg-white/20 px-3 py-1 rounded-full">
            今日 vs 歷史
          </div>
        </div>
      </div>

      {/* 即時天氣 */}
      {realtime && (
        <div className="px-6 py-4 bg-gradient-to-r from-blue-50 to-indigo-50 border-b">
          <h4 className="text-sm font-medium text-gray-500 mb-3">即時天氣</h4>
          <div className="grid grid-cols-3 gap-4">
            {realtime.temp !== null && (
              <div className="text-center">
                <div className="text-3xl font-bold text-orange-500">
                  {realtime.temp.toFixed(1)}°
                </div>
                <div className="text-xs text-gray-500">目前溫度</div>
              </div>
            )}
            {realtime.humidity !== null && (
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-500">
                  {realtime.humidity.toFixed(0)}%
                </div>
                <div className="text-xs text-gray-500">相對濕度</div>
              </div>
            )}
            {realtime.precipitation !== null && (
              <div className="text-center">
                <div className="text-2xl font-bold text-cyan-500">
                  {realtime.precipitation.toFixed(1)}mm
                </div>
                <div className="text-xs text-gray-500">今日雨量</div>
              </div>
            )}
          </div>
          {realtime.weather && (
            <div className="mt-3 text-center text-sm text-gray-600">
              {realtime.weather}
            </div>
          )}
          {realtime.obs_time && (
            <div className="mt-2 text-center text-xs text-gray-400">
              觀測時間：{new Date(realtime.obs_time).toLocaleTimeString("zh-TW")}
            </div>
          )}
        </div>
      )}

      {/* 比較列表 */}
      <div className="px-6 py-4">
        <h4 className="text-sm font-medium text-gray-500 mb-3">與歷史同期比較</h4>
        <div className="space-y-3">
          {comparisons.map((comp, index) => (
            <div
              key={index}
              className={`p-3 rounded-lg border ${getStatusColor(comp.status)}`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{comp.metric}</span>
                  <span className="text-xs px-2 py-0.5 bg-white/50 rounded">
                    {getStatusLabel(comp.status)}
                  </span>
                </div>
                {comp.difference !== null && (
                  <span className="text-sm font-semibold">
                    {getDifferenceIcon(comp.difference)}
                    {Math.abs(comp.difference).toFixed(1)}
                  </span>
                )}
              </div>
              <div className="mt-2 flex items-center justify-between text-sm">
                <div>
                  <span className="text-gray-500">今日：</span>
                  <span className="font-medium">
                    {comp.current !== null ? comp.current : "N/A"}
                  </span>
                </div>
                <div>
                  <span className="text-gray-500">歷史平均：</span>
                  <span className="font-medium">
                    {comp.historical_avg !== null ? comp.historical_avg : "N/A"}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 綜合評語 */}
      <div className="px-6 py-4 bg-gray-50 border-t">
        <p className="text-center text-gray-600">{summary}</p>
      </div>
    </div>
  );
}
