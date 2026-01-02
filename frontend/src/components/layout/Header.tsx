"use client";

import { Search, Bell, User, CheckCircle, AlertCircle } from "lucide-react";
import { useState } from "react";

interface HeaderProps {
  title: string;
  subtitle?: string;
}

export default function Header({ title, subtitle }: HeaderProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [syncStatus] = useState<"idle" | "syncing" | "success" | "error">("idle");

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-border bg-dark/95 backdrop-blur-sm px-6">
      {/* Page Title */}
      <div>
        <h1 className="text-xl font-bold text-white">{title}</h1>
        {subtitle && <p className="text-sm text-slate-500">{subtitle}</p>}
      </div>

      {/* Search & Actions */}
      <div className="flex items-center gap-4">
        {/* Search Bar */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            placeholder="Search sermons..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input w-64 pl-10"
          />
        </div>

        {/* Sync Status */}
        <div className="flex items-center gap-2 text-sm">
          {syncStatus === "idle" && (
            <span className="flex items-center gap-1 text-slate-400">
              <CheckCircle size={16} className="text-success" />
              Synced
            </span>
          )}
          {syncStatus === "syncing" && (
            <span className="flex items-center gap-1 text-accent">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-accent border-t-transparent" />
              Syncing...
            </span>
          )}
          {syncStatus === "error" && (
            <span className="flex items-center gap-1 text-danger">
              <AlertCircle size={16} />
              Sync failed
            </span>
          )}
        </div>

        {/* Notifications */}
        <button className="btn-ghost relative p-2">
          <Bell size={20} className="text-slate-400" />
          <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-marker" />
        </button>

        {/* Profile */}
        <button className="flex items-center gap-2 rounded-lg p-2 hover:bg-[#1a2942] transition-colors">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-accent shadow-glow">
            <User size={16} className="text-dark" />
          </div>
        </button>
      </div>
    </header>
  );
}
