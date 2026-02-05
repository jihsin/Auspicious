// frontend/src/app/recommend/page.tsx
"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { fetchBestDates, fetchStationsExtended } from "@/lib/api";
import { StationInfoExtended, BestDatesResponse, PreferenceType } from "@/lib/types";
import { RecommendationCard } from "@/components";

const PREFERENCES: { value: PreferenceType; label: string; emoji: string; desc: string }[] = [
  { value: "sunny", label: "晴天活動", emoji: "☀️", desc: "重視晴天率" },
  { value: "outdoor", label: "戶外活動", emoji: "🏕️", desc: "晴天+適溫+少雨" },
  { value: "wedding", label: "婚禮宴客", emoji: "💒", desc: "最重視少雨" },
  { value: "mild", label: "舒適氣溫", emoji: "🌤️", desc: "18-25°C 最佳" },
  { value: "cool", label: "涼爽天氣", emoji: "🍃", desc: "15-20°C 最佳" },
];

const MONTHS = Array.from({ length: 12 }, (_, i) => ({
  value: i + 1,
  label: `${i + 1} 月`,
}));

export default function RecommendPage() {
  const [stations, setStations] = useState<StationInfoExtended[]>([]);
  const [selectedStation, setSelectedStation] = useState<string>("");
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth() + 1);
  const [selectedPreference, setSelectedPreference] = useState<PreferenceType>("sunny");
  const [result, setResult] = useState<BestDatesResponse | null>(null);
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

  // 查詢推薦
  const handleSearch = useCallback(async () => {
    if (!selectedStation) return;

    setLoading(true);
    setError(null);

    try {
      const data = await fetchBestDates(
        selectedStation,
        selectedMonth,
        selectedPreference,
        5
      );
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "查詢失敗");
    } finally {
      setLoading(false);
    }
  }, [selectedStation, selectedMonth, selectedPreference]);

  // 站點變更時自動查詢
  useEffect(() => {
    if (selectedStation) {
      handleSearch();
    }
  }, [selectedStation, selectedMonth, selectedPreference, handleSearch]);

  return (
    <main className="min-h-screen bg-gradient-to-b from-purple-100 to-blue-50 p-4 md:p-8">
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
            好日子推薦
          </h1>
          <p className="text-gray-600">
            根據歷史天氣統計，找出最適合的日子
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
              className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {stations.map((s) => (
                <option key={s.station_id} value={s.station_id}>
                  {s.name} ({s.county})
                </option>
              ))}
            </select>
          </div>

          {/* 月份選擇 */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              選擇月份
            </label>
            <div className="grid grid-cols-6 gap-2">
              {MONTHS.map((m) => (
                <button
                  key={m.value}
                  onClick={() => setSelectedMonth(m.value)}
                  className={`
                    py-2 rounded-lg text-sm font-medium transition-colors
                    ${selectedMonth === m.value
                      ? "bg-blue-500 text-white"
                      : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                    }
                  `}
                >
                  {m.label}
                </button>
              ))}
            </div>
          </div>

          {/* 偏好選擇 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              活動類型
            </label>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
              {PREFERENCES.map((p) => (
                <button
                  key={p.value}
                  onClick={() => setSelectedPreference(p.value)}
                  className={`
                    p-3 rounded-lg text-left transition-all
                    ${selectedPreference === p.value
                      ? "bg-purple-500 text-white ring-2 ring-purple-300"
                      : "bg-gray-50 text-gray-700 hover:bg-gray-100"
                    }
                  `}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-xl">{p.emoji}</span>
                    <span className="font-medium">{p.label}</span>
                  </div>
                  <p className={`text-xs mt-1 ${
                    selectedPreference === p.value ? "text-purple-100" : "text-gray-500"
                  }`}>
                    {p.desc}
                  </p>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* 載入中 */}
        {loading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin text-4xl mb-4">🔮</div>
            <p className="text-gray-500">正在分析歷史資料...</p>
          </div>
        )}

        {/* 錯誤訊息 */}
        {error && !loading && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
            <p className="text-red-600">{error}</p>
            <button
              onClick={handleSearch}
              className="mt-2 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600"
            >
              重試
            </button>
          </div>
        )}

        {/* 推薦結果 */}
        {result && !loading && (
          <RecommendationCard
            recommendations={result.recommendations}
            preference={selectedPreference}
            month={selectedMonth}
          />
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
