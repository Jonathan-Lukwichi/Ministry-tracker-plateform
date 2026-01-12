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
  variant?: "default" | "cyan" | "magenta" | "gold" | "lime";
}

const VARIANTS = {
  default: {
    bg: "bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900",
    border: "border-purple-500/30",
    glow: "shadow-[0_0_30px_rgba(139,92,246,0.3)]",
    accent: "from-purple-500 to-violet-600",
    iconBg: "bg-purple-500/20",
    iconColor: "text-purple-400",
  },
  cyan: {
    bg: "bg-gradient-to-br from-slate-900 via-cyan-900 to-slate-900",
    border: "border-cyan-500/30",
    glow: "shadow-[0_0_30px_rgba(6,182,212,0.3)]",
    accent: "from-cyan-400 to-teal-500",
    iconBg: "bg-cyan-500/20",
    iconColor: "text-cyan-400",
  },
  magenta: {
    bg: "bg-gradient-to-br from-slate-900 via-pink-900 to-slate-900",
    border: "border-pink-500/30",
    glow: "shadow-[0_0_30px_rgba(236,72,153,0.3)]",
    accent: "from-pink-500 to-rose-600",
    iconBg: "bg-pink-500/20",
    iconColor: "text-pink-400",
  },
  gold: {
    bg: "bg-gradient-to-br from-slate-900 via-amber-900 to-slate-900",
    border: "border-amber-500/30",
    glow: "shadow-[0_0_30px_rgba(245,158,11,0.3)]",
    accent: "from-amber-400 to-yellow-500",
    iconBg: "bg-amber-500/20",
    iconColor: "text-amber-400",
  },
  lime: {
    bg: "bg-gradient-to-br from-slate-900 via-lime-900 to-slate-900",
    border: "border-lime-500/30",
    glow: "shadow-[0_0_30px_rgba(132,204,22,0.3)]",
    accent: "from-lime-400 to-green-500",
    iconBg: "bg-lime-500/20",
    iconColor: "text-lime-400",
  },
};

export default function KPICard({
  title,
  value,
  description,
  trend,
  trendLabel = "vs last year",
  icon,
  variant = "default",
}: KPICardProps) {
  const style = VARIANTS[variant];

  const getTrendIcon = () => {
    if (trend === undefined || trend === null) return null;
    if (trend > 0) return <TrendingUp size={16} />;
    if (trend < 0) return <TrendingDown size={16} />;
    return <Minus size={16} />;
  };

  const getTrendColor = () => {
    if (trend === undefined || trend === null) return "text-slate-400";
    if (trend > 0) return "text-emerald-400";
    if (trend < 0) return "text-rose-400";
    return "text-slate-400";
  };

  const formatTrend = () => {
    if (trend === undefined || trend === null) return null;
    const prefix = trend > 0 ? "+" : "";
    return `${prefix}${trend.toFixed(1)}%`;
  };

  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-xl border p-6 transition-all duration-300 hover:scale-[1.02]",
        style.bg,
        style.border,
        style.glow
      )}
    >
      {/* Decorative gradient line at top */}
      <div
        className={cn(
          "absolute top-0 left-0 right-0 h-1 bg-gradient-to-r",
          style.accent
        )}
      />

      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-slate-400 uppercase tracking-wider">
            {title}
          </p>
          <p className={cn(
            "mt-3 text-4xl font-bold bg-gradient-to-r bg-clip-text text-transparent",
            style.accent
          )}>
            {value}
          </p>
          {description && (
            <p className="mt-2 text-sm text-slate-400">{description}</p>
          )}
          {trend !== undefined && trend !== null && (
            <div
              className={cn(
                "mt-3 flex items-center gap-2 text-sm font-medium",
                getTrendColor()
              )}
            >
              <span className="flex items-center gap-1 px-2 py-1 rounded-full bg-slate-800/50">
                {getTrendIcon()}
                <span>{formatTrend()}</span>
              </span>
              <span className="text-slate-500">{trendLabel}</span>
            </div>
          )}
        </div>
        {icon && (
          <div
            className={cn(
              "flex h-14 w-14 items-center justify-center rounded-xl",
              style.iconBg
            )}
          >
            <div className={style.iconColor}>{icon}</div>
          </div>
        )}
      </div>
    </div>
  );
}
