"use client";

/**
 * 好日子 - 首頁
 * 顯示今日的歷史天氣統計資料
 * 支援 GPS 定位和站點選擇
 */

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { WeatherCard, StationSelector, LunarCard } from "@/components";
import { fetchTodayWeather } from "@/lib/api";
import { DailyWeatherData, ApiError, StationInfoExtended } from "@/lib/types";

// 預設站點：臺北
const DEFAULT_STATION: StationInfoExtended = {
  station_id: "466920",
  name: "臺北",
  county: "臺北市",
  town: null,
  latitude: 25.0375,
  longitude: 121.5148,
  altitude: 6.3,
  has_statistics: true,
};

// localStorage key
const STATION_STORAGE_KEY = "auspicious_selected_station";

export default function Home() {
  const [data, setData] = useState<DailyWeatherData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentStation, setCurrentStation] =
    useState<StationInfoExtended | null>(null);
  const [distance, setDistance] = useState<number | null>(null);

  // 從 localStorage 讀取上次選擇的站點
  useEffect(() => {
    const savedStation = localStorage.getItem(STATION_STORAGE_KEY);
    if (savedStation) {
      try {
        const parsed = JSON.parse(savedStation);
        setCurrentStation(parsed);
      } catch {
        setCurrentStation(DEFAULT_STATION);
      }
    } else {
      setCurrentStation(DEFAULT_STATION);
    }
  }, []);

  // 載入天氣資料
  useEffect(() => {
    if (!currentStation) return;

    async function loadTodayWeather() {
      try {
        setLoading(true);
        setError(null);
        const weatherData = await fetchTodayWeather(currentStation!.station_id);
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
  }, [currentStation]);

  // 處理站點變更
  const handleStationChange = useCallback(
    (station: StationInfoExtended, dist?: number) => {
      setCurrentStation(station);
      setDistance(dist ?? null);
      // 儲存到 localStorage
      localStorage.setItem(STATION_STORAGE_KEY, JSON.stringify(station));
    },
    []
  );

  return (
    <main className="min-h-screen bg-gradient-to-b from-blue-100 to-white">
      {/* 頁首 */}
      <header className="py-8 text-center">
        <h1 className="text-4xl font-bold text-gray-800 mb-2">好日子</h1>
        <p className="text-gray-600">歷史氣象大數據 x 傳統曆法智慧</p>
      </header>

      {/* 站點選擇器 */}
      <div className="flex flex-col items-center px-4 mb-6">
        <StationSelector
          currentStation={currentStation}
          onStationChange={handleStationChange}
        />
        {/* 距離顯示 */}
        {distance !== null && (
          <p className="mt-2 text-sm text-gray-500">
            距離您 {distance.toFixed(1)} 公里
          </p>
        )}
      </div>

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
            <div className="text-red-500 text-4xl mb-3">!</div>
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
        {data && !loading && !error && <WeatherCard data={data} />}

        {/* 農曆卡片 */}
        {data && !loading && !error && data.lunar_date && data.yi_ji && (
          <div className="mt-6 w-full max-w-md">
            <LunarCard
              lunarDate={data.lunar_date}
              yiJi={data.yi_ji}
              jieqi={data.jieqi}
            />
          </div>
        )}

        {/* 功能連結 */}
        <div className="mt-8 flex flex-wrap justify-center gap-4">
          <Link
            href="/recommend"
            className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-500 to-blue-500 text-white rounded-xl shadow-lg hover:shadow-xl transition-all"
          >
            <span className="text-xl">🔮</span>
            <span className="font-medium">好日子推薦</span>
          </Link>
          <Link
            href="/compare"
            className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-green-500 to-teal-500 text-white rounded-xl shadow-lg hover:shadow-xl transition-all"
          >
            <span className="text-xl">🗺️</span>
            <span className="font-medium">多站點比較</span>
          </Link>
        </div>

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
