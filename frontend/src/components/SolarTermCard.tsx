// frontend/src/components/SolarTermCard.tsx
"use client";

import { useState, useEffect } from "react";
import { SolarTermInfo, CurrentSolarTermResponse } from "@/lib/types";
import { fetchSolarTerm, fetchCurrentSolarTerm } from "@/lib/api";

interface SolarTermCardProps {
  termName?: string; // 如果不提供，顯示當前節氣
  showDetails?: boolean;
}

export function SolarTermCard({ termName, showDetails = true }: SolarTermCardProps) {
  const [termInfo, setTermInfo] = useState<SolarTermInfo | null>(null);
  const [currentInfo, setCurrentInfo] = useState<CurrentSolarTermResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showProverbs, setShowProverbs] = useState(false);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      setError(null);

      try {
        // 取得當前節氣資訊
        const current = await fetchCurrentSolarTerm();
        setCurrentInfo(current);

        // 如果有指定節氣名稱，取得該節氣；否則取得最近的節氣
        const name = termName || current.nearest_term;
        if (name) {
          const info = await fetchSolarTerm(name);
          setTermInfo(info);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "載入失敗");
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [termName]);

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-lg p-6 animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
        <div className="h-4 bg-gray-200 rounded w-2/3 mb-2"></div>
        <div className="h-4 bg-gray-200 rounded w-1/2"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 rounded-xl shadow-lg p-6 border border-red-200">
        <p className="text-red-600">{error}</p>
      </div>
    );
  }

  if (!termInfo) {
    return null;
  }

  // 季節對應的顏色
  const seasonColors: Record<string, { bg: string; text: string; accent: string }> = {
    春: { bg: "bg-green-50", text: "text-green-800", accent: "bg-green-500" },
    夏: { bg: "bg-orange-50", text: "text-orange-800", accent: "bg-orange-500" },
    秋: { bg: "bg-amber-50", text: "text-amber-800", accent: "bg-amber-500" },
    冬: { bg: "bg-blue-50", text: "text-blue-800", accent: "bg-blue-500" },
  };

  const colors = seasonColors[termInfo.season] || seasonColors.春;

  return (
    <div className={`${colors.bg} rounded-xl shadow-lg overflow-hidden`}>
      {/* 標題區 */}
      <div className={`${colors.accent} text-white px-6 py-4`}>
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold">{termInfo.name}</h2>
            <p className="text-sm opacity-90">{termInfo.name_en}</p>
          </div>
          <div className="text-right">
            <p className="text-sm opacity-90">第 {termInfo.order} 個節氣</p>
            <p className="text-lg font-semibold">{termInfo.season}季</p>
          </div>
        </div>
        {currentInfo && currentInfo.current_term === termInfo.name && (
          <div className="mt-2 inline-block bg-white/20 px-3 py-1 rounded-full text-sm">
            當前節氣
          </div>
        )}
        {currentInfo && currentInfo.nearest_term === termInfo.name && currentInfo.current_term !== termInfo.name && (
          <div className="mt-2 inline-block bg-white/20 px-3 py-1 rounded-full text-sm">
            最近節氣（{currentInfo.days_until_next} 天後進入 {currentInfo.next_term}）
          </div>
        )}
      </div>

      {/* 內容區 */}
      <div className="p-6 space-y-4">
        {/* 基本資訊 */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500">太陽黃經</span>
            <p className={`${colors.text} font-medium`}>{termInfo.solar_longitude}°</p>
          </div>
          <div>
            <span className="text-gray-500">典型日期</span>
            <p className={`${colors.text} font-medium`}>{termInfo.typical_date}</p>
          </div>
        </div>

        {showDetails && (
          <>
            {/* 天文意義 */}
            <div>
              <h3 className={`${colors.text} font-semibold mb-1`}>天文意義</h3>
              <p className="text-gray-600 text-sm">{termInfo.astronomy}</p>
            </div>

            {/* 農業意義 */}
            <div>
              <h3 className={`${colors.text} font-semibold mb-1`}>農業意義</h3>
              <p className="text-gray-600 text-sm">{termInfo.agriculture}</p>
            </div>

            {/* 臺灣氣候 */}
            <div>
              <h3 className={`${colors.text} font-semibold mb-1`}>臺灣氣候特徵</h3>
              <p className="text-gray-600 text-sm">{termInfo.weather}</p>
            </div>

            {/* 三候 */}
            {termInfo.phenology && termInfo.phenology.length > 0 && (
              <div>
                <h3 className={`${colors.text} font-semibold mb-2`}>物候（三候）</h3>
                <div className="flex flex-wrap gap-2">
                  {termInfo.phenology.map((p, i) => (
                    <span
                      key={i}
                      className={`${colors.accent} text-white text-xs px-2 py-1 rounded-full`}
                    >
                      {p}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* 養生建議 */}
            <div>
              <h3 className={`${colors.text} font-semibold mb-1`}>養生建議</h3>
              <p className="text-gray-600 text-sm">{termInfo.health_tips}</p>
            </div>

            {/* 相關諺語 */}
            {termInfo.proverbs && termInfo.proverbs.length > 0 && (
              <div>
                <button
                  onClick={() => setShowProverbs(!showProverbs)}
                  className={`${colors.text} font-semibold flex items-center gap-2`}
                >
                  相關諺語
                  <span className="text-xs">
                    {showProverbs ? "▲" : "▼"}
                  </span>
                </button>
                {showProverbs && (
                  <div className="mt-2 space-y-2">
                    {termInfo.proverbs.map((proverb, i) => (
                      <div
                        key={i}
                        className="bg-white/50 rounded-lg p-3 text-sm text-gray-700 italic"
                      >
                        「{proverb}」
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
