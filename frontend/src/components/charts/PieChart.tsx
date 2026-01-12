"use client";

import {
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

interface DataPoint {
  name: string;
  value: number;
  percentage?: number;
  [key: string]: string | number | undefined;
}

interface PieChartProps {
  data: DataPoint[];
  title: string;
  height?: number;
  showLegend?: boolean;
  donut?: boolean;
  highlightFirst?: boolean;
}

// Vibrant fluorescent Power BI-style colors
const PIE_COLORS = [
  "#22D3EE", // Cyan (main)
  "#F472B6", // Pink/Magenta
  "#A3E635", // Lime green
  "#FBBF24", // Gold/Amber
  "#818CF8", // Indigo/Purple
  "#FB923C", // Orange
  "#2DD4BF", // Teal
  "#F87171", // Red/Coral
  "#C084FC", // Light purple
  "#4ADE80", // Green
  "#60A5FA", // Blue
  "#FACC15", // Yellow
];

export default function PieChart({
  data,
  title,
  height = 300,
  showLegend = true,
  donut = false,
  highlightFirst = true,
}: PieChartProps) {
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const item = payload[0];
      const total = data.reduce((a, b) => a + b.value, 0);
      const percentage = item.payload.percentage || ((item.value / total) * 100).toFixed(1);
      return (
        <div className="rounded-xl border border-slate-700 bg-slate-900/95 p-4 shadow-2xl backdrop-blur-sm">
          <p className="font-bold text-white text-lg">{item.name}</p>
          <div className="mt-2 space-y-1">
            <p className="text-sm" style={{ color: item.payload.fill }}>
              <span className="text-slate-400">Count:</span>{" "}
              <span className="font-bold">{item.value} sermons</span>
            </p>
            <p className="text-sm text-slate-300">
              <span className="text-slate-400">Share:</span>{" "}
              <span className="font-bold">{percentage}%</span>
            </p>
          </div>
        </div>
      );
    }
    return null;
  };

  const renderCustomLabel = ({
    cx,
    cy,
    midAngle,
    innerRadius,
    outerRadius,
    percent,
    name,
    value,
  }: any) => {
    if (percent < 0.05) return null; // Don't show labels for tiny slices

    const RADIAN = Math.PI / 180;
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    return (
      <text
        x={x}
        y={y}
        fill="white"
        textAnchor="middle"
        dominantBaseline="central"
        fontSize={11}
        fontWeight="700"
        style={{ textShadow: "0 2px 4px rgba(0,0,0,0.8)" }}
      >
        {name}
      </text>
    );
  };

  // Filter out zero values for cleaner display
  const filteredData = data.filter((d) => d.value > 0);

  return (
    <div className="relative overflow-hidden rounded-xl border border-slate-700/50 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6 shadow-[0_0_40px_rgba(0,0,0,0.3)]">
      {/* Decorative corner accents */}
      <div className="absolute top-0 left-0 w-24 h-24 bg-gradient-to-br from-pink-500/10 to-transparent pointer-events-none" />
      <div className="absolute bottom-0 right-0 w-24 h-24 bg-gradient-to-tl from-cyan-500/10 to-transparent pointer-events-none" />

      <h3 className="mb-4 text-xl font-bold text-white tracking-tight">{title}</h3>
      <ResponsiveContainer width="100%" height={height}>
        <RechartsPieChart>
          <defs>
            {PIE_COLORS.map((color, index) => (
              <linearGradient
                key={`gradient-${index}`}
                id={`pieGradient-${index}`}
                x1="0"
                y1="0"
                x2="1"
                y2="1"
              >
                <stop offset="0%" stopColor={color} stopOpacity={1} />
                <stop offset="100%" stopColor={color} stopOpacity={0.7} />
              </linearGradient>
            ))}
            <filter id="glow">
              <feGaussianBlur stdDeviation="2" result="coloredBlur" />
              <feMerge>
                <feMergeNode in="coloredBlur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
          <Pie
            data={filteredData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={renderCustomLabel}
            outerRadius={donut ? 100 : 110}
            innerRadius={donut ? 60 : 0}
            fill="#8884d8"
            dataKey="value"
            nameKey="name"
            animationBegin={0}
            animationDuration={800}
            stroke="rgba(15, 23, 42, 0.8)"
            strokeWidth={2}
          >
            {filteredData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={PIE_COLORS[index % PIE_COLORS.length]}
                style={{
                  filter:
                    highlightFirst && index === 0
                      ? "drop-shadow(0 0 12px rgba(34, 211, 238, 0.8))"
                      : "drop-shadow(0 0 4px rgba(0,0,0,0.5))",
                }}
              />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          {showLegend && (
            <Legend
              layout="vertical"
              align="right"
              verticalAlign="middle"
              formatter={(value, entry: any) => (
                <span className="text-sm text-slate-300 font-medium">
                  {value}:{" "}
                  <span className="text-white font-bold">{entry.payload.value}</span>
                </span>
              )}
              wrapperStyle={{
                paddingLeft: 20,
              }}
            />
          )}
        </RechartsPieChart>
      </ResponsiveContainer>
    </div>
  );
}
