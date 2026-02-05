// frontend/src/app/historical/page.tsx
"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { fetchHistoricalCompare, fetchStationsExtended } from "@/lib/api";
import { StationInfoExtended, HistoricalCompareResponse } from "@/lib/types";
import { HistoricalCompareCard } from "@/components/HistoricalCompareCard";

export default function HistoricalPage() {
  const [stations, setStations] = useState<StationInfoExtended[]>([]);
  const [selectedStation, setSelectedStation] = useState<string>("");
  const [result, setResult] = useState<HistoricalCompareResponse | null>(null);
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

  // 查詢歷史比較
  const handleSearch = useCallback(async () => {
    if (!selectedStation) return;

    setLoading(true);
    setError(null);

    try {
      const data = await fetchHistoricalCompare(selectedStation);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "查詢失敗");
    } finally {
      setLoading(false);
    }
  }, [selectedStation]);

  // 自動查詢
  useEffect(() => {
    if (selectedStation) {
      handleSearch();
    }
  }, [selectedStation, handleSearch]);

  return (
    <main className="min-h-screen bg-gradient-to-b from-indigo-100 to-purple-50 p-4 md:p-8">
      <div className="max-w-2xl mx-auto">
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
            歷史同期比較
          </h1>
          <p className="text-gray-600">
            比較今日即時天氣與歷史平均
          </p>
        </header>

        {/* 站點選擇 */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            選擇站點
          </label>
          <select
            value={selectedStation}
            onChange={(e) => setSelectedStation(e.target.value)}
            className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            {stations.map((s) => (
              <option key={s.station_id} value={s.station_id}>
                {s.name} ({s.county})
              </option>
            ))}
          </select>

          <button
            onClick={handleSearch}
            disabled={loading || !selectedStation}
            className="mt-4 w-full px-4 py-2 bg-indigo-500 text-white rounded-lg hover:bg-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? "查詢中..." : "重新查詢"}
          </button>
        </div>

        {/* 載入中 */}
        {loading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin text-4xl mb-4">🔄</div>
            <p className="text-gray-500">正在查詢即時天氣...</p>
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

        {/* 比較結果 */}
        {result && !loading && (
          <HistoricalCompareCard
            station={result.station}
            date={result.date}
            realtime={result.realtime}
            comparisons={result.comparisons}
            summary={result.summary}
            lunarDate={result.lunar_date}
            jieqi={result.jieqi}
            // Phase 3.1 年代統計
            percentile={result.percentile}
            extremeRecords={result.extreme_records}
            decades={result.decades}
            climateTrend={result.climate_trend}
          />
        )}

        {/* 說明 */}
        <div className="mt-6 bg-indigo-50 rounded-lg p-4 text-sm text-indigo-700">
          <p className="font-medium mb-2">關於歷史同期比較</p>
          <ul className="list-disc list-inside space-y-1 text-indigo-600">
            <li>即時資料來自中央氣象署觀測站</li>
            <li>歷史平均根據過去數十年同日統計</li>
            <li>異常標示代表偏離歷史平均超過 2 個標準差</li>
          </ul>
        </div>

        {/* Footer */}
        <footer className="mt-8 text-center text-sm text-gray-400">
          <p>即時資料來源：中央氣象署</p>
          <p>歷史統計：根據過去數十年觀測資料</p>
        </footer>
      </div>
    </main>
  );
}
