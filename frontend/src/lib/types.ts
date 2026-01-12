/**
 * Type definitions for Ministry Analytics Platform
 */

// Content type classification
export type ContentType = "PREACHING" | "MUSIC" | "UNKNOWN";

// Language detection
export type Language = "FR" | "EN" | "UNKNOWN";

// Video metadata from database
export interface Video {
  video_id: string;
  title: string;
  description?: string;
  duration?: number;
  upload_date?: string;
  view_count?: number;
  like_count?: number;
  thumbnail_url?: string;
  channel_name?: string;
  channel_id?: string;
  channel_url?: string;
  video_url?: string;
  content_type: ContentType;
  confidence_score: number;
  needs_review: boolean;
  language_detected: Language;
  fetched_at?: string;
  search_query_used?: string;
}

// Channel breakdown
export interface ChannelStats {
  name: string;
  count: number;
}

// Content type breakdown
export interface ContentTypeStats {
  PREACHING?: number;
  MUSIC?: number;
  UNKNOWN?: number;
}

// Language breakdown
export interface LanguageStats {
  FR?: number;
  EN?: number;
  UNKNOWN?: number;
}

// API Stats Response
export interface StatsResponse {
  total_videos: number;
  by_content_type: ContentTypeStats;
  by_language: LanguageStats;
  needs_review: number;
  unique_channels: number;
  total_preaching_hours: number;
  oldest_video?: string;
  newest_video?: string;
  top_channels: ChannelStats[];
}

// API Videos Response
export interface VideosResponse {
  videos: Video[];
  total: number;
}

// Navigation item
export interface NavItem {
  label: string;
  href: string;
  icon: string;
}

// KPI Card data
export interface KPIData {
  label: string;
  value: string | number;
  icon?: React.ReactNode;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  color?: "primary" | "secondary" | "success" | "warning" | "danger";
}

// Year grouping
export interface YearGroup {
  year: string;
  count: number;
  total_duration: number;
}

// Month grouping
export interface MonthGroup {
  year: string;
  month: number;
  month_name: string;
  year_month: string;
  count: number;
  total_duration: number;
}

// Week grouping
export interface WeekGroup {
  week_start: string;
  week_end: string;
  week_label: string;
  count: number;
  total_duration: number;
}

// API responses for groupings
export interface YearsResponse {
  years: YearGroup[];
}

export interface MonthsResponse {
  months: MonthGroup[];
}

export interface WeeksResponse {
  weeks: WeekGroup[];
}

export interface ChannelsResponse {
  channels: ChannelStats[];
}

// Place grouping
export interface PlaceStats {
  name: string;
  count: number;
  total_duration: number;
}

export interface PlacesResponse {
  places: PlaceStats[];
}

// Analytics types
export interface AnalyticsTrends {
  sermonsChange: number;
  hoursChange: number;
  durationChange: number;
  viewsChange: number;
}

export interface AnalyticsSummary {
  totalSermons: number;
  totalHours: number;
  avgDuration: number;
  totalViews: number;
  trends: AnalyticsTrends;
}

export interface TimeSeriesPoint {
  period: string;
  value: number;
  average?: number;
}

export interface TimeSeriesData {
  data: TimeSeriesPoint[];
  period: "year" | "month" | "week";
}

export interface AnalyticsSummaryResponse {
  summary: AnalyticsSummary;
}

export interface TimeSeriesResponse {
  data: TimeSeriesPoint[];
  period: string;
}

// Pie Chart Types
export interface YearDistributionPoint {
  year: string;
  value: number;
  percentage: number;
}

export interface YearDistributionResponse {
  data: YearDistributionPoint[];
  busiestYear: string | null;
  totalSermons: number;
}

// Monthly breakdown for selected year
export interface MonthlyBreakdown {
  month: string;
  monthNum: number;
  value: number;
}

export interface MonthsByYearResponse {
  data: MonthlyBreakdown[];
  year: number;
  busiestMonth: string | null;
  totalSermons: number;
}

// Busiest months histogram
export interface BusiestMonthPoint {
  month: string;
  monthNum: number;
  total: number;
  average: number;
}

export interface BusiestMonthsResponse {
  data: BusiestMonthPoint[];
}

// Year-specific summary (for 2025 tab)
export interface YearSummary {
  year: number;
  totalSermons: number;
  totalHours: number;
  avgDuration: number;
  totalViews: number;
  busiestMonth: string | null;
  trends: {
    sermonsChange: number;
    hoursChange: number;
    viewsChange: number;
  };
}

// =============================================================================
// MAP TYPES
// =============================================================================

export interface MapLocation {
  name: string;
  country: string;
  lat: number;
  lng: number;
  sermonCount: number;
  isHomeBase: boolean;
}

export interface MapLocationsResponse {
  locations: MapLocation[];
}

export interface Journey {
  date: string;
  from: string;
  to: string;
  fromCoords: [number, number];
  toCoords: [number, number];
  distanceKm: number;
  estimatedHours: number;
}

export interface JourneysResponse {
  journeys: Journey[];
  totalTrips: number;
  totalDistanceKm: number;
  countriesVisited: number;
}

export interface TravelStatsByYear {
  year: string;
  trips: number;
  distanceKm: number;
}

export interface TravelStatsByMonth {
  month: string;
  trips: number;
}

export interface TravelStatsResponse {
  byYear: TravelStatsByYear[];
  byMonth: TravelStatsByMonth[];
  totalTrips: number;
  totalDistanceKm: number;
  countriesVisited: number;
  citiesVisited: number;
}

// =============================================================================
// FORECASTING TYPES
// =============================================================================

export interface ForecastHistoricalPoint {
  period: string;
  value: number;
  duration?: number;
}

export interface ForecastPrediction {
  period: string;
  month: string;
  value: number;
  lower: number;
  upper: number;
}

export interface ForecastModelMetrics {
  mae: number;
  rmse: number;
  samples: number;
}

export interface SermonForecastResponse {
  historical: ForecastHistoricalPoint[];
  predictions: ForecastPrediction[];
  totalPredicted: number;
  confidence: number;
  modelMetrics: ForecastModelMetrics;
  error?: string;
}

export interface TripPrediction {
  period: string;
  month: string;
  trips: number;
}

export interface TripHistoricalPoint {
  period: string;
  trips: number;
}

export interface TripForecastResponse {
  historical: TripHistoricalPoint[];
  predictions: TripPrediction[];
  totalPredicted: number;
  predictedDistanceKm: number;
  modelMetrics: ForecastModelMetrics;
  error?: string;
}

export interface ModelStatus {
  trained: boolean;
  lastUpdated?: string;
  samples?: number;
  mae?: number;
  rmse?: number;
}

export interface ForecastModelStatusResponse {
  sermonModel: ModelStatus;
  tripModel: ModelStatus;
  xgboostAvailable: boolean;
}

// =============================================================================
// HEALTH INSIGHTS TYPES
// =============================================================================

export interface HealthScoreBreakdown {
  weeklyWorkload: number;
  monthlyTravel: number;
  hoursPreached: number;
  restDeficit: number;
  upcomingLoad: number;
}

export interface HealthScore {
  score: number;
  status: "good" | "moderate" | "high";
  breakdown: HealthScoreBreakdown;
}

export interface HealthMetrics {
  sermonsThisWeek: number;
  hoursThisWeek: number;
  sermonsThisMonth: number;
  hoursThisMonth: number;
  tripsThisMonth: number;
  daysSinceRest: number;
  consecutiveBusyWeeks: number;
  travelThisMonthKm: number;
  calculatedAt: string;
}

export interface HealthReport {
  generatedAt: string;
  score: HealthScore;
  metrics: HealthMetrics;
  summary: string;
  concerns: string[];
  restRecommendations: string[];
  sleepGuidelines: string[];
  holidayRecommendations: string[];
  positiveObservations: string[];
  ollamaAvailable: boolean;
  aiGenerated: boolean;
  error?: string;
}

export interface WorkloadTrend {
  week_start: string;
  sermons: number;
  hours: number;
}

export interface HealthTrendsResponse {
  trends: WorkloadTrend[];
  error?: string;
}

// =============================================================================
// PLANNING TYPES
// =============================================================================

export interface TripRecommendation {
  destination: string;
  suggestedPeriod: string;
  reason: string;
  priority: "high" | "medium" | "low";
}

export interface MeetingSuggestion {
  type: string;
  suggestedDay: string;
  suggestedTime: string;
  reason: string;
}

export interface RestWindow {
  start: string;
  end: string;
  type: "rest" | "ministry" | "travel";
  note: string;
}

export interface MonthlyPattern {
  month: string;
  avgSermons: number;
}

export interface DailyPattern {
  day: string;
  sermons: number;
}

export interface LocationFrequency {
  location: string;
  count: number;
}

export interface HistoricalPatterns {
  monthlyPatterns: MonthlyPattern[];
  dailyPatterns: DailyPattern[];
  busiestMonth: string;
  quietestMonth: string;
  locationFrequency: LocationFrequency[];
  totalSermons: number;
  yearsOfData: number;
}

export interface UpcomingMonth {
  month: number;
  year: number;
  monthName: string;
  predictedSermons: number;
  predictedTrips: number;
  healthScore: number;
  busyDays: string[];
}

export interface UpcomingPredictions {
  nextMonth: UpcomingMonth;
  error?: string;
}

export interface PlanningReport {
  generatedAt: string;
  upcomingOverview: string;
  tripRecommendations: TripRecommendation[];
  meetingSuggestions: MeetingSuggestion[];
  restWindows: RestWindow[];
  highDemandWarnings: string[];
  patterns: HistoricalPatterns;
  upcoming: UpcomingPredictions;
  ollamaAvailable: boolean;
  aiGenerated: boolean;
  error?: string;
}

// =============================================================================
// AI STATUS TYPES
// =============================================================================

export interface AIStatus {
  available: boolean;
  model: string | null;
  models?: string[];
  hasRequestedModel?: boolean;
  message: string;
}

// =============================================================================
// PREACHER TYPES
// =============================================================================

export interface Preacher {
  id: number;
  name: string;
  aliases: string[];
  title?: string;
  primary_church?: string;
  bio?: string;
  is_active: boolean;
  created_at?: string;
  video_count?: number;
}

export interface PreacherCreate {
  name: string;
  title?: string;
  primary_church?: string;
  bio?: string;
}

export interface PreachersResponse {
  preachers: Preacher[];
  total: number;
}

export interface PreacherPhoto {
  id: number;
  preacher_id: number;
  file_path: string;
  original_filename: string;
  uploaded_at: string;
  data?: string;
  mime_type?: string;
}

export interface PreacherPhotosResponse {
  photos: PreacherPhoto[];
  total: number;
}

export interface PreacherFetchResult {
  status: string;
  preacher_id: number;
  platform: string;
  videos_found: number;
  videos_added: number;
  videos_updated: number;
  errors: string[];
}

export interface PreacherSearchQueries {
  preacher_id: number;
  preacher_name: string;
  youtube: string[];
  facebook: string[];
}

// =============================================================================
// PLATFORM TYPES
// =============================================================================

export interface PlatformStats {
  name: string;
  count: number;
  total_duration?: number;
}

export interface PlatformBreakdown {
  youtube: number;
  facebook: number;
  hours_by_platform: {
    youtube?: number;
    facebook?: number;
  };
}

export interface PlatformResponse {
  platforms: PlatformStats[];
}

export interface PlatformVideosResponse {
  videos: Video[];
  total: number;
  platform: string;
}
