"use client";

import { useEffect, useState } from "react";
import Header from "@/components/layout/Header";
import Tabs from "@/components/ui/Tabs";
import SermonCard from "@/components/ui/SermonCard";
import {
  Calendar,
  CalendarDays,
  CalendarRange,
  MapPin,
  Video,
  Clock,
  ChevronLeft,
  Loader2,
  Globe,
} from "lucide-react";
import {
  Video as VideoType,
  YearGroup,
  MonthGroup,
  WeekGroup,
  ChannelStats,
  PlaceStats,
  PlatformStats,
} from "@/lib/types";
import { formatHours, cn } from "@/lib/utils";
import api from "@/lib/api";

type TabType = "year" | "month" | "week" | "channel" | "place" | "platform";

export default function SermonsPage() {
  const [activeTab, setActiveTab] = useState<TabType>("year");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Data for each tab
  const [years, setYears] = useState<YearGroup[]>([]);
  const [months, setMonths] = useState<MonthGroup[]>([]);
  const [weeks, setWeeks] = useState<WeekGroup[]>([]);
  const [channels, setChannels] = useState<ChannelStats[]>([]);
  const [places, setPlaces] = useState<PlaceStats[]>([]);
  const [platforms, setPlatforms] = useState<PlatformStats[]>([]);

  // Selected filters
  const [selectedYear, setSelectedYear] = useState<string | null>(null);
  const [selectedMonth, setSelectedMonth] = useState<string | null>(null);
  const [selectedChannel, setSelectedChannel] = useState<string | null>(null);
  const [selectedPlace, setSelectedPlace] = useState<string | null>(null);
  const [selectedPlatform, setSelectedPlatform] = useState<"youtube" | "facebook" | null>(null);

  // Videos for the selected filter
  const [videos, setVideos] = useState<VideoType[]>([]);
  const [videosLoading, setVideosLoading] = useState(false);

  // Tabs configuration
  const tabs = [
    { id: "year", label: "By Year", icon: <Calendar size={18} /> },
    { id: "month", label: "By Month", icon: <CalendarDays size={18} /> },
    { id: "week", label: "By Week", icon: <CalendarRange size={18} /> },
    { id: "channel", label: "By Channel", icon: <Video size={18} /> },
    { id: "place", label: "By Place", icon: <MapPin size={18} /> },
    { id: "platform", label: "By Source", icon: <Globe size={18} /> },
  ];

  // Load initial data based on active tab
  useEffect(() => {
    async function loadData() {
      setLoading(true);
      setError(null);

      try {
        switch (activeTab) {
          case "year":
            const yearsData = await api.getVideosByYear();
            setYears(yearsData.years);
            break;
          case "month":
            const monthsData = await api.getVideosByMonth();
            setMonths(monthsData.months);
            break;
          case "week":
            const weeksData = await api.getVideosRecentWeeks();
            setWeeks(weeksData.weeks);
            break;
          case "channel":
            const channelsData = await api.getVideosByChannel();
            setChannels(channelsData.channels);
            break;
          case "place":
            const placesData = await api.getVideosByPlace();
            setPlaces(placesData.places);
            break;
          case "platform":
            const platformData = await api.getVideosByPlatform();
            const platformStats: PlatformStats[] = [
              {
                name: "YouTube",
                count: platformData.youtube,
                total_duration: (platformData.hours_by_platform?.youtube || 0) * 3600
              },
              {
                name: "Facebook",
                count: platformData.facebook,
                total_duration: (platformData.hours_by_platform?.facebook || 0) * 3600
              },
            ];
            setPlatforms(platformStats);
            break;
        }
      } catch (err) {
        setError("Failed to load data");
        console.error(err);
      } finally {
        setLoading(false);
      }
    }

    // Reset selections when tab changes
    setSelectedYear(null);
    setSelectedMonth(null);
    setSelectedChannel(null);
    setSelectedPlace(null);
    setSelectedPlatform(null);
    setVideos([]);

    loadData();
  }, [activeTab]);

  // Load videos when a filter is selected
  useEffect(() => {
    async function loadVideos() {
      setVideosLoading(true);

      try {
        let data;
        if (selectedYear) {
          const [year, month] = selectedYear.split("-");
          data = await api.getSermons({
            year: parseInt(year),
            month: month ? parseInt(month) : undefined,
            limit: 50,
          });
        } else if (selectedChannel) {
          data = await api.getSermons({ channel: selectedChannel, limit: 50 });
        } else if (selectedPlace) {
          data = await api.getSermons({ place: selectedPlace, limit: 50 });
        } else if (selectedPlatform) {
          data = await api.getPlatformVideos(selectedPlatform, 100);
        }

        if (data) {
          setVideos(data.videos);
        }
      } catch (err) {
        console.error("Failed to load videos:", err);
      } finally {
        setVideosLoading(false);
      }
    }

    if (selectedYear || selectedChannel || selectedPlace || selectedPlatform) {
      loadVideos();
    }
  }, [selectedYear, selectedChannel, selectedPlace, selectedPlatform]);

  // Handle clicking on a year
  const handleYearClick = (year: string) => {
    setSelectedYear(year);
    setSelectedMonth(null);
  };

  // Handle clicking on a month
  const handleMonthClick = (yearMonth: string) => {
    const year = yearMonth.slice(0, 4);
    const month = yearMonth.slice(4, 6);
    setSelectedYear(`${year}-${month}`);
  };

  // Handle clicking on a channel
  const handleChannelClick = (channelName: string) => {
    setSelectedChannel(channelName);
  };

  // Handle clicking on a place
  const handlePlaceClick = (placeName: string) => {
    setSelectedPlace(placeName);
  };

  // Handle clicking on a platform
  const handlePlatformClick = (platform: "youtube" | "facebook") => {
    setSelectedPlatform(platform);
  };

  // Go back to list view
  const handleBack = () => {
    setSelectedYear(null);
    setSelectedMonth(null);
    setSelectedChannel(null);
    setSelectedPlace(null);
    setSelectedPlatform(null);
    setVideos([]);
  };

  // Render the list view for each tab
  const renderListView = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      );
    }

    if (error) {
      return (
        <div className="rounded-lg bg-red-50 p-6 text-center text-red-600">
          {error}
        </div>
      );
    }

    switch (activeTab) {
      case "year":
        return (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {years.map((year) => (
              <button
                key={year.year}
                onClick={() => handleYearClick(year.year)}
                className="card flex items-center justify-between text-left transition-all hover:border-primary hover:shadow-card-hover"
              >
                <div>
                  <h3 className="text-2xl font-bold text-primary">{year.year}</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    {year.count} sermons
                  </p>
                  <p className="text-xs text-gray-400">
                    {formatHours(year.total_duration / 3600)}
                  </p>
                </div>
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary-50">
                  <Video className="h-6 w-6 text-primary" />
                </div>
              </button>
            ))}
          </div>
        );

      case "month":
        return (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {months.map((month) => (
              <button
                key={month.year_month}
                onClick={() => handleMonthClick(month.year_month)}
                className="card flex items-center justify-between text-left transition-all hover:border-primary hover:shadow-card-hover"
              >
                <div>
                  <h3 className="text-xl font-bold text-primary">
                    {month.month_name} {month.year}
                  </h3>
                  <p className="mt-1 text-sm text-gray-500">
                    {month.count} sermons
                  </p>
                  <p className="text-xs text-gray-400">
                    {formatHours(month.total_duration / 3600)}
                  </p>
                </div>
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-secondary-50">
                  <CalendarDays className="h-5 w-5 text-secondary-dark" />
                </div>
              </button>
            ))}
          </div>
        );

      case "week":
        return (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {weeks.map((week, index) => (
              <div
                key={week.week_start}
                className={cn(
                  "card",
                  week.count > 0 ? "border-l-4 border-l-primary" : "opacity-60"
                )}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold text-gray-900">
                      {week.week_label}
                    </h3>
                    <p className="text-xs text-gray-400">
                      {week.week_start} - {week.week_end}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-primary">
                      {week.count}
                    </p>
                    <p className="text-xs text-gray-500">sermons</p>
                  </div>
                </div>
                {week.count > 0 && (
                  <div className="mt-3 flex items-center gap-1 text-xs text-gray-400">
                    <Clock size={12} />
                    {formatHours(week.total_duration / 3600)}
                  </div>
                )}
              </div>
            ))}
          </div>
        );

      case "channel":
        return (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {channels.map((channel, index) => (
              <button
                key={channel.name}
                onClick={() => handleChannelClick(channel.name)}
                className="card flex items-center gap-4 text-left transition-all hover:border-primary hover:shadow-card-hover"
              >
                <div
                  className={cn(
                    "flex h-12 w-12 items-center justify-center rounded-full text-white font-bold",
                    index === 0
                      ? "bg-primary"
                      : index === 1
                      ? "bg-primary-light"
                      : "bg-gray-400"
                  )}
                >
                  {index + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="truncate font-semibold text-gray-900">
                    {channel.name}
                  </h3>
                  <p className="text-sm text-gray-500">{channel.count} videos</p>
                </div>
                <div className="text-2xl font-bold text-primary">
                  {channel.count}
                </div>
              </button>
            ))}
          </div>
        );

      case "place":
        return (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {places.map((place, index) => (
              <button
                key={place.name}
                onClick={() => handlePlaceClick(place.name)}
                className="card flex items-center justify-between text-left transition-all hover:border-primary hover:shadow-card-hover"
              >
                <div>
                  <h3 className="text-xl font-bold text-primary">{place.name}</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    {place.count} sermons
                  </p>
                  <p className="text-xs text-gray-400">
                    {formatHours(place.total_duration / 3600)}
                  </p>
                </div>
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-secondary-50">
                  <MapPin className="h-6 w-6 text-secondary-dark" />
                </div>
              </button>
            ))}
          </div>
        );

      case "platform":
        return (
          <div className="grid gap-6 sm:grid-cols-2">
            {platforms.map((platform) => {
              const isYouTube = platform.name === "YouTube";
              return (
                <button
                  key={platform.name}
                  onClick={() => handlePlatformClick(isYouTube ? "youtube" : "facebook")}
                  className={cn(
                    "card flex items-center gap-6 text-left transition-all hover:shadow-card-hover",
                    isYouTube ? "hover:border-red-500" : "hover:border-blue-500"
                  )}
                >
                  <div
                    className={cn(
                      "flex h-16 w-16 items-center justify-center rounded-full",
                      isYouTube ? "bg-red-100" : "bg-blue-100"
                    )}
                  >
                    {isYouTube ? (
                      <svg className="h-8 w-8 text-red-600" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
                      </svg>
                    ) : (
                      <svg className="h-8 w-8 text-blue-600" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                      </svg>
                    )}
                  </div>
                  <div className="flex-1">
                    <h3 className={cn(
                      "text-2xl font-bold",
                      isYouTube ? "text-red-600" : "text-blue-600"
                    )}>
                      {platform.name}
                    </h3>
                    <p className="mt-1 text-lg text-gray-700">
                      {platform.count} videos
                    </p>
                    {platform.total_duration && platform.total_duration > 0 && (
                      <p className="text-sm text-gray-400">
                        {formatHours(platform.total_duration / 3600)}
                      </p>
                    )}
                  </div>
                  <div className={cn(
                    "text-4xl font-bold",
                    isYouTube ? "text-red-500" : "text-blue-500"
                  )}>
                    {platform.count}
                  </div>
                </button>
              );
            })}
          </div>
        );

      default:
        return null;
    }
  };

  // Render the videos grid
  const renderVideosView = () => {
    const title = selectedYear
      ? selectedYear.includes("-")
        ? `Sermons from ${selectedYear.replace("-", "/")}`
        : `Sermons from ${selectedYear}`
      : selectedChannel
      ? `Sermons from ${selectedChannel}`
      : selectedPlace
      ? `Sermons from ${selectedPlace}`
      : selectedPlatform
      ? `Videos from ${selectedPlatform === "youtube" ? "YouTube" : "Facebook"}`
      : "";

    return (
      <div>
        {/* Back button and title */}
        <div className="mb-6 flex items-center gap-4">
          <button
            onClick={handleBack}
            className="btn-ghost flex items-center gap-2"
          >
            <ChevronLeft size={20} />
            Back
          </button>
          <h2 className="text-xl font-semibold text-gray-900">{title}</h2>
          <span className="badge-primary">{videos.length} videos</span>
        </div>

        {videosLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        ) : videos.length > 0 ? (
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {videos.map((video) => (
              <SermonCard key={video.video_id} video={video} />
            ))}
          </div>
        ) : (
          <div className="rounded-lg bg-gray-50 p-12 text-center">
            <Video className="mx-auto h-12 w-12 text-gray-400" />
            <p className="mt-4 text-gray-500">No sermons found</p>
          </div>
        )}
      </div>
    );
  };

  const showVideos = selectedYear || selectedChannel || selectedPlace || selectedPlatform;

  return (
    <div>
      <Header title="Sermons" subtitle="Browse and filter sermons" />

      <div className="p-6">
        {/* Tabs */}
        <div className="card mb-6 p-0">
          <Tabs
            tabs={tabs}
            activeTab={activeTab}
            onTabChange={(tab) => setActiveTab(tab as TabType)}
          />
        </div>

        {/* Content */}
        {showVideos ? renderVideosView() : renderListView()}
      </div>
    </div>
  );
}
