"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Area,
  ComposedChart,
} from "recharts";

interface HistoricalPoint {
  period: string;
  value: number;
}

interface PredictionPoint {
  period: string;
  month: string;
  value: number;
  lower: number;
  upper: number;
}

interface ForecastChartProps {
  historical: HistoricalPoint[];
  predictions: PredictionPoint[];
  title: string;
  height?: number;
  valueLabel?: string;
  showConfidenceInterval?: boolean;
}

export default function ForecastChart({
  historical,
  predictions,
  title,
  height = 350,
  valueLabel = "Sermons",
  showConfidenceInterval = true,
}: ForecastChartProps) {
  // Combine historical and prediction data
  const combinedData = [
    ...historical.slice(-24).map((h) => ({
      period: h.period,
      actual: h.value,
      predicted: null as number | null,
      lower: null as number | null,
      upper: null as number | null,
      isPrediction: false,
    })),
    ...predictions.map((p) => ({
      period: p.period,
      actual: null as number | null,
      predicted: p.value,
      lower: p.lower,
      upper: p.upper,
      isPrediction: true,
    })),
  ];

  // Find the dividing point between historical and predicted
  const divideIndex = historical.length > 24 ? 24 : historical.length;

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      const isPrediction = data.isPrediction;

      return (
        <div className="rounded-lg border bg-white p-3 shadow-lg">
          <p className="font-semibold text-gray-900">{label}</p>
          {isPrediction ? (
            <>
              <p className="text-sm text-purple-600">
                Predicted: {data.predicted} {valueLabel.toLowerCase()}
              </p>
              {showConfidenceInterval && (
                <p className="text-xs text-gray-500">
                  Range: {data.lower} - {data.upper}
                </p>
              )}
            </>
          ) : (
            <p className="text-sm text-blue-600">
              Actual: {data.actual} {valueLabel.toLowerCase()}
            </p>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="card">
      <h3 className="mb-4 text-lg font-semibold text-gray-900">{title}</h3>
      <ResponsiveContainer width="100%" height={height}>
        <ComposedChart
          data={combinedData}
          margin={{ top: 10, right: 30, left: 0, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
          <XAxis
            dataKey="period"
            tick={{ fill: "#666666", fontSize: 10 }}
            axisLine={{ stroke: "#E2E8F0" }}
            angle={-45}
            textAnchor="end"
            height={60}
            interval={Math.floor(combinedData.length / 12)}
          />
          <YAxis
            tick={{ fill: "#666666", fontSize: 12 }}
            axisLine={{ stroke: "#E2E8F0" }}
          />
          <Tooltip content={<CustomTooltip />} />

          {/* Reference line at 2026 start */}
          <ReferenceLine
            x={predictions[0]?.period}
            stroke="#FFD700"
            strokeWidth={2}
            strokeDasharray="5 5"
            label={{
              value: "2026 Predictions",
              position: "top",
              fill: "#B8860B",
              fontSize: 12,
            }}
          />

          {/* Confidence interval area for predictions */}
          {showConfidenceInterval && (
            <Area
              type="monotone"
              dataKey="upper"
              stroke="none"
              fill="#E1BEE7"
              fillOpacity={0.3}
              connectNulls={false}
            />
          )}

          {/* Historical actual line */}
          <Line
            type="monotone"
            dataKey="actual"
            stroke="#3B82F6"
            strokeWidth={2}
            dot={{ fill: "#3B82F6", strokeWidth: 0, r: 3 }}
            activeDot={{ r: 5, fill: "#3B82F6" }}
            connectNulls={false}
            name="Historical"
          />

          {/* Predicted line */}
          <Line
            type="monotone"
            dataKey="predicted"
            stroke="#4A148C"
            strokeWidth={3}
            strokeDasharray="8 4"
            dot={{ fill: "#4A148C", strokeWidth: 0, r: 4 }}
            activeDot={{ r: 6, fill: "#4A148C" }}
            connectNulls={false}
            name="Predicted"
          />
        </ComposedChart>
      </ResponsiveContainer>

      {/* Legend */}
      <div className="mt-4 flex justify-center gap-6">
        <div className="flex items-center gap-2">
          <div className="h-0.5 w-6 bg-blue-500"></div>
          <span className="text-sm text-gray-600">Historical</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-0.5 w-6 border-t-2 border-dashed border-purple-900"></div>
          <span className="text-sm text-gray-600">2026 Prediction</span>
        </div>
        {showConfidenceInterval && (
          <div className="flex items-center gap-2">
            <div className="h-4 w-6 bg-purple-200 opacity-50"></div>
            <span className="text-sm text-gray-600">Confidence Range</span>
          </div>
        )}
      </div>
    </div>
  );
}
