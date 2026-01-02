"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Video,
  BarChart3,
  MapPin,
  TrendingUp,
  Heart,
  Database,
  Globe,
  Tag,
  RefreshCw,
  Download,
  Church,
  ScanFace,
  Calendar,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface NavItem {
  label: string;
  href: string;
  icon: React.ReactNode;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

const navigation: NavSection[] = [
  {
    title: "Main",
    items: [
      { label: "Dashboard", href: "/", icon: <LayoutDashboard size={20} /> },
      { label: "Sermons", href: "/sermons", icon: <Video size={20} /> },
      { label: "Analytics", href: "/analytics", icon: <BarChart3 size={20} /> },
      { label: "Ministry Map", href: "/map", icon: <MapPin size={20} /> },
      { label: "Forecasting", href: "/forecasting", icon: <TrendingUp size={20} /> },
      { label: "Health Insights", href: "/health", icon: <Heart size={20} /> },
      { label: "Planning", href: "/planning", icon: <Calendar size={20} /> },
    ],
  },
  {
    title: "Settings",
    items: [
      { label: "Face Recognition", href: "/settings/faces", icon: <ScanFace size={20} /> },
      { label: "Data Sources", href: "/settings/sources", icon: <Database size={20} /> },
      { label: "Locations", href: "/settings/locations", icon: <Globe size={20} /> },
      { label: "Themes", href: "/settings/themes", icon: <Tag size={20} /> },
    ],
  },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-64 border-r border-border bg-dark">
      {/* Logo */}
      <div className="flex h-16 items-center gap-3 border-b border-border px-6">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-accent shadow-glow">
          <Church className="h-5 w-5 text-dark" />
        </div>
        <div>
          <h1 className="text-sm font-bold text-white">Ministry Analytics</h1>
          <p className="text-xs text-slate-500">Ramah Full Gospel</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="h-[calc(100vh-8rem)] overflow-y-auto p-4 scrollbar-thin">
        {navigation.map((section) => (
          <div key={section.title} className="mb-6">
            <h2 className="nav-section-title">{section.title}</h2>
            <ul className="space-y-1">
              {section.items.map((item) => {
                const isActive = pathname === item.href;
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      className={cn("nav-link", isActive && "active")}
                    >
                      <span className={cn(
                        "transition-colors",
                        isActive ? "text-accent" : "text-slate-400 group-hover:text-white"
                      )}>
                        {item.icon}
                      </span>
                      <span>{item.label}</span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      {/* Actions */}
      <div className="absolute bottom-0 left-0 right-0 border-t border-border bg-dark p-4">
        <div className="flex gap-2">
          <button className="btn-primary flex-1 gap-2">
            <RefreshCw size={16} />
            <span>Sync</span>
          </button>
          <button className="btn-outline px-3">
            <Download size={16} />
          </button>
        </div>
      </div>
    </aside>
  );
}
