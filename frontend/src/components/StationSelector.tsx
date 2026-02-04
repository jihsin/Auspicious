// frontend/src/components/StationSelector.tsx
"use client";

/**
 * 站點選擇器組件
 * 提供 GPS 定位和手動選擇站點功能
 */

import { useState, useEffect, useCallback } from "react";
import { StationInfoExtended } from "@/lib/types";
import { fetchStationsExtended, fetchNearestStation } from "@/lib/api";
import { useGeolocation } from "@/hooks/useGeolocation";

interface StationSelectorProps {
  currentStation: StationInfoExtended | null;
  onStationChange: (station: StationInfoExtended, distance?: number) => void;
}

export default function StationSelector({
  currentStation,
  onStationChange,
}: StationSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [stations, setStations] = useState<StationInfoExtended[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [gpsLoading, setGpsLoading] = useState(false);

  const { location, status, error, requestLocation } = useGeolocation();

  // 載入站點列表
  useEffect(() => {
    if (isOpen && stations.length === 0) {
      setLoading(true);
      fetchStationsExtended({ hasStatistics: true })
        .then(setStations)
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [isOpen, stations.length]);

  // GPS 定位成功後取得最近站點
  useEffect(() => {
    if (location && status === "success" && gpsLoading) {
      fetchNearestStation(location.latitude, location.longitude, true)
        .then((result) => {
          onStationChange(result.station, result.distance_km);
          setIsOpen(false);
        })
        .catch(console.error)
        .finally(() => setGpsLoading(false));
    }
  }, [location, status, gpsLoading, onStationChange]);

  // 處理 GPS 定位請求
  const handleGpsRequest = useCallback(() => {
    setGpsLoading(true);
    requestLocation();
  }, [requestLocation]);

  // 處理定位失敗時重設 loading 狀態
  useEffect(() => {
    if (status === "error" || status === "denied") {
      setGpsLoading(false);
    }
  }, [status]);

  // 過濾站點
  const filteredStations = stations.filter(
    (s) =>
      s.name.includes(searchQuery) ||
      s.county?.includes(searchQuery) ||
      s.town?.includes(searchQuery)
  );

  // 點擊外部關閉選單
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (isOpen && !target.closest("[data-station-selector]")) {
        setIsOpen(false);
        setSearchQuery("");
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isOpen]);

  return (
    <div className="relative" data-station-selector>
      {/* 當前站點顯示 */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-4 py-2 bg-white rounded-lg shadow hover:shadow-md transition-shadow"
      >
        <span className="text-lg font-semibold">
          {currentStation?.name || "選擇站點"}
        </span>
        {currentStation?.county && (
          <span className="text-sm text-gray-500">{currentStation.county}</span>
        )}
        <svg
          className={`w-4 h-4 transition-transform ${isOpen ? "rotate-180" : ""}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {/* 下拉選單 */}
      {isOpen && (
        <div className="absolute top-full left-0 mt-2 w-80 bg-white rounded-lg shadow-lg z-50 max-h-96 overflow-hidden">
          {/* GPS 定位按鈕 */}
          <div className="p-3 border-b">
            <button
              onClick={handleGpsRequest}
              disabled={status === "loading" || gpsLoading}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {status === "loading" || gpsLoading ? (
                <>
                  <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  定位中...
                </>
              ) : (
                <>
                  <svg
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                    />
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                  </svg>
                  使用 GPS 定位
                </>
              )}
            </button>
            {error && <p className="mt-2 text-sm text-red-500">{error}</p>}
          </div>

          {/* 搜尋框 */}
          <div className="p-3 border-b">
            <input
              type="text"
              placeholder="搜尋站點名稱或地區..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* 站點列表 */}
          <div className="max-h-60 overflow-y-auto">
            {loading ? (
              <div className="p-4 text-center text-gray-500">
                <span className="inline-block w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mr-2" />
                載入中...
              </div>
            ) : filteredStations.length === 0 ? (
              <div className="p-4 text-center text-gray-500">
                找不到符合的站點
              </div>
            ) : (
              filteredStations.map((station) => (
                <button
                  key={station.station_id}
                  onClick={() => {
                    onStationChange(station);
                    setIsOpen(false);
                    setSearchQuery("");
                  }}
                  className={`w-full px-4 py-3 text-left hover:bg-gray-50 border-b last:border-b-0 transition-colors ${
                    currentStation?.station_id === station.station_id
                      ? "bg-blue-50"
                      : ""
                  }`}
                >
                  <div className="font-medium">{station.name}</div>
                  <div className="text-sm text-gray-500">
                    {station.county} {station.town}
                  </div>
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
