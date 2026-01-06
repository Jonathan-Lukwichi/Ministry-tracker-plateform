"use client";

import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { cn } from "@/lib/utils";

interface KPICardProps {
  title: string;
  value: string | number;
  description?: string;
  trend?: number;
  trendLabel?: string;
  icon?: React.ReactNode;
  formatValue?: (value: number) => string;
}

export default function KPICard({
  title,
  value,
  description,
  trend,
  trendLabel = "vs last year",
  icon,
}: KPICardProps) {
  const getTrendIcon = () => {
    if (trend === undefined || trend === null) return null;
    if (trend > 0) return <TrendingUp size={16} />;
    if (trend < 0) return <TrendingDown size={16} />;
    return <Minus size={16} />;
  };

  const getTrendColor = () => {
    if (trend === undefined || trend === null) return "text-gray-500";
    if (trend > 0) return "text-green-600";
    if (trend < 0) return "text-red-600";
    return "text-gray-500";
  };

  const formatTrend = () => {
    if (trend === undefined || trend === null) return null;
    const prefix = trend > 0 ? "+" : "";
    return `${prefix}${trend.toFixed(1)}%`;
  };

  return (
    <div className="card flex items-start justify-between">
      <div className="flex-1">
        <p className="text-sm font-medium text-gray-500">{title}</p>
        <p className="mt-2 text-3xl font-bold text-gray-900">{value}</p>
        {description && (
          <p className="mt-1 text-sm text-gray-500">{description}</p>
        )}
        {trend !== undefined && trend !== null && (
          <div className={cn("mt-2 flex items-center gap-1 text-sm", getTrendColor())}>
            {getTrendIcon()}
            <span className="font-medium">{formatTrend()}</span>
            <span className="text-gray-400">{trendLabel}</span>
          </div>
        )}
      </div>
      {icon && (
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary-50">
          {icon}
        </div>
      )}
    </div>
  );
}
