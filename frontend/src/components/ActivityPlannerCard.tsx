// frontend/src/components/ActivityPlannerCard.tsx
"use client";

import { useState, useEffect } from "react";
import { ActivityType, PlannerResult, DayScore } from "@/lib/types";
import { fetchActivityTypes, fetchQuickPlan, fetchPlanActivity } from "@/lib/api";
import { DayInsightCard } from "@/components/DayInsightCard";

interface ActivityPlannerCardProps {
  stationId?: string;
  stationName?: string;
}

export function ActivityPlannerCard({
  stationId = "466920",
  stationName = "臺北",
}: ActivityPlannerCardProps) {
  const [activityTypes, setActivityTypes] = useState<ActivityType[]>([]);
  const [selectedActivity, setSelectedActivity] = useState<string>("");
  const [planResult, setPlanResult] = useState<PlannerResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingTypes, setLoadingTypes] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<"quick" | "custom">("quick");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  // 載入活動類型
  useEffect(() => {
    async function loadTypes() {
      try {
        const types = await fetchActivityTypes();
        setActivityTypes(types);
        if (types.length > 0) {
          setSelectedActivity(types[0].key);
        }
      } catch (err) {
        setError("無法載入活動類型");
      } finally {
        setLoadingTypes(false);
      }
    }
    loadTypes();

    // 設定預設日期範圍
    const today = new Date();
    const thirtyDaysLater = new Date(today);
    thirtyDaysLater.setDate(today.getDate() + 30);
    setStartDate(today.toISOString().split("T")[0]);
    setEndDate(thirtyDaysLater.toISOString().split("T")[0]);
  }, []);

  async function handlePlan() {
    if (!selectedActivity) return;

    setLoading(true);
    setError(null);
    setPlanResult(null);

    try {
      let result: PlannerResult;
      if (mode === "quick") {
        result = await fetchQuickPlan(selectedActivity, stationId);
      } else {
        result = await fetchPlanActivity(
          selectedActivity,
          stationId,
          startDate,
          endDate
        );
      }
      setPlanResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "規劃失敗");
    } finally {
      setLoading(false);
    }
  }

  // 評分顏色
  function getScoreColor(score: number): string {
    if (score >= 80) return "text-green-600 bg-green-100";
    if (score >= 65) return "text-blue-600 bg-blue-100";
    if (score >= 50) return "text-yellow-600 bg-yellow-100";
    return "text-red-600 bg-red-100";
  }

  // 格式化日期顯示
  function formatDate(dateStr: string): string {
    const date = new Date(dateStr);
    return `${date.getMonth() + 1}/${date.getDate()} (${["日", "一", "二", "三", "四", "五", "六"][date.getDay()]})`;
  }

  return (
    <div className="bg-white rounded-xl shadow-lg overflow-hidden">
      {/* 標題 */}
      <div className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white px-6 py-4">
        <h2 className="text-xl font-bold">智慧活動規劃</h2>
        <p className="text-sm opacity-90">根據歷史天氣、節氣、農民曆推薦最佳日期</p>
      </div>

      {/* 設定區 */}
      <div className="p-6 space-y-4 border-b">
        {/* 模式選擇 */}
        <div className="flex gap-2">
          <button
            onClick={() => setMode("quick")}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
              mode === "quick"
                ? "bg-purple-600 text-white"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            快速規劃（30天）
          </button>
          <button
            onClick={() => setMode("custom")}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
              mode === "custom"
                ? "bg-purple-600 text-white"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            自訂日期
          </button>
        </div>

        {/* 活動類型選擇 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            活動類型
          </label>
          {loadingTypes ? (
            <div className="h-10 bg-gray-100 rounded animate-pulse"></div>
          ) : (
            <select
              value={selectedActivity}
              onChange={(e) => setSelectedActivity(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
            >
              {activityTypes.map((type) => (
                <option key={type.key} value={type.key}>
                  {type.type} - {type.description}
                </option>
              ))}
            </select>
          )}
        </div>

        {/* 自訂日期 */}
        {mode === "custom" && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                開始日期
              </label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                結束日期
              </label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
              />
            </div>
          </div>
        )}

        {/* 地點顯示 */}
        <div className="text-sm text-gray-500">
          地點：{stationName}
        </div>

        {/* 規劃按鈕 */}
        <button
          onClick={handlePlan}
          disabled={loading || !selectedActivity}
          className="w-full py-3 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg font-medium hover:from-purple-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
        >
          {loading ? "規劃中..." : "開始規劃"}
        </button>

        {error && (
          <p className="text-red-500 text-sm text-center">{error}</p>
        )}
      </div>

      {/* 結果區 */}
      {planResult && (
        <div className="p-6 space-y-4">
          {/* 摘要 */}
          <div className="bg-purple-50 rounded-lg p-4">
            <h3 className="font-semibold text-purple-800 mb-2">規劃摘要</h3>
            <p className="text-gray-700">{planResult.summary}</p>
          </div>

          {/* 最佳日期 */}
          {planResult.best_date && (
            <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg p-4 border border-green-200">
              <div className="flex justify-between items-start">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">🏆</span>
                    <h3 className="text-lg font-bold text-green-800">
                      最佳日期：{formatDate(planResult.best_date.date)}
                    </h3>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">
                    農曆 {planResult.best_date.lunar_date}
                    {planResult.best_date.solar_term && (
                      <span className="ml-2 text-purple-600">
                        節氣：{planResult.best_date.solar_term}
                      </span>
                    )}
                  </p>
                </div>
                <div className={`px-3 py-1 rounded-full font-bold ${getScoreColor(planResult.best_date.score)}`}>
                  {planResult.best_date.score.toFixed(0)} 分
                </div>
              </div>
              {/* 宜忌 */}
              <div className="mt-3 flex flex-wrap gap-2 text-xs">
                {planResult.best_date.lunar_yi.map((yi, i) => (
                  <span key={i} className="bg-green-200 text-green-800 px-2 py-0.5 rounded">
                    宜 {yi}
                  </span>
                ))}
                {planResult.best_date.lunar_ji.slice(0, 2).map((ji, i) => (
                  <span key={i} className="bg-red-200 text-red-800 px-2 py-0.5 rounded">
                    忌 {ji}
                  </span>
                ))}
              </div>
              {/* 備註 */}
              {planResult.best_date.notes.length > 0 && (
                <div className="mt-2 text-sm text-gray-600">
                  {planResult.best_date.notes.join(" | ")}
                </div>
              )}
            </div>
          )}

          {/* 其他推薦 */}
          {planResult.recommendations.length > 1 && (
            <div>
              <h3 className="font-semibold text-gray-700 mb-2">其他推薦日期</h3>
              <div className="space-y-2">
                {planResult.recommendations.slice(1).map((day, i) => (
                  <DayScoreRow key={i} day={day} formatDate={formatDate} getScoreColor={getScoreColor} stationId={stationId} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// 日期分數行組件
function DayScoreRow({
  day,
  formatDate,
  getScoreColor,
  stationId,
}: {
  day: DayScore;
  formatDate: (d: string) => string;
  getScoreColor: (s: number) => string;
  stationId: string;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="bg-gray-50 rounded-lg p-3">
      <div
        className="flex justify-between items-center cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-3">
          <span className="font-medium">{formatDate(day.date)}</span>
          <span className="text-sm text-gray-500">
            農曆 {day.lunar_date}
          </span>
          {day.solar_term && (
            <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded">
              {day.solar_term}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <span className={`px-2 py-0.5 rounded text-sm font-medium ${getScoreColor(day.score)}`}>
            {day.score.toFixed(0)} 分
          </span>
          <span className="text-gray-400">{expanded ? "▲" : "▼"}</span>
        </div>
      </div>
      {expanded && (
        <div className="mt-2 pt-2 border-t text-sm text-gray-600">
          <div className="grid grid-cols-3 gap-2 mb-2">
            <div>降雨機率：{(day.rain_probability * 100).toFixed(0)}%</div>
            <div>平均溫度：{day.temp_avg.toFixed(1)}°C</div>
            <div>晴天比例：{(day.sunny_ratio * 100).toFixed(0)}%</div>
          </div>
          <div className="my-3">
            <DayInsightCard
              stationId={stationId}
              month={parseInt(day.date.slice(5, 7), 10)}
              day={parseInt(day.date.slice(8, 10), 10)}
            />
          </div>
          <div className="flex flex-wrap gap-1">
            {day.lunar_yi.map((yi, i) => (
              <span key={i} className="bg-green-100 text-green-700 px-1.5 py-0.5 rounded text-xs">
                宜{yi}
              </span>
            ))}
            {day.lunar_ji.map((ji, i) => (
              <span key={i} className="bg-red-100 text-red-700 px-1.5 py-0.5 rounded text-xs">
                忌{ji}
              </span>
            ))}
          </div>
          {day.notes.length > 0 && (
            <div className="mt-1 text-gray-500">{day.notes.join(" | ")}</div>
          )}
        </div>
      )}
    </div>
  );
}
