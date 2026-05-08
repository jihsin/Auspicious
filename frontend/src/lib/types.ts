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

// ============================================
// 歷史同期比較相關型別
// ============================================

export interface RealtimeWeatherInfo {
  obs_time: string | null;
  weather: string | null;
  temp: number | null;
  temp_max: number | null;
  temp_min: number | null;
  humidity: number | null;
  precipitation: number | null;
}

export interface HistoricalComparison {
  metric: string;
  current: number | null;
  historical_avg: number | null;
  difference: number | null;
  percentile: number | null;
  status: "normal" | "above_normal" | "below_normal" | "extreme";
}

// ============================================
// Phase 3.1 年代分層統計相關型別
// ============================================

export interface ExtremeRecord {
  value: number;
  year: number;
}

export interface ExtremeRecords {
  max_temp: ExtremeRecord | null;
  min_temp: ExtremeRecord | null;
  max_precip: ExtremeRecord | null;
}

export interface DecadeStats {
  decade: string;         // "1990s", "2000s", "2010s", "2020s"
  start_year: number;
  end_year: number;
  years_count: number;
  temp_avg: number | null;
  temp_max_avg: number | null;
  temp_min_avg: number | null;
  precip_prob: number | null;
  precip_avg: number | null;
}

export interface ClimateTrend {
  trend_per_decade: number;
  interpretation: string;
  data_years: number;
}

export interface HistoricalCompareResponse {
  station: StationInfo;
  date: string;
  realtime: RealtimeWeatherInfo | null;
  comparisons: HistoricalComparison[];
  summary: string;
  lunar_date?: LunarDateInfo;
  jieqi?: string | null;
  // Phase 3.1 年代分層統計
  percentile?: number | null;
  extreme_records?: ExtremeRecords | null;
  decades?: DecadeStats[] | null;
  climate_trend?: ClimateTrend | null;
}

// ============================================
// Phase 3.2 節氣相關型別
// ============================================

export interface SolarTermInfo {
  name: string;
  name_en: string;
  order: number;
  season: string;
  solar_longitude: number;
  typical_date: string;
  astronomy: string;
  agriculture: string;
  weather: string;
  phenology: string[];
  proverbs: string[];
  health_tips: string;
}

export interface CurrentSolarTermResponse {
  current_term: string | null;
  nearest_term: string;
  days_until_next: number;
  next_term: string;
}

// ============================================
// Phase 3.4 活動規劃相關型別
// ============================================

export interface ActivityType {
  type: string;
  key: string;
  description: string;
}

export interface DayScore {
  date: string;
  score: number;
  weather_score: number;
  rain_probability: number;
  temp_avg: number;
  sunny_ratio: number;
  solar_term: string | null;
  lunar_date: string;
  lunar_yi: string[];
  lunar_ji: string[];
  notes: string[];
}

export interface PlannerResult {
  activity_type: string;
  location: string;
  station_id: string;
  station_name: string;
  date_range: [string, string];
  recommendations: DayScore[];
  best_date: DayScore | null;
  summary: string;
}

// ============================================
// DayInsight 相關型別 (T7)
// 對應 backend/app/schemas/day_insight.py
// ============================================

export interface DayInsightLabel {
  text: string | null;
  category: "seasonal" | "anomaly" | "record" | "solar_term" | null;
}

export interface DayInsightCore {
  metric: "precip_probability";
  value: number;
  anomaly_year: number;
  anomaly_month: number;
}

export interface DayInsightSideBadge {
  metric: "temp_avg" | "humidity_avg";
  label: string;
  direction: "above" | "below";
  z_score: number;
}

export interface DayInsightExtremeRecord {
  year: number;
  value: number;
}

export interface DayInsightExtremes {
  wettest: DayInsightExtremeRecord | null;
  driest: DayInsightExtremeRecord | null;
}

export interface DayInsightMeta {
  years_analyzed: number;
  start_year: number;
  end_year: number;
}

export interface DayInsight {
  station_id: string;
  month: number;
  day: number;
  label: DayInsightLabel;
  core: DayInsightCore;
  side_badges: DayInsightSideBadge[];
  extremes: DayInsightExtremes;
  meta: DayInsightMeta;
}

// ============================================
// Divination 卦象詮釋型別 (T16)
// 對應 backend/app/schemas/day_insight.py Divination block
// ============================================

export interface HexagramRef {
  num: number;
  name: string;
  judgement?: string | null;
  image?: string | null;
  upper_trigram?: string | null;
  lower_trigram?: string | null;
  weather_persona?: string;  // NEW · ≤30 字 weather-relatable life advice
}

export interface DivinationNarrative {
  climate_portrait: string;
  anomaly_layer: string;
  imagination: string;
  headline: string;        // NEW · ≤12 字
  subtitle: string;        // NEW · ≤30 字
  tags: string[];          // NEW · 3 個 ≤4 字
}

export interface YaoCiEntry {
  original: string;
  vernacular: string;
}

export interface Divination {
  ben: HexagramRef;
  zhi: HexagramRef;
  cuo: HexagramRef;
  zong: HexagramRef;
  hu: HexagramRef;
  changing_positions: number[];
  line_values: number[];
  narrative: DivinationNarrative;
  var_yao_ci: Record<number, YaoCiEntry>;  // NEW
}

export interface DayInsightInterpretation {
  station_id: string;
  month: number;
  day: number;
  divination: Divination;
}
