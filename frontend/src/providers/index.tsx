"use client";

import { ReactNode } from "react";
import { QueryProvider } from "./query-provider";
import { RealtimeProvider } from "./realtime-provider";
import { Toaster } from "@/components/ui/toaster";

interface ProvidersProps {
  children: ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  return (
    <QueryProvider>
      <RealtimeProvider>
        {children}
        <Toaster />
      </RealtimeProvider>
    </QueryProvider>
  );
}
