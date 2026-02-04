"use client";

/**
 * 好日子 - 首頁
 * 顯示今日的歷史天氣統計資料
 */

import { useState, useEffect } from "react";
import WeatherCard from "@/components/WeatherCard";
import { fetchTodayWeather } from "@/lib/api";
import { DailyWeatherData, ApiError } from "@/lib/types";

// 預設站點：臺北
const DEFAULT_STATION_ID = "466920";

export default function Home() {
  const [data, setData] = useState<DailyWeatherData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadTodayWeather() {
      try {
        setLoading(true);
        setError(null);
        const weatherData = await fetchTodayWeather(DEFAULT_STATION_ID);
        setData(weatherData);
      } catch (err) {
        if (err instanceof ApiError) {
          setError(`載入失敗：${err.message}`);
        } else if (err instanceof Error) {
          setError(`載入失敗：${err.message}`);
        } else {
          setError("載入失敗：未知錯誤");
        }
      } finally {
        setLoading(false);
      }
    }

    loadTodayWeather();
  }, []);

  return (
    <main className="min-h-screen bg-gradient-to-b from-blue-100 to-white">
      {/* 頁首 */}
      <header className="py-8 text-center">
        <h1 className="text-4xl font-bold text-gray-800 mb-2">好日子</h1>
        <p className="text-gray-600">
          歷史氣象大數據 × 傳統曆法智慧
        </p>
      </header>

      {/* 主內容 */}
      <div className="flex flex-col items-center justify-center px-4 pb-12">
        {/* 載入中狀態 */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
            <p className="mt-4 text-gray-600">載入歷史天氣資料中...</p>
          </div>
        )}

        {/* 錯誤狀態 */}
        {error && !loading && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-6 max-w-md w-full text-center">
            <div className="text-red-500 text-4xl mb-3">⚠️</div>
            <h2 className="text-red-700 font-medium mb-2">無法載入資料</h2>
            <p className="text-red-600 text-sm mb-4">{error}</p>
            <button
              onClick={() => window.location.reload()}
              className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg text-sm transition-colors"
            >
              重新載入
            </button>
          </div>
        )}

        {/* 天氣卡片 */}
        {data && !loading && !error && (
          <WeatherCard data={data} />
        )}

        {/* 說明文字 */}
        <div className="mt-8 max-w-md text-center text-gray-500 text-sm">
          <p>
            根據過去數十年的氣象觀測資料，統計分析每一天的天氣特性。
            <br />
            幫助您了解特定日期「通常」會是什麼樣的天氣。
          </p>
        </div>
      </div>

      {/* 頁尾 */}
      <footer className="py-6 text-center text-gray-400 text-xs border-t border-gray-200">
        <p>好日子 Auspicious &copy; 2024</p>
        <p className="mt-1">資料來源：中央氣象署歷史觀測資料</p>
      </footer>
    </main>
  );
}
