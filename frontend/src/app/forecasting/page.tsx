"use client";

import { useEffect, useState } from "react";
import Header from "@/components/layout/Header";
import ForecastChart from "@/components/charts/ForecastChart";
import { api } from "@/lib/api";
import {
  SermonForecastResponse,
  TripForecastResponse,
  ForecastModelStatusResponse,
} from "@/lib/types";
import {
  TrendingUp,
  Calendar,
  Plane,
  CheckCircle,
  XCircle,
  RefreshCw,
  Brain,
  Target,
  Activity,
  BarChart3,
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

export default function ForecastingPage() {
  const [sermonForecast, setSermonForecast] = useState<SermonForecastResponse | null>(null);
  const [tripForecast, setTripForecast] = useState<TripForecastResponse | null>(null);
  const [modelStatus, setModelStatus] = useState<ForecastModelStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [retraining, setRetraining] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [sermons, trips, status] = await Promise.all([
        api.getSermonForecast(),
        api.getTripForecast(),
        api.getForecastModelStatus(),
      ]);

      setSermonForecast(sermons);
      setTripForecast(trips);
      setModelStatus(status);
    } catch (err) {
      setError("Failed to load forecast data");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleRetrain = async () => {
    try {
      setRetraining(true);
      await api.retrainForecastModels();
      await loadData();
    } catch (err) {
      console.error("Failed to retrain models:", err);
    } finally {
      setRetraining(false);
    }
  };

  // Chart colors
  const MONTH_COLORS = [
    "#4A148C", "#5E1B99", "#6A1B9A", "#7B1FA2", "#8E24AA", "#9C27B0",
    "#AB47BC", "#BA68C8", "#CE93D8", "#D4A5DC", "#E1BEE7", "#EDE7F6",
  ];

  if (loading) {
    return (
      <div>
        <Header title="ML Forecasting" subtitle="2026 Predictions" />
        <div className="flex h-96 items-center justify-center">
          <div className="text-center">
            <Brain className="mx-auto h-12 w-12 animate-pulse text-purple-500" />
            <p className="mt-4 text-gray-500">Training models and generating predictions...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <Header title="ML Forecasting" subtitle="2026 Predictions" />

      <div className="space-y-6 p-6">
        {/* Model Status Banner */}
        <div className="card bg-gradient-to-r from-purple-50 to-purple-100">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="rounded-full bg-white p-3 shadow">
                <Brain className="h-6 w-6 text-purple-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">XGBoost Forecasting Model</h3>
                <div className="flex items-center gap-4 mt-1">
                  <div className="flex items-center gap-1">
                    {modelStatus?.sermonModel.trained ? (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    ) : (
                      <XCircle className="h-4 w-4 text-red-500" />
                    )}
                    <span className="text-sm text-gray-600">
                      Sermon Model: {modelStatus?.sermonModel.trained ? "Ready" : "Not Trained"}
                    </span>
                  </div>
                  <div className="flex items-center gap-1">
                    {modelStatus?.tripModel.trained ? (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    ) : (
                      <XCircle className="h-4 w-4 text-red-500" />
                    )}
                    <span className="text-sm text-gray-600">
                      Trip Model: {modelStatus?.tripModel.trained ? "Ready" : "Not Trained"}
                    </span>
                  </div>
                </div>
              </div>
            </div>
            <button
              onClick={handleRetrain}
              disabled={retraining}
              className="flex items-center gap-2 rounded-lg bg-purple-600 px-4 py-2 text-white hover:bg-purple-700 disabled:opacity-50"
            >
              <RefreshCw className={`h-4 w-4 ${retraining ? "animate-spin" : ""}`} />
              {retraining ? "Retraining..." : "Retrain Models"}
            </button>
          </div>
        </div>

        {/* Error Display */}
        {(sermonForecast?.error || tripForecast?.error) && (
          <div className="rounded-lg bg-yellow-50 border border-yellow-200 p-4">
            <p className="text-sm text-yellow-700">
              {sermonForecast?.error || tripForecast?.error}
            </p>
          </div>
        )}

        {/* KPI Summary Cards */}
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          <div className="card text-center">
            <div className="mb-2 flex justify-center">
              <div className="rounded-full bg-purple-100 p-3">
                <Calendar className="h-6 w-6 text-purple-600" />
              </div>
            </div>
            <div className="text-3xl font-bold text-purple-600">
              {sermonForecast?.totalPredicted || 0}
            </div>
            <div className="text-sm text-gray-500">Predicted Sermons (2026)</div>
          </div>

          <div className="card text-center">
            <div className="mb-2 flex justify-center">
              <div className="rounded-full bg-blue-100 p-3">
                <Plane className="h-6 w-6 text-blue-600" />
              </div>
            </div>
            <div className="text-3xl font-bold text-blue-600">
              {tripForecast?.totalPredicted || 0}
            </div>
            <div className="text-sm text-gray-500">Predicted Trips (2026)</div>
          </div>

          <div className="card text-center">
            <div className="mb-2 flex justify-center">
              <div className="rounded-full bg-green-100 p-3">
                <Target className="h-6 w-6 text-green-600" />
              </div>
            </div>
            <div className="text-3xl font-bold text-green-600">
              {Math.round((sermonForecast?.confidence || 0) * 100)}%
            </div>
            <div className="text-sm text-gray-500">Model Confidence</div>
          </div>

          <div className="card text-center">
            <div className="mb-2 flex justify-center">
              <div className="rounded-full bg-yellow-100 p-3">
                <Activity className="h-6 w-6 text-yellow-600" />
              </div>
            </div>
            <div className="text-3xl font-bold text-yellow-600">
              {sermonForecast?.modelMetrics?.samples || 0}
            </div>
            <div className="text-sm text-gray-500">Training Samples</div>
          </div>
        </div>

        {/* Sermon Predictions Section */}
        <div className="space-y-6">
          <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
            <TrendingUp className="h-5 w-5 text-purple-600" />
            2026 Sermon Predictions
          </h2>

          {/* Main Forecast Chart */}
          {sermonForecast && sermonForecast.historical.length > 0 && (
            <ForecastChart
              historical={sermonForecast.historical}
              predictions={sermonForecast.predictions}
              title="Sermon Count Forecast: Historical + 2026 Predictions"
              valueLabel="Sermons"
              showConfidenceInterval={true}
            />
          )}

          {/* Monthly Predictions Bar Chart */}
          <div className="card">
            <h3 className="mb-4 text-lg font-semibold text-gray-900">
              Monthly Breakdown - 2026 Predictions
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={sermonForecast?.predictions || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                <XAxis
                  dataKey="month"
                  tick={{ fill: "#666666", fontSize: 12 }}
                  axisLine={{ stroke: "#E2E8F0" }}
                />
                <YAxis
                  tick={{ fill: "#666666", fontSize: 12 }}
                  axisLine={{ stroke: "#E2E8F0" }}
                />
                <Tooltip
                  content={({ active, payload, label }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      return (
                        <div className="rounded-lg border bg-white p-3 shadow-lg">
                          <p className="font-semibold">{label} 2026</p>
                          <p className="text-sm text-purple-600">
                            Predicted: {data.value} sermons
                          </p>
                          <p className="text-xs text-gray-500">
                            Range: {data.lower} - {data.upper}
                          </p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {(sermonForecast?.predictions || []).map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={MONTH_COLORS[index % 12]}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Predictions Table */}
          <div className="card">
            <h3 className="mb-4 text-lg font-semibold text-gray-900">
              Detailed Sermon Predictions
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b text-left text-sm text-gray-500">
                    <th className="pb-3 font-medium">Month</th>
                    <th className="pb-3 font-medium text-center">Predicted</th>
                    <th className="pb-3 font-medium text-center">Lower Bound</th>
                    <th className="pb-3 font-medium text-center">Upper Bound</th>
                  </tr>
                </thead>
                <tbody>
                  {sermonForecast?.predictions.map((pred, index) => (
                    <tr key={pred.period} className="border-b last:border-0">
                      <td className="py-3 font-medium">{pred.month} 2026</td>
                      <td className="py-3 text-center">
                        <span className="rounded-full bg-purple-100 px-3 py-1 font-semibold text-purple-700">
                          {pred.value}
                        </span>
                      </td>
                      <td className="py-3 text-center text-gray-500">{pred.lower}</td>
                      <td className="py-3 text-center text-gray-500">{pred.upper}</td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="border-t-2 bg-purple-50">
                    <td className="py-3 font-bold text-gray-900">Total 2026</td>
                    <td className="py-3 text-center">
                      <span className="rounded-full bg-purple-600 px-4 py-1 font-bold text-white">
                        {sermonForecast?.totalPredicted || 0}
                      </span>
                    </td>
                    <td className="py-3 text-center text-gray-500">
                      {sermonForecast?.predictions.reduce((sum, p) => sum + p.lower, 0) || 0}
                    </td>
                    <td className="py-3 text-center text-gray-500">
                      {sermonForecast?.predictions.reduce((sum, p) => sum + p.upper, 0) || 0}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        </div>

        {/* Trip Predictions Section */}
        <div className="space-y-6">
          <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
            <Plane className="h-5 w-5 text-blue-600" />
            2026 Trip Predictions
          </h2>

          {/* Trip Monthly Predictions Bar Chart */}
          <div className="card">
            <h3 className="mb-4 text-lg font-semibold text-gray-900">
              Predicted Ministry Trips by Month (2026)
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={tripForecast?.predictions || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                <XAxis
                  dataKey="month"
                  tick={{ fill: "#666666", fontSize: 12 }}
                  axisLine={{ stroke: "#E2E8F0" }}
                />
                <YAxis
                  tick={{ fill: "#666666", fontSize: 12 }}
                  axisLine={{ stroke: "#E2E8F0" }}
                />
                <Tooltip
                  content={({ active, payload, label }) => {
                    if (active && payload && payload.length) {
                      return (
                        <div className="rounded-lg border bg-white p-3 shadow-lg">
                          <p className="font-semibold">{label} 2026</p>
                          <p className="text-sm text-blue-600">
                            Predicted: {payload[0].value} trips
                          </p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Bar dataKey="trips" fill="#3B82F6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Trip Summary Card */}
          <div className="grid gap-6 md:grid-cols-2">
            <div className="card bg-gradient-to-br from-blue-50 to-blue-100">
              <h4 className="text-lg font-semibold text-gray-900">2026 Trip Summary</h4>
              <div className="mt-4 space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">Total Predicted Trips:</span>
                  <span className="font-bold text-blue-600">
                    {tripForecast?.totalPredicted || 0}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Estimated Distance:</span>
                  <span className="font-bold text-blue-600">
                    {(tripForecast?.predictedDistanceKm || 0).toLocaleString()} km
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Avg Trips per Month:</span>
                  <span className="font-bold text-blue-600">
                    {((tripForecast?.totalPredicted || 0) / 12).toFixed(1)}
                  </span>
                </div>
              </div>
            </div>

            {/* Model Performance Card */}
            <div className="card">
              <h4 className="flex items-center gap-2 text-lg font-semibold text-gray-900">
                <BarChart3 className="h-5 w-5 text-purple-600" />
                Model Performance
              </h4>
              <div className="mt-4 space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">Model Type:</span>
                  <span className="font-medium">XGBoost Regressor</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">MAE (Sermons):</span>
                  <span className="font-medium">
                    {sermonForecast?.modelMetrics?.mae?.toFixed(2) || "N/A"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">RMSE (Sermons):</span>
                  <span className="font-medium">
                    {sermonForecast?.modelMetrics?.rmse?.toFixed(2) || "N/A"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Training Data Points:</span>
                  <span className="font-medium">
                    {sermonForecast?.modelMetrics?.samples || 0} months
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Model Info Footer */}
        <div className="rounded-lg bg-gray-50 p-4 text-center text-sm text-gray-600">
          <p>
            Predictions generated using XGBoost machine learning model trained on historical ministry data.
            Features include: month, quarter, lag values (1, 3, 12 months), rolling averages, and trend indicators.
          </p>
        </div>
      </div>
    </div>
  );
}
