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
