"use client";

import { useEffect, useState } from "react";
import Header from "@/components/layout/Header";
import LineChart from "@/components/charts/LineChart";
import BarChart from "@/components/charts/BarChart";
import KPICard from "@/components/charts/KPICard";
import PieChart from "@/components/charts/PieChart";
import Histogram from "@/components/charts/Histogram";
import { Video, Clock, Eye, Loader2, Calendar, TrendingUp } from "lucide-react";
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
      <div>
        <Header title="Analytics" subtitle="Time series analysis and insights" />
        <div className="flex items-center justify-center p-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <span className="ml-3 text-gray-500">Loading analytics...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <Header title="Analytics" subtitle="Time series analysis and insights" />
        <div className="p-6">
          <div className="rounded-lg bg-red-50 p-6 text-center text-red-600">
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
          <h2 className="mb-4 text-lg font-semibold text-gray-900">{year} Key Metrics</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <KPICard
              title={`${year} Sermons`}
              value={yearSummary?.totalSermons || 0}
              trend={yearSummary?.trends.sermonsChange}
              icon={<Video className="h-6 w-6 text-primary" />}
            />
            <KPICard
              title={`${year} Hours`}
              value={formatHours(yearSummary?.totalHours || 0)}
              trend={yearSummary?.trends.hoursChange}
              icon={<Clock className="h-6 w-6 text-primary" />}
            />
            <KPICard
              title="Avg Duration"
              value={`${Math.round(yearSummary?.avgDuration || 0)} min`}
              icon={<Clock className="h-6 w-6 text-secondary-dark" />}
            />
            <KPICard
              title={`${year} Views`}
              value={formatViews(yearSummary?.totalViews || 0)}
              trend={yearSummary?.trends.viewsChange}
              icon={<Eye className="h-6 w-6 text-secondary-dark" />}
            />
          </div>
        </section>

        {/* Year Highlights */}
        <section>
          <h2 className="mb-4 text-lg font-semibold text-gray-900">{year} Highlights</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="card bg-gradient-to-br from-primary to-primary-light text-white">
              <p className="text-sm opacity-80">Busiest Month</p>
              <p className="mt-1 text-2xl font-bold">{yearSummary?.busiestMonth || "N/A"}</p>
            </div>
            <div className="card bg-gradient-to-br from-secondary-dark to-secondary text-gray-900">
              <p className="text-sm opacity-80">Total Preaching</p>
              <p className="mt-1 text-2xl font-bold">{formatHours(yearSummary?.totalHours || 0)}</p>
            </div>
            <div className="card border-2 border-primary">
              <p className="text-sm text-gray-500">Avg Sermon Length</p>
              <p className="mt-1 text-2xl font-bold text-primary">
                {Math.floor((yearSummary?.avgDuration || 0) / 60)}h{" "}
                {Math.round((yearSummary?.avgDuration || 0) % 60)}m
              </p>
            </div>
            <div
              className={cn(
                "card border-2",
                (yearSummary?.trends.sermonsChange || 0) >= 0 ? "border-green-500" : "border-red-500"
              )}
            >
              <p className="text-sm text-gray-500">vs {prevYear}</p>
              <p
                className={cn(
                  "mt-1 text-2xl font-bold",
                  (yearSummary?.trends.sermonsChange || 0) >= 0 ? "text-green-600" : "text-red-600"
                )}
              >
                {trendSign}
                {yearSummary?.trends.sermonsChange || 0}% sermons
              </p>
            </div>
          </div>
        </section>

        {/* Year Monthly Trends */}
        <section>
          <h2 className="mb-4 text-lg font-semibold text-gray-900">{year} Monthly Trends</h2>
          <div className="grid gap-6 lg:grid-cols-2">
            <LineChart
              data={monthsLineData}
              title={`Sermons per Month in ${year}`}
              valueLabel="Sermons"
              height={300}
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
          <h2 className="mb-4 text-lg font-semibold text-gray-900">{year} Month by Month</h2>
          <div className="card overflow-hidden p-0">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Month</th>
                  <th className="px-4 py-3 text-right text-sm font-semibold text-gray-900">Sermons</th>
                  <th className="px-4 py-3 text-right text-sm font-semibold text-gray-900">Progress</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {months.map((month) => {
                  const maxSermons = Math.max(...months.map((m) => m.value), 1);
                  const percentage = (month.value / maxSermons) * 100;
                  return (
                    <tr key={month.month} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm font-medium text-gray-900">{month.month}</td>
                      <td className="px-4 py-3 text-right text-sm text-gray-700">{month.value}</td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="h-2 flex-1 rounded-full bg-gray-200">
                            <div
                              className="h-2 rounded-full bg-primary"
                              style={{ width: `${percentage}%` }}
                            />
                          </div>
                          <span className="text-xs text-gray-500 w-10">
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
    <div>
      <Header title="Analytics" subtitle="Time series analysis and insights" />

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 px-6 overflow-x-auto">
        <nav className="flex gap-1 min-w-max">
          <button
            onClick={() => setActiveTab("overview")}
            className={cn(
              "px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap",
              activeTab === "overview"
                ? "border-primary text-primary"
                : "border-transparent text-gray-500 hover:text-gray-700"
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
                "px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap",
                activeTab === year
                  ? "border-primary text-primary"
                  : "border-transparent text-gray-500 hover:text-gray-700"
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
        <div className="p-6 space-y-8">
          {/* KPI Cards */}
          <section>
            <h2 className="mb-4 text-lg font-semibold text-gray-900">Key Metrics</h2>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <KPICard
                title="Total Sermons"
                value={summary?.totalSermons || 0}
                trend={summary?.trends.sermonsChange}
                icon={<Video className="h-6 w-6 text-primary" />}
              />
              <KPICard
                title="Total Hours"
                value={formatHours(summary?.totalHours || 0)}
                trend={summary?.trends.hoursChange}
                icon={<Clock className="h-6 w-6 text-primary" />}
              />
              <KPICard
                title="Avg Duration"
                value={`${Math.round(summary?.avgDuration || 0)} min`}
                trend={summary?.trends.durationChange}
                icon={<Clock className="h-6 w-6 text-secondary-dark" />}
              />
              <KPICard
                title="Total Views"
                value={formatViews(summary?.totalViews || 0)}
                trend={summary?.trends.viewsChange}
                icon={<Eye className="h-6 w-6 text-secondary-dark" />}
              />
            </div>
          </section>

          {/* Year Comparison Pie Charts */}
          <section>
            <h2 className="mb-4 text-lg font-semibold text-gray-900">Year Comparison</h2>
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
              <div className="card">
                <div className="mb-4 flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900">Monthly Breakdown</h3>
                  <select
                    value={selectedYear}
                    onChange={(e) => setSelectedYear(parseInt(e.target.value))}
                    className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary focus:outline-none"
                  >
                    {availableYears.map((year) => (
                      <option key={year} value={year}>
                        {year}
                      </option>
                    ))}
                  </select>
                </div>
                <PieChart data={monthPieData} title="" height={260} showLegend={false} />
                <div className="mt-2 text-center text-sm text-gray-500">
                  {selectedYear}: {monthsByYear.reduce((a, b) => a + b.value, 0)} sermons
                </div>
              </div>
            </div>
          </section>

          {/* Busiest Months Histogram */}
          <section>
            <h2 className="mb-4 text-lg font-semibold text-gray-900">Historically Busiest Months</h2>
            <Histogram
              data={busiestMonths}
              title="Total Sermons by Month (All Years Combined)"
              height={320}
              showAverage
            />
          </section>

          {/* Sermon Count Charts */}
          <section>
            <h2 className="mb-4 text-lg font-semibold text-gray-900">Sermon Frequency</h2>
            <div className="grid gap-6 lg:grid-cols-3">
              <LineChart data={sermonsByYear} title="Sermons by Year" valueLabel="Sermons" height={280} />
              <LineChart
                data={sermonsByMonth}
                title="Sermons by Month (Last 24)"
                valueLabel="Sermons"
                height={280}
              />
              <LineChart
                data={sermonsByWeek}
                title="Sermons by Week (Last 12)"
                valueLabel="Sermons"
                height={280}
              />
            </div>
          </section>

          {/* Duration Charts */}
          <section>
            <h2 className="mb-4 text-lg font-semibold text-gray-900">Average Duration Analysis</h2>
            <div className="grid gap-6 lg:grid-cols-3">
              <LineChart
                data={durationByYear}
                title="Avg Hours per Sermon by Year"
                valueLabel="Hours"
                height={280}
                formatValue={formatHours}
              />
              <LineChart
                data={durationByMonth}
                title="Avg Hours per Sermon by Month"
                valueLabel="Hours"
                height={280}
                formatValue={formatHours}
              />
              <LineChart
                data={durationByWeek}
                title="Total Hours by Week"
                valueLabel="Hours"
                height={280}
                formatValue={formatHours}
              />
            </div>
          </section>

          {/* Views Charts */}
          <section>
            <h2 className="mb-4 text-lg font-semibold text-gray-900">Views Analysis</h2>
            <div className="grid gap-6 lg:grid-cols-3">
              <LineChart
                data={viewsByYear}
                title="Avg Views per Sermon by Year"
                valueLabel="Views"
                height={280}
                formatValue={formatViews}
              />
              <LineChart
                data={viewsByMonth}
                title="Avg Views per Sermon by Month"
                valueLabel="Views"
                height={280}
                formatValue={formatViews}
              />
              <LineChart
                data={viewsByWeek}
                title="Avg Views by Week"
                valueLabel="Views"
                height={280}
                formatValue={formatViews}
              />
            </div>
          </section>

          {/* Location Distribution */}
          <section>
            <h2 className="mb-4 text-lg font-semibold text-gray-900">Sermons by Location</h2>
            <div className="grid gap-6 lg:grid-cols-2">
              <BarChart data={placesChartData} title="Sermon Count by Place" height={350} horizontal />
              <div className="card">
                <h3 className="mb-4 text-lg font-semibold text-gray-900">Location Details</h3>
                <div className="space-y-3">
                  {places.map((place, index) => (
                    <div
                      key={place.name}
                      className="flex items-center justify-between rounded-lg bg-gray-50 p-3"
                    >
                      <div className="flex items-center gap-3">
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-sm font-bold text-white">
                          {index + 1}
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">{place.name}</p>
                          <p className="text-xs text-gray-500">
                            {formatHours(place.total_duration / 3600)} total
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-xl font-bold text-primary">{place.count}</p>
                        <p className="text-xs text-gray-500">sermons</p>
                      </div>
                    </div>
                  ))}
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
