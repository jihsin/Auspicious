// frontend/src/components/RecommendationCard.tsx
"use client";

import { RecommendedDate, PreferenceType } from "@/lib/types";

interface RecommendationCardProps {
  recommendations: RecommendedDate[];
  preference: PreferenceType;
  month: number;
}

const PREFERENCE_LABELS: Record<PreferenceType, string> = {
  sunny: "晴天活動",
  mild: "舒適氣溫",
  cool: "涼爽天氣",
  outdoor: "戶外活動",
  wedding: "婚禮宴客",
};

const MONTH_NAMES = [
  "一月", "二月", "三月", "四月", "五月", "六月",
  "七月", "八月", "九月", "十月", "十一月", "十二月"
];

function getScoreColor(score: number): string {
  if (score >= 80) return "text-green-600 bg-green-50";
  if (score >= 60) return "text-blue-600 bg-blue-50";
  if (score >= 40) return "text-yellow-600 bg-yellow-50";
  return "text-gray-600 bg-gray-50";
}

function getScoreEmoji(score: number): string {
  if (score >= 80) return "🌟";
  if (score >= 60) return "👍";
  if (score >= 40) return "🤔";
  return "😐";
}

export function RecommendationCard({
  recommendations,
  preference,
  month,
}: RecommendationCardProps) {
  if (recommendations.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-lg p-6 text-center text-gray-500">
        沒有找到推薦日期
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-lg overflow-hidden">
      {/* 標題 */}
      <div className="bg-gradient-to-r from-blue-500 to-purple-500 px-6 py-4">
        <h3 className="text-white font-semibold text-lg">
          {MONTH_NAMES[month - 1]} 最佳日期推薦
        </h3>
        <p className="text-blue-100 text-sm">
          偏好：{PREFERENCE_LABELS[preference]}
        </p>
      </div>

      {/* 推薦列表 */}
      <div className="divide-y divide-gray-100">
        {recommendations.map((rec, index) => (
          <div
            key={rec.month_day}
            className="px-6 py-4 hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-start justify-between">
              {/* 左側：排名和日期 */}
              <div className="flex items-center gap-3">
                <span className="text-2xl font-bold text-gray-300">
                  #{index + 1}
                </span>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-lg font-semibold text-gray-800">
                      {rec.month_day.split("-")[1]} 日
                    </span>
                    {rec.lunar_date && (
                      <span className="text-sm text-red-600">
                        {rec.lunar_date.month_cn}{rec.lunar_date.day_cn}
                      </span>
                    )}
                    {rec.jieqi && rec.jieqi !== "無" && (
                      <span className="px-2 py-0.5 bg-amber-100 text-amber-700 text-xs rounded">
                        {rec.jieqi}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-500 mt-1">
                    {rec.reason}
                  </p>
                </div>
              </div>

              {/* 右側：分數 */}
              <div className={`px-3 py-1 rounded-full ${getScoreColor(rec.score)}`}>
                <span className="text-sm font-semibold">
                  {getScoreEmoji(rec.score)} {rec.score}
                </span>
              </div>
            </div>

            {/* 天氣數據 */}
            <div className="flex items-center gap-4 mt-3 text-sm">
              {rec.temp_avg !== null && (
                <div className="flex items-center gap-1 text-orange-600">
                  <span>🌡️</span>
                  <span>{rec.temp_avg.toFixed(1)}°C</span>
                </div>
              )}
              {rec.precip_prob !== null && (
                <div className="flex items-center gap-1 text-blue-600">
                  <span>🌧️</span>
                  <span>{(rec.precip_prob * 100).toFixed(0)}%</span>
                </div>
              )}
              {rec.sunny_rate !== null && (
                <div className="flex items-center gap-1 text-yellow-600">
                  <span>☀️</span>
                  <span>{(rec.sunny_rate * 100).toFixed(0)}%</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
