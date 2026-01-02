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

// Purple gradient colors
const PIE_COLORS = [
  "#4A148C", // Deep purple (busiest)
  "#6A1B9A",
  "#7B1FA2",
  "#8E24AA",
  "#9C27B0",
  "#AB47BC",
  "#BA68C8",
  "#CE93D8",
  "#E1BEE7",
  "#F3E5F5", // Lightest
  "#D4AF37", // Gold for overflow
  "#FFD700",
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
      return (
        <div className="rounded-lg border bg-white p-3 shadow-lg">
          <p className="font-semibold text-gray-900">{item.name}</p>
          <p className="text-sm text-primary">
            {item.value} sermons ({item.payload.percentage || ((item.value / data.reduce((a, b) => a + b.value, 0)) * 100).toFixed(1)}%)
          </p>
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
        fontSize={12}
        fontWeight="bold"
      >
        {name}
      </text>
    );
  };

  // Filter out zero values for cleaner display
  const filteredData = data.filter(d => d.value > 0);

  return (
    <div className="card">
      <h3 className="mb-4 text-lg font-semibold text-gray-900">{title}</h3>
      <ResponsiveContainer width="100%" height={height}>
        <RechartsPieChart>
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
          >
            {filteredData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={PIE_COLORS[index % PIE_COLORS.length]}
                stroke={highlightFirst && index === 0 ? "#FFD700" : "white"}
                strokeWidth={highlightFirst && index === 0 ? 3 : 1}
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
                <span className="text-sm text-gray-700">
                  {value}: {entry.payload.value}
                </span>
              )}
            />
          )}
        </RechartsPieChart>
      </ResponsiveContainer>
    </div>
  );
}
