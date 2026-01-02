"use client";

import { useEffect, useState, useCallback } from "react";
import Header from "@/components/layout/Header";
import {
  User,
  Upload,
  Trash2,
  CheckCircle,
  XCircle,
  Loader2,
  AlertCircle,
  Play,
  RefreshCw,
} from "lucide-react";
import api, {
  ReferencePhoto,
  FaceRecognitionStatus,
  FaceTestResult,
} from "@/lib/api";
import { cn } from "@/lib/utils";

export default function FacesPage() {
  const [status, setStatus] = useState<FaceRecognitionStatus | null>(null);
  const [photos, setPhotos] = useState<ReferencePhoto[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [testUrl, setTestUrl] = useState("");
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<FaceTestResult | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [statusRes, photosRes] = await Promise.all([
        api.getFaceRecognitionStatus(),
        api.getReferencePhotos(),
      ]);

      setStatus(statusRes);
      setPhotos(photosRes.photos || []);
    } catch (err) {
      setError("Failed to load face recognition data");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setUploading(true);
    setError(null);

    try {
      for (const file of Array.from(files)) {
        await api.uploadReferencePhoto(file);
      }
      await loadData();
    } catch (err: any) {
      setError(err.message || "Failed to upload photo");
    } finally {
      setUploading(false);
      // Reset input
      e.target.value = "";
    }
  };

  const handleDelete = async (filename: string) => {
    if (!confirm(`Delete reference photo "${filename}"?`)) return;

    try {
      await api.deleteReferencePhoto(filename);
      await loadData();
    } catch (err: any) {
      setError(err.message || "Failed to delete photo");
    }
  };

  const handleTest = async () => {
    if (!testUrl.trim()) {
      setError("Please enter a video URL");
      return;
    }

    setTesting(true);
    setTestResult(null);
    setError(null);

    try {
      const result = await api.testFaceRecognition(testUrl);
      setTestResult(result);
    } catch (err: any) {
      setError(err.message || "Failed to test face recognition");
    } finally {
      setTesting(false);
    }
  };

  if (loading) {
    return (
      <div>
        <Header
          title="Face Recognition"
          subtitle="Manage reference photos for face detection"
        />
        <div className="flex items-center justify-center p-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </div>
    );
  }

  return (
    <div>
      <Header
        title="Face Recognition"
        subtitle="Manage reference photos for face detection"
      />

      <div className="p-6 space-y-6">
        {/* Status Card */}
        <div className="card">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div
                className={cn(
                  "flex h-12 w-12 items-center justify-center rounded-full",
                  status?.available
                    ? status?.fallback_mode
                      ? "bg-yellow-100"
                      : "bg-green-100"
                    : "bg-red-100"
                )}
              >
                {status?.available ? (
                  status?.fallback_mode ? (
                    <AlertCircle className="h-6 w-6 text-yellow-600" />
                  ) : (
                    <CheckCircle className="h-6 w-6 text-green-600" />
                  )
                ) : (
                  <XCircle className="h-6 w-6 text-red-600" />
                )}
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">
                  {status?.available
                    ? status?.fallback_mode
                      ? "Face Detection Active (Limited)"
                      : "Face Recognition Active"
                    : "Face Recognition Unavailable"}
                </h3>
                <p className="text-sm text-gray-500">
                  {status?.model_loaded
                    ? `Model: ${status.config?.model_name || "VGG-Face"}`
                    : status?.error || "Model not loaded"}
                </p>
              </div>
            </div>
            <button
              onClick={loadData}
              className="btn-ghost flex items-center gap-2"
            >
              <RefreshCw size={16} />
              Refresh
            </button>
          </div>

          {status?.config && (
            <div className="mt-4 grid grid-cols-3 gap-4 border-t pt-4">
              <div>
                <p className="text-xs text-gray-500 uppercase">Reference Photos</p>
                <p className="text-lg font-semibold text-primary">
                  {photos.length}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500 uppercase">Detector</p>
                <p className="text-lg font-semibold">
                  {status.config.detector_backend}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500 uppercase">Frame Extraction</p>
                <p className="text-lg font-semibold">
                  {status.config.frame_extraction_enabled ? "Enabled" : "Disabled"}
                </p>
              </div>
            </div>
          )}

          {/* Fallback Mode Warning */}
          {status?.fallback_mode && (
            <div className="mt-4 flex items-start gap-3 rounded-lg bg-yellow-50 p-4 text-yellow-800 border border-yellow-200">
              <AlertCircle className="h-5 w-5 mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-semibold">Limited Functionality Mode</p>
                <p className="text-sm mt-1">
                  {status.warning || "Face detection is active but cannot verify identity against reference photos."}
                </p>
                <p className="text-xs mt-2 text-yellow-700">
                  For full face recognition, install TensorFlow with Python 3.11 or 3.12.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Error Alert */}
        {error && (
          <div className="flex items-center gap-3 rounded-lg bg-red-50 p-4 text-red-700">
            <AlertCircle size={20} />
            <span>{error}</span>
            <button
              onClick={() => setError(null)}
              className="ml-auto text-red-500 hover:text-red-700"
            >
              <XCircle size={16} />
            </button>
          </div>
        )}

        {/* Reference Photos Section */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              Reference Photos
            </h2>
            <label className="btn-primary flex items-center gap-2 cursor-pointer">
              {uploading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Upload size={16} />
              )}
              Upload Photo
              <input
                type="file"
                accept="image/jpeg,image/png"
                multiple
                onChange={handleFileUpload}
                disabled={uploading}
                className="hidden"
              />
            </label>
          </div>

          <p className="text-sm text-gray-500 mb-4">
            Upload clear photos of Apostle Narcisse Majila&apos;s face for accurate
            recognition. Multiple photos from different angles improve accuracy.
          </p>

          {photos.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 border-2 border-dashed border-gray-200 rounded-lg">
              <User className="h-12 w-12 text-gray-300" />
              <p className="mt-4 text-gray-500">No reference photos uploaded</p>
              <label className="mt-4 btn-primary cursor-pointer">
                <Upload size={16} className="mr-2" />
                Upload First Photo
                <input
                  type="file"
                  accept="image/jpeg,image/png"
                  multiple
                  onChange={handleFileUpload}
                  disabled={uploading}
                  className="hidden"
                />
              </label>
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
              {photos.map((photo) => (
                <div
                  key={photo.filename}
                  className="group relative aspect-square rounded-lg overflow-hidden bg-gray-100 border"
                >
                  {photo.data ? (
                    <img
                      src={`data:${photo.mime_type};base64,${photo.data}`}
                      alt={photo.filename}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="flex items-center justify-center h-full">
                      <User className="h-8 w-8 text-gray-400" />
                    </div>
                  )}
                  <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                    <button
                      onClick={() => handleDelete(photo.filename)}
                      className="p-2 bg-red-500 text-white rounded-full hover:bg-red-600"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                  <div className="absolute bottom-0 left-0 right-0 bg-black/60 px-2 py-1 text-xs text-white truncate">
                    {photo.filename}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Test Face Recognition */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Test Face Recognition
          </h2>
          <p className="text-sm text-gray-500 mb-4">
            Enter a YouTube video URL to test if the face recognition can detect
            Apostle Narcisse Majila.
          </p>

          <div className="flex gap-3">
            <input
              type="text"
              value={testUrl}
              onChange={(e) => setTestUrl(e.target.value)}
              placeholder="https://www.youtube.com/watch?v=..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
            />
            <button
              onClick={handleTest}
              disabled={testing || !testUrl.trim()}
              className="btn-primary flex items-center gap-2"
            >
              {testing ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Play size={16} />
              )}
              Test
            </button>
          </div>

          {testResult && (
            <div
              className={cn(
                "mt-4 p-4 rounded-lg",
                testResult.verified ? "bg-green-50" : "bg-yellow-50"
              )}
            >
              <div className="flex items-center gap-3 mb-3">
                {testResult.verified ? (
                  <CheckCircle className="h-6 w-6 text-green-600" />
                ) : (
                  <XCircle className="h-6 w-6 text-yellow-600" />
                )}
                <span
                  className={cn(
                    "font-semibold",
                    testResult.verified ? "text-green-700" : "text-yellow-700"
                  )}
                >
                  {testResult.verified
                    ? "Face Verified!"
                    : "Face Not Detected"}
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
                <div>
                  <p className="text-gray-500">Confidence</p>
                  <p className="font-medium">
                    {(testResult.confidence * 100).toFixed(1)}%
                  </p>
                </div>
                <div>
                  <p className="text-gray-500">Source</p>
                  <p className="font-medium">{testResult.source}</p>
                </div>
                <div>
                  <p className="text-gray-500">Distance</p>
                  <p className="font-medium">{testResult.distance.toFixed(3)}</p>
                </div>
                <div>
                  <p className="text-gray-500">Model</p>
                  <p className="font-medium">{testResult.model || "N/A"}</p>
                </div>
              </div>

              {testResult.error && (
                <p className="mt-3 text-sm text-red-600">{testResult.error}</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
