/**
 * API Client for Ministry Analytics Platform
 */

import {
  StatsResponse,
  VideosResponse,
  YearsResponse,
  MonthsResponse,
  WeeksResponse,
  ChannelsResponse,
  PlacesResponse,
  AnalyticsSummaryResponse,
  TimeSeriesResponse,
  YearDistributionResponse,
  MonthsByYearResponse,
  BusiestMonthsResponse,
  YearSummary,
  MapLocationsResponse,
  JourneysResponse,
  TravelStatsResponse,
  SermonForecastResponse,
  TripForecastResponse,
  ForecastModelStatusResponse,
  HealthScore,
  HealthMetrics,
  HealthReport,
  WorkloadTrend,
  PlanningReport,
  UpcomingPredictions,
  HistoricalPatterns,
  AIStatus,
  Preacher,
  PreacherCreate,
  PreachersResponse,
  PreacherPhotosResponse,
  PreacherFetchResult,
  PreacherSearchQueries,
} from "./types";

// API base URL - change this to your backend URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Generic fetch wrapper with error handling
 */
async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`Failed to fetch ${endpoint}:`, error);
    throw error;
  }
}

/**
 * API Methods
 */
export const api = {
  /**
   * Get dashboard statistics
   */
  getStats: async (): Promise<StatsResponse> => {
    return fetchAPI<StatsResponse>("/api/stats");
  },

  /**
   * Get videos with optional limit
   */
  getVideos: async (limit: number = 10): Promise<VideosResponse> => {
    return fetchAPI<VideosResponse>(`/api/videos?limit=${limit}`);
  },

  /**
   * Get all sermons (preaching videos)
   */
  getSermons: async (params?: {
    limit?: number;
    offset?: number;
    channel?: string;
    language?: string;
    year?: number;
    month?: number;
    place?: string;
  }): Promise<VideosResponse> => {
    const searchParams = new URLSearchParams();

    if (params?.limit) searchParams.set("limit", params.limit.toString());
    if (params?.offset) searchParams.set("offset", params.offset.toString());
    if (params?.channel) searchParams.set("channel", params.channel);
    if (params?.language) searchParams.set("language", params.language);
    if (params?.year) searchParams.set("year", params.year.toString());
    if (params?.month) searchParams.set("month", params.month.toString());
    if (params?.place) searchParams.set("place", params.place);

    const query = searchParams.toString();
    return fetchAPI<VideosResponse>(`/api/videos${query ? `?${query}` : ""}`);
  },

  /**
   * Get videos grouped by year
   */
  getVideosByYear: async (): Promise<YearsResponse> => {
    return fetchAPI<YearsResponse>("/api/videos/by-year");
  },

  /**
   * Get videos grouped by month
   */
  getVideosByMonth: async (year?: number): Promise<MonthsResponse> => {
    const query = year ? `?year=${year}` : "";
    return fetchAPI<MonthsResponse>(`/api/videos/by-month${query}`);
  },

  /**
   * Get videos from recent weeks
   */
  getVideosRecentWeeks: async (): Promise<WeeksResponse> => {
    return fetchAPI<WeeksResponse>("/api/videos/recent-weeks");
  },

  /**
   * Get videos grouped by channel
   */
  getVideosByChannel: async (): Promise<ChannelsResponse> => {
    return fetchAPI<ChannelsResponse>("/api/videos/by-channel");
  },

  /**
   * Get videos grouped by place/location
   */
  getVideosByPlace: async (): Promise<PlacesResponse> => {
    return fetchAPI<PlacesResponse>("/api/videos/by-place");
  },

  // =========================================================================
  // ANALYTICS API
  // =========================================================================

  /**
   * Get analytics summary with KPIs and trends
   */
  getAnalyticsSummary: async (): Promise<AnalyticsSummaryResponse> => {
    return fetchAPI<AnalyticsSummaryResponse>("/api/analytics/summary");
  },

  /**
   * Get sermon counts by time period
   */
  getSermonsByPeriod: async (period: "year" | "month" | "week" = "year"): Promise<TimeSeriesResponse> => {
    return fetchAPI<TimeSeriesResponse>(`/api/analytics/sermons-by-period?period=${period}`);
  },

  /**
   * Get duration statistics by time period
   */
  getDurationByPeriod: async (period: "year" | "month" | "week" = "year"): Promise<TimeSeriesResponse> => {
    return fetchAPI<TimeSeriesResponse>(`/api/analytics/duration-by-period?period=${period}`);
  },

  /**
   * Get view statistics by time period
   */
  getViewsByPeriod: async (period: "year" | "month" | "week" = "year"): Promise<TimeSeriesResponse> => {
    return fetchAPI<TimeSeriesResponse>(`/api/analytics/views-by-period?period=${period}`);
  },

  // =========================================================================
  // PIE CHART & HISTOGRAM API
  // =========================================================================

  /**
   * Get year distribution for pie chart
   */
  getYearDistribution: async (): Promise<YearDistributionResponse> => {
    return fetchAPI<YearDistributionResponse>("/api/analytics/year-distribution");
  },

  /**
   * Get monthly breakdown for a specific year
   */
  getMonthsByYear: async (year: number): Promise<MonthsByYearResponse> => {
    return fetchAPI<MonthsByYearResponse>(`/api/analytics/months-by-year?year=${year}`);
  },

  /**
   * Get busiest months histogram data
   */
  getBusiestMonths: async (): Promise<BusiestMonthsResponse> => {
    return fetchAPI<BusiestMonthsResponse>("/api/analytics/busiest-months");
  },

  /**
   * Get year-specific summary (for 2025 tab)
   */
  getYearSummary: async (year: number): Promise<YearSummary> => {
    return fetchAPI<YearSummary>(`/api/analytics/year-summary?year=${year}`);
  },

  // =========================================================================
  // MAP API
  // =========================================================================

  /**
   * Get all locations with coordinates and sermon counts
   */
  getMapLocations: async (): Promise<MapLocationsResponse> => {
    return fetchAPI<MapLocationsResponse>("/api/map/locations");
  },

  /**
   * Get travel journeys (optionally filtered by year)
   */
  getMapJourneys: async (year?: number): Promise<JourneysResponse> => {
    const query = year ? `?year=${year}` : "";
    return fetchAPI<JourneysResponse>(`/api/map/journeys${query}`);
  },

  /**
   * Get travel statistics by year and month
   */
  getTravelStats: async (): Promise<TravelStatsResponse> => {
    return fetchAPI<TravelStatsResponse>("/api/map/travel-stats");
  },

  // =========================================================================
  // FORECASTING API
  // =========================================================================

  /**
   * Get sermon predictions for 2026
   */
  getSermonForecast: async (): Promise<SermonForecastResponse> => {
    return fetchAPI<SermonForecastResponse>("/api/forecast/sermons");
  },

  /**
   * Get trip predictions for 2026
   */
  getTripForecast: async (): Promise<TripForecastResponse> => {
    return fetchAPI<TripForecastResponse>("/api/forecast/trips");
  },

  /**
   * Get forecast model status
   */
  getForecastModelStatus: async (): Promise<ForecastModelStatusResponse> => {
    return fetchAPI<ForecastModelStatusResponse>("/api/forecast/model-status");
  },

  /**
   * Retrain forecast models
   */
  retrainForecastModels: async (): Promise<{ success: boolean; message: string }> => {
    return fetchAPI<{ success: boolean; message: string }>("/api/forecast/retrain", {
      method: "POST",
    });
  },

  // =========================================================================
  // HEALTH & PLANNING API
  // =========================================================================

  /**
   * Get the current health score
   */
  getHealthScore: async (): Promise<HealthScore> => {
    return fetchAPI<HealthScore>("/api/health/score");
  },

  /**
   * Get detailed health metrics
   */
  getHealthMetrics: async (): Promise<HealthMetrics> => {
    return fetchAPI<HealthMetrics>("/api/health/metrics");
  },

  /**
   * Get the full AI-generated health report
   */
  getHealthReport: async (): Promise<HealthReport> => {
    return fetchAPI<HealthReport>("/api/health/report");
  },

  /**
   * Get workload trend data for charts
   */
  getHealthTrends: async (): Promise<WorkloadTrend[]> => {
    return fetchAPI<WorkloadTrend[]>("/api/health/trends");
  },

  /**
   * Get the full AI-generated planning report
   */
  getPlanningReport: async (): Promise<PlanningReport> => {
    return fetchAPI<PlanningReport>("/api/planning/report");
  },

  /**
   * Get upcoming forecast predictions for planning
   */
  getUpcomingPredictions: async (): Promise<UpcomingPredictions> => {
    return fetchAPI<UpcomingPredictions>("/api/planning/upcoming");
  },

  /**
   * Get historical ministry patterns for planning
   */
  getHistoricalPatterns: async (): Promise<HistoricalPatterns> => {
    return fetchAPI<HistoricalPatterns>("/api/planning/patterns");
  },

  /**
   * Get the status of the AI (Ollama) service
   */
  getAIStatus: async (): Promise<AIStatus> => {
    return fetchAPI<AIStatus>("/api/ai/status");
  },

  // =========================================================================
  // PREACHER API
  // =========================================================================

  /**
   * Create a new preacher
   */
  createPreacher: async (data: PreacherCreate): Promise<Preacher> => {
    return fetchAPI<Preacher>("/api/preachers", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  /**
   * Get all preachers
   */
  getPreachers: async (): Promise<PreachersResponse> => {
    return fetchAPI<PreachersResponse>("/api/preachers");
  },

  /**
   * Get a preacher by ID
   */
  getPreacher: async (preacherId: number): Promise<Preacher> => {
    return fetchAPI<Preacher>(`/api/preachers/${preacherId}`);
  },

  /**
   * Update a preacher
   */
  updatePreacher: async (preacherId: number, data: Partial<PreacherCreate>): Promise<Preacher> => {
    return fetchAPI<Preacher>(`/api/preachers/${preacherId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  },

  /**
   * Delete a preacher
   */
  deletePreacher: async (preacherId: number): Promise<{ success: boolean; message: string }> => {
    return fetchAPI<{ success: boolean; message: string }>(`/api/preachers/${preacherId}`, {
      method: "DELETE",
    });
  },

  /**
   * Get preacher photos
   */
  getPreacherPhotos: async (preacherId: number): Promise<PreacherPhotosResponse> => {
    return fetchAPI<PreacherPhotosResponse>(`/api/preachers/${preacherId}/photos`);
  },

  /**
   * Upload a preacher photo
   */
  uploadPreacherPhoto: async (preacherId: number, file: File): Promise<{ success: boolean; filename: string; message: string }> => {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE_URL}/api/preachers/${preacherId}/photos`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to upload photo");
    }

    return response.json();
  },

  /**
   * Delete a preacher photo
   */
  deletePreacherPhoto: async (preacherId: number, photoId: number): Promise<{ success: boolean; message: string }> => {
    const response = await fetch(`${API_BASE_URL}/api/preachers/${preacherId}/photos/${photoId}`, {
      method: "DELETE",
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to delete photo");
    }

    return response.json();
  },

  /**
   * Get preacher stats
   */
  getPreacherStats: async (preacherId: number): Promise<StatsResponse> => {
    return fetchAPI<StatsResponse>(`/api/preachers/${preacherId}/stats`);
  },

  /**
   * Get preacher videos
   */
  getPreacherVideos: async (preacherId: number, limit: number = 10): Promise<VideosResponse> => {
    return fetchAPI<VideosResponse>(`/api/preachers/${preacherId}/videos?limit=${limit}`);
  },

  /**
   * Fetch videos for a preacher from a platform
   */
  fetchForPreacher: async (preacherId: number, platform: "youtube" | "facebook"): Promise<PreacherFetchResult> => {
    return fetchAPI<PreacherFetchResult>(`/api/preachers/${preacherId}/fetch/${platform}`, {
      method: "POST",
    });
  },

  /**
   * Get auto-generated search queries for a preacher
   */
  getPreacherSearchQueries: async (preacherId: number): Promise<PreacherSearchQueries> => {
    return fetchAPI<PreacherSearchQueries>(`/api/preachers/${preacherId}/search-queries`);
  },

  // =========================================================================
  // FACE RECOGNITION API
  // =========================================================================

  /**
   * Get face recognition status
   */
  getFaceRecognitionStatus: async (): Promise<FaceRecognitionStatus> => {
    return fetchAPI<FaceRecognitionStatus>("/api/face-recognition/status");
  },

  /**
   * Get reference photos
   */
  getReferencePhotos: async (): Promise<ReferencePhotosResponse> => {
    return fetchAPI<ReferencePhotosResponse>("/api/reference-photos");
  },

  /**
   * Upload a reference photo
   */
  uploadReferencePhoto: async (file: File): Promise<{ success: boolean; filename: string; message: string }> => {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE_URL}/api/reference-photos`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to upload photo");
    }

    return response.json();
  },

  /**
   * Delete a reference photo
   */
  deleteReferencePhoto: async (filename: string): Promise<{ success: boolean; message: string }> => {
    const response = await fetch(`${API_BASE_URL}/api/reference-photos/${encodeURIComponent(filename)}`, {
      method: "DELETE",
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to delete photo");
    }

    return response.json();
  },

  /**
   * Test face recognition on a video
   */
  testFaceRecognition: async (videoUrl: string, thumbnailUrl?: string): Promise<FaceTestResult> => {
    return fetchAPI<FaceTestResult>("/api/face-test", {
      method: "POST",
      body: JSON.stringify({ video_url: videoUrl, thumbnail_url: thumbnailUrl }),
    });
  },
};

// Types for face recognition
export interface FaceRecognitionStatus {
  available: boolean;
  model_loaded: boolean;
  reference_photos: number;
  error?: string;
  fallback_mode?: boolean;
  warning?: string;
  config?: {
    model_name: string;
    detector_backend: string;
    frame_extraction_enabled: boolean;
  };
}

export interface ReferencePhoto {
  filename: string;
  size: number;
  data: string | null;
  mime_type: string | null;
}

export interface ReferencePhotosResponse {
  photos: ReferencePhoto[];
  available: boolean;
  model_loaded?: boolean;
  error?: string;
}

export interface FaceTestResult {
  verified: boolean;
  confidence: number;
  source: string;
  distance: number;
  model: string;
  error?: string;
  reference_photos: number;
}

export default api;
