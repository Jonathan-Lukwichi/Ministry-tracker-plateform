"use client";

import { useEffect, useState } from "react";
import Header from "@/components/layout/Header";
import MinistryMap from "@/components/maps/MinistryMap";
import { api } from "@/lib/api";
import {
  MapLocation,
  Journey,
  TravelStatsResponse,
} from "@/lib/types";
import {
  MapPin,
  Plane,
  Globe,
  Navigation,
  Calendar,
  ChevronDown,
  Route,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

// Import Leaflet CSS
import "leaflet/dist/leaflet.css";

export default function MapPage() {
  const [locations, setLocations] = useState<MapLocation[]>([]);
  const [journeys, setJourneys] = useState<Journey[]>([]);
  const [travelStats, setTravelStats] = useState<TravelStatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedYear, setSelectedYear] = useState<number | null>(null);
  const [showRoutes, setShowRoutes] = useState(true);

  // Get available years for filter
  const availableYears = travelStats?.byYear
    .map((y) => parseInt(y.year))
    .filter((y) => !isNaN(y))
    .sort((a, b) => b - a) || [];

  useEffect(() => {
    loadData();
  }, [selectedYear]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [locationsRes, journeysRes, statsRes] = await Promise.all([
        api.getMapLocations(),
        api.getMapJourneys(selectedYear || undefined),
        api.getTravelStats(),
      ]);

      setLocations(locationsRes.locations);
      setJourneys(journeysRes.journeys);
      setTravelStats(statsRes);
    } catch (err) {
      setError("Failed to load map data");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Format distance for display
  const formatDistance = (km: number): string => {
    if (km >= 1000) {
      return `${(km / 1000).toFixed(1)}K`;
    }
    return km.toLocaleString();
  };

  // Chart colors for dark theme
  const CHART_COLORS = [
    "#00d4ff", "#00a8cc", "#007f99", "#5ce1ff", "#33dfff",
    "#ff3e7f", "#ff6b9d", "#cc2a5f", "#ffd700", "#ffe44d",
  ];

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Header title="Ministry Map" subtitle="Global Ministry Footprint" />
        <div className="flex h-[70vh] items-center justify-center">
          <div className="text-slate-500">Loading map data...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background">
        <Header title="Ministry Map" subtitle="Global Ministry Footprint" />
        <div className="p-8">
          <div className="rounded-lg bg-danger/10 border border-danger/30 p-4 text-danger">{error}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-slate-200">
      {/* Compact Header with Controls */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-border">
        <div>
          <h1 className="text-xl font-bold text-slate-100">Ministry Map</h1>
          <p className="text-sm text-slate-500">Global Ministry Footprint</p>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-slate-500" />
            <div className="relative">
              <select
                value={selectedYear || "all"}
                onChange={(e) =>
                  setSelectedYear(
                    e.target.value === "all" ? null : parseInt(e.target.value)
                  )
                }
                className="select pr-8 py-1.5 text-sm"
              >
                <option value="all">All Years</option>
                {availableYears.map((year) => (
                  <option key={year} value={year}>
                    {year}
                  </option>
                ))}
              </select>
              <ChevronDown className="pointer-events-none absolute right-2 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
            </div>
          </div>

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={showRoutes}
              onChange={(e) => setShowRoutes(e.target.checked)}
              className="h-4 w-4 rounded border-border bg-[#152238] text-accent focus:ring-accent"
            />
            <Route className="h-4 w-4 text-slate-500" />
            <span className="text-sm text-slate-400">Routes</span>
          </label>
        </div>
      </div>

      {/* Hero Map - Full Width, Tall */}
      <div className="relative">
        <MinistryMap
          locations={locations}
          journeys={journeys}
          showRoutes={showRoutes}
          selectedYear={selectedYear}
          height="60vh"
        />

        {/* Floating Stats Overlay */}
        <div className="absolute bottom-4 left-4 right-4 z-[1000]">
          <div className="flex gap-3 justify-center">
            <div className="bg-dark/90 backdrop-blur-sm border border-border rounded-lg px-4 py-2 flex items-center gap-3">
              <Plane className="h-5 w-5 text-accent" />
              <div>
                <div className="text-lg font-bold text-slate-100">{travelStats?.totalTrips || 0}</div>
                <div className="text-xs text-slate-500">Trips</div>
              </div>
            </div>
            <div className="bg-dark/90 backdrop-blur-sm border border-border rounded-lg px-4 py-2 flex items-center gap-3">
              <Navigation className="h-5 w-5 text-marker" />
              <div>
                <div className="text-lg font-bold text-slate-100">{formatDistance(travelStats?.totalDistanceKm || 0)} <span className="text-xs font-normal text-slate-500">km</span></div>
                <div className="text-xs text-slate-500">Distance</div>
              </div>
            </div>
            <div className="bg-dark/90 backdrop-blur-sm border border-border rounded-lg px-4 py-2 flex items-center gap-3">
              <Globe className="h-5 w-5 text-success" />
              <div>
                <div className="text-lg font-bold text-slate-100">{travelStats?.countriesVisited || 0}</div>
                <div className="text-xs text-slate-500">Countries</div>
              </div>
            </div>
            <div className="bg-dark/90 backdrop-blur-sm border border-border rounded-lg px-4 py-2 flex items-center gap-3">
              <MapPin className="h-5 w-5 text-secondary" />
              <div>
                <div className="text-lg font-bold text-slate-100">{travelStats?.citiesVisited || 0}</div>
                <div className="text-xs text-slate-500">Cities</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Section - Charts and Tables */}
      <div className="p-6 space-y-6">
        {/* Charts Row */}
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Trips by Year */}
          <div className="card">
            <h3 className="mb-4 text-lg font-semibold text-slate-100">
              Trips by Year
            </h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={travelStats?.byYear || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e3a5f" vertical={false} />
                <XAxis
                  dataKey="year"
                  tick={{ fill: "#64748b", fontSize: 11 }}
                  axisLine={{ stroke: "#1e3a5f" }}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: "#64748b", fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  content={({ active, payload, label }) => {
                    if (active && payload && payload.length) {
                      return (
                        <div className="chart-tooltip">
                          <p className="font-semibold text-slate-100">{label}</p>
                          <p className="text-sm text-accent">
                            {payload[0].value} trips
                          </p>
                          <p className="text-xs text-slate-500">
                            {payload[0].payload.distanceKm?.toLocaleString()} km
                          </p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Bar dataKey="trips" radius={[4, 4, 0, 0]}>
                  {(travelStats?.byYear || []).map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={CHART_COLORS[index % CHART_COLORS.length]}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Trips by Month */}
          <div className="card">
            <h3 className="mb-4 text-lg font-semibold text-slate-100">
              Monthly Distribution
            </h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={travelStats?.byMonth || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e3a5f" vertical={false} />
                <XAxis
                  dataKey="month"
                  tick={{ fill: "#64748b", fontSize: 10 }}
                  axisLine={{ stroke: "#1e3a5f" }}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: "#64748b", fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  content={({ active, payload, label }) => {
                    if (active && payload && payload.length) {
                      return (
                        <div className="chart-tooltip">
                          <p className="font-semibold text-slate-100">{label}</p>
                          <p className="text-sm text-marker">
                            {payload[0].value} trips
                          </p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Bar dataKey="trips" fill="#ff3e7f" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Locations Grid */}
        <div className="card">
          <h3 className="mb-4 text-lg font-semibold text-slate-100">
            Ministry Locations
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-3">
            {locations
              .filter((loc) => loc.sermonCount > 0)
              .sort((a, b) => b.sermonCount - a.sermonCount)
              .map((location) => (
                <div
                  key={location.name}
                  className={`p-3 rounded-lg border transition-all cursor-pointer hover:border-accent/50 ${
                    location.isHomeBase
                      ? "bg-accent/10 border-accent/30"
                      : "bg-[#1a2942] border-border"
                  }`}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <div
                      className={`h-2 w-2 rounded-full ${
                        location.isHomeBase ? "bg-accent" : "bg-marker"
                      }`}
                    ></div>
                    <span className="text-sm font-medium text-slate-100 truncate">
                      {location.name}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-500">{location.country}</span>
                    <span className={`text-sm font-bold ${location.isHomeBase ? "text-accent" : "text-marker"}`}>
                      {location.sermonCount}
                    </span>
                  </div>
                </div>
              ))}
          </div>
        </div>
      </div>
    </div>
  );
}
