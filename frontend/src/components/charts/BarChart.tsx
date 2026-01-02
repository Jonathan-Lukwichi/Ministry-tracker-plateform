"use client";

import {
  BarChart as RechartsBarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

interface DataPoint {
  name: string;
  value: number;
}

interface BarChartProps {
  data: DataPoint[];
  title: string;
  xAxisLabel?: string;
  yAxisLabel?: string;
  height?: number;
  horizontal?: boolean;
  formatValue?: (value: number) => string;
  showGradient?: boolean;
}

// Purple gradient colors
const COLORS = [
  "#4A148C", // Deep purple
  "#6A1B9A",
  "#7B1FA2",
  "#8E24AA",
  "#9C27B0",
  "#AB47BC",
  "#BA68C8",
  "#CE93D8",
];

export default function BarChart({
  data,
  title,
  xAxisLabel,
  yAxisLabel,
  height = 300,
  horizontal = false,
  formatValue = (v) => v.toLocaleString(),
  showGradient = true,
}: BarChartProps) {
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="rounded-lg border bg-white p-3 shadow-lg">
          <p className="font-semibold text-gray-900">{label}</p>
          <p className="text-sm text-primary">
            {formatValue(payload[0].value)}
          </p>
        </div>
      );
    }
    return null;
  };

  if (horizontal) {
    return (
      <div className="card">
        <h3 className="mb-4 text-lg font-semibold text-gray-900">{title}</h3>
        <ResponsiveContainer width="100%" height={height}>
          <RechartsBarChart
            data={data}
            layout="vertical"
            margin={{ top: 5, right: 30, left: 80, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
            <XAxis
              type="number"
              tick={{ fill: "#666666", fontSize: 12 }}
              axisLine={{ stroke: "#E2E8F0" }}
              tickFormatter={formatValue}
            />
            <YAxis
              type="category"
              dataKey="name"
              tick={{ fill: "#666666", fontSize: 12 }}
              axisLine={{ stroke: "#E2E8F0" }}
              width={70}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="value" radius={[0, 4, 4, 0]}>
              {data.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={showGradient ? COLORS[index % COLORS.length] : "#4A148C"}
                />
              ))}
            </Bar>
          </RechartsBarChart>
        </ResponsiveContainer>
      </div>
    );
  }

  return (
    <div className="card">
      <h3 className="mb-4 text-lg font-semibold text-gray-900">{title}</h3>
      <ResponsiveContainer width="100%" height={height}>
        <RechartsBarChart
          data={data}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
          <XAxis
            dataKey="name"
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
          <Bar dataKey="value" radius={[4, 4, 0, 0]}>
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={showGradient ? COLORS[index % COLORS.length] : "#4A148C"}
              />
            ))}
          </Bar>
        </RechartsBarChart>
      </ResponsiveContainer>
    </div>
  );
}
