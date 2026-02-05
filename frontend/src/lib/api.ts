// frontend/src/lib/api.ts
/**
 * API 客戶端
 * 與後端 FastAPI 服務通訊
 */

import {
  ApiResponse,
  ApiError,
  DailyWeatherData,
  StationInfo,
  StationInfoExtended,
  NearestStationResponse,
  DateRangeResponse,
  BestDatesResponse,
  PreferenceType,
  CompareResponse,
  HistoricalCompareResponse,
} from "./types";

// API 基礎 URL，支援環境變數設定
const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ============================================
// 通用請求處理函數
// ============================================

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorMessage = `API 錯誤: ${response.status}`;
    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorMessage;
    } catch {
      // 無法解析錯誤回應，使用預設訊息
    }
    throw new ApiError(errorMessage, response.status);
  }

  const result: ApiResponse<T> = await response.json();

  if (!result.success || result.data === undefined) {
    throw new ApiError(
      result.error || "未知錯誤",
      response.status
    );
  }

  return result.data;
}

// ============================================
// 天氣 API
// ============================================

/**
 * 查詢指定日期的歷史天氣統計
 *
 * @param stationId - 氣象站代碼（如 466920 為臺北站）
 * @param monthDay - 日期，格式為 MM-DD（如 02-04 為 2 月 4 日）
 * @returns 每日天氣統計資料
 * @throws ApiError 當 API 請求失敗時
 *
 * @example
 * const weather = await fetchDailyWeather("466920", "02-04");
 * console.log(weather.temperature.avg.mean); // 平均溫度
 */
export async function fetchDailyWeather(
  stationId: string,
  monthDay: string
): Promise<DailyWeatherData> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/weather/daily/${stationId}/${monthDay}`
  );

  return handleResponse<DailyWeatherData>(response);
}

/**
 * 查詢今日的歷史天氣統計
 *
 * @param stationId - 氣象站代碼
 * @returns 今日對應日期的歷史天氣統計資料
 * @throws ApiError 當 API 請求失敗時
 *
 * @example
 * const todayWeather = await fetchTodayWeather("466920");
 * console.log(todayWeather.precipitation.probability); // 降雨機率
 */
export async function fetchTodayWeather(
  stationId: string
): Promise<DailyWeatherData> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/weather/today/${stationId}`
  );

  return handleResponse<DailyWeatherData>(response);
}

// ============================================
// 站點 API
// ============================================

/**
 * 取得所有氣象站列表
 *
 * @returns 所有支援的氣象站資訊陣列
 * @throws ApiError 當 API 請求失敗時
 *
 * @example
 * const stations = await fetchStations();
 * stations.forEach(s => console.log(s.name)); // 臺北, 臺中, ...
 */
export async function fetchStations(): Promise<StationInfo[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/stations`);

  return handleResponse<StationInfo[]>(response);
}

/**
 * 取得單一站點資訊
 *
 * @param stationId - 氣象站代碼
 * @returns 站點詳細資訊
 * @throws ApiError 當找不到站點時
 *
 * @example
 * const station = await fetchStation("466920");
 * console.log(station.city); // 臺北市
 */
export async function fetchStation(
  stationId: string
): Promise<StationInfo> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/stations/${stationId}`
  );

  return handleResponse<StationInfo>(response);
}

/**
 * 取得所有站點（擴展版）
 * 支援依據縣市和是否有統計資料進行過濾
 *
 * @param options - 過濾選項
 * @returns 站點詳細資訊陣列
 * @throws ApiError 當 API 請求失敗時
 *
 * @example
 * const stations = await fetchStationsExtended({ hasStatistics: true });
 * stations.forEach(s => console.log(s.name, s.county));
 */
export async function fetchStationsExtended(options?: {
  county?: string;
  hasStatistics?: boolean;
}): Promise<StationInfoExtended[]> {
  const params = new URLSearchParams();
  if (options?.county) params.set("county", options.county);
  if (options?.hasStatistics !== undefined) {
    params.set("has_statistics", String(options.hasStatistics));
  }

  const url = `${API_BASE_URL}/api/v1/stations/${params.toString() ? "?" + params.toString() : ""}`;
  const response = await fetch(url);

  return handleResponse<StationInfoExtended[]>(response);
}

/**
 * 取得最近站點
 * 根據 GPS 座標找到最近的氣象站
 *
 * @param latitude - 緯度
 * @param longitude - 經度
 * @param hasStatistics - 是否僅搜尋有統計資料的站點（預設 true）
 * @returns 最近站點資訊及距離
 * @throws ApiError 當 API 請求失敗時
 *
 * @example
 * const result = await fetchNearestStation(25.0330, 121.5654);
 * console.log(result.station.name, result.distance_km);
 */
export async function fetchNearestStation(
  latitude: number,
  longitude: number,
  hasStatistics: boolean = true
): Promise<NearestStationResponse> {
  const params = new URLSearchParams({
    lat: String(latitude),
    lon: String(longitude),
    has_statistics: String(hasStatistics),
  });

  const response = await fetch(
    `${API_BASE_URL}/api/v1/stations/nearest?${params.toString()}`
  );

  return handleResponse<NearestStationResponse>(response);
}

// ============================================
// 輔助函數
// ============================================

/**
 * 格式化日期為 MM-DD 格式
 *
 * @param date - Date 物件
 * @returns MM-DD 格式的字串
 *
 * @example
 * formatMonthDay(new Date(2024, 1, 4)); // "02-04"
 */
export function formatMonthDay(date: Date): string {
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${month}-${day}`;
}

/**
 * 判斷主導天氣傾向
 *
 * @param tendency - 天氣傾向資料
 * @returns 主導天氣類型 ("sunny" | "cloudy" | "rainy" | null)
 *
 * @example
 * getDominantTendency({ sunny: 0.4, cloudy: 0.35, rainy: 0.25 }); // "sunny"
 */
export function getDominantTendency(tendency: {
  sunny: number | null;
  cloudy: number | null;
  rainy: number | null;
}): "sunny" | "cloudy" | "rainy" | null {
  const { sunny, cloudy, rainy } = tendency;

  if (sunny === null && cloudy === null && rainy === null) {
    return null;
  }

  const values: [string, number][] = [
    ["sunny", sunny ?? 0],
    ["cloudy", cloudy ?? 0],
    ["rainy", rainy ?? 0],
  ];

  const dominant = values.reduce((max, current) =>
    current[1] > max[1] ? current : max
  );

  return dominant[0] as "sunny" | "cloudy" | "rainy";
}

// ============================================
// 日期範圍查詢 API
// ============================================

/**
 * 查詢日期範圍的歷史天氣統計
 *
 * @param stationId - 氣象站代碼
 * @param startDate - 起始日期 (MM-DD)
 * @param endDate - 結束日期 (MM-DD)
 * @returns 範圍內每日統計與摘要
 * @throws ApiError 當 API 請求失敗時
 *
 * @example
 * const result = await fetchDateRange("466920", "03-01", "03-15");
 * console.log(result.summary.best_day); // 最佳日期
 */
export async function fetchDateRange(
  stationId: string,
  startDate: string,
  endDate: string
): Promise<DateRangeResponse> {
  const params = new URLSearchParams({
    start: startDate,
    end: endDate,
  });

  const response = await fetch(
    `${API_BASE_URL}/api/v1/weather/range/${stationId}?${params.toString()}`
  );

  return handleResponse<DateRangeResponse>(response);
}

// ============================================
// 最佳日期推薦 API
// ============================================

/**
 * 取得最佳日期推薦
 *
 * @param stationId - 氣象站代碼
 * @param month - 月份 (1-12)
 * @param preference - 偏好類型
 * @param limit - 推薦數量 (預設 5)
 * @returns 推薦日期列表
 * @throws ApiError 當 API 請求失敗時
 *
 * @example
 * const result = await fetchBestDates("466920", 4, "wedding", 5);
 * result.recommendations.forEach(r => console.log(r.month_day, r.score));
 */
export async function fetchBestDates(
  stationId: string,
  month: number,
  preference: PreferenceType = "sunny",
  limit: number = 5
): Promise<BestDatesResponse> {
  const params = new URLSearchParams({
    month: String(month),
    preference,
    limit: String(limit),
  });

  const response = await fetch(
    `${API_BASE_URL}/api/v1/weather/recommend/${stationId}?${params.toString()}`
  );

  return handleResponse<BestDatesResponse>(response);
}

// ============================================
// 多站點比較 API
// ============================================

/**
 * 比較多個站點在指定日期的天氣統計
 *
 * @param stationIds - 站點代碼陣列 (2-5 個)
 * @param date - 比較日期 (MM-DD)
 * @returns 多站點天氣比較結果
 * @throws ApiError 當 API 請求失敗時
 *
 * @example
 * const result = await fetchCompareStations(["466920", "467490", "467440"], "03-15");
 * console.log(result.best_station); // 晴天率最高的站點
 */
export async function fetchCompareStations(
  stationIds: string[],
  date: string
): Promise<CompareResponse> {
  const params = new URLSearchParams({
    stations: stationIds.join(","),
    date,
  });

  const response = await fetch(
    `${API_BASE_URL}/api/v1/weather/compare?${params.toString()}`
  );

  return handleResponse<CompareResponse>(response);
}

// ============================================
// 歷史同期比較 API
// ============================================

/**
 * 取得歷史同期比較資料
 *
 * @param stationId - 氣象站代碼
 * @returns 今日即時天氣與歷史統計的比較結果
 * @throws ApiError 當 API 請求失敗時
 *
 * @example
 * const result = await fetchHistoricalCompare("466920");
 * console.log(result.summary); // 綜合評語
 */
export async function fetchHistoricalCompare(
  stationId: string
): Promise<HistoricalCompareResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/weather/historical/${stationId}`
  );

  return handleResponse<HistoricalCompareResponse>(response);
}
