"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
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
  ChevronDown,
  Plus,
  User,
  Check,
} from "lucide-react";
import { cn } from "@/lib/utils";
import api from "@/lib/api";
import { Preacher } from "@/lib/types";

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
      { label: "Dashboard", href: "/dashboard", icon: <LayoutDashboard size={20} /> },
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
  const router = useRouter();
  const searchParams = useSearchParams();
  const [preachers, setPreachers] = useState<Preacher[]>([]);
  const [selectedPreacher, setSelectedPreacher] = useState<Preacher | null>(null);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  // Get current preacher ID from URL or localStorage
  const currentPreacherId = searchParams.get("preacher")
    ? parseInt(searchParams.get("preacher")!)
    : typeof window !== "undefined"
      ? parseInt(localStorage.getItem("selectedPreacherId") || "1")
      : 1;

  useEffect(() => {
    async function fetchPreachers() {
      try {
        const response = await api.getPreachers();
        setPreachers(response.preachers);

        // Find and set current preacher
        const current = response.preachers.find(p => p.id === currentPreacherId);
        if (current) {
          setSelectedPreacher(current);
        } else if (response.preachers.length > 0) {
          setSelectedPreacher(response.preachers[0]);
        }
      } catch (error) {
        console.error("Failed to fetch preachers:", error);
      } finally {
        setLoading(false);
      }
    }

    fetchPreachers();
  }, [currentPreacherId]);

  const handlePreacherSelect = (preacher: Preacher) => {
    setSelectedPreacher(preacher);
    setIsDropdownOpen(false);

    // Store in localStorage
    if (typeof window !== "undefined") {
      localStorage.setItem("selectedPreacherId", preacher.id.toString());
    }

    // Navigate to dashboard with preacher context
    router.push(`/dashboard?preacher=${preacher.id}`);
  };

  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-64 border-r border-border bg-dark">
      {/* Logo */}
      <div className="flex h-16 items-center gap-3 border-b border-border px-6">
        <Link href="/" className="flex items-center gap-3 group">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-accent to-purple-600 shadow-lg shadow-accent/25 transition-shadow group-hover:shadow-accent/40">
            <Church className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-white">Ministry Analytics</h1>
            <p className="text-xs text-slate-500">Multi-Preacher Platform</p>
          </div>
        </Link>
      </div>

      {/* Preacher Selector */}
      <div className="border-b border-border p-4">
        <div className="relative">
          <button
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className="flex w-full items-center justify-between rounded-lg border border-border bg-[#1a2942] p-3 transition-all hover:border-accent/50 hover:bg-[#1e3350]"
          >
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-accent/20">
                <User className="h-4 w-4 text-accent" />
              </div>
              <div className="text-left">
                {loading ? (
                  <div className="h-4 w-24 animate-pulse rounded bg-slate-700" />
                ) : selectedPreacher ? (
                  <>
                    <p className="text-sm font-medium text-white truncate max-w-[120px]">
                      {selectedPreacher.title ? `${selectedPreacher.title} ` : ""}
                      {selectedPreacher.name.split(" ").slice(-1)[0]}
                    </p>
                    <p className="text-xs text-slate-500">
                      {selectedPreacher.video_count || 0} videos
                    </p>
                  </>
                ) : (
                  <p className="text-sm text-slate-400">Select Preacher</p>
                )}
              </div>
            </div>
            <ChevronDown
              className={cn(
                "h-4 w-4 text-slate-400 transition-transform",
                isDropdownOpen && "rotate-180"
              )}
            />
          </button>

          {/* Dropdown */}
          {isDropdownOpen && (
            <div className="absolute left-0 right-0 top-full z-50 mt-2 rounded-lg border border-border bg-dark shadow-xl">
              <div className="max-h-64 overflow-y-auto py-1">
                {preachers.map((preacher) => (
                  <button
                    key={preacher.id}
                    onClick={() => handlePreacherSelect(preacher)}
                    className={cn(
                      "flex w-full items-center gap-3 px-3 py-2.5 text-left transition-colors hover:bg-[#1a2942]",
                      selectedPreacher?.id === preacher.id && "bg-accent/10"
                    )}
                  >
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-accent/20">
                      <User className="h-4 w-4 text-accent" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-white truncate">
                        {preacher.title ? `${preacher.title} ` : ""}
                        {preacher.name}
                      </p>
                      <p className="text-xs text-slate-500">
                        {preacher.video_count || 0} videos
                      </p>
                    </div>
                    {selectedPreacher?.id === preacher.id && (
                      <Check className="h-4 w-4 text-accent flex-shrink-0" />
                    )}
                  </button>
                ))}
              </div>

              {/* Add New Preacher */}
              <div className="border-t border-border p-2">
                <Link
                  href="/setup"
                  onClick={() => setIsDropdownOpen(false)}
                  className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left transition-colors hover:bg-accent/10"
                >
                  <div className="flex h-8 w-8 items-center justify-center rounded-full border border-dashed border-accent/50">
                    <Plus className="h-4 w-4 text-accent" />
                  </div>
                  <span className="text-sm font-medium text-accent">Add New Preacher</span>
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Navigation */}
      <nav className="h-[calc(100vh-12rem)] overflow-y-auto p-4 scrollbar-thin">
        {navigation.map((section) => (
          <div key={section.title} className="mb-6">
            <h2 className="nav-section-title">{section.title}</h2>
            <ul className="space-y-1">
              {section.items.map((item) => {
                const isActive = pathname === item.href ||
                  (item.href === "/dashboard" && pathname === "/dashboard");
                // Add preacher query param to navigation links
                const href = selectedPreacher
                  ? `${item.href}?preacher=${selectedPreacher.id}`
                  : item.href;
                return (
                  <li key={item.href}>
                    <Link
                      href={href}
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
