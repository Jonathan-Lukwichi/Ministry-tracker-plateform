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

// Vibrant gradient colors for 12 months - Power BI style
const MONTH_COLORS = [
  "#22D3EE", // Jan - Cyan
  "#38BDF8", // Feb - Sky
  "#60A5FA", // Mar - Blue
  "#818CF8", // Apr - Indigo
  "#A78BFA", // May - Violet
  "#C084FC", // Jun - Purple
  "#E879F9", // Jul - Fuchsia
  "#F472B6", // Aug - Pink
  "#FB7185", // Sep - Rose
  "#FB923C", // Oct - Orange
  "#FBBF24", // Nov - Amber
  "#A3E635", // Dec - Lime
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
      const isMax = payload[0].value === maxValue;
      return (
        <div className="rounded-xl border border-slate-700 bg-slate-900/95 p-4 shadow-2xl backdrop-blur-sm">
          <div className="flex items-center gap-2">
            <p className="font-bold text-white text-lg">{label}</p>
            {isMax && (
              <span className="px-2 py-0.5 text-xs font-bold bg-gradient-to-r from-amber-500 to-yellow-400 text-slate-900 rounded-full">
                PEAK
              </span>
            )}
          </div>
          <div className="mt-2 space-y-1">
            <p className="text-sm text-cyan-400">
              <span className="text-slate-400">Total:</span>{" "}
              <span className="font-bold">{payload[0].value} sermons</span>
            </p>
            {showAverage && payload[0].payload.average && (
              <p className="text-sm text-amber-400">
                <span className="text-slate-400">Avg/year:</span>{" "}
                <span className="font-bold">{payload[0].payload.average}</span>
              </p>
            )}
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="relative overflow-hidden rounded-xl border border-slate-700/50 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6 shadow-[0_0_40px_rgba(0,0,0,0.3)]">
      {/* Decorative accents */}
      <div className="absolute top-0 right-0 w-40 h-40 bg-gradient-to-bl from-amber-500/10 to-transparent pointer-events-none" />

      <h3 className="mb-6 text-xl font-bold text-white tracking-tight">{title}</h3>
      <ResponsiveContainer width="100%" height={height}>
        <BarChart
          data={data}
          margin={{ top: 10, right: 30, left: 0, bottom: 5 }}
        >
          <defs>
            {MONTH_COLORS.map((color, index) => (
              <linearGradient
                key={`barGradient-${index}`}
                id={`barGradient-${index}`}
                x1="0"
                y1="0"
                x2="0"
                y2="1"
              >
                <stop offset="0%" stopColor={color} stopOpacity={1} />
                <stop offset="100%" stopColor={color} stopOpacity={0.6} />
              </linearGradient>
            ))}
            <linearGradient id="maxBarGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#FBBF24" stopOpacity={1} />
              <stop offset="50%" stopColor="#F59E0B" stopOpacity={1} />
              <stop offset="100%" stopColor="#D97706" stopOpacity={0.9} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" strokeOpacity={0.5} />
          <XAxis
            dataKey="month"
            tick={{ fill: "#94A3B8", fontSize: 11, fontWeight: 500 }}
            axisLine={{ stroke: "#475569" }}
            tickLine={{ stroke: "#475569" }}
          />
          <YAxis
            tick={{ fill: "#94A3B8", fontSize: 12, fontWeight: 500 }}
            axisLine={{ stroke: "#475569" }}
            tickLine={{ stroke: "#475569" }}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(148, 163, 184, 0.1)" }} />
          <Bar
            dataKey="total"
            radius={[6, 6, 0, 0]}
            animationBegin={0}
            animationDuration={800}
          >
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={
                  entry.total === maxValue
                    ? "url(#maxBarGradient)"
                    : `url(#barGradient-${index % 12})`
                }
                style={{
                  filter:
                    entry.total === maxValue
                      ? "drop-shadow(0 0 12px rgba(251, 191, 36, 0.7))"
                      : "drop-shadow(0 0 4px rgba(0,0,0,0.3))",
                }}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      {/* Legend showing which month is busiest */}
      <div className="mt-4 flex items-center justify-center gap-4">
        <div className="flex items-center gap-2">
          <div
            className="h-4 w-4 rounded"
            style={{
              background: "linear-gradient(to bottom, #FBBF24, #D97706)",
              boxShadow: "0 0 8px rgba(251, 191, 36, 0.6)"
            }}
          />
          <span className="text-sm text-slate-400 font-medium">
            Peak Month
          </span>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-4 w-4 rounded bg-gradient-to-b from-cyan-400 to-cyan-600" />
          <span className="text-sm text-slate-400 font-medium">
            Regular
          </span>
        </div>
      </div>
    </div>
  );
}
