"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowRight,
  ArrowLeft,
  User,
  Upload,
  Youtube,
  Facebook,
  Check,
  X,
  Loader2,
  Camera,
  Sparkles,
  ChevronRight,
} from "lucide-react";
import api from "@/lib/api";

// Types
interface PreacherForm {
  name: string;
  title: string;
  primaryChurch: string;
}

interface UploadedPhoto {
  id: number;
  filename: string;
  preview?: string;
}

// Step indicator component
function StepIndicator({ currentStep }: { currentStep: number }) {
  const steps = [
    { number: 1, label: "Basic Info" },
    { number: 2, label: "Photos" },
    { number: 3, label: "Fetch" },
  ];

  return (
    <div className="flex items-center justify-center gap-2">
      {steps.map((step, index) => (
        <div key={step.number} className="flex items-center">
          <div
            className={`flex h-10 w-10 items-center justify-center rounded-full border-2 transition-all ${
              currentStep >= step.number
                ? "border-accent bg-accent text-white"
                : "border-slate-600 text-slate-500"
            }`}
          >
            {currentStep > step.number ? (
              <Check className="h-5 w-5" />
            ) : (
              <span className="text-sm font-semibold">{step.number}</span>
            )}
          </div>
          {index < steps.length - 1 && (
            <div
              className={`h-0.5 w-12 transition-all ${
                currentStep > step.number ? "bg-accent" : "bg-slate-700"
              }`}
            />
          )}
        </div>
      ))}
    </div>
  );
}

// Step 1: Basic Info
function Step1BasicInfo({
  form,
  setForm,
  onNext,
}: {
  form: PreacherForm;
  setForm: (form: PreacherForm) => void;
  onNext: () => void;
}) {
  const titles = ["Apostle", "Pastor", "Bishop", "Prophet", "Evangelist", "Reverend", "Doctor"];

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-white">Add a Preacher</h2>
        <p className="mt-2 text-slate-400">
          Enter the preacher's information to generate search queries
        </p>
      </div>

      <div className="space-y-4">
        {/* Full Name */}
        <div>
          <label className="mb-2 block text-sm font-medium text-slate-300">
            Full Name <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            placeholder="e.g., Narcisse Majila"
            className="w-full rounded-lg border border-slate-600 bg-slate-800 px-4 py-3 text-white placeholder-slate-500 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
          />
        </div>

        {/* Title */}
        <div>
          <label className="mb-2 block text-sm font-medium text-slate-300">
            Title
          </label>
          <select
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
            className="w-full rounded-lg border border-slate-600 bg-slate-800 px-4 py-3 text-white focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
          >
            <option value="">Select a title...</option>
            {titles.map((title) => (
              <option key={title} value={title}>
                {title}
              </option>
            ))}
          </select>
        </div>

        {/* Primary Church */}
        <div>
          <label className="mb-2 block text-sm font-medium text-slate-300">
            Primary Church/Ministry
          </label>
          <input
            type="text"
            value={form.primaryChurch}
            onChange={(e) => setForm({ ...form, primaryChurch: e.target.value })}
            placeholder="e.g., Ramah Full Gospel Church Pretoria"
            className="w-full rounded-lg border border-slate-600 bg-slate-800 px-4 py-3 text-white placeholder-slate-500 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
          />
        </div>
      </div>

      {/* Search Queries Preview */}
      {form.name && (
        <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-4">
          <h3 className="mb-2 text-sm font-medium text-slate-300">
            Auto-generated search terms:
          </h3>
          <div className="flex flex-wrap gap-2">
            {[
              `"${form.name}"`,
              form.title && `"${form.title} ${form.name}"`,
              `"${form.name}" sermon`,
              `"${form.name}" predication`,
            ]
              .filter(Boolean)
              .map((term, i) => (
                <span
                  key={i}
                  className="rounded-full bg-slate-700 px-3 py-1 text-xs text-slate-300"
                >
                  {term}
                </span>
              ))}
          </div>
        </div>
      )}

      <button
        onClick={onNext}
        disabled={!form.name}
        className="flex w-full items-center justify-center gap-2 rounded-lg bg-accent px-6 py-3 font-semibold text-white transition-all hover:bg-accent/90 disabled:cursor-not-allowed disabled:opacity-50"
      >
        Continue to Photos
        <ArrowRight className="h-5 w-5" />
      </button>
    </div>
  );
}

// Step 2: Photo Upload
function Step2Photos({
  preacherId,
  photos,
  setPhotos,
  onBack,
  onNext,
}: {
  preacherId: number;
  photos: UploadedPhoto[];
  setPhotos: (photos: UploadedPhoto[]) => void;
  onBack: () => void;
  onNext: () => void;
}) {
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  const handleUpload = async (files: FileList) => {
    setUploading(true);
    const newPhotos: UploadedPhoto[] = [];

    for (const file of Array.from(files)) {
      try {
        const result = await api.uploadPreacherPhoto(preacherId, file);
        if (result.success) {
          newPhotos.push({
            id: result.id,
            filename: result.filename,
            preview: URL.createObjectURL(file),
          });
        }
      } catch (err) {
        console.error("Upload error:", err);
      }
    }

    setPhotos([...photos, ...newPhotos]);
    setUploading(false);
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    if (e.dataTransfer.files) {
      handleUpload(e.dataTransfer.files);
    }
  }, [preacherId, photos]);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(true);
  };

  const handleDragLeave = () => {
    setDragActive(false);
  };

  const removePhoto = async (photoId: number) => {
    try {
      await api.deletePreacherPhoto(preacherId, photoId);
      setPhotos(photos.filter((p) => p.id !== photoId));
    } catch (err) {
      console.error("Delete error:", err);
    }
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-white">Upload Reference Photos</h2>
        <p className="mt-2 text-slate-400">
          Upload 3-6 clear photos of the preacher for face recognition
        </p>
      </div>

      {/* Upload zone */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`rounded-xl border-2 border-dashed p-8 text-center transition-all ${
          dragActive
            ? "border-accent bg-accent/10"
            : "border-slate-600 hover:border-slate-500"
        }`}
      >
        {uploading ? (
          <div className="flex flex-col items-center">
            <Loader2 className="h-12 w-12 animate-spin text-accent" />
            <p className="mt-4 text-slate-400">Uploading photos...</p>
          </div>
        ) : (
          <>
            <Camera className="mx-auto h-12 w-12 text-slate-500" />
            <p className="mt-4 text-slate-300">
              Drag and drop photos here, or{" "}
              <label className="cursor-pointer text-accent hover:underline">
                browse
                <input
                  type="file"
                  accept="image/*"
                  multiple
                  onChange={(e) => e.target.files && handleUpload(e.target.files)}
                  className="hidden"
                />
              </label>
            </p>
            <p className="mt-2 text-sm text-slate-500">
              JPG, PNG up to 10MB each
            </p>
          </>
        )}
      </div>

      {/* Photo grid */}
      {photos.length > 0 && (
        <div className="grid grid-cols-3 gap-4">
          {photos.map((photo) => (
            <div
              key={photo.id}
              className="group relative aspect-square overflow-hidden rounded-lg bg-slate-800"
            >
              {photo.preview ? (
                <img
                  src={photo.preview}
                  alt={photo.filename}
                  className="h-full w-full object-cover"
                />
              ) : (
                <div className="flex h-full items-center justify-center">
                  <User className="h-8 w-8 text-slate-600" />
                </div>
              )}
              <button
                onClick={() => removePhoto(photo.id)}
                className="absolute right-2 top-2 rounded-full bg-red-500 p-1 opacity-0 transition-opacity group-hover:opacity-100"
              >
                <X className="h-4 w-4 text-white" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Progress indicator */}
      <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-4">
        <div className="flex items-center justify-between">
          <span className="text-sm text-slate-400">Photos uploaded</span>
          <span
            className={`font-medium ${
              photos.length >= 3 ? "text-green-500" : "text-yellow-500"
            }`}
          >
            {photos.length} / 6 (minimum 3)
          </span>
        </div>
        <div className="mt-2 h-2 rounded-full bg-slate-700">
          <div
            className={`h-full rounded-full transition-all ${
              photos.length >= 3 ? "bg-green-500" : "bg-yellow-500"
            }`}
            style={{ width: `${Math.min(photos.length / 6, 1) * 100}%` }}
          />
        </div>
      </div>

      <div className="flex gap-4">
        <button
          onClick={onBack}
          className="flex items-center gap-2 rounded-lg border border-slate-600 px-6 py-3 font-medium text-slate-300 transition-all hover:border-slate-500"
        >
          <ArrowLeft className="h-5 w-5" />
          Back
        </button>
        <button
          onClick={onNext}
          disabled={photos.length < 3}
          className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-accent px-6 py-3 font-semibold text-white transition-all hover:bg-accent/90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Continue to Fetch
          <ArrowRight className="h-5 w-5" />
        </button>
      </div>
    </div>
  );
}

// Step 3: Fetch Videos
function Step3Fetch({
  preacherId,
  preacherName,
  onBack,
}: {
  preacherId: number;
  preacherName: string;
  onBack: () => void;
}) {
  const router = useRouter();
  const [fetching, setFetching] = useState<string | null>(null);
  const [results, setResults] = useState<{
    youtube?: { videos_found: number; videos_added: number };
    facebook?: { videos_found: number; videos_added: number };
  }>({});
  const [completed, setCompleted] = useState(false);

  const handleFetch = async (platform: "youtube" | "facebook") => {
    setFetching(platform);
    try {
      const result = await api.fetchForPreacher(preacherId, platform);
      setResults((prev) => ({
        ...prev,
        [platform]: {
          videos_found: result.videos_found,
          videos_added: result.videos_added,
        },
      }));
    } catch (err) {
      console.error(`${platform} fetch error:`, err);
    }
    setFetching(null);
    setCompleted(true);
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-white">Fetch Videos</h2>
        <p className="mt-2 text-slate-400">
          Search YouTube and Facebook for videos of {preacherName}
        </p>
      </div>

      {/* Platform buttons */}
      <div className="space-y-4">
        {/* YouTube */}
        <button
          onClick={() => handleFetch("youtube")}
          disabled={fetching !== null}
          className={`flex w-full items-center gap-4 rounded-xl border p-4 transition-all ${
            results.youtube
              ? "border-green-500/50 bg-green-500/10"
              : "border-slate-600 hover:border-red-500/50 hover:bg-red-500/10"
          } disabled:cursor-not-allowed disabled:opacity-50`}
        >
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-red-500">
            <Youtube className="h-6 w-6 text-white" />
          </div>
          <div className="flex-1 text-left">
            <h3 className="font-semibold text-white">YouTube</h3>
            <p className="text-sm text-slate-400">
              {results.youtube
                ? `Found ${results.youtube.videos_found} videos, added ${results.youtube.videos_added}`
                : "Search YouTube channels and videos"}
            </p>
          </div>
          {fetching === "youtube" ? (
            <Loader2 className="h-6 w-6 animate-spin text-accent" />
          ) : results.youtube ? (
            <Check className="h-6 w-6 text-green-500" />
          ) : (
            <ChevronRight className="h-6 w-6 text-slate-500" />
          )}
        </button>

        {/* Facebook */}
        <button
          onClick={() => handleFetch("facebook")}
          disabled={fetching !== null}
          className={`flex w-full items-center gap-4 rounded-xl border p-4 transition-all ${
            results.facebook
              ? "border-green-500/50 bg-green-500/10"
              : "border-slate-600 hover:border-blue-500/50 hover:bg-blue-500/10"
          } disabled:cursor-not-allowed disabled:opacity-50`}
        >
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-blue-600">
            <Facebook className="h-6 w-6 text-white" />
          </div>
          <div className="flex-1 text-left">
            <h3 className="font-semibold text-white">Facebook</h3>
            <p className="text-sm text-slate-400">
              {results.facebook
                ? `Found ${results.facebook.videos_found} videos, added ${results.facebook.videos_added}`
                : "Search Facebook pages and videos"}
            </p>
          </div>
          {fetching === "facebook" ? (
            <Loader2 className="h-6 w-6 animate-spin text-accent" />
          ) : results.facebook ? (
            <Check className="h-6 w-6 text-green-500" />
          ) : (
            <ChevronRight className="h-6 w-6 text-slate-500" />
          )}
        </button>
      </div>

      {/* Success message */}
      {completed && (results.youtube || results.facebook) && (
        <div className="rounded-lg border border-green-500/50 bg-green-500/10 p-4 text-center">
          <Check className="mx-auto h-12 w-12 text-green-500" />
          <h3 className="mt-2 font-semibold text-white">Fetch Complete!</h3>
          <p className="text-sm text-slate-400">
            Videos have been added to the database
          </p>
        </div>
      )}

      <div className="flex gap-4">
        <button
          onClick={onBack}
          className="flex items-center gap-2 rounded-lg border border-slate-600 px-6 py-3 font-medium text-slate-300 transition-all hover:border-slate-500"
        >
          <ArrowLeft className="h-5 w-5" />
          Back
        </button>
        <Link
          href={`/dashboard?preacher=${preacherId}`}
          className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-accent px-6 py-3 font-semibold text-white transition-all hover:bg-accent/90"
        >
          Go to Dashboard
          <ArrowRight className="h-5 w-5" />
        </Link>
      </div>
    </div>
  );
}

// Main Setup Page
export default function SetupPage() {
  const [step, setStep] = useState(1);
  const [form, setForm] = useState<PreacherForm>({
    name: "",
    title: "",
    primaryChurch: "",
  });
  const [preacherId, setPreacherId] = useState<number | null>(null);
  const [photos, setPhotos] = useState<UploadedPhoto[]>([]);
  const [creating, setCreating] = useState(false);

  const handleStep1Next = async () => {
    if (!form.name) return;

    setCreating(true);
    try {
      const result = await api.createPreacher({
        name: form.name,
        title: form.title || undefined,
        primary_church: form.primaryChurch || undefined,
      });
      setPreacherId(result.id);
      setStep(2);
    } catch (err) {
      console.error("Create preacher error:", err);
    }
    setCreating(false);
  };

  return (
    <div className="relative min-h-screen bg-[#0a0f1a]">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-[#0a0f1a] via-[#0f1729] to-[#1a0f29]" />

      {/* Floating orbs (subtle) */}
      <div className="absolute -left-32 -top-32 h-64 w-64 rounded-full bg-purple-600 opacity-10 blur-3xl" />
      <div className="absolute -right-32 bottom-0 h-64 w-64 rounded-full bg-cyan-500 opacity-10 blur-3xl" />

      {/* Content */}
      <div className="relative z-10 flex min-h-screen flex-col">
        {/* Header */}
        <header className="flex items-center justify-between p-6">
          <Link href="/" className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-accent to-purple-600">
              <Sparkles className="h-5 w-5 text-white" />
            </div>
            <span className="text-xl font-bold text-white">Ministry Analytics</span>
          </Link>
        </header>

        {/* Main content */}
        <main className="flex flex-1 flex-col items-center justify-center px-6 py-8">
          <div className="w-full max-w-lg">
            {/* Step indicator */}
            <div className="mb-8">
              <StepIndicator currentStep={step} />
            </div>

            {/* Step content */}
            <div className="rounded-2xl border border-slate-700 bg-slate-800/50 p-6 backdrop-blur-sm">
              {step === 1 && (
                <Step1BasicInfo
                  form={form}
                  setForm={setForm}
                  onNext={handleStep1Next}
                />
              )}
              {step === 2 && preacherId && (
                <Step2Photos
                  preacherId={preacherId}
                  photos={photos}
                  setPhotos={setPhotos}
                  onBack={() => setStep(1)}
                  onNext={() => setStep(3)}
                />
              )}
              {step === 3 && preacherId && (
                <Step3Fetch
                  preacherId={preacherId}
                  preacherName={form.name}
                  onBack={() => setStep(2)}
                />
              )}
            </div>
          </div>
        </main>
      </div>

      {/* Loading overlay */}
      {creating && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="flex flex-col items-center">
            <Loader2 className="h-12 w-12 animate-spin text-accent" />
            <p className="mt-4 text-white">Creating preacher...</p>
          </div>
        </div>
      )}
    </div>
  );
}
