import Header from "@/components/layout/Header";
import { Database } from "lucide-react";

export default function SourcesPage() {
  return (
    <div>
      <Header title="Data Sources" subtitle="Manage YouTube & Facebook Sources" />
      <div className="flex flex-col items-center justify-center p-12">
        <div className="rounded-full bg-primary-50 p-6">
          <Database className="h-12 w-12 text-primary" />
        </div>
        <h2 className="mt-6 text-xl font-semibold text-gray-900">Data Sources</h2>
        <p className="mt-2 text-gray-500">Coming soon - Manage video sources</p>
      </div>
    </div>
  );
}
