import Header from "@/components/layout/Header";
import { Globe } from "lucide-react";

export default function LocationsPage() {
  return (
    <div>
      <Header title="Locations" subtitle="Manage Ministry Locations" />
      <div className="flex flex-col items-center justify-center p-12">
        <div className="rounded-full bg-primary-50 p-6">
          <Globe className="h-12 w-12 text-primary" />
        </div>
        <h2 className="mt-6 text-xl font-semibold text-gray-900">Locations Manager</h2>
        <p className="mt-2 text-gray-500">Coming soon - Manage churches and venues</p>
      </div>
    </div>
  );
}
