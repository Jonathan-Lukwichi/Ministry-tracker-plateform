"use client";

import {
  LineChart as RechartsLineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

interface DataPoint {
  period: string;
  value: number;
  average?: number;
}

interface LineChartProps {
  data: DataPoint[];
  title: string;
  xAxisLabel?: string;
  yAxisLabel?: string;
  valueLabel?: string;
  showAverage?: boolean;
  height?: number;
  formatValue?: (value: number) => string;
}

export default function LineChart({
  data,
  title,
  xAxisLabel,
  yAxisLabel,
  valueLabel = "Value",
  showAverage = false,
  height = 300,
  formatValue = (v) => v.toLocaleString(),
}: LineChartProps) {
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="rounded-lg border bg-white p-3 shadow-lg">
          <p className="font-semibold text-gray-900">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} style={{ color: entry.color }} className="text-sm">
              {entry.name}: {formatValue(entry.value)}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="card">
      <h3 className="mb-4 text-lg font-semibold text-gray-900">{title}</h3>
      <ResponsiveContainer width="100%" height={height}>
        <RechartsLineChart
          data={data}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
          <XAxis
            dataKey="period"
            tick={{ fill: "#666666", fontSize: 12 }}
            axisLine={{ stroke: "#E2E8F0" }}
            label={
              xAxisLabel
                ? { value: xAxisLabel, position: "bottom", fill: "#666666" }
                : undefined
            }
          />
          <YAxis
            tick={{ fill: "#666666", fontSize: 12 }}
            axisLine={{ stroke: "#E2E8F0" }}
            tickFormatter={formatValue}
            label={
              yAxisLabel
                ? {
                    value: yAxisLabel,
                    angle: -90,
                    position: "insideLeft",
                    fill: "#666666",
                  }
                : undefined
            }
          />
          <Tooltip content={<CustomTooltip />} />
          {showAverage && <Legend />}
          <Line
            type="monotone"
            dataKey="value"
            name={valueLabel}
            stroke="#4A148C"
            strokeWidth={2}
            dot={{ fill: "#4A148C", strokeWidth: 2, r: 4 }}
            activeDot={{ r: 6, fill: "#7B1FA2" }}
          />
          {showAverage && (
            <Line
              type="monotone"
              dataKey="average"
              name="Average"
              stroke="#FFD700"
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={false}
            />
          )}
        </RechartsLineChart>
      </ResponsiveContainer>
    </div>
  );
}
