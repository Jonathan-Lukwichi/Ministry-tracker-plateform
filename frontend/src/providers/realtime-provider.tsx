"use client";

import { createContext, useContext, useEffect, useState, ReactNode, useCallback } from "react";

interface RealtimeEvent {
  type: string;
  data: unknown;
  timestamp: Date;
}

interface RealtimeContextType {
  isConnected: boolean;
  lastEvent: RealtimeEvent | null;
  subscribe: (eventType: string, callback: (data: unknown) => void) => () => void;
  reconnect: () => void;
}

const RealtimeContext = createContext<RealtimeContextType | null>(null);

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function RealtimeProvider({ children }: { children: ReactNode }) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState<RealtimeEvent | null>(null);
  const [eventSource, setEventSource] = useState<EventSource | null>(null);
  const [subscribers, setSubscribers] = useState<Map<string, Set<(data: unknown) => void>>>(new Map());

  const connect = useCallback(() => {
    // Close existing connection
    if (eventSource) {
      eventSource.close();
    }

    try {
      const sse = new EventSource(`${API_URL}/api/events/stream`);

      sse.onopen = () => {
        setIsConnected(true);
        console.log("SSE Connected");
      };

      sse.onerror = () => {
        setIsConnected(false);
        console.log("SSE Disconnected, attempting reconnect...");
        // Auto-reconnect after 5 seconds
        setTimeout(connect, 5000);
      };

      sse.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          const realtimeEvent: RealtimeEvent = {
            type: data.type || "message",
            data: data.payload || data,
            timestamp: new Date(),
          };
          setLastEvent(realtimeEvent);

          // Notify subscribers
          const typeSubscribers = subscribers.get(realtimeEvent.type);
          if (typeSubscribers) {
            typeSubscribers.forEach((callback) => callback(realtimeEvent.data));
          }

          // Also notify "all" subscribers
          const allSubscribers = subscribers.get("*");
          if (allSubscribers) {
            allSubscribers.forEach((callback) => callback(realtimeEvent));
          }
        } catch (e) {
          console.error("Error parsing SSE message:", e);
        }
      };

      // Listen for specific event types
      sse.addEventListener("sync_complete", (event) => {
        const data = JSON.parse(event.data);
        const typeSubscribers = subscribers.get("sync_complete");
        if (typeSubscribers) {
          typeSubscribers.forEach((callback) => callback(data));
        }
      });

      sse.addEventListener("video_added", (event) => {
        const data = JSON.parse(event.data);
        const typeSubscribers = subscribers.get("video_added");
        if (typeSubscribers) {
          typeSubscribers.forEach((callback) => callback(data));
        }
      });

      sse.addEventListener("stats_updated", (event) => {
        const data = JSON.parse(event.data);
        const typeSubscribers = subscribers.get("stats_updated");
        if (typeSubscribers) {
          typeSubscribers.forEach((callback) => callback(data));
        }
      });

      setEventSource(sse);
    } catch (error) {
      console.error("Failed to connect SSE:", error);
      setIsConnected(false);
    }
  }, [eventSource, subscribers]);

  const subscribe = useCallback((eventType: string, callback: (data: unknown) => void) => {
    setSubscribers((prev) => {
      const newMap = new Map(prev);
      const typeSubscribers = newMap.get(eventType) || new Set();
      typeSubscribers.add(callback);
      newMap.set(eventType, typeSubscribers);
      return newMap;
    });

    // Return unsubscribe function
    return () => {
      setSubscribers((prev) => {
        const newMap = new Map(prev);
        const typeSubscribers = newMap.get(eventType);
        if (typeSubscribers) {
          typeSubscribers.delete(callback);
          if (typeSubscribers.size === 0) {
            newMap.delete(eventType);
          }
        }
        return newMap;
      });
    };
  }, []);

  const reconnect = useCallback(() => {
    connect();
  }, [connect]);

  useEffect(() => {
    connect();

    return () => {
      if (eventSource) {
        eventSource.close();
      }
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <RealtimeContext.Provider value={{ isConnected, lastEvent, subscribe, reconnect }}>
      {children}
    </RealtimeContext.Provider>
  );
}

export function useRealtime() {
  const context = useContext(RealtimeContext);
  if (!context) {
    throw new Error("useRealtime must be used within a RealtimeProvider");
  }
  return context;
}

// Hook for subscribing to specific event types
export function useRealtimeEvent<T = unknown>(
  eventType: string,
  callback: (data: T) => void
) {
  const { subscribe } = useRealtime();

  useEffect(() => {
    const unsubscribe = subscribe(eventType, callback as (data: unknown) => void);
    return unsubscribe;
  }, [eventType, callback, subscribe]);
}
