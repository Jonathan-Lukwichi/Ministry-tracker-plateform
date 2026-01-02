"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";

// Location data type
interface MapLocation {
  name: string;
  country: string;
  lat: number;
  lng: number;
  sermonCount: number;
  isHomeBase: boolean;
}

// Journey data type
interface Journey {
  date: string;
  from: string;
  to: string;
  fromCoords: [number, number];
  toCoords: [number, number];
  distanceKm: number;
  estimatedHours: number;
}

interface MinistryMapProps {
  locations: MapLocation[];
  journeys: Journey[];
  showRoutes?: boolean;
  selectedYear?: number | null;
  height?: string;
}

// Dynamically import Leaflet components (no SSR)
const MapContainer = dynamic(
  () => import("react-leaflet").then((mod) => mod.MapContainer),
  { ssr: false }
);

const TileLayer = dynamic(
  () => import("react-leaflet").then((mod) => mod.TileLayer),
  { ssr: false }
);

const CircleMarker = dynamic(
  () => import("react-leaflet").then((mod) => mod.CircleMarker),
  { ssr: false }
);

const Popup = dynamic(
  () => import("react-leaflet").then((mod) => mod.Popup),
  { ssr: false }
);

const Polyline = dynamic(
  () => import("react-leaflet").then((mod) => mod.Polyline),
  { ssr: false }
);

export default function MinistryMap({
  locations,
  journeys,
  showRoutes = true,
  selectedYear,
  height = "100%",
}: MinistryMapProps) {
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  // Center map on Africa (roughly between SA and Europe)
  const mapCenter: [number, number] = [5, 15];
  const mapZoom = 2.5;

  // Calculate marker size based on sermon count - smaller dots like in reference
  const getMarkerSize = (count: number, isHome: boolean): number => {
    if (isHome) return 8;
    if (count === 0) return 3;
    if (count < 5) return 4;
    if (count < 10) return 5;
    if (count < 30) return 6;
    if (count < 50) return 7;
    return 8;
  };

  // Get marker color - pink dots like in reference image
  const getMarkerColor = (location: MapLocation): string => {
    if (location.isHomeBase) return "#00d4ff"; // Cyan for home base
    return "#ff3e7f"; // Pink/magenta for other locations
  };

  if (!isMounted) {
    return (
      <div
        className="flex items-center justify-center bg-dark"
        style={{ height }}
      >
        <div className="text-slate-500">Loading map...</div>
      </div>
    );
  }

  return (
    <div className="relative w-full overflow-hidden" style={{ height }}>
      <MapContainer
        center={mapCenter}
        zoom={mapZoom}
        style={{ height: "100%", width: "100%", background: "#0a1628" }}
        scrollWheelZoom={true}
        zoomControl={true}
        minZoom={2}
        maxZoom={12}
      >
        {/* Dark theme map tiles */}
        <TileLayer
          attribution='&copy; <a href="https://carto.com/">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png"
        />

        {/* Country/region labels layer */}
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_only_labels/{z}/{x}/{y}{r}.png"
        />

        {/* Draw route lines with glow effect */}
        {showRoutes &&
          journeys.map((journey, index) => (
            <Polyline
              key={`route-${index}`}
              positions={[journey.fromCoords, journey.toCoords]}
              pathOptions={{
                color: "#00d4ff",
                weight: 1.5,
                opacity: 0.4,
                dashArray: "4, 8",
              }}
            />
          ))}

        {/* Draw location markers as dots */}
        {locations.map((location) => (
          <CircleMarker
            key={location.name}
            center={[location.lat, location.lng]}
            radius={getMarkerSize(location.sermonCount, location.isHomeBase)}
            pathOptions={{
              color: location.isHomeBase ? "#00d4ff" : "#ff3e7f",
              fillColor: getMarkerColor(location),
              fillOpacity: 0.9,
              weight: location.isHomeBase ? 2 : 1,
            }}
          >
            <Popup>
              <div className="min-w-[160px] p-1">
                <h3 className="font-bold text-white flex items-center gap-2">
                  {location.name}
                  {location.isHomeBase && (
                    <span className="text-xs px-1.5 py-0.5 rounded bg-accent/20 text-accent">Home</span>
                  )}
                </h3>
                <p className="text-sm text-slate-400">{location.country}</p>
                <div className="mt-2 pt-2 border-t border-border">
                  <p className="text-sm">
                    <span className="font-bold text-accent">
                      {location.sermonCount}
                    </span>{" "}
                    <span className="text-slate-400">sermons preached</span>
                  </p>
                </div>
              </div>
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>

      {/* Minimal Legend - positioned top right */}
      <div className="absolute top-4 right-4 z-[1000] rounded-lg bg-dark/90 backdrop-blur-sm border border-border p-3">
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-2">
            <div className="h-2.5 w-2.5 rounded-full bg-accent shadow-glow"></div>
            <span className="text-slate-400">Home Base</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-2.5 w-2.5 rounded-full bg-marker shadow-glow-pink"></div>
            <span className="text-slate-400">Ministry Sites</span>
          </div>
        </div>
      </div>
    </div>
  );
}
