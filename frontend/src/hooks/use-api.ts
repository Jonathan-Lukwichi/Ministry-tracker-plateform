"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

// Query keys for cache management
export const queryKeys = {
  stats: ["stats"] as const,
  videos: (params?: Record<string, unknown>) => ["videos", params] as const,
  videosByYear: ["videos", "by-year"] as const,
  videosByMonth: (year?: number) => ["videos", "by-month", year] as const,
  videosByChannel: ["videos", "by-channel"] as const,
  videosByPlace: ["videos", "by-place"] as const,
  analyticsOverview: ["analytics", "overview"] as const,
  analyticsSummary: ["analytics", "summary"] as const,
  yearDistribution: ["analytics", "year-distribution"] as const,
  monthsByYear: (year: number) => ["analytics", "months-by-year", year] as const,
  busiestMonths: ["analytics", "busiest-months"] as const,
  yearSummary: (year: number) => ["analytics", "year-summary", year] as const,
  mapLocations: ["map", "locations"] as const,
  mapJourneys: (year?: number) => ["map", "journeys", year] as const,
  travelStats: ["map", "travel-stats"] as const,
  sermonForecast: ["forecast", "sermons"] as const,
  tripForecast: ["forecast", "trips"] as const,
  forecastModelStatus: ["forecast", "model-status"] as const,
  healthScore: ["health", "score"] as const,
  healthMetrics: ["health", "metrics"] as const,
  healthReport: ["health", "report"] as const,
  healthTrends: ["health", "trends"] as const,
  planningReport: ["planning", "report"] as const,
  upcomingPredictions: ["planning", "upcoming"] as const,
  historicalPatterns: ["planning", "patterns"] as const,
  aiStatus: ["ai", "status"] as const,
  preachers: ["preachers"] as const,
  preacher: (id: number) => ["preachers", id] as const,
  preacherPhotos: (id: number) => ["preachers", id, "photos"] as const,
  preacherStats: (id: number) => ["preachers", id, "stats"] as const,
  preacherVideos: (id: number, limit?: number) => ["preachers", id, "videos", limit] as const,
  faceRecognitionStatus: ["face-recognition", "status"] as const,
  referencePhotos: ["reference-photos"] as const,
};

// Stats
export function useStats() {
  return useQuery({
    queryKey: queryKeys.stats,
    queryFn: api.getStats,
  });
}

// Videos
export function useVideos(limit?: number) {
  return useQuery({
    queryKey: queryKeys.videos({ limit }),
    queryFn: () => api.getVideos(limit),
  });
}

export function useSermons(params?: Parameters<typeof api.getSermons>[0]) {
  return useQuery({
    queryKey: queryKeys.videos(params),
    queryFn: () => api.getSermons(params),
  });
}

export function useVideosByYear() {
  return useQuery({
    queryKey: queryKeys.videosByYear,
    queryFn: api.getVideosByYear,
  });
}

export function useVideosByMonth(year?: number) {
  return useQuery({
    queryKey: queryKeys.videosByMonth(year),
    queryFn: () => api.getVideosByMonth(year),
  });
}

export function useVideosByChannel() {
  return useQuery({
    queryKey: queryKeys.videosByChannel,
    queryFn: api.getVideosByChannel,
  });
}

export function useVideosByPlace() {
  return useQuery({
    queryKey: queryKeys.videosByPlace,
    queryFn: api.getVideosByPlace,
  });
}

// Analytics
export function useAnalyticsSummary() {
  return useQuery({
    queryKey: queryKeys.analyticsSummary,
    queryFn: api.getAnalyticsSummary,
  });
}

export function useYearDistribution() {
  return useQuery({
    queryKey: queryKeys.yearDistribution,
    queryFn: api.getYearDistribution,
  });
}

export function useMonthsByYear(year: number) {
  return useQuery({
    queryKey: queryKeys.monthsByYear(year),
    queryFn: () => api.getMonthsByYear(year),
    enabled: !!year,
  });
}

export function useBusiestMonths() {
  return useQuery({
    queryKey: queryKeys.busiestMonths,
    queryFn: api.getBusiestMonths,
  });
}

export function useYearSummary(year: number) {
  return useQuery({
    queryKey: queryKeys.yearSummary(year),
    queryFn: () => api.getYearSummary(year),
    enabled: !!year,
  });
}

// Map
export function useMapLocations() {
  return useQuery({
    queryKey: queryKeys.mapLocations,
    queryFn: api.getMapLocations,
  });
}

export function useMapJourneys(year?: number) {
  return useQuery({
    queryKey: queryKeys.mapJourneys(year),
    queryFn: () => api.getMapJourneys(year),
  });
}

export function useTravelStats() {
  return useQuery({
    queryKey: queryKeys.travelStats,
    queryFn: api.getTravelStats,
  });
}

// Forecasting
export function useSermonForecast() {
  return useQuery({
    queryKey: queryKeys.sermonForecast,
    queryFn: api.getSermonForecast,
  });
}

export function useTripForecast() {
  return useQuery({
    queryKey: queryKeys.tripForecast,
    queryFn: api.getTripForecast,
  });
}

export function useForecastModelStatus() {
  return useQuery({
    queryKey: queryKeys.forecastModelStatus,
    queryFn: api.getForecastModelStatus,
  });
}

export function useRetrainForecastModels() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: api.retrainForecastModels,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["forecast"] });
    },
  });
}

// Health
export function useHealthScore() {
  return useQuery({
    queryKey: queryKeys.healthScore,
    queryFn: api.getHealthScore,
  });
}

export function useHealthMetrics() {
  return useQuery({
    queryKey: queryKeys.healthMetrics,
    queryFn: api.getHealthMetrics,
  });
}

export function useHealthReport() {
  return useQuery({
    queryKey: queryKeys.healthReport,
    queryFn: api.getHealthReport,
  });
}

export function useHealthTrends() {
  return useQuery({
    queryKey: queryKeys.healthTrends,
    queryFn: api.getHealthTrends,
  });
}

// Planning
export function usePlanningReport() {
  return useQuery({
    queryKey: queryKeys.planningReport,
    queryFn: api.getPlanningReport,
  });
}

export function useUpcomingPredictions() {
  return useQuery({
    queryKey: queryKeys.upcomingPredictions,
    queryFn: api.getUpcomingPredictions,
  });
}

export function useHistoricalPatterns() {
  return useQuery({
    queryKey: queryKeys.historicalPatterns,
    queryFn: api.getHistoricalPatterns,
  });
}

export function useAIStatus() {
  return useQuery({
    queryKey: queryKeys.aiStatus,
    queryFn: api.getAIStatus,
  });
}

// Preachers
export function usePreachers() {
  return useQuery({
    queryKey: queryKeys.preachers,
    queryFn: api.getPreachers,
  });
}

export function usePreacher(id: number) {
  return useQuery({
    queryKey: queryKeys.preacher(id),
    queryFn: () => api.getPreacher(id),
    enabled: !!id,
  });
}

export function useCreatePreacher() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: api.createPreacher,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.preachers });
    },
  });
}

export function useUpdatePreacher(id: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Parameters<typeof api.updatePreacher>[1]) =>
      api.updatePreacher(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.preacher(id) });
      queryClient.invalidateQueries({ queryKey: queryKeys.preachers });
    },
  });
}

export function useDeletePreacher() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: api.deletePreacher,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.preachers });
    },
  });
}

export function usePreacherPhotos(id: number) {
  return useQuery({
    queryKey: queryKeys.preacherPhotos(id),
    queryFn: () => api.getPreacherPhotos(id),
    enabled: !!id,
  });
}

export function useUploadPreacherPhoto(id: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (file: File) => api.uploadPreacherPhoto(id, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.preacherPhotos(id) });
    },
  });
}

export function usePreacherStats(id: number) {
  return useQuery({
    queryKey: queryKeys.preacherStats(id),
    queryFn: () => api.getPreacherStats(id),
    enabled: !!id,
  });
}

export function usePreacherVideos(id: number, limit?: number) {
  return useQuery({
    queryKey: queryKeys.preacherVideos(id, limit),
    queryFn: () => api.getPreacherVideos(id, limit),
    enabled: !!id,
  });
}

export function useFetchForPreacher(id: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (platform: "youtube" | "facebook") =>
      api.fetchForPreacher(id, platform),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.preacherVideos(id) });
      queryClient.invalidateQueries({ queryKey: queryKeys.preacherStats(id) });
      queryClient.invalidateQueries({ queryKey: queryKeys.stats });
    },
  });
}

// Face Recognition
export function useFaceRecognitionStatus() {
  return useQuery({
    queryKey: queryKeys.faceRecognitionStatus,
    queryFn: api.getFaceRecognitionStatus,
  });
}

export function useReferencePhotos() {
  return useQuery({
    queryKey: queryKeys.referencePhotos,
    queryFn: api.getReferencePhotos,
  });
}

export function useUploadReferencePhoto() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: api.uploadReferencePhoto,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.referencePhotos });
      queryClient.invalidateQueries({ queryKey: queryKeys.faceRecognitionStatus });
    },
  });
}

export function useDeleteReferencePhoto() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: api.deleteReferencePhoto,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.referencePhotos });
      queryClient.invalidateQueries({ queryKey: queryKeys.faceRecognitionStatus });
    },
  });
}

export function useTestFaceRecognition() {
  return useMutation({
    mutationFn: ({ videoUrl, thumbnailUrl }: { videoUrl: string; thumbnailUrl?: string }) =>
      api.testFaceRecognition(videoUrl, thumbnailUrl),
  });
}
