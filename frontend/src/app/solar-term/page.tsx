// frontend/src/app/solar-term/page.tsx
"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { SolarTermCard } from "@/components/SolarTermCard";
import { SolarTermInfo } from "@/lib/types";
import { fetchAllSolarTerms, fetchCurrentSolarTerm } from "@/lib/api";

export default function SolarTermPage() {
  const [allTerms, setAllTerms] = useState<SolarTermInfo[]>([]);
  const [selectedTerm, setSelectedTerm] = useState<string | null>(null);
  const [currentTerm, setCurrentTerm] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [terms, current] = await Promise.all([
          fetchAllSolarTerms(),
          fetchCurrentSolarTerm(),
        ]);
        setAllTerms(terms);
        setCurrentTerm(current.nearest_term);
        setSelectedTerm(current.nearest_term);
      } catch (err) {
        console.error("載入失敗", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  // 按季節分組
  const termsBySeason = {
    春: allTerms.filter((t) => t.season === "春"),
    夏: allTerms.filter((t) => t.season === "夏"),
    秋: allTerms.filter((t) => t.season === "秋"),
    冬: allTerms.filter((t) => t.season === "冬"),
  };

  const seasonColors: Record<string, string> = {
    春: "bg-green-500",
    夏: "bg-orange-500",
    秋: "bg-amber-500",
    冬: "bg-blue-500",
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-100 to-slate-200 py-8">
      <div className="max-w-6xl mx-auto px-4">
        {/* 頁頭 */}
        <div className="mb-8">
          <Link
            href="/"
            className="text-blue-600 hover:underline text-sm mb-2 inline-block"
          >
            ← 返回首頁
          </Link>
          <h1 className="text-3xl font-bold text-gray-800">二十四節氣</h1>
          <p className="text-gray-600 mt-1">
            探索千年智慧，了解臺灣的節氣特徵
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {/* 左側：節氣選擇器 */}
          <div className="md:col-span-1 space-y-4">
            {loading ? (
              <div className="bg-white rounded-xl p-4 animate-pulse">
                <div className="h-6 bg-gray-200 rounded w-1/2 mb-4"></div>
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="h-20 bg-gray-100 rounded mb-2"></div>
                ))}
              </div>
            ) : (
              Object.entries(termsBySeason).map(([season, terms]) => (
                <div key={season} className="bg-white rounded-xl overflow-hidden shadow">
                  <div className={`${seasonColors[season]} text-white px-4 py-2 font-semibold`}>
                    {season}季（{terms.length} 節氣）
                  </div>
                  <div className="p-2">
                    {terms.map((term) => (
                      <button
                        key={term.name}
                        onClick={() => setSelectedTerm(term.name)}
                        className={`w-full text-left px-3 py-2 rounded-lg transition ${
                          selectedTerm === term.name
                            ? "bg-gray-100 font-semibold"
                            : "hover:bg-gray-50"
                        } ${
                          currentTerm === term.name
                            ? "border-l-4 border-purple-500"
                            : ""
                        }`}
                      >
                        <div className="flex justify-between items-center">
                          <span>{term.name}</span>
                          <span className="text-xs text-gray-500">
                            {term.typical_date}
                          </span>
                        </div>
                        {currentTerm === term.name && (
                          <span className="text-xs text-purple-600">當前</span>
                        )}
                      </button>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>

          {/* 右側：節氣詳情 */}
          <div className="md:col-span-2">
            {selectedTerm ? (
              <SolarTermCard termName={selectedTerm} showDetails={true} />
            ) : (
              <div className="bg-white rounded-xl p-8 text-center text-gray-500">
                請選擇一個節氣
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
