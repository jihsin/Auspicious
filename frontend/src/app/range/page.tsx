// frontend/src/app/range/page.tsx
"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { fetchDateRange, fetchStationsExtended } from "@/lib/api";
import { StationInfoExtended, DateRangeResponse } from "@/lib/types";
import { TemperatureChart, PrecipChart } from "@/components";

// 預設日期範圍（今日前後 7 天）
const today = new Date();
const defaultStart = new Date(today);
defaultStart.setDate(today.getDate() - 3);
const defaultEnd = new Date(today);
defaultEnd.setDate(today.getDate() + 3);

function formatDate(d: Date): string {
  return `${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

export default function RangePage() {
  const [stations, setStations] = useState<StationInfoExtended[]>([]);
  const [selectedStation, setSelectedStation] = useState<string>("");
  const [startDate, setStartDate] = useState(formatDate(defaultStart));
  const [endDate, setEndDate] = useState(formatDate(defaultEnd));
  const [result, setResult] = useState<DateRangeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 載入站點列表
  useEffect(() => {
    fetchStationsExtended({ hasStatistics: true })
      .then((data) => {
        setStations(data);
        if (data.length > 0) {
          setSelectedStation(data[0].station_id);
        }
      })
      .catch(console.error);
  }, []);

  // 查詢日期範圍
  const handleSearch = useCallback(async () => {
    if (!selectedStation) return;

    setLoading(true);
    setError(null);

    try {
      const data = await fetchDateRange(selectedStation, startDate, endDate);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "查詢失敗");
    } finally {
      setLoading(false);
    }
  }, [selectedStation, startDate, endDate]);

  // 自動查詢
  useEffect(() => {
    if (selectedStation) {
      handleSearch();
    }
  }, [selectedStation, startDate, endDate, handleSearch]);

  return (
    <main className="min-h-screen bg-gradient-to-b from-orange-100 to-yellow-50 p-4 md:p-8">
      <div className="max-w-3xl mx-auto">
        {/* 導航 */}
        <nav className="mb-6">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-800"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            返回首頁
          </Link>
        </nav>

        {/* 標題 */}
        <header className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">
            日期範圍分析
          </h1>
          <p className="text-gray-600">
            查看特定時段的歷史天氣趨勢
          </p>
        </header>

        {/* 篩選條件 */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          {/* 站點選擇 */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              選擇站點
            </label>
            <select
              value={selectedStation}
              onChange={(e) => setSelectedStation(e.target.value)}
              className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
            >
              {stations.map((s) => (
                <option key={s.station_id} value={s.station_id}>
                  {s.name} ({s.county})
                </option>
              ))}
            </select>
          </div>

          {/* 日期範圍選擇 */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                起始日期
              </label>
              <div className="flex gap-2">
                <select
                  value={startDate.split("-")[0]}
                  onChange={(e) => setStartDate(`${e.target.value}-${startDate.split("-")[1]}`)}
                  className="flex-1 px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
                >
                  {Array.from({ length: 12 }, (_, i) => (
                    <option key={i + 1} value={String(i + 1).padStart(2, "0")}>
                      {i + 1} 月
                    </option>
                  ))}
                </select>
                <select
                  value={startDate.split("-")[1]}
                  onChange={(e) => setStartDate(`${startDate.split("-")[0]}-${e.target.value}`)}
                  className="flex-1 px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
                >
                  {Array.from({ length: 31 }, (_, i) => (
                    <option key={i + 1} value={String(i + 1).padStart(2, "0")}>
                      {i + 1} 日
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                結束日期
              </label>
              <div className="flex gap-2">
                <select
                  value={endDate.split("-")[0]}
                  onChange={(e) => setEndDate(`${e.target.value}-${endDate.split("-")[1]}`)}
                  className="flex-1 px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
                >
                  {Array.from({ length: 12 }, (_, i) => (
                    <option key={i + 1} value={String(i + 1).padStart(2, "0")}>
                      {i + 1} 月
                    </option>
                  ))}
                </select>
                <select
                  value={endDate.split("-")[1]}
                  onChange={(e) => setEndDate(`${endDate.split("-")[0]}-${e.target.value}`)}
                  className="flex-1 px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
                >
                  {Array.from({ length: 31 }, (_, i) => (
                    <option key={i + 1} value={String(i + 1).padStart(2, "0")}>
                      {i + 1} 日
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* 範圍提示 */}
          <p className="mt-3 text-xs text-gray-500 text-center">
            最多查詢 31 天範圍
          </p>
        </div>

        {/* 載入中 */}
        {loading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin text-4xl mb-4">📊</div>
            <p className="text-gray-500">正在分析歷史資料...</p>
          </div>
        )}

        {/* 錯誤訊息 */}
        {error && !loading && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center mb-6">
            <p className="text-red-600">{error}</p>
            <button
              onClick={handleSearch}
              className="mt-2 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600"
            >
              重試
            </button>
          </div>
        )}

        {/* 結果 */}
        {result && !loading && (
          <div className="space-y-6">
            {/* 摘要卡片 */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">
                {result.station.name} · {startDate} ~ {endDate} 統計摘要
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-3 bg-orange-50 rounded-lg">
                  <div className="text-2xl font-bold text-orange-600">
                    {result.summary.avg_temp?.toFixed(1) ?? "N/A"}°C
                  </div>
                  <div className="text-xs text-gray-500">平均溫度</div>
                </div>
                <div className="text-center p-3 bg-yellow-50 rounded-lg">
                  <div className="text-2xl font-bold text-yellow-600">
                    {result.summary.avg_sunny_rate
                      ? `${(result.summary.avg_sunny_rate * 100).toFixed(0)}%`
                      : "N/A"}
                  </div>
                  <div className="text-xs text-gray-500">平均晴天率</div>
                </div>
                <div className="text-center p-3 bg-blue-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">
                    {result.summary.avg_precip_prob
                      ? `${(result.summary.avg_precip_prob * 100).toFixed(0)}%`
                      : "N/A"}
                  </div>
                  <div className="text-xs text-gray-500">平均降雨機率</div>
                </div>
                <div className="text-center p-3 bg-green-50 rounded-lg">
                  <div className="text-lg font-bold text-green-600">
                    {result.summary.best_day?.split("-")[1]}日
                  </div>
                  <div className="text-xs text-gray-500">最佳日期</div>
                </div>
              </div>
            </div>

            {/* 溫度趨勢圖 */}
            <TemperatureChart data={result.days} height={280} />

            {/* 降雨與晴天機率圖 */}
            <PrecipChart data={result.days} height={220} />
          </div>
        )}

        {/* Footer */}
        <footer className="mt-8 text-center text-sm text-gray-400">
          <p>根據過去數十年的氣象觀測資料統計分析</p>
          <p>實際天氣可能與歷史統計有所差異</p>
        </footer>
      </div>
    </main>
  );
}
