"use client";

import { Video, ExternalLink, Clock, Eye } from "lucide-react";
import { Video as VideoType } from "@/lib/types";
import { formatDuration, formatDate, formatNumber, cn } from "@/lib/utils";

interface SermonCardProps {
  video: VideoType;
  className?: string;
}

export default function SermonCard({ video, className }: SermonCardProps) {
  const videoUrl = video.video_url || `https://youtube.com/watch?v=${video.video_id}`;

  return (
    <a
      href={videoUrl}
      target="_blank"
      rel="noopener noreferrer"
      className={cn(
        "group flex flex-col overflow-hidden rounded-xl border border-border bg-surface transition-all hover:border-primary hover:shadow-card-hover",
        className
      )}
    >
      {/* Thumbnail */}
      <div className="relative aspect-video w-full overflow-hidden bg-gray-100">
        {video.thumbnail_url ? (
          <img
            src={video.thumbnail_url}
            alt={video.title}
            className="h-full w-full object-cover transition-transform group-hover:scale-105"
          />
        ) : (
          <div className="flex h-full items-center justify-center bg-gray-200">
            <Video className="h-12 w-12 text-gray-400" />
          </div>
        )}

        {/* Duration overlay */}
        <div className="absolute bottom-2 right-2 flex items-center gap-1 rounded bg-black/80 px-2 py-1 text-xs text-white">
          <Clock size={12} />
          {formatDuration(video.duration)}
        </div>

        {/* External link icon */}
        <div className="absolute right-2 top-2 rounded-full bg-white/90 p-1.5 opacity-0 transition-opacity group-hover:opacity-100">
          <ExternalLink size={14} className="text-primary" />
        </div>
      </div>

      {/* Info */}
      <div className="flex flex-1 flex-col p-4">
        {/* Title */}
        <h3 className="line-clamp-2 text-sm font-semibold text-gray-900 group-hover:text-primary">
          {video.title || "Untitled"}
        </h3>

        {/* Channel */}
        <p className="mt-1 truncate text-xs text-gray-500">
          {video.channel_name || "Unknown Channel"}
        </p>

        {/* Meta info */}
        <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-gray-400">
          <span>{formatDate(video.upload_date)}</span>
          {video.view_count && (
            <>
              <span>•</span>
              <span className="flex items-center gap-1">
                <Eye size={12} />
                {formatNumber(video.view_count)}
              </span>
            </>
          )}
        </div>

        {/* Badges */}
        <div className="mt-3 flex flex-wrap gap-1">
          {video.content_type === "PREACHING" && (
            <span className="badge-success">PREACHING</span>
          )}
          {video.content_type === "UNKNOWN" && (
            <span className="badge-warning">REVIEW</span>
          )}
          {video.language_detected === "FR" && (
            <span className="badge-info">FR</span>
          )}
          {video.language_detected === "EN" && (
            <span className="badge bg-pink-100 text-pink-800">EN</span>
          )}
        </div>
      </div>
    </a>
  );
}
