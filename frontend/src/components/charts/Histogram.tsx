"use client";

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

interface DataPoint {
  month: string;
  total: number;
  average?: number;
}

interface HistogramProps {
  data: DataPoint[];
  title: string;
  height?: number;
  showAverage?: boolean;
}

// Purple gradient colors for 12 months
const MONTH_COLORS = [
  "#4A148C", // Jan - darkest
  "#5E1B99",
  "#6A1B9A",
  "#7B1FA2",
  "#8E24AA",
  "#9C27B0",
  "#AB47BC",
  "#BA68C8",
  "#CE93D8",
  "#D4A5DC",
  "#E1BEE7",
  "#EDE7F6", // Dec - lightest
];

export default function Histogram({
  data,
  title,
  height = 300,
  showAverage = false,
}: HistogramProps) {
  // Find max value to highlight it
  const maxValue = Math.max(...data.map((d) => d.total));

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="rounded-lg border bg-white p-3 shadow-lg">
          <p className="font-semibold text-gray-900">{label}</p>
          <p className="text-sm text-primary">
            Total: {payload[0].value} sermons
          </p>
          {showAverage && payload[0].payload.average && (
            <p className="text-xs text-gray-500">
              Avg per year: {payload[0].payload.average}
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
        <BarChart
          data={data}
          margin={{ top: 10, right: 30, left: 0, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
          <XAxis
            dataKey="month"
            tick={{ fill: "#666666", fontSize: 11 }}
            axisLine={{ stroke: "#E2E8F0" }}
          />
          <YAxis
            tick={{ fill: "#666666", fontSize: 12 }}
            axisLine={{ stroke: "#E2E8F0" }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar
            dataKey="total"
            radius={[4, 4, 0, 0]}
            animationBegin={0}
            animationDuration={800}
          >
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.total === maxValue ? "#FFD700" : MONTH_COLORS[index % 12]}
                stroke={entry.total === maxValue ? "#4A148C" : "transparent"}
                strokeWidth={entry.total === maxValue ? 2 : 0}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      {/* Legend showing which month is busiest */}
      <div className="mt-2 text-center text-sm text-gray-500">
        <span className="inline-flex items-center gap-1">
          <span className="h-3 w-3 rounded" style={{ backgroundColor: "#FFD700" }}></span>
          Busiest month highlighted in gold
        </span>
      </div>
    </div>
  );
}
