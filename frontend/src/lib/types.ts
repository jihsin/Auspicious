// frontend/src/lib/types.ts
/**
 * TypeScript 型別定義
 * 與後端 API (backend/app/schemas/weather.py) 保持一致
 */

// ============================================
// 站點相關型別
// ============================================

export interface StationInfo {
  station_id: string;
  name: string;
  city: string;
}

// ============================================
// 溫度相關型別
// ============================================

export interface TemperatureStats {
  mean: number | null;
  median: number | null;
  stddev: number | null;
}

export interface TemperatureRecord {
  value: number | null;
}

export interface TemperatureResponse {
  avg: TemperatureStats;
  max_mean: number | null;
  max_record: TemperatureRecord;
  min_mean: number | null;
  min_record: TemperatureRecord;
}

// ============================================
// 降水相關型別
// ============================================

export interface PrecipitationResponse {
  probability: number | null;
  avg_when_rain: number | null;
  heavy_probability: number | null;
  max_record: number | null;
}

// ============================================
// 天氣傾向型別
// ============================================

export interface WeatherTendencyResponse {
  sunny: number | null;
  cloudy: number | null;
  rainy: number | null;
}

// ============================================
// 分析期間型別
// ============================================

export interface AnalysisPeriod {
  years_analyzed: number | null;
  start_year: number | null;
  end_year: number | null;
}

// ============================================
// 每日天氣完整回應
// ============================================

export interface DailyWeatherData {
  station: StationInfo;
  month_day: string; // MM-DD 格式
  analysis_period: AnalysisPeriod;
  temperature: TemperatureResponse;
  precipitation: PrecipitationResponse;
  tendency: WeatherTendencyResponse;
  computed_at: string; // ISO 8601 日期時間格式
}

// ============================================
// API 回應包裝型別
// ============================================

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

// ============================================
// API 錯誤型別
// ============================================

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public detail?: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// ============================================
// 站點相關型別（擴展）
// ============================================

export interface StationInfoExtended {
  station_id: string;
  name: string;
  county: string | null;
  town: string | null;
  latitude: number;
  longitude: number;
  altitude: number | null;
  has_statistics: boolean;
}

export interface NearestStationResponse {
  station: StationInfoExtended;
  distance_km: number;
}

// ============================================
// GPS 定位相關型別
// ============================================

export interface GeoLocation {
  latitude: number;
  longitude: number;
  accuracy: number;
}

export type LocationStatus = "idle" | "loading" | "success" | "error" | "denied";
