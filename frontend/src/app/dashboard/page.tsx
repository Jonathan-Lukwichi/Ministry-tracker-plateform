"use client";

import { useEffect, useState } from "react";
import Header from "@/components/layout/Header";
import KPICard from "@/components/ui/KPICard";
import { Video, Clock, Globe, Eye, Users, AlertCircle, ExternalLink, Play } from "lucide-react";
import { StatsResponse, Video as VideoType } from "@/lib/types";
import { formatDuration, formatDate, formatHours, formatNumber, truncate } from "@/lib/utils";
import api from "@/lib/api";

export default function DashboardPage() {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [videos, setVideos] = useState<VideoType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        setError(null);

        const [statsData, videosData] = await Promise.all([
          api.getStats(),
          api.getVideos(6),
        ]);

        setStats(statsData);
        setVideos(videosData.videos);
      } catch (err) {
        setError("Failed to load data. Make sure the API server is running.");
        console.error(err);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-accent border-t-transparent" />
          <p className="text-slate-500">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <Header title="Dashboard" subtitle="Ministry Overview" />
        <div className="mt-8 flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-danger/30 bg-danger/5 p-12">
          <AlertCircle className="h-12 w-12 text-danger" />
          <h2 className="mt-4 text-xl font-semibold text-white">Connection Error</h2>
          <p className="mt-2 text-slate-400">{error}</p>
          <p className="mt-4 text-sm text-slate-500">
            Run the API server with: <code className="rounded bg-[#1a2942] px-2 py-1 text-accent">python api.py</code>
          </p>
        </div>
      </div>
    );
  }

  const preachingCount = (stats?.by_content_type?.PREACHING || 0) + (stats?.by_content_type?.UNKNOWN || 0);

  return (
    <div>
      <Header title="Dashboard" subtitle="Ministry Overview" />

      <div className="p-6">
        {/* KPI Cards */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <KPICard
            label="Total Videos"
            value={formatNumber(stats?.total_videos || 0)}
            icon={<Video size={24} />}
            color="primary"
          />
          <KPICard
            label="Preaching Videos"
            value={formatNumber(preachingCount)}
            icon={<Play size={24} />}
            color="secondary"
          />
          <KPICard
            label="Total Duration"
            value={formatHours(stats?.total_preaching_hours || 0)}
            icon={<Clock size={24} />}
            color="success"
          />
          <KPICard
            label="Channels"
            value={stats?.unique_channels || 0}
            icon={<Users size={24} />}
            color="primary"
          />
          <KPICard
            label="Need Review"
            value={stats?.needs_review || 0}
            icon={<AlertCircle size={24} />}
            color={stats?.needs_review ? "warning" : "success"}
          />
        </div>

        {/* Date Range */}
        {stats?.oldest_video && stats?.newest_video && (
          <div className="mt-6 text-center text-sm text-slate-500">
            Data from <span className="font-medium text-accent">{formatDate(stats.oldest_video)}</span> to{" "}
            <span className="font-medium text-accent">{formatDate(stats.newest_video)}</span>
          </div>
        )}

        {/* Content Grid */}
        <div className="mt-8 grid gap-6 lg:grid-cols-3">
          {/* Top Channels */}
          <div className="card lg:col-span-1">
            <h2 className="mb-4 text-lg font-semibold text-white flex items-center gap-2">
              <span className="h-1 w-4 rounded-full bg-accent"></span>
              Top Channels
            </h2>
            {stats?.top_channels && stats.top_channels.length > 0 ? (
              <ul className="space-y-2">
                {stats.top_channels.map((channel, index) => (
                  <li
                    key={index}
                    className="flex items-center justify-between rounded-lg bg-[#1a2942] px-3 py-2.5 border border-border hover:border-accent/30 transition-colors"
                  >
                    <span className="truncate text-sm font-medium text-slate-300">
                      {truncate(channel.name, 30)}
                    </span>
                    <span className="ml-2 rounded-full bg-accent/20 px-2.5 py-0.5 text-xs font-medium text-accent">
                      {channel.count}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-slate-500">No channels found</p>
            )}
          </div>

          {/* Recent Sermons */}
          <div className="card lg:col-span-2">
            <h2 className="mb-4 text-lg font-semibold text-white flex items-center gap-2">
              <span className="h-1 w-4 rounded-full bg-marker"></span>
              Recent Sermons
            </h2>
            {videos.length > 0 ? (
              <div className="grid gap-3 sm:grid-cols-2">
                {videos.map((video) => (
                  <a
                    key={video.video_id}
                    href={video.video_url || `https://youtube.com/watch?v=${video.video_id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="group flex gap-3 rounded-lg border border-border bg-[#1a2942] p-3 transition-all hover:border-accent/50 hover:shadow-card-hover"
                  >
                    {/* Thumbnail */}
                    <div className="relative h-20 w-32 flex-shrink-0 overflow-hidden rounded bg-[#152238]">
                      {video.thumbnail_url ? (
                        <img
                          src={video.thumbnail_url}
                          alt={video.title}
                          className="h-full w-full object-cover"
                        />
                      ) : (
                        <div className="flex h-full items-center justify-center">
                          <Video className="h-8 w-8 text-slate-600" />
                        </div>
                      )}
                      {/* Duration overlay */}
                      <div className="absolute bottom-1 right-1 rounded bg-dark/90 px-1.5 py-0.5 text-xs text-white">
                        {formatDuration(video.duration)}
                      </div>
                      {/* Play overlay */}
                      <div className="absolute inset-0 flex items-center justify-center bg-dark/50 opacity-0 group-hover:opacity-100 transition-opacity">
                        <Play className="h-8 w-8 text-accent" fill="currentColor" />
                      </div>
                    </div>

                    {/* Info */}
                    <div className="flex flex-1 flex-col justify-between overflow-hidden">
                      <div>
                        <h3 className="line-clamp-2 text-sm font-medium text-white group-hover:text-accent transition-colors">
                          {video.title || "Untitled"}
                        </h3>
                        <p className="mt-1 truncate text-xs text-slate-500">
                          {video.channel_name || "Unknown Channel"}
                        </p>
                      </div>
                      <div className="mt-1 flex items-center gap-2">
                        <span className="text-xs text-slate-600">
                          {formatDate(video.upload_date)}
                        </span>
                        {video.view_count && (
                          <>
                            <span className="text-slate-700">•</span>
                            <span className="text-xs text-slate-600">
                              {formatNumber(video.view_count)} views
                            </span>
                          </>
                        )}
                      </div>
                    </div>

                    {/* External link icon */}
                    <ExternalLink className="h-4 w-4 flex-shrink-0 text-slate-600 group-hover:text-accent transition-colors" />
                  </a>
                ))}
              </div>
            ) : (
              <p className="text-slate-500">No videos found</p>
            )}
          </div>
        </div>

        {/* Language & Content Type Breakdown */}
        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          {/* Content Type */}
          <div className="card">
            <h2 className="mb-4 text-lg font-semibold text-white flex items-center gap-2">
              <span className="h-1 w-4 rounded-full bg-success"></span>
              Content Classification
            </h2>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-2 rounded bg-[#1a2942]">
                <span className="flex items-center gap-2 text-slate-300">
                  <span className="h-2.5 w-2.5 rounded-full bg-success" />
                  Preaching
                </span>
                <span className="font-medium text-white">{stats?.by_content_type?.PREACHING || 0}</span>
              </div>
              <div className="flex items-center justify-between p-2 rounded bg-[#1a2942]">
                <span className="flex items-center gap-2 text-slate-300">
                  <span className="h-2.5 w-2.5 rounded-full bg-warning" />
                  Unknown (Needs Review)
                </span>
                <span className="font-medium text-white">{stats?.by_content_type?.UNKNOWN || 0}</span>
              </div>
              <div className="flex items-center justify-between p-2 rounded bg-[#1a2942]">
                <span className="flex items-center gap-2 text-slate-300">
                  <span className="h-2.5 w-2.5 rounded-full bg-danger" />
                  Music (Excluded)
                </span>
                <span className="font-medium text-white">{stats?.by_content_type?.MUSIC || 0}</span>
              </div>
            </div>
          </div>

          {/* Language */}
          <div className="card">
            <h2 className="mb-4 text-lg font-semibold text-white flex items-center gap-2">
              <span className="h-1 w-4 rounded-full bg-info"></span>
              Language Distribution
            </h2>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-2 rounded bg-[#1a2942]">
                <span className="flex items-center gap-2 text-slate-300">
                  <span className="h-2.5 w-2.5 rounded-full bg-info" />
                  French (FR)
                </span>
                <span className="font-medium text-white">{stats?.by_language?.FR || 0}</span>
              </div>
              <div className="flex items-center justify-between p-2 rounded bg-[#1a2942]">
                <span className="flex items-center gap-2 text-slate-300">
                  <span className="h-2.5 w-2.5 rounded-full bg-marker" />
                  English (EN)
                </span>
                <span className="font-medium text-white">{stats?.by_language?.EN || 0}</span>
              </div>
              <div className="flex items-center justify-between p-2 rounded bg-[#1a2942]">
                <span className="flex items-center gap-2 text-slate-300">
                  <span className="h-2.5 w-2.5 rounded-full bg-slate-500" />
                  Unknown
                </span>
                <span className="font-medium text-white">{stats?.by_language?.UNKNOWN || 0}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
