"use client";

import { usePathname } from "next/navigation";
import Sidebar from "./Sidebar";

// Pages that should NOT show the sidebar
const noSidebarPages = ["/", "/setup"];

export default function ConditionalLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  // Check if current page should show sidebar
  const showSidebar = !noSidebarPages.includes(pathname);

  return (
    <div className="flex min-h-screen">
      {/* Sidebar - only show on dashboard pages */}
      {showSidebar && <Sidebar />}

      {/* Main Content */}
      <main className={showSidebar ? "ml-64 flex-1" : "flex-1"}>
        {children}
      </main>
    </div>
  );
}
