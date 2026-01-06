"use client";

import { useEffect, useState } from "react";
import Header from "@/components/layout/Header";
import KPICard from "@/components/charts/KPICard";
import LineChart from "@/components/charts/LineChart";
import {
  AlertTriangle,
  FileText,
  HeartPulse,
  LineChart as LineChartIcon,
  Loader2,
  ThumbsUp,
  Zap,
} from "lucide-react";
import api from "@/lib/api";
import {
  AIStatus,
  HealthReport,
  HealthScore,
  WorkloadTrend,
} from "@/lib/types";
import { cn } from "@/lib/utils";

// Helper component for displaying report sections
const ReportSection = ({
  title,
  items,
  icon,
  color = "text-primary",
}: {
  title: string;
  items: string[];
  icon: React.ReactNode;
  color?: string;
}) => {
  if (!items || items.length === 0) return null;
  return (
    <div className="card">
      <h3 className={cn("mb-3 text-lg font-semibold flex items-center", color)}>
        {icon}
        <span className="ml-2">{title}</span>
      </h3>
      <ul className="space-y-2">
        {items.map((item, index) => (
          <li key={index} className="flex items-start">
            <span className={cn("mr-3 mt-1 h-2 w-2 rounded-full", color.replace("text-", "bg-"))}></span>
            <span className="text-gray-700">{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
};

// Main Health Page Component
export default function HealthPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<HealthReport | null>(null);
  const [trends, setTrends] = useState<WorkloadTrend[]>([]);
  const [aiStatus, setAIStatus] = useState<AIStatus | null>(null);

  useEffect(() => {
    async function loadHealthData() {
      setLoading(true);
      setError(null);
      try {
        const [reportRes, trendsRes, aiStatusRes] = await Promise.all([
          api.getHealthReport(),
          api.getHealthTrends(),
          api.getAIStatus(),
        ]);
        setReport(reportRes);
        // Handle both array and object responses for trends
        if (Array.isArray(trendsRes)) {
          setTrends(trendsRes);
        } else if (trendsRes && typeof trendsRes === 'object' && 'trends' in trendsRes && Array.isArray((trendsRes as { trends: WorkloadTrend[] }).trends)) {
          setTrends((trendsRes as { trends: WorkloadTrend[] }).trends);
        } else {
          setTrends([]);
        }
        setAIStatus(aiStatusRes);
      } catch (err) {
        console.error("Failed to load health data:", err);
        setError("Failed to load health data. Please ensure the backend is running.");
      } finally {
        setLoading(false);
      }
    }
    loadHealthData();
  }, []);

  const getScoreColor = (status: "good" | "moderate" | "high") => {
    if (status === "good") return "text-green-500";
    if (status === "moderate") return "text-yellow-500";
    return "text-red-500";
  };

  const workloadChartData = Array.isArray(trends)
    ? trends.map((t) => ({
        period: t.week_start,
        value: t.hours,
      }))
    : [];

  if (loading) {
    return (
      <div>
        <Header
          title="Health Insights"
          subtitle="AI-powered analysis of workload and well-being"
        />
        <div className="flex items-center justify-center p-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <span className="ml-3 text-gray-500">Loading Health Report...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <Header
          title="Health Insights"
          subtitle="AI-powered analysis of workload and well-being"
        />
        <div className="p-6">
          <div className="rounded-lg bg-red-50 p-6 text-center text-red-600">
            {error}
          </div>
        </div>
      </div>
    );
  }

  if (!report) return null;

  const { score, metrics } = report;

  return (
    <div>
      <Header
        title="Health Insights"
        subtitle="AI-powered analysis of workload and well-being"
      />

      <div className="p-6 space-y-8">
        {/* AI Status & Health Score */}
        <section className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <div className={cn("card h-full flex flex-col justify-between", {
              "bg-green-50 border-green-200": score.status === "good",
              "bg-yellow-50 border-yellow-200": score.status === "moderate",
              "bg-red-50 border-red-200": score.status === "high",
            })}>
              <div>
                <h2 className="text-xl font-bold text-gray-900 mb-2">Health Score</h2>
                <div className="flex items-center">
                  <p className={cn("text-6xl font-bold", getScoreColor(score.status))}>
                    {score.score.toFixed(0)}
                    <span className="text-4xl">/100</span>
                  </p>
                  <p className={cn("ml-4 text-2xl font-semibold capitalize", getScoreColor(score.status))}>
                    ({score.status} Workload)
                  </p>
                </div>
              </div>
              <p className="mt-4 text-gray-600">
                {report.summary}
              </p>
            </div>
          </div>

          <div className="card">
            <h3 className="text-lg font-semibold mb-3">AI Status</h3>
            {aiStatus?.available ? (
              <div className="text-green-600 flex items-center">
                <Zap size={20} className="mr-2"/>
                <span>Ollama Service: <span className="font-bold">Available</span> ({aiStatus.model})</span>
              </div>
            ) : (
              <div className="text-red-500 flex items-center">
                <AlertTriangle size={20} className="mr-2"/>
                <span>Ollama Service: <span className="font-bold">Unavailable</span></span>
              </div>
            )}
            <p className="text-sm text-gray-500 mt-2">
              {aiStatus?.message}
            </p>
            <div className="mt-4 pt-4 border-t">
              <h3 className="text-lg font-semibold mb-2">Report Info</h3>
              <p className="text-sm text-gray-600">
                Generated: {new Date(report.generatedAt).toLocaleString()}
              </p>
              <p className="text-sm text-gray-600">
                Source: {report.aiGenerated ? "AI-Generated" : "Rule-Based Fallback"}
              </p>
            </div>
          </div>
        </section>

        {/* AI Generated Report */}
        <section>
          <h2 className="mb-4 text-xl font-bold text-gray-900 flex items-center">
            <FileText className="mr-3 text-primary"/>
            AI Doctor's Report
          </h2>
          <div className="grid gap-6 lg:grid-cols-2">
            <ReportSection
              title="Key Concerns"
              items={report.concerns}
              icon={<AlertTriangle size={20} />}
              color="text-red-500"
            />
            <ReportSection
              title="Positive Observations"
              items={report.positiveObservations}
              icon={<ThumbsUp size={20} />}
              color="text-green-500"
            />
          </div>
          <div className="grid gap-6 lg:grid-cols-3 mt-6">
             <ReportSection
              title="Rest Recommendations"
              items={report.restRecommendations}
              icon={<HeartPulse size={20} />}
              color="text-blue-500"
            />
            <ReportSection
              title="Sleep Guidelines"
              items={report.sleepGuidelines}
              icon={<HeartPulse size={20} />}
              color="text-indigo-500"
            />
            <ReportSection
              title="Holiday & Recovery"
              items={report.holidayRecommendations}
              icon={<HeartPulse size={20} />}
              color="text-purple-500"
            />
          </div>
        </section>

        {/* Workload Metrics & Trends */}
        <section>
          <h2 className="mb-4 text-xl font-bold text-gray-900 flex items-center">
            <LineChartIcon className="mr-3 text-primary"/>
            Workload Analysis
          </h2>
          <div className="grid gap-6 lg:grid-cols-3">
            <div className="lg:col-span-1 space-y-4">
              <KPICard title="Sermons This Week" value={`${metrics.sermonsThisWeek}`} description={`${metrics.hoursThisWeek.toFixed(1)} hours preached`} />
              <KPICard title="Sermons This Month" value={`${metrics.sermonsThisMonth}`} description={`${metrics.hoursThisMonth.toFixed(1)} hours preached`} />
              <KPICard title="Trips This Month" value={`${metrics.tripsThisMonth}`} description={`${metrics.travelThisMonthKm.toFixed(0)} km traveled`} />
              <KPICard title="Days Since Rest" value={`${metrics.daysSinceRest}`} description={`${metrics.consecutiveBusyWeeks} consecutive busy weeks`} />
            </div>
            <div className="lg:col-span-2 card h-full">
              <LineChart
                data={workloadChartData}
                title="Preaching Hours Trend (Weekly)"
                valueLabel="Hours"
                height={300}
              />
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}