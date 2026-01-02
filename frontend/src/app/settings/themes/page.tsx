import Header from "@/components/layout/Header";
import { Tag } from "lucide-react";

export default function ThemesPage() {
  return (
    <div>
      <Header title="Themes" subtitle="Manage Sermon Topics" />
      <div className="flex flex-col items-center justify-center p-12">
        <div className="rounded-full bg-primary-50 p-6">
          <Tag className="h-12 w-12 text-primary" />
        </div>
        <h2 className="mt-6 text-xl font-semibold text-gray-900">Themes Manager</h2>
        <p className="mt-2 text-gray-500">Coming soon - Categorize sermon topics</p>
      </div>
    </div>
  );
}
