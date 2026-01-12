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
  variant?: "rainbow" | "cyan" | "magenta" | "lime";
}

// Vibrant Power BI-style colors
const RAINBOW_COLORS = [
  "#22D3EE", // Cyan
  "#F472B6", // Pink
  "#A3E635", // Lime
  "#FBBF24", // Amber
  "#818CF8", // Indigo
  "#FB923C", // Orange
  "#2DD4BF", // Teal
  "#F87171", // Red
];

const VARIANT_COLORS = {
  cyan: "#22D3EE",
  magenta: "#F472B6",
  lime: "#A3E635",
  rainbow: "", // Will use RAINBOW_COLORS array
};

export default function BarChart({
  data,
  title,
  xAxisLabel,
  yAxisLabel,
  height = 300,
  horizontal = false,
  formatValue = (v) => v.toLocaleString(),
  showGradient = true,
  variant = "rainbow",
}: BarChartProps) {
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="rounded-xl border border-slate-700 bg-slate-900/95 p-4 shadow-2xl backdrop-blur-sm">
          <p className="font-bold text-white text-lg">{label}</p>
          <p className="mt-1 text-sm font-medium" style={{ color: payload[0].fill }}>
            <span className="font-bold">{formatValue(payload[0].value)}</span>
          </p>
        </div>
      );
    }
    return null;
  };

  const getBarFill = (index: number): string => {
    if (variant === "rainbow" && showGradient) {
      return `url(#barColorGradient-${index % RAINBOW_COLORS.length})`;
    }
    return `url(#singleColorGradient)`;
  };

  const chartContent = (
    <>
      <defs>
        {/* Rainbow gradients */}
        {RAINBOW_COLORS.map((color, index) => (
          <linearGradient
            key={`barColorGradient-${index}`}
            id={`barColorGradient-${index}`}
            x1="0"
            y1="0"
            x2={horizontal ? "1" : "0"}
            y2={horizontal ? "0" : "1"}
          >
            <stop offset="0%" stopColor={color} stopOpacity={1} />
            <stop offset="100%" stopColor={color} stopOpacity={0.6} />
          </linearGradient>
        ))}
        {/* Single color gradient for non-rainbow variants */}
        <linearGradient
          id="singleColorGradient"
          x1="0"
          y1="0"
          x2={horizontal ? "1" : "0"}
          y2={horizontal ? "0" : "1"}
        >
          <stop offset="0%" stopColor={VARIANT_COLORS[variant] || VARIANT_COLORS.cyan} stopOpacity={1} />
          <stop offset="100%" stopColor={VARIANT_COLORS[variant] || VARIANT_COLORS.cyan} stopOpacity={0.6} />
        </linearGradient>
      </defs>
      <CartesianGrid strokeDasharray="3 3" stroke="#334155" strokeOpacity={0.5} />
    </>
  );

  if (horizontal) {
    return (
      <div className="relative overflow-hidden rounded-xl border border-slate-700/50 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6 shadow-[0_0_40px_rgba(0,0,0,0.3)]">
        {/* Decorative accent */}
        <div className="absolute top-0 left-0 w-32 h-32 bg-gradient-to-br from-cyan-500/10 to-transparent pointer-events-none" />

        <h3 className="mb-6 text-xl font-bold text-white tracking-tight">{title}</h3>
        <ResponsiveContainer width="100%" height={height}>
          <RechartsBarChart
            data={data}
            layout="vertical"
            margin={{ top: 5, right: 30, left: 80, bottom: 5 }}
          >
            {chartContent}
            <XAxis
              type="number"
              tick={{ fill: "#94A3B8", fontSize: 12, fontWeight: 500 }}
              axisLine={{ stroke: "#475569" }}
              tickLine={{ stroke: "#475569" }}
              tickFormatter={formatValue}
            />
            <YAxis
              type="category"
              dataKey="name"
              tick={{ fill: "#94A3B8", fontSize: 12, fontWeight: 500 }}
              axisLine={{ stroke: "#475569" }}
              tickLine={{ stroke: "#475569" }}
              width={70}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(148, 163, 184, 0.1)" }} />
            <Bar dataKey="value" radius={[0, 6, 6, 0]} animationDuration={800}>
              {data.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={getBarFill(index)}
                  style={{ filter: "drop-shadow(0 0 6px rgba(34, 211, 238, 0.4))" }}
                />
              ))}
            </Bar>
          </RechartsBarChart>
        </ResponsiveContainer>
      </div>
    );
  }

  return (
    <div className="relative overflow-hidden rounded-xl border border-slate-700/50 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6 shadow-[0_0_40px_rgba(0,0,0,0.3)]">
      {/* Decorative accent */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-bl from-pink-500/10 to-transparent pointer-events-none" />

      <h3 className="mb-6 text-xl font-bold text-white tracking-tight">{title}</h3>
      <ResponsiveContainer width="100%" height={height}>
        <RechartsBarChart
          data={data}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          {chartContent}
          <XAxis
            dataKey="name"
            tick={{ fill: "#94A3B8", fontSize: 12, fontWeight: 500 }}
            axisLine={{ stroke: "#475569" }}
            tickLine={{ stroke: "#475569" }}
            label={
              xAxisLabel
                ? { value: xAxisLabel, position: "bottom", fill: "#94A3B8", fontWeight: 600 }
                : undefined
            }
          />
          <YAxis
            tick={{ fill: "#94A3B8", fontSize: 12, fontWeight: 500 }}
            axisLine={{ stroke: "#475569" }}
            tickLine={{ stroke: "#475569" }}
            tickFormatter={formatValue}
            label={
              yAxisLabel
                ? {
                    value: yAxisLabel,
                    angle: -90,
                    position: "insideLeft",
                    fill: "#94A3B8",
                    fontWeight: 600,
                  }
                : undefined
            }
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(148, 163, 184, 0.1)" }} />
          <Bar dataKey="value" radius={[6, 6, 0, 0]} animationDuration={800}>
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={getBarFill(index)}
                style={{ filter: "drop-shadow(0 0 6px rgba(34, 211, 238, 0.4))" }}
              />
            ))}
          </Bar>
        </RechartsBarChart>
      </ResponsiveContainer>
    </div>
  );
}
