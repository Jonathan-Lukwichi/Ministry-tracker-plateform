"use client";

import { useEffect, useState } from "react";
import Header from "@/components/layout/Header";
import LineChart from "@/components/charts/LineChart";
import BarChart from "@/components/charts/BarChart";
import KPICard from "@/components/charts/KPICard";
import PieChart from "@/components/charts/PieChart";
import Histogram from "@/components/charts/Histogram";
import { Video, Clock, Eye, Loader2, Calendar, TrendingUp, BarChart3, MapPin } from "lucide-react";
import api from "@/lib/api";
import {
  AnalyticsSummary,
  TimeSeriesPoint,
  PlaceStats,
  YearDistributionPoint,
  MonthlyBreakdown,
  BusiestMonthPoint,
  YearSummary,
} from "@/lib/types";
import { cn } from "@/lib/utils";

// Years with significant data for individual tabs
const ANALYSIS_YEARS = [2025, 2024, 2023, 2022, 2021, 2020, 2019];

type TabType = "overview" | number;

export default function AnalyticsPage() {
  const [activeTab, setActiveTab] = useState<TabType>("overview");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // KPI Summary
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);

  // Time series data
  const [sermonsByYear, setSermonsByYear] = useState<TimeSeriesPoint[]>([]);
  const [sermonsByMonth, setSermonsByMonth] = useState<TimeSeriesPoint[]>([]);
  const [sermonsByWeek, setSermonsByWeek] = useState<TimeSeriesPoint[]>([]);

  const [durationByYear, setDurationByYear] = useState<TimeSeriesPoint[]>([]);
  const [durationByMonth, setDurationByMonth] = useState<TimeSeriesPoint[]>([]);
  const [durationByWeek, setDurationByWeek] = useState<TimeSeriesPoint[]>([]);

  const [viewsByYear, setViewsByYear] = useState<TimeSeriesPoint[]>([]);
  const [viewsByMonth, setViewsByMonth] = useState<TimeSeriesPoint[]>([]);
  const [viewsByWeek, setViewsByWeek] = useState<TimeSeriesPoint[]>([]);

  // Places data
  const [places, setPlaces] = useState<PlaceStats[]>([]);

  // Pie chart & histogram data
  const [yearDistribution, setYearDistribution] = useState<YearDistributionPoint[]>([]);
  const [busiestYear, setBusiestYear] = useState<string | null>(null);
  const [monthsByYear, setMonthsByYear] = useState<MonthlyBreakdown[]>([]);
  const [selectedYear, setSelectedYear] = useState<number>(2025);
  const [busiestMonths, setBusiestMonths] = useState<BusiestMonthPoint[]>([]);

  // Year-specific data (for tabs)
  const [yearSummaries, setYearSummaries] = useState<Record<number, YearSummary>>({});
  const [yearMonths, setYearMonths] = useState<Record<number, MonthlyBreakdown[]>>({});

  // Available years for dropdown
  const availableYears = yearDistribution
    .map((y) => parseInt(y.year))
    .filter((y) => !isNaN(y))
    .sort((a, b) => b - a);

  useEffect(() => {
    async function loadAnalytics() {
      setLoading(true);
      setError(null);

      try {
        // Load base data in parallel
        const [
          summaryRes,
          sermonsYearRes,
          sermonsMonthRes,
          sermonsWeekRes,
          durationYearRes,
          durationMonthRes,
          durationWeekRes,
          viewsYearRes,
          viewsMonthRes,
          viewsWeekRes,
          placesRes,
          yearDistRes,
          busiestMonthsRes,
        ] = await Promise.all([
          api.getAnalyticsSummary(),
          api.getSermonsByPeriod("year"),
          api.getSermonsByPeriod("month"),
          api.getSermonsByPeriod("week"),
          api.getDurationByPeriod("year"),
          api.getDurationByPeriod("month"),
          api.getDurationByPeriod("week"),
          api.getViewsByPeriod("year"),
          api.getViewsByPeriod("month"),
          api.getViewsByPeriod("week"),
          api.getVideosByPlace(),
          api.getYearDistribution(),
          api.getBusiestMonths(),
        ]);

        // Load year-specific data for all years
        const yearSummaryPromises = ANALYSIS_YEARS.map((year) =>
          api.getYearSummary(year).then((res) => ({ year, data: res }))
        );
        const yearMonthsPromises = ANALYSIS_YEARS.map((year) =>
          api.getMonthsByYear(year).then((res) => ({ year, data: res.data }))
        );

        const yearSummaryResults = await Promise.all(yearSummaryPromises);
        const yearMonthsResults = await Promise.all(yearMonthsPromises);

        // Build year summaries and months objects
        const summaries: Record<number, YearSummary> = {};
        const months: Record<number, MonthlyBreakdown[]> = {};

        yearSummaryResults.forEach(({ year, data }) => {
          summaries[year] = data;
        });
        yearMonthsResults.forEach(({ year, data }) => {
          months[year] = data;
        });

        setSummary(summaryRes.summary);
        setSermonsByYear(sermonsYearRes.data);
        setSermonsByMonth(sermonsMonthRes.data);
        setSermonsByWeek(sermonsWeekRes.data);
        setDurationByYear(durationYearRes.data);
        setDurationByMonth(durationMonthRes.data);
        setDurationByWeek(durationWeekRes.data);
        setViewsByYear(viewsYearRes.data);
        setViewsByMonth(viewsMonthRes.data);
        setViewsByWeek(viewsWeekRes.data);
        setPlaces(placesRes.places);
        setYearDistribution(yearDistRes.data);
        setBusiestYear(yearDistRes.busiestYear);
        setBusiestMonths(busiestMonthsRes.data);
        setYearSummaries(summaries);
        setYearMonths(months);
        setMonthsByYear(months[2025] || []);
      } catch (err) {
        console.error("Failed to load analytics:", err);
        setError("Failed to load analytics data. Please try again.");
      } finally {
        setLoading(false);
      }
    }

    loadAnalytics();
  }, []);

  // Load months when selected year changes (for overview dropdown)
  useEffect(() => {
    if (selectedYear && yearMonths[selectedYear]) {
      setMonthsByYear(yearMonths[selectedYear]);
    }
  }, [selectedYear, yearMonths]);

  const formatHours = (hours: number) => `${hours.toFixed(1)}h`;
  const formatViews = (views: number) => {
    if (views >= 1000000) return `${(views / 1000000).toFixed(1)}M`;
    if (views >= 1000) return `${(views / 1000).toFixed(1)}K`;
    return views.toLocaleString();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <Header title="Analytics" subtitle="Time series analysis and insights" />
        <div className="flex items-center justify-center p-12">
          <div className="flex flex-col items-center gap-4">
            <div className="relative">
              <Loader2 className="h-12 w-12 animate-spin text-cyan-400" />
              <div className="absolute inset-0 h-12 w-12 animate-ping rounded-full bg-cyan-400/20" />
            </div>
            <span className="text-slate-400 font-medium">Loading analytics...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <Header title="Analytics" subtitle="Time series analysis and insights" />
        <div className="p-6">
          <div className="rounded-xl border border-red-500/30 bg-red-950/50 p-6 text-center text-red-400 shadow-[0_0_30px_rgba(239,68,68,0.2)]">
            {error}
          </div>
        </div>
      </div>
    );
  }

  // Convert data for charts
  const placesChartData = places.map((p) => ({
    name: p.name,
    value: p.count,
  }));

  const yearPieData = yearDistribution.map((y) => ({
    name: y.year,
    value: y.value,
    percentage: y.percentage,
  }));

  const monthPieData = monthsByYear
    .filter((m) => m.value > 0)
    .map((m) => ({
      name: m.month,
      value: m.value,
    }));

  // Render year analysis tab content
  const renderYearAnalysis = (year: number) => {
    const yearSummary = yearSummaries[year];
    const months = yearMonths[year] || [];
    const monthsLineData = months.map((m) => ({
      period: m.month,
      value: m.value,
    }));
    const monthsPieData = months
      .filter((m) => m.value > 0)
      .map((m) => ({
        name: m.month,
        value: m.value,
      }));

    const prevYear = year - 1;
    const trendSign = (yearSummary?.trends.sermonsChange || 0) >= 0 ? "+" : "";

    return (
      <div className="p-6 space-y-8">
        {/* Year KPI Cards */}
        <section>
          <h2 className="mb-6 text-xl font-bold text-white flex items-center gap-3">
            <div className="h-8 w-1 bg-gradient-to-b from-cyan-400 to-cyan-600 rounded-full" />
            {year} Key Metrics
          </h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <KPICard
              title={`${year} Sermons`}
              value={yearSummary?.totalSermons || 0}
              trend={yearSummary?.trends.sermonsChange}
              icon={<Video className="h-6 w-6" />}
              variant="cyan"
            />
            <KPICard
              title={`${year} Hours`}
              value={formatHours(yearSummary?.totalHours || 0)}
              trend={yearSummary?.trends.hoursChange}
              icon={<Clock className="h-6 w-6" />}
              variant="magenta"
            />
            <KPICard
              title="Avg Duration"
              value={`${Math.round(yearSummary?.avgDuration || 0)} min`}
              icon={<Clock className="h-6 w-6" />}
              variant="gold"
            />
            <KPICard
              title={`${year} Views`}
              value={formatViews(yearSummary?.totalViews || 0)}
              trend={yearSummary?.trends.viewsChange}
              icon={<Eye className="h-6 w-6" />}
              variant="lime"
            />
          </div>
        </section>

        {/* Year Highlights */}
        <section>
          <h2 className="mb-6 text-xl font-bold text-white flex items-center gap-3">
            <div className="h-8 w-1 bg-gradient-to-b from-pink-400 to-pink-600 rounded-full" />
            {year} Highlights
          </h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="relative overflow-hidden rounded-xl border border-cyan-500/30 bg-gradient-to-br from-slate-900 via-cyan-950 to-slate-900 p-6 shadow-[0_0_30px_rgba(6,182,212,0.2)]">
              <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-cyan-400 to-teal-500" />
              <p className="text-sm text-cyan-300/80 uppercase tracking-wider">Busiest Month</p>
              <p className="mt-2 text-3xl font-bold bg-gradient-to-r from-cyan-400 to-teal-400 bg-clip-text text-transparent">
                {yearSummary?.busiestMonth || "N/A"}
              </p>
            </div>
            <div className="relative overflow-hidden rounded-xl border border-amber-500/30 bg-gradient-to-br from-slate-900 via-amber-950 to-slate-900 p-6 shadow-[0_0_30px_rgba(245,158,11,0.2)]">
              <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-amber-400 to-yellow-500" />
              <p className="text-sm text-amber-300/80 uppercase tracking-wider">Total Preaching</p>
              <p className="mt-2 text-3xl font-bold bg-gradient-to-r from-amber-400 to-yellow-400 bg-clip-text text-transparent">
                {formatHours(yearSummary?.totalHours || 0)}
              </p>
            </div>
            <div className="relative overflow-hidden rounded-xl border border-purple-500/30 bg-gradient-to-br from-slate-900 via-purple-950 to-slate-900 p-6 shadow-[0_0_30px_rgba(139,92,246,0.2)]">
              <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-purple-400 to-violet-500" />
              <p className="text-sm text-purple-300/80 uppercase tracking-wider">Avg Sermon Length</p>
              <p className="mt-2 text-3xl font-bold bg-gradient-to-r from-purple-400 to-violet-400 bg-clip-text text-transparent">
                {Math.floor((yearSummary?.avgDuration || 0) / 60)}h {Math.round((yearSummary?.avgDuration || 0) % 60)}m
              </p>
            </div>
            <div
              className={cn(
                "relative overflow-hidden rounded-xl border p-6",
                (yearSummary?.trends.sermonsChange || 0) >= 0
                  ? "border-emerald-500/30 bg-gradient-to-br from-slate-900 via-emerald-950 to-slate-900 shadow-[0_0_30px_rgba(16,185,129,0.2)]"
                  : "border-rose-500/30 bg-gradient-to-br from-slate-900 via-rose-950 to-slate-900 shadow-[0_0_30px_rgba(244,63,94,0.2)]"
              )}
            >
              <div
                className={cn(
                  "absolute top-0 left-0 right-0 h-1 bg-gradient-to-r",
                  (yearSummary?.trends.sermonsChange || 0) >= 0
                    ? "from-emerald-400 to-green-500"
                    : "from-rose-400 to-red-500"
                )}
              />
              <p className={cn(
                "text-sm uppercase tracking-wider",
                (yearSummary?.trends.sermonsChange || 0) >= 0 ? "text-emerald-300/80" : "text-rose-300/80"
              )}>
                vs {prevYear}
              </p>
              <p
                className={cn(
                  "mt-2 text-3xl font-bold bg-gradient-to-r bg-clip-text text-transparent",
                  (yearSummary?.trends.sermonsChange || 0) >= 0
                    ? "from-emerald-400 to-green-400"
                    : "from-rose-400 to-red-400"
                )}
              >
                {trendSign}{yearSummary?.trends.sermonsChange || 0}%
              </p>
            </div>
          </div>
        </section>

        {/* Year Monthly Trends */}
        <section>
          <h2 className="mb-6 text-xl font-bold text-white flex items-center gap-3">
            <div className="h-8 w-1 bg-gradient-to-b from-lime-400 to-lime-600 rounded-full" />
            {year} Monthly Trends
          </h2>
          <div className="grid gap-6 lg:grid-cols-2">
            <LineChart
              data={monthsLineData}
              title={`Sermons per Month in ${year}`}
              valueLabel="Sermons"
              height={300}
              variant="cyan"
            />
            <PieChart
              data={monthsPieData}
              title={`${year} Monthly Distribution`}
              height={300}
              donut
            />
          </div>
        </section>

        {/* Year Monthly Breakdown Table */}
        <section>
          <h2 className="mb-6 text-xl font-bold text-white flex items-center gap-3">
            <div className="h-8 w-1 bg-gradient-to-b from-amber-400 to-amber-600 rounded-full" />
            {year} Month by Month
          </h2>
          <div className="overflow-hidden rounded-xl border border-slate-700/50 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 shadow-[0_0_40px_rgba(0,0,0,0.3)]">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700/50 bg-slate-800/50">
                  <th className="px-6 py-4 text-left text-sm font-bold text-slate-300 uppercase tracking-wider">Month</th>
                  <th className="px-6 py-4 text-right text-sm font-bold text-slate-300 uppercase tracking-wider">Sermons</th>
                  <th className="px-6 py-4 text-right text-sm font-bold text-slate-300 uppercase tracking-wider">Progress</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/30">
                {months.map((month, index) => {
                  const maxSermons = Math.max(...months.map((m) => m.value), 1);
                  const percentage = (month.value / maxSermons) * 100;
                  const isMax = month.value === maxSermons && month.value > 0;
                  return (
                    <tr
                      key={month.month}
                      className={cn(
                        "transition-colors",
                        isMax ? "bg-amber-950/30" : "hover:bg-slate-800/50"
                      )}
                    >
                      <td className="px-6 py-4 text-sm font-medium text-white flex items-center gap-2">
                        {month.month}
                        {isMax && (
                          <span className="px-2 py-0.5 text-xs font-bold bg-gradient-to-r from-amber-500 to-yellow-400 text-slate-900 rounded-full">
                            PEAK
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-right text-sm text-cyan-400 font-bold">{month.value}</td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="h-2 flex-1 rounded-full bg-slate-700/50 overflow-hidden">
                            <div
                              className={cn(
                                "h-2 rounded-full transition-all duration-500",
                                isMax
                                  ? "bg-gradient-to-r from-amber-400 to-yellow-500 shadow-[0_0_10px_rgba(251,191,36,0.5)]"
                                  : "bg-gradient-to-r from-cyan-500 to-teal-500"
                              )}
                              style={{ width: `${percentage}%` }}
                            />
                          </div>
                          <span className="text-xs text-slate-400 w-12 text-right font-medium">
                            {month.value > 0 ? `${Math.round(percentage)}%` : "-"}
                          </span>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <Header title="Analytics" subtitle="Time series analysis and insights" />

      {/* Tab Navigation */}
      <div className="border-b border-slate-700/50 px-6 overflow-x-auto bg-slate-900/50 backdrop-blur-sm">
        <nav className="flex gap-1 min-w-max">
          <button
            onClick={() => setActiveTab("overview")}
            className={cn(
              "px-5 py-4 text-sm font-medium border-b-2 transition-all duration-300 whitespace-nowrap",
              activeTab === "overview"
                ? "border-cyan-400 text-cyan-400 bg-cyan-500/10"
                : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
            )}
          >
            <span className="flex items-center gap-2">
              <TrendingUp size={18} />
              Overview
            </span>
          </button>
          {ANALYSIS_YEARS.map((year) => (
            <button
              key={year}
              onClick={() => setActiveTab(year)}
              className={cn(
                "px-5 py-4 text-sm font-medium border-b-2 transition-all duration-300 whitespace-nowrap",
                activeTab === year
                  ? "border-cyan-400 text-cyan-400 bg-cyan-500/10"
                  : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
              )}
            >
              <span className="flex items-center gap-2">
                <Calendar size={16} />
                {year}
              </span>
            </button>
          ))}
        </nav>
      </div>

      {activeTab === "overview" ? (
        <div className="p-6 space-y-10">
          {/* KPI Cards */}
          <section>
            <h2 className="mb-6 text-xl font-bold text-white flex items-center gap-3">
              <div className="h-8 w-1 bg-gradient-to-b from-cyan-400 to-cyan-600 rounded-full" />
              Key Metrics
            </h2>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <KPICard
                title="Total Sermons"
                value={summary?.totalSermons || 0}
                trend={summary?.trends.sermonsChange}
                icon={<Video className="h-6 w-6" />}
                variant="cyan"
              />
              <KPICard
                title="Total Hours"
                value={formatHours(summary?.totalHours || 0)}
                trend={summary?.trends.hoursChange}
                icon={<Clock className="h-6 w-6" />}
                variant="magenta"
              />
              <KPICard
                title="Avg Duration"
                value={`${Math.round(summary?.avgDuration || 0)} min`}
                trend={summary?.trends.durationChange}
                icon={<Clock className="h-6 w-6" />}
                variant="gold"
              />
              <KPICard
                title="Total Views"
                value={formatViews(summary?.totalViews || 0)}
                trend={summary?.trends.viewsChange}
                icon={<Eye className="h-6 w-6" />}
                variant="lime"
              />
            </div>
          </section>

          {/* Year Comparison Pie Charts */}
          <section>
            <h2 className="mb-6 text-xl font-bold text-white flex items-center gap-3">
              <div className="h-8 w-1 bg-gradient-to-b from-pink-400 to-pink-600 rounded-full" />
              Year Comparison
            </h2>
            <div className="grid gap-6 lg:grid-cols-2">
              <PieChart
                data={yearPieData}
                title={`Busiest Years (${busiestYear} leads with ${
                  yearDistribution.find((y) => y.year === busiestYear)?.value || 0
                } sermons)`}
                height={320}
                donut
                highlightFirst
              />
              <div className="relative overflow-hidden rounded-xl border border-slate-700/50 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6 shadow-[0_0_40px_rgba(0,0,0,0.3)]">
                <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-bl from-purple-500/10 to-transparent pointer-events-none" />
                <div className="mb-4 flex items-center justify-between">
                  <h3 className="text-lg font-bold text-white">Monthly Breakdown</h3>
                  <select
                    value={selectedYear}
                    onChange={(e) => setSelectedYear(parseInt(e.target.value))}
                    className="rounded-lg border border-slate-600 bg-slate-800 px-4 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 transition-all"
                  >
                    {availableYears.map((year) => (
                      <option key={year} value={year}>
                        {year}
                      </option>
                    ))}
                  </select>
                </div>
                <PieChart data={monthPieData} title="" height={240} showLegend={false} />
                <div className="mt-3 text-center">
                  <span className="px-4 py-2 rounded-full bg-slate-800 text-sm text-slate-300 font-medium">
                    {selectedYear}: <span className="text-cyan-400 font-bold">{monthsByYear.reduce((a, b) => a + b.value, 0)}</span> sermons
                  </span>
                </div>
              </div>
            </div>
          </section>

          {/* Busiest Months Histogram */}
          <section>
            <h2 className="mb-6 text-xl font-bold text-white flex items-center gap-3">
              <div className="h-8 w-1 bg-gradient-to-b from-amber-400 to-amber-600 rounded-full" />
              <BarChart3 className="h-5 w-5 text-amber-400" />
              Historically Busiest Months
            </h2>
            <Histogram
              data={busiestMonths}
              title="Total Sermons by Month (All Years Combined)"
              height={320}
              showAverage
            />
          </section>

          {/* Sermon Count Charts */}
          <section>
            <h2 className="mb-6 text-xl font-bold text-white flex items-center gap-3">
              <div className="h-8 w-1 bg-gradient-to-b from-lime-400 to-lime-600 rounded-full" />
              Sermon Frequency
            </h2>
            <div className="grid gap-6 lg:grid-cols-3">
              <LineChart data={sermonsByYear} title="Sermons by Year" valueLabel="Sermons" height={280} variant="cyan" />
              <LineChart
                data={sermonsByMonth}
                title="Sermons by Month (Last 24)"
                valueLabel="Sermons"
                height={280}
                variant="magenta"
              />
              <LineChart
                data={sermonsByWeek}
                title="Sermons by Week (Last 12)"
                valueLabel="Sermons"
                height={280}
                variant="lime"
              />
            </div>
          </section>

          {/* Duration Charts */}
          <section>
            <h2 className="mb-6 text-xl font-bold text-white flex items-center gap-3">
              <div className="h-8 w-1 bg-gradient-to-b from-purple-400 to-purple-600 rounded-full" />
              Average Duration Analysis
            </h2>
            <div className="grid gap-6 lg:grid-cols-3">
              <LineChart
                data={durationByYear}
                title="Avg Hours per Sermon by Year"
                valueLabel="Hours"
                height={280}
                formatValue={formatHours}
                variant="gold"
              />
              <LineChart
                data={durationByMonth}
                title="Avg Hours per Sermon by Month"
                valueLabel="Hours"
                height={280}
                formatValue={formatHours}
                variant="cyan"
              />
              <LineChart
                data={durationByWeek}
                title="Total Hours by Week"
                valueLabel="Hours"
                height={280}
                formatValue={formatHours}
                variant="magenta"
              />
            </div>
          </section>

          {/* Views Charts */}
          <section>
            <h2 className="mb-6 text-xl font-bold text-white flex items-center gap-3">
              <div className="h-8 w-1 bg-gradient-to-b from-rose-400 to-rose-600 rounded-full" />
              Views Analysis
            </h2>
            <div className="grid gap-6 lg:grid-cols-3">
              <LineChart
                data={viewsByYear}
                title="Avg Views per Sermon by Year"
                valueLabel="Views"
                height={280}
                formatValue={formatViews}
                variant="lime"
              />
              <LineChart
                data={viewsByMonth}
                title="Avg Views per Sermon by Month"
                valueLabel="Views"
                height={280}
                formatValue={formatViews}
                variant="gold"
              />
              <LineChart
                data={viewsByWeek}
                title="Avg Views by Week"
                valueLabel="Views"
                height={280}
                formatValue={formatViews}
                variant="cyan"
              />
            </div>
          </section>

          {/* Location Distribution */}
          <section>
            <h2 className="mb-6 text-xl font-bold text-white flex items-center gap-3">
              <div className="h-8 w-1 bg-gradient-to-b from-teal-400 to-teal-600 rounded-full" />
              <MapPin className="h-5 w-5 text-teal-400" />
              Sermons by Location
            </h2>
            <div className="grid gap-6 lg:grid-cols-2">
              <BarChart data={placesChartData} title="Sermon Count by Place" height={350} horizontal />
              <div className="relative overflow-hidden rounded-xl border border-slate-700/50 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6 shadow-[0_0_40px_rgba(0,0,0,0.3)]">
                <div className="absolute top-0 left-0 w-32 h-32 bg-gradient-to-br from-teal-500/10 to-transparent pointer-events-none" />
                <h3 className="mb-6 text-xl font-bold text-white">Location Details</h3>
                <div className="space-y-3">
                  {places.map((place, index) => {
                    const colors = ["from-cyan-500 to-teal-500", "from-pink-500 to-rose-500", "from-amber-500 to-yellow-500", "from-lime-500 to-green-500", "from-purple-500 to-violet-500"];
                    return (
                      <div
                        key={place.name}
                        className="flex items-center justify-between rounded-xl bg-slate-800/50 p-4 border border-slate-700/30 hover:border-slate-600/50 transition-all"
                      >
                        <div className="flex items-center gap-4">
                          <div className={cn(
                            "flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br text-sm font-bold text-white shadow-lg",
                            colors[index % colors.length]
                          )}>
                            {index + 1}
                          </div>
                          <div>
                            <p className="font-medium text-white">{place.name}</p>
                            <p className="text-xs text-slate-400">
                              {formatHours(place.total_duration / 3600)} total preaching
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-teal-400 bg-clip-text text-transparent">
                            {place.count}
                          </p>
                          <p className="text-xs text-slate-500">sermons</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </section>
        </div>
      ) : (
        renderYearAnalysis(activeTab as number)
      )}
    </div>
  );
}
