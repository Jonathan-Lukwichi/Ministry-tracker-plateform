"use client";

import { useEffect, useState } from "react";
import Header from "@/components/layout/Header";
import {
  AlertTriangle,
  Calendar,
  Car,
  Coffee,
  Loader2,
  Map,
  TrendingUp,
  Users,
  Zap,
} from "lucide-react";
import api from "@/lib/api";
import { AIStatus, PlanningReport } from "@/lib/types";
import { cn } from "@/lib/utils";

// Helper component for displaying report sections
const ReportSectionList = ({
  title,
  items,
  icon,
  color = "text-primary",
  renderItem,
}: {
  title: string;
  items: any[];
  icon: React.ReactNode;
  color?: string;
  renderItem: (item: any, index: number) => React.ReactNode;
}) => {
  if (!items || items.length === 0) return null;
  return (
    <div className="card h-full">
      <h3 className={cn("mb-3 text-lg font-semibold flex items-center", color)}>
        {icon}
        <span className="ml-2">{title}</span>
      </h3>
      <div className="space-y-3">
        {items.map((item, index) => renderItem(item, index))}
      </div>
    </div>
  );
};

// Main Planning Page Component
export default function PlanningPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<PlanningReport | null>(null);
  const [aiStatus, setAIStatus] = useState<AIStatus | null>(null);

  useEffect(() => {
    async function loadPlanningData() {
      setLoading(true);
      setError(null);
      try {
        const [reportRes, aiStatusRes] = await Promise.all([
          api.getPlanningReport(),
          api.getAIStatus(),
        ]);
        setReport(reportRes);
        setAIStatus(aiStatusRes);
      } catch (err) {
        console.error("Failed to load planning data:", err);
        setError("Failed to load planning data. Please ensure the backend is running.");
      } finally {
        setLoading(false);
      }
    }
    loadPlanningData();
  }, []);

  if (loading) {
    return (
      <div>
        <Header
          title="Planning Assistant"
          subtitle="AI-powered recommendations for trips and meetings"
        />
        <div className="flex items-center justify-center p-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <span className="ml-3 text-gray-500">Loading Planning Report...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <Header
          title="Planning Assistant"
          subtitle="AI-powered recommendations for trips and meetings"
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

  return (
    <div>
      <Header
        title="Planning Assistant"
        subtitle="AI-powered recommendations for trips and meetings"
      />

      <div className="p-6 space-y-8">
        {/* AI Status & Overview */}
        <section className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2 card bg-gradient-to-br from-primary to-primary-light text-white">
            <h2 className="text-xl font-bold mb-2">Upcoming Month Overview</h2>
            <p className="opacity-90">{report.upcomingOverview}</p>
            {report.highDemandWarnings && report.highDemandWarnings.length > 0 && (
              <div className="mt-4 rounded-lg bg-primary-dark p-3">
                <h4 className="font-semibold flex items-center"><AlertTriangle size={18} className="mr-2"/> High-Demand Periods</h4>
                <ul className="mt-2 text-sm list-disc list-inside">
                  {report.highDemandWarnings.map((warning, i) => <li key={i}>{warning}</li>)}
                </ul>
              </div>
            )}
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

        {/* AI Recommendations */}
        <section>
          <h2 className="mb-4 text-xl font-bold text-gray-900">
            AI-Powered Recommendations
          </h2>
          <div className="grid gap-6 lg:grid-cols-3">
            <ReportSectionList
              title="Trip Recommendations"
              items={report.tripRecommendations || []}
              icon={<Car size={20} />}
              color="text-blue-500"
              renderItem={(item, i) => (
                <div key={i} className="p-3 rounded-lg bg-blue-50">
                  <p className="font-semibold">{item.destination}</p>
                  <p className="text-sm text-gray-700">{item.reason}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    Period: {item.suggestedPeriod} | Priority: <span className="capitalize">{item.priority}</span>
                  </p>
                </div>
              )}
            />
            <ReportSectionList
              title="Meeting Suggestions"
              items={report.meetingSuggestions || []}
              icon={<Users size={20} />}
              color="text-purple-500"
              renderItem={(item, i) => (
                <div key={i} className="p-3 rounded-lg bg-purple-50">
                  <p className="font-semibold">{item.type}</p>
                  <p className="text-sm text-gray-700">{item.reason}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {item.suggestedDay} - {item.suggestedTime}
                  </p>
                </div>
              )}
            />
            <ReportSectionList
              title="Suggested Rest Windows"
              items={report.restWindows || []}
              icon={<Coffee size={20} />}
              color="text-green-500"
              renderItem={(item, i) => (
                <div key={i} className="p-3 rounded-lg bg-green-50">
                  <p className="font-semibold">{item.start} to {item.end}</p>
                  <p className="text-sm text-gray-700">{item.note}</p>
                  <p className="text-xs text-gray-500 mt-1 capitalize">Type: {item.type}</p>
                </div>
              )}
            />
          </div>
        </section>

        {/* Data Foundations */}
        <section>
          <h2 className="mb-4 text-xl font-bold text-gray-900">
            Data Foundations
          </h2>
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Upcoming Predictions */}
            <div className="card">
              <h3 className="mb-3 text-lg font-semibold flex items-center text-primary-dark">
                <TrendingUp size={20} className="mr-2"/>
                Upcoming Predictions ({report.upcoming?.nextMonth?.monthName || "Next Month"})
              </h3>
              <div className="space-y-3">
                <div className="p-3 rounded-lg bg-gray-50 flex justify-between items-center">
                    <div>
                        <p className="font-semibold">Sermon Count</p>
                        <p className="text-sm text-gray-600">Predicted number of sermons</p>
                    </div>
                    <p className="text-2xl font-bold text-primary">{report.upcoming?.nextMonth?.predictedSermons ?? 0}</p>
                </div>
                <div className="p-3 rounded-lg bg-gray-50 flex justify-between items-center">
                    <div>
                        <p className="font-semibold">Travel Days</p>
                        <p className="text-sm text-gray-600">Predicted number of travel days</p>
                    </div>
                    <p className="text-2xl font-bold text-primary">{report.upcoming?.nextMonth?.predictedTrips ?? 0}</p>
                </div>
              </div>
            </div>

            {/* Historical Patterns */}
            <div className="card">
                <h3 className="mb-3 text-lg font-semibold flex items-center text-secondary-dark">
                    <Map size={20} className="mr-2"/>
                    Historical Patterns
                </h3>
                <div className="space-y-3">
                    <div className="p-3 rounded-lg bg-gray-50">
                        <p className="font-semibold">Busiest Month</p>
                        <p className="text-sm text-gray-600">{report.patterns?.busiestMonth || "N/A"} (Quietest: {report.patterns?.quietestMonth || "N/A"})</p>
                    </div>
                     <div className="p-3 rounded-lg bg-gray-50">
                        <p className="font-semibold">Most Visited Places</p>
                        <p className="text-sm text-gray-600">
                          {report.patterns?.locationFrequency?.slice(0, 5).map((loc: any) => loc.location).join(", ") || "N/A"}
                        </p>
                    </div>
                    <div className="p-3 rounded-lg bg-gray-50">
                        <p className="font-semibold">Total Data</p>
                        <p className="text-sm text-gray-600">{report.patterns?.totalSermons || 0} sermons over {report.patterns?.yearsOfData || 0} years</p>
                    </div>
                </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
