// frontend/src/app/compare/page.tsx
"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { fetchCompareStations, fetchStationsExtended } from "@/lib/api";
import { StationInfoExtended, CompareResponse } from "@/lib/types";
import { ComparisonCard, StationCompareChart } from "@/components";
import { DayInsightCard } from "@/components/DayInsightCard";

// 預設月份和日期
const today = new Date();

export default function ComparePage() {
  const [stations, setStations] = useState<StationInfoExtended[]>([]);
  const [selectedStations, setSelectedStations] = useState<string[]>([]);
  const [selectedMonth, setSelectedMonth] = useState(today.getMonth() + 1);
  const [selectedDay, setSelectedDay] = useState(today.getDate());
  const [result, setResult] = useState<CompareResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 載入站點列表
  useEffect(() => {
    fetchStationsExtended({ hasStatistics: true })
      .then((data) => {
        setStations(data);
        // 預設選擇前 3 個站點
        if (data.length >= 3) {
          setSelectedStations(data.slice(0, 3).map((s) => s.station_id));
        }
      })
      .catch(console.error);
  }, []);

  // 切換站點選擇
  const toggleStation = useCallback((stationId: string) => {
    setSelectedStations((prev) => {
      if (prev.includes(stationId)) {
        return prev.filter((id) => id !== stationId);
      }
      if (prev.length >= 5) {
        return prev; // 最多 5 個
      }
      return [...prev, stationId];
    });
  }, []);

  // 執行比較
  const handleCompare = useCallback(async () => {
    if (selectedStations.length < 2) {
      setError("請至少選擇 2 個站點");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const date = `${String(selectedMonth).padStart(2, "0")}-${String(selectedDay).padStart(2, "0")}`;
      const data = await fetchCompareStations(selectedStations, date);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "查詢失敗");
    } finally {
      setLoading(false);
    }
  }, [selectedStations, selectedMonth, selectedDay]);

  // 當選擇變更時自動查詢
  useEffect(() => {
    if (selectedStations.length >= 2) {
      handleCompare();
    }
  }, [selectedStations, selectedMonth, selectedDay, handleCompare]);

  // 取得該月天數
  const daysInMonth = new Date(2000, selectedMonth, 0).getDate();

  return (
    <main className="min-h-screen bg-gradient-to-b from-green-100 to-blue-50 p-4 md:p-8">
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
            多站點比較
          </h1>
          <p className="text-gray-600">
            比較不同地區在同一天的歷史天氣
          </p>
        </header>

        {/* 篩選條件 */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          {/* 日期選擇 */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              選擇日期
            </label>
            <div className="flex gap-4">
              {/* 月份 */}
              <div className="flex-1">
                <select
                  value={selectedMonth}
                  onChange={(e) => setSelectedMonth(parseInt(e.target.value))}
                  className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                >
                  {Array.from({ length: 12 }, (_, i) => (
                    <option key={i + 1} value={i + 1}>
                      {i + 1} 月
                    </option>
                  ))}
                </select>
              </div>
              {/* 日期 */}
              <div className="flex-1">
                <select
                  value={selectedDay}
                  onChange={(e) => setSelectedDay(parseInt(e.target.value))}
                  className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                >
                  {Array.from({ length: daysInMonth }, (_, i) => (
                    <option key={i + 1} value={i + 1}>
                      {i + 1} 日
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* 站點選擇 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              選擇站點 (2-5 個)
              <span className="text-gray-400 ml-2">
                已選 {selectedStations.length}/5
              </span>
            </label>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2 max-h-60 overflow-y-auto">
              {stations.map((station) => {
                const isSelected = selectedStations.includes(station.station_id);
                return (
                  <button
                    key={station.station_id}
                    onClick={() => toggleStation(station.station_id)}
                    disabled={!isSelected && selectedStations.length >= 5}
                    className={`
                      p-3 rounded-lg text-left transition-all text-sm
                      ${isSelected
                        ? "bg-green-500 text-white ring-2 ring-green-300"
                        : "bg-gray-50 text-gray-700 hover:bg-gray-100"
                      }
                      ${!isSelected && selectedStations.length >= 5
                        ? "opacity-50 cursor-not-allowed"
                        : ""
                      }
                    `}
                  >
                    <div className="font-medium">{station.name}</div>
                    <div className={`text-xs ${isSelected ? "text-green-100" : "text-gray-500"}`}>
                      {station.county}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* 載入中 */}
        {loading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin text-4xl mb-4">🔄</div>
            <p className="text-gray-500">正在比較站點資料...</p>
          </div>
        )}

        {/* 錯誤訊息 */}
        {error && !loading && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center mb-6">
            <p className="text-red-600">{error}</p>
            <button
              onClick={handleCompare}
              className="mt-2 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600"
            >
              重試
            </button>
          </div>
        )}

        {/* 比較結果 */}
        {result && !loading && (
          <>
            <ComparisonCard
              date={result.date}
              stations={result.stations}
              bestStation={result.best_station}
              lunarDate={result.lunar_date}
              jieqi={result.jieqi}
            />

            {/* 圖表比較 */}
            <div className="mt-6 space-y-4">
              <StationCompareChart
                data={result.stations}
                metric="sunny_rate"
                height={200}
              />
              <StationCompareChart
                data={result.stations}
                metric="temp_avg"
                height={200}
              />
            </div>

            {/* 每站日洞察 */}
            <div className="mt-6 space-y-4">
              {selectedStations.map((stationId) => (
                <DayInsightCard
                  key={stationId}
                  stationId={stationId}
                  month={selectedMonth}
                  day={selectedDay}
                />
              ))}
            </div>
          </>
        )}

        {/* Footer */}
        <footer className="mt-8 text-center text-sm text-gray-400">
          <p>根據過去數十年的氣象觀測資料統計分析</p>
          <p>排名依據歷史晴天率，實際天氣可能有所不同</p>
        </footer>
      </div>
    </main>
  );
}
