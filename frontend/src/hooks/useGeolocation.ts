// frontend/src/hooks/useGeolocation.ts
"use client";

/**
 * GPS 定位 Hook
 * 提供瀏覽器地理位置 API 的 React 封裝
 */

import { useState, useCallback, useRef } from "react";
import { GeoLocation, LocationStatus } from "@/lib/types";

interface UseGeolocationOptions {
  enableHighAccuracy?: boolean;
  timeout?: number;
  maximumAge?: number;
}

interface UseGeolocationReturn {
  location: GeoLocation | null;
  status: LocationStatus;
  error: string | null;
  requestLocation: () => void;
}

const defaultOptions: UseGeolocationOptions = {
  enableHighAccuracy: true,
  timeout: 10000,
  maximumAge: 60000, // 1 分鐘快取
};

export function useGeolocation(
  options: UseGeolocationOptions = {}
): UseGeolocationReturn {
  const [location, setLocation] = useState<GeoLocation | null>(null);
  const [status, setStatus] = useState<LocationStatus>("idle");
  const [error, setError] = useState<string | null>(null);

  // 使用 ref 儲存選項，避免每次渲染都重新建立 callback
  const optionsRef = useRef({ ...defaultOptions, ...options });
  optionsRef.current = { ...defaultOptions, ...options };

  const requestLocation = useCallback(() => {
    if (!navigator.geolocation) {
      setStatus("error");
      setError("您的瀏覽器不支援定位功能");
      return;
    }

    setStatus("loading");
    setError(null);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocation({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy,
        });
        setStatus("success");
      },
      (err) => {
        switch (err.code) {
          case err.PERMISSION_DENIED:
            setStatus("denied");
            setError("您拒絕了定位權限請求");
            break;
          case err.POSITION_UNAVAILABLE:
            setStatus("error");
            setError("無法取得您的位置");
            break;
          case err.TIMEOUT:
            setStatus("error");
            setError("定位請求逾時");
            break;
          default:
            setStatus("error");
            setError("定位時發生未知錯誤");
        }
      },
      optionsRef.current
    );
  }, []);

  return { location, status, error, requestLocation };
}
