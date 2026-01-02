"use client";

import { cn } from "@/lib/utils";
import { TrendingUp, TrendingDown } from "lucide-react";

interface KPICardProps {
  label: string;
  value: string | number;
  icon?: React.ReactNode;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  color?: "primary" | "secondary" | "success" | "warning" | "danger";
  className?: string;
}

const colorClasses = {
  primary: "text-accent",
  secondary: "text-secondary",
  success: "text-success",
  warning: "text-warning",
  danger: "text-danger",
};

const bgClasses = {
  primary: "bg-accent/10 text-accent",
  secondary: "bg-secondary/10 text-secondary",
  success: "bg-success/10 text-success",
  warning: "bg-warning/10 text-warning",
  danger: "bg-danger/10 text-danger",
};

export default function KPICard({
  label,
  value,
  icon,
  trend,
  color = "primary",
  className,
}: KPICardProps) {
  return (
    <div className={cn("card flex flex-col items-center text-center", className)}>
      {/* Icon */}
      {icon && (
        <div
          className={cn(
            "mb-3 flex h-12 w-12 items-center justify-center rounded-xl",
            bgClasses[color]
          )}
        >
          {icon}
        </div>
      )}

      {/* Value */}
      <div className={cn("text-3xl font-bold", colorClasses[color])}>{value}</div>

      {/* Label */}
      <div className="mt-1 text-sm uppercase tracking-wide text-slate-500">
        {label}
      </div>

      {/* Trend */}
      {trend && (
        <div
          className={cn(
            "mt-2 flex items-center gap-1 text-sm",
            trend.isPositive ? "text-success" : "text-danger"
          )}
        >
          {trend.isPositive ? (
            <TrendingUp size={14} />
          ) : (
            <TrendingDown size={14} />
          )}
          <span>{trend.value}%</span>
        </div>
      )}
    </div>
  );
}
