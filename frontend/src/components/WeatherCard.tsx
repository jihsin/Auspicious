"use client";

/**
 * WeatherCard 組件
 * 展示歷史天氣統計資料的卡片
 */

import { DailyWeatherData } from "@/lib/types";

interface WeatherCardProps {
  data: DailyWeatherData;
}

/**
 * 格式化溫度顯示
 */
function formatTemperature(value: number | null): string {
  if (value === null) return "--";
  return `${value.toFixed(1)}°C`;
}

/**
 * 格式化百分比顯示
 */
function formatPercentage(value: number | null): string {
  if (value === null) return "--";
  return `${(value * 100).toFixed(0)}%`;
}

/**
 * 格式化降水量顯示
 */
function formatPrecipitation(value: number | null): string {
  if (value === null) return "--";
  return `${value.toFixed(1)} mm`;
}

/**
 * 取得天氣傾向的主導類型和圖示
 */
function getTendencyIcon(type: "sunny" | "cloudy" | "rainy"): string {
  const icons = {
    sunny: "☀️",
    cloudy: "☁️",
    rainy: "🌧️",
  };
  return icons[type];
}

/**
 * 計算天氣傾向條的寬度百分比
 */
function calculateTendencyWidth(value: number | null): string {
  if (value === null) return "0%";
  return `${(value * 100).toFixed(0)}%`;
}

export default function WeatherCard({ data }: WeatherCardProps) {
  const { station, month_day, analysis_period, temperature, precipitation, tendency } = data;

  // 格式化日期顯示：從 "02-04" 轉為 "2月4日"
  const [month, day] = month_day.split("-");
  const formattedDate = `${parseInt(month)}月${parseInt(day)}日`;

  // 計算分析期間字串
  const periodText = analysis_period.start_year && analysis_period.end_year
    ? `${analysis_period.start_year}-${analysis_period.end_year} (${analysis_period.years_analyzed}年)`
    : "資料不足";

  return (
    <div className="bg-white rounded-2xl shadow-lg overflow-hidden max-w-md w-full">
      {/* 標題區 */}
      <div className="bg-gradient-to-r from-blue-500 to-blue-600 px-6 py-4 text-white">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-2xl font-bold">{station.name}</h2>
            <p className="text-blue-100 text-sm">{station.city}</p>
          </div>
          <div className="text-right">
            <p className="text-3xl font-light">{formattedDate}</p>
            <p className="text-blue-200 text-xs">歷史統計</p>
          </div>
        </div>
        <p className="mt-2 text-blue-200 text-xs">
          分析期間：{periodText}
        </p>
      </div>

      {/* 溫度區 */}
      <div className="px-6 py-4">
        <h3 className="text-gray-500 text-sm font-medium mb-3">溫度統計</h3>
        <div className="grid grid-cols-3 gap-3">
          {/* 平均溫度 */}
          <div className="bg-blue-50 rounded-xl p-3 text-center">
            <p className="text-gray-500 text-xs mb-1">平均</p>
            <p className="text-blue-600 text-xl font-bold">
              {formatTemperature(temperature.avg.mean)}
            </p>
          </div>
          {/* 歷史最高 */}
          <div className="bg-red-50 rounded-xl p-3 text-center">
            <p className="text-gray-500 text-xs mb-1">歷史最高</p>
            <p className="text-red-600 text-xl font-bold">
              {formatTemperature(temperature.max_record.value)}
            </p>
          </div>
          {/* 歷史最低 */}
          <div className="bg-cyan-50 rounded-xl p-3 text-center">
            <p className="text-gray-500 text-xs mb-1">歷史最低</p>
            <p className="text-cyan-600 text-xl font-bold">
              {formatTemperature(temperature.min_record.value)}
            </p>
          </div>
        </div>
        {/* 額外溫度資訊 */}
        <div className="mt-3 flex justify-between text-xs text-gray-400">
          <span>平均高溫：{formatTemperature(temperature.max_mean)}</span>
          <span>平均低溫：{formatTemperature(temperature.min_mean)}</span>
        </div>
      </div>

      {/* 降水區 */}
      <div className="px-6 py-4 border-t border-gray-100">
        <h3 className="text-gray-500 text-sm font-medium mb-3">降水統計</h3>

        {/* 降雨機率進度條 */}
        <div className="mb-3">
          <div className="flex justify-between items-center mb-1">
            <span className="text-gray-600 text-sm">降雨機率</span>
            <span className="text-blue-600 font-medium">
              {formatPercentage(precipitation.probability)}
            </span>
          </div>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-500 rounded-full transition-all duration-500"
              style={{ width: calculateTendencyWidth(precipitation.probability) }}
            />
          </div>
        </div>

        {/* 降水量資訊 */}
        <div className="flex justify-between text-sm">
          <div>
            <span className="text-gray-500">有雨時平均：</span>
            <span className="text-gray-700 font-medium">
              {formatPrecipitation(precipitation.avg_when_rain)}
            </span>
          </div>
          <div>
            <span className="text-gray-500">大雨機率：</span>
            <span className="text-gray-700 font-medium">
              {formatPercentage(precipitation.heavy_probability)}
            </span>
          </div>
        </div>
      </div>

      {/* 天氣傾向區 */}
      <div className="px-6 py-4 border-t border-gray-100">
        <h3 className="text-gray-500 text-sm font-medium mb-3">天氣傾向</h3>

        {/* 傾向條 */}
        <div className="h-4 rounded-full overflow-hidden flex">
          {tendency.sunny !== null && tendency.sunny > 0 && (
            <div
              className="bg-yellow-400 transition-all duration-500"
              style={{ width: calculateTendencyWidth(tendency.sunny) }}
              title={`晴天 ${formatPercentage(tendency.sunny)}`}
            />
          )}
          {tendency.cloudy !== null && tendency.cloudy > 0 && (
            <div
              className="bg-gray-400 transition-all duration-500"
              style={{ width: calculateTendencyWidth(tendency.cloudy) }}
              title={`陰天 ${formatPercentage(tendency.cloudy)}`}
            />
          )}
          {tendency.rainy !== null && tendency.rainy > 0 && (
            <div
              className="bg-blue-400 transition-all duration-500"
              style={{ width: calculateTendencyWidth(tendency.rainy) }}
              title={`雨天 ${formatPercentage(tendency.rainy)}`}
            />
          )}
        </div>

        {/* 傾向標籤 */}
        <div className="flex justify-between mt-2 text-xs">
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full bg-yellow-400" />
            <span className="text-gray-600">晴 {formatPercentage(tendency.sunny)}</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full bg-gray-400" />
            <span className="text-gray-600">陰 {formatPercentage(tendency.cloudy)}</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full bg-blue-400" />
            <span className="text-gray-600">雨 {formatPercentage(tendency.rainy)}</span>
          </div>
        </div>
      </div>

      {/* 底部資訊 */}
      <div className="px-6 py-3 bg-gray-50 text-center">
        <p className="text-gray-400 text-xs">
          資料來源：中央氣象署 | 站點代碼：{station.station_id}
        </p>
      </div>
    </div>
  );
}
