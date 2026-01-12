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
  Area,
  ComposedChart,
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
  variant?: "cyan" | "magenta" | "lime" | "gold";
}

const VARIANTS = {
  cyan: {
    stroke: "#22D3EE",
    fill: "url(#cyanGradient)",
    glow: "drop-shadow(0 0 8px rgba(34, 211, 238, 0.6))",
    dot: "#06B6D4",
    activeDot: "#67E8F9",
  },
  magenta: {
    stroke: "#F472B6",
    fill: "url(#magentaGradient)",
    glow: "drop-shadow(0 0 8px rgba(244, 114, 182, 0.6))",
    dot: "#EC4899",
    activeDot: "#F9A8D4",
  },
  lime: {
    stroke: "#A3E635",
    fill: "url(#limeGradient)",
    glow: "drop-shadow(0 0 8px rgba(163, 230, 53, 0.6))",
    dot: "#84CC16",
    activeDot: "#BEF264",
  },
  gold: {
    stroke: "#FBBF24",
    fill: "url(#goldGradient)",
    glow: "drop-shadow(0 0 8px rgba(251, 191, 36, 0.6))",
    dot: "#F59E0B",
    activeDot: "#FCD34D",
  },
};

export default function LineChart({
  data,
  title,
  xAxisLabel,
  yAxisLabel,
  valueLabel = "Value",
  showAverage = false,
  height = 300,
  formatValue = (v) => v.toLocaleString(),
  variant = "cyan",
}: LineChartProps) {
  const style = VARIANTS[variant];

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="rounded-xl border border-slate-700 bg-slate-900/95 p-4 shadow-2xl backdrop-blur-sm">
          <p className="font-bold text-white text-lg mb-2">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p
              key={index}
              className="text-sm font-medium"
              style={{ color: entry.color }}
            >
              {entry.name}: <span className="font-bold">{formatValue(entry.value)}</span>
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="relative overflow-hidden rounded-xl border border-slate-700/50 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6 shadow-[0_0_40px_rgba(0,0,0,0.3)]">
      {/* Decorative corner accent */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-bl from-cyan-500/10 to-transparent pointer-events-none" />

      <h3 className="mb-6 text-xl font-bold text-white tracking-tight">{title}</h3>
      <ResponsiveContainer width="100%" height={height}>
        <ComposedChart
          data={data}
          margin={{ top: 10, right: 30, left: 10, bottom: 10 }}
        >
          <defs>
            <linearGradient id="cyanGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#22D3EE" stopOpacity={0.4} />
              <stop offset="100%" stopColor="#22D3EE" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="magentaGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#F472B6" stopOpacity={0.4} />
              <stop offset="100%" stopColor="#F472B6" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="limeGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#A3E635" stopOpacity={0.4} />
              <stop offset="100%" stopColor="#A3E635" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="goldGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#FBBF24" stopOpacity={0.4} />
              <stop offset="100%" stopColor="#FBBF24" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" strokeOpacity={0.5} />
          <XAxis
            dataKey="period"
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
          <Tooltip content={<CustomTooltip />} />
          {showAverage && (
            <Legend
              wrapperStyle={{ paddingTop: 20 }}
              formatter={(value) => <span className="text-slate-300 font-medium">{value}</span>}
            />
          )}
          <Area
            type="monotone"
            dataKey="value"
            fill={style.fill}
            stroke="transparent"
          />
          <Line
            type="monotone"
            dataKey="value"
            name={valueLabel}
            stroke={style.stroke}
            strokeWidth={3}
            dot={{ fill: style.dot, strokeWidth: 0, r: 5 }}
            activeDot={{ r: 8, fill: style.activeDot, stroke: style.stroke, strokeWidth: 2 }}
            style={{ filter: style.glow }}
          />
          {showAverage && (
            <Line
              type="monotone"
              dataKey="average"
              name="Average"
              stroke="#FBBF24"
              strokeWidth={2}
              strokeDasharray="8 4"
              dot={false}
              style={{ filter: "drop-shadow(0 0 4px rgba(251, 191, 36, 0.5))" }}
            />
          )}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
