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
  // 農曆資訊（可選）
  lunar_date?: LunarDateInfo;
  yi_ji?: YiJiInfo;
  jieqi?: string | null;
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

// ============================================
// 農曆相關型別
// ============================================

export interface LunarDateInfo {
  year: number;
  month: number;
  day: number;
  year_cn: string;
  month_cn: string;
  day_cn: string;
  干支年: string;
  干支月: string;
  干支日: string;
  生肖: string;
  is_leap: boolean;
}

export interface YiJiInfo {
  yi: string[];  // 宜
  ji: string[];  // 忌
}

// ============================================
// 日期範圍查詢相關型別
// ============================================

export interface DailyWeatherSummary {
  month_day: string;
  temp_avg: number | null;
  temp_max: number | null;
  temp_min: number | null;
  precip_prob: number | null;
  sunny_rate: number | null;
  lunar_date?: LunarDateInfo;
  jieqi?: string | null;
}

export interface RangeSummary {
  avg_temp: number | null;
  avg_precip_prob: number | null;
  avg_sunny_rate: number | null;
  best_day: string | null;
  worst_day: string | null;
}

export interface DateRangeResponse {
  station: StationInfo;
  start_date: string;
  end_date: string;
  days: DailyWeatherSummary[];
  summary: RangeSummary;
}

// ============================================
// 最佳日期推薦相關型別
// ============================================

export interface RecommendedDate {
  month_day: string;
  score: number;
  reason: string;
  temp_avg: number | null;
  precip_prob: number | null;
  sunny_rate: number | null;
  lunar_date?: LunarDateInfo;
  jieqi?: string | null;
}

export interface BestDatesResponse {
  station: StationInfo;
  month: number;
  preference: string;
  recommendations: RecommendedDate[];
}

export type PreferenceType = "sunny" | "mild" | "cool" | "outdoor" | "wedding";

// ============================================
// 多站點比較相關型別
// ============================================

export interface StationWeatherComparison {
  station: StationInfo;
  temp_avg: number | null;
  temp_max: number | null;
  temp_min: number | null;
  precip_prob: number | null;
  sunny_rate: number | null;
  years_analyzed: number | null;
  rank: number | null;
}

export interface CompareResponse {
  date: string;
  stations: StationWeatherComparison[];
  best_station: string | null;
  lunar_date?: LunarDateInfo;
  jieqi?: string | null;
}
