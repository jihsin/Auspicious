// frontend/src/app/planner/page.tsx
"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { ActivityPlannerCard } from "@/components/ActivityPlannerCard";
import { SolarTermCard } from "@/components/SolarTermCard";
import { StationInfoExtended } from "@/lib/types";
import { fetchStationsExtended } from "@/lib/api";

export default function PlannerPage() {
  const [stations, setStations] = useState<StationInfoExtended[]>([]);
  const [selectedStation, setSelectedStation] = useState<StationInfoExtended | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadStations() {
      try {
        const data = await fetchStationsExtended({ hasStatistics: true });
        setStations(data);
        // 預設選擇臺北
        const taipei = data.find((s) => s.station_id === "466920");
        setSelectedStation(taipei || data[0]);
      } catch (err) {
        console.error("載入站點失敗", err);
      } finally {
        setLoading(false);
      }
    }
    loadStations();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-indigo-100 py-8">
      <div className="max-w-6xl mx-auto px-4">
        {/* 頁頭 */}
        <div className="mb-8">
          <Link
            href="/"
            className="text-purple-600 hover:underline text-sm mb-2 inline-block"
          >
            ← 返回首頁
          </Link>
          <h1 className="text-3xl font-bold text-gray-800">智慧活動規劃</h1>
          <p className="text-gray-600 mt-1">
            根據歷史天氣、節氣、農民曆，為你的活動找到最佳日期
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {/* 左側：站點選擇 + 節氣卡片 */}
          <div className="md:col-span-1 space-y-4">
            {/* 站點選擇 */}
            <div className="bg-white rounded-xl shadow p-4">
              <h3 className="font-semibold text-gray-700 mb-3">選擇地點</h3>
              {loading ? (
                <div className="h-10 bg-gray-100 rounded animate-pulse"></div>
              ) : (
                <select
                  value={selectedStation?.station_id || ""}
                  onChange={(e) => {
                    const station = stations.find((s) => s.station_id === e.target.value);
                    setSelectedStation(station || null);
                  }}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                >
                  {stations.map((station) => (
                    <option key={station.station_id} value={station.station_id}>
                      {station.name} ({station.county})
                    </option>
                  ))}
                </select>
              )}
              {selectedStation && (
                <div className="mt-2 text-sm text-gray-500">
                  海拔：{selectedStation.altitude?.toFixed(0) || "N/A"} 公尺
                </div>
              )}
            </div>

            {/* 當前節氣 */}
            <SolarTermCard showDetails={false} />
          </div>

          {/* 右側：活動規劃器 */}
          <div className="md:col-span-2">
            {selectedStation ? (
              <ActivityPlannerCard
                stationId={selectedStation.station_id}
                stationName={`${selectedStation.name} (${selectedStation.county})`}
              />
            ) : (
              <div className="bg-white rounded-xl p-8 text-center text-gray-500">
                請選擇一個地點
              </div>
            )}
          </div>
        </div>

        {/* 使用說明 */}
        <div className="mt-8 bg-white rounded-xl shadow p-6">
          <h3 className="font-semibold text-gray-800 mb-4">使用說明</h3>
          <div className="grid md:grid-cols-3 gap-6 text-sm text-gray-600">
            <div>
              <div className="text-purple-600 font-semibold mb-1">1. 選擇地點</div>
              <p>選擇你的活動地點，系統會使用該地區 36 年的歷史天氣資料進行分析。</p>
            </div>
            <div>
              <div className="text-purple-600 font-semibold mb-1">2. 選擇活動類型</div>
              <p>不同活動對天氣的需求不同。例如戶外婚禮需要晴天，登山則偏好涼爽天氣。</p>
            </div>
            <div>
              <div className="text-purple-600 font-semibold mb-1">3. 查看推薦</div>
              <p>系統會綜合考慮降雨機率、溫度、農曆宜忌，推薦最適合的日期。</p>
            </div>
          </div>
        </div>

        {/* 活動類型說明 */}
        <div className="mt-4 bg-white rounded-xl shadow p-6">
          <h3 className="font-semibold text-gray-800 mb-4">活動類型天氣需求</h3>
          <div className="grid md:grid-cols-4 gap-4 text-sm">
            <div className="bg-red-50 rounded-lg p-3">
              <div className="font-semibold text-red-700">高要求</div>
              <p className="text-gray-600 mt-1">戶外婚禮、觀星、烤肉</p>
              <p className="text-xs text-gray-500 mt-1">降雨容忍度極低</p>
            </div>
            <div className="bg-orange-50 rounded-lg p-3">
              <div className="font-semibold text-orange-700">中高要求</div>
              <p className="text-gray-600 mt-1">婚禮、野餐、露營、海邊</p>
              <p className="text-xs text-gray-500 mt-1">需要較好天氣</p>
            </div>
            <div className="bg-yellow-50 rounded-lg p-3">
              <div className="font-semibold text-yellow-700">中等要求</div>
              <p className="text-gray-600 mt-1">騎車、節慶、市集</p>
              <p className="text-xs text-gray-500 mt-1">可接受部分雲天</p>
            </div>
            <div className="bg-green-50 rounded-lg p-3">
              <div className="font-semibold text-green-700">彈性要求</div>
              <p className="text-gray-600 mt-1">登山、跑步、攝影、賞花</p>
              <p className="text-xs text-gray-500 mt-1">各種天氣皆可</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
