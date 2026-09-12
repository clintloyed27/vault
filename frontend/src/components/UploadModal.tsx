"use client";

import React, { useState, useRef, useEffect } from "react";
import { api } from "@/lib/api";
import { UploadQueueItem } from "@/types";
import {
  X,
  UploadCloud,
  CheckCircle2,
  AlertCircle,
  RotateCcw,
  Trash2,
  FileImage,
  Camera,
  Image as ImageIcon,
  SwitchCamera,
} from "lucide-react";

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadComplete: () => void;
}

const MAX_FILE_SIZE_MB = 25;
const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp", "image/gif"];

export default function UploadModal({
  isOpen,
  onClose,
  onUploadComplete,
}: UploadModalProps) {
  const [activeTab, setActiveTab] = useState<"gallery" | "camera">("gallery");
  const [queue, setQueue] = useState<UploadQueueItem[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [cameraActive, setCameraActive] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [facingMode, setFacingMode] = useState<"user" | "environment">("environment");

  const fileInputRef = useRef<HTMLInputElement>(null);
  const mobileCameraInputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // Stop camera stream when closing modal or leaving camera tab
  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    setCameraActive(false);
  };

  useEffect(() => {
    if (!isOpen) {
      stopCamera();
    }
  }, [isOpen]);

  useEffect(() => {
    if (activeTab !== "camera") {
      stopCamera();
    }
  }, [activeTab]);

  const startCamera = async (mode: "user" | "environment" = facingMode) => {
    stopCamera();
    setCameraError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: mode,
          width: { ideal: 1920 },
          height: { ideal: 1080 },
        },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      }
      setCameraActive(true);
    } catch (err: any) {
      console.warn("Camera access failed or unavailable:", err);
      setCameraError(
        err.name === "NotAllowedError"
          ? "Camera permission was denied. Please allow camera access in browser settings."
          : "Could not open camera stream. You can still use the device camera button below."
      );
      setCameraActive(false);
    }
  };

  const toggleFacingMode = () => {
    const nextMode = facingMode === "environment" ? "user" : "environment";
    setFacingMode(nextMode);
    if (cameraActive) {
      startCamera(nextMode);
    }
  };

  const capturePhoto = () => {
    if (!videoRef.current || !canvasRef.current) return;
    const video = videoRef.current;
    const canvas = canvasRef.current;

    canvas.width = video.videoWidth || 1280;
    canvas.height = video.videoHeight || 720;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Draw video frame to canvas
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(
      (blob) => {
        if (!blob) return;
        const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
        const file = new File([blob], `capture_${timestamp}.jpg`, {
          type: "image/jpeg",
        });

        // Add captured photo to upload queue
        const previewUrl = URL.createObjectURL(file);
        setQueue((prev) => [
          ...prev,
          {
            id: Math.random().toString(36).substring(2, 9),
            file,
            previewUrl,
            status: "pending",
            progress: 0,
          },
        ]);

        // Return to gallery queue to review/upload
        setActiveTab("gallery");
        stopCamera();
      },
      "image/jpeg",
      0.95
    );
  };

  const handleFiles = (files: FileList | null) => {
    if (!files || files.length === 0) return;

    const newItems: UploadQueueItem[] = [];
    Array.from(files).forEach((file) => {
      // Validate format
      if (!ALLOWED_TYPES.includes(file.type)) {
        alert(`File ${file.name} is not a supported format (JPEG, PNG, WebP, GIF)`);
        return;
      }
      // Validate size
      if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
        alert(`File ${file.name} exceeds the maximum size limit of ${MAX_FILE_SIZE_MB}MB`);
        return;
      }

      const previewUrl = URL.createObjectURL(file);
      newItems.push({
        id: Math.random().toString(36).substring(2, 9),
        file,
        previewUrl,
        status: "pending",
        progress: 0,
      });
    });

    setQueue((prev) => [...prev, ...newItems]);
  };

  const uploadItem = async (item: UploadQueueItem) => {
    // Update status to uploading
    setQueue((prev) =>
      prev.map((i) => (i.id === item.id ? { ...i, status: "uploading", progress: 0 } : i))
    );

    try {
      await api.images.upload(item.file, (percent) => {
        setQueue((prev) =>
          prev.map((i) =>
            i.id === item.id
              ? {
                  ...i,
                  progress: percent,
                  status: percent >= 100 ? "processing" : "uploading",
                }
              : i
          )
        );
      });

      setQueue((prev) =>
        prev.map((i) =>
          i.id === item.id ? { ...i, status: "success", progress: 100 } : i
        )
      );
      onUploadComplete();
    } catch (err: any) {
      setQueue((prev) =>
        prev.map((i) =>
          i.id === item.id
            ? {
                ...i,
                status: "error",
                errorMessage: err.message || "Upload failed",
              }
            : i
        )
      );
    }
  };

  const startUploadAll = async () => {
    const pendingItems = queue.filter((i) => i.status === "pending" || i.status === "error");
    for (const item of pendingItems) {
      uploadItem(item);
    }
  };

  const removeItem = (id: string) => {
    setQueue((prev) => {
      const item = prev.find((i) => i.id === id);
      if (item) URL.revokeObjectURL(item.previewUrl);
      return prev.filter((i) => i.id !== id);
    });
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFiles(e.dataTransfer.files);
  };

  const pendingCount = queue.filter((i) => i.status === "pending").length;
  const inProgressCount = queue.filter((i) => i.status === "uploading" || i.status === "processing").length;
  const successCount = queue.filter((i) => i.status === "success").length;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in">
      <div className="w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-cyan-950/80 border border-cyan-800/40 text-cyan-400">
              <UploadCloud className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-slate-100">
                Secure Ingestion Portal
              </h3>
              <p className="text-xs text-slate-400">
                Files are validated, stripped of metadata, and isolated server-side.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-white rounded-xl hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Selection Mode Switcher: Gallery vs Camera */}
        <div className="px-6 pt-4 flex items-center gap-2 border-b border-slate-800">
          <button
            onClick={() => setActiveTab("gallery")}
            className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition ${
              activeTab === "gallery"
                ? "border-cyan-400 text-cyan-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <ImageIcon className="w-4 h-4" />
            <span>Upload from Gallery</span>
          </button>

          <button
            onClick={() => {
              setActiveTab("camera");
              startCamera();
            }}
            className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition ${
              activeTab === "camera"
                ? "border-cyan-400 text-cyan-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            <Camera className="w-4 h-4" />
            <span>Take Photo (Camera)</span>
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-5 overflow-y-auto flex-1">
          {/* TAB 1: GALLERY UPLOAD */}
          {activeTab === "gallery" && (
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-2xl p-8 flex flex-col items-center justify-center text-center cursor-pointer transition ${
                isDragging
                  ? "border-cyan-400 bg-cyan-950/20"
                  : "border-slate-700/80 hover:border-cyan-500/50 bg-slate-950/40"
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept="image/jpeg,image/png,image/webp,image/gif"
                className="hidden"
                onChange={(e) => handleFiles(e.target.files)}
              />
              <div className="w-12 h-12 rounded-2xl bg-slate-800/80 border border-slate-700 flex items-center justify-center mb-3 text-cyan-400">
                <ImageIcon className="w-6 h-6" />
              </div>
              <p className="text-sm font-medium text-slate-200">
                Drop images here or <span className="text-cyan-400 underline">browse photo gallery</span>
              </p>
              <p className="text-xs text-slate-500 mt-1">
                Supports JPEG, PNG, WebP, GIF • Up to {MAX_FILE_SIZE_MB}MB per file
              </p>
            </div>
          )}

          {/* TAB 2: LIVE CAMERA CAPTURE */}
          {activeTab === "camera" && (
            <div className="space-y-4">
              <div className="relative rounded-2xl overflow-hidden bg-black border border-slate-800 aspect-video flex items-center justify-center">
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  className={`w-full h-full object-cover ${cameraActive ? "block" : "hidden"}`}
                />

                {!cameraActive && (
                  <div className="text-center p-6 space-y-3">
                    <div className="w-12 h-12 rounded-2xl bg-slate-800 border border-slate-700 flex items-center justify-center mx-auto text-slate-400">
                      <Camera className="w-6 h-6" />
                    </div>
                    {cameraError ? (
                      <p className="text-xs text-rose-400 max-w-sm">{cameraError}</p>
                    ) : (
                      <p className="text-xs text-slate-400">Camera preview inactive</p>
                    )}
                    <div className="flex flex-wrap items-center justify-center gap-2 pt-2">
                      <button
                        onClick={() => startCamera()}
                        className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 rounded-xl transition"
                      >
                        Start Live Camera
                      </button>
                      <button
                        onClick={() => mobileCameraInputRef.current?.click()}
                        className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-xs font-semibold text-white rounded-xl transition"
                      >
                        Open Device Camera
                      </button>
                    </div>
                  </div>
                )}

                {/* Live Controls Overlay */}
                {cameraActive && (
                  <div className="absolute inset-x-0 bottom-3 flex items-center justify-center gap-4 px-4 z-10">
                    <button
                      onClick={toggleFacingMode}
                      className="p-2.5 rounded-full bg-black/60 hover:bg-black/80 backdrop-blur-md text-white border border-white/20 transition"
                      title="Switch Camera (Front/Rear)"
                    >
                      <SwitchCamera className="w-4 h-4" />
                    </button>

                    <button
                      onClick={capturePhoto}
                      className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-white text-slate-900 font-bold text-xs shadow-xl hover:bg-slate-200 transition active:scale-95"
                    >
                      <div className="w-3 h-3 rounded-full bg-rose-500 animate-pulse" />
                      <span>Capture Photo</span>
                    </button>

                    <button
                      onClick={stopCamera}
                      className="p-2.5 rounded-full bg-black/60 hover:bg-black/80 backdrop-blur-md text-white border border-white/20 transition"
                      title="Turn Off Camera"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                )}

                {/* Hidden canvas used to capture frame */}
                <canvas ref={canvasRef} className="hidden" />

                {/* Native mobile camera fallback input */}
                <input
                  ref={mobileCameraInputRef}
                  type="file"
                  accept="image/*"
                  capture="environment"
                  className="hidden"
                  onChange={(e) => {
                    handleFiles(e.target.files);
                    setActiveTab("gallery");
                  }}
                />
              </div>

              <div className="flex items-center justify-between text-xs text-slate-400 px-1">
                <span>Direct capture automatically strips GPS telemetry upon upload.</span>
                <button
                  onClick={() => mobileCameraInputRef.current?.click()}
                  className="text-cyan-400 hover:underline"
                >
                  Use Native Mobile App
                </button>
              </div>
            </div>
          )}

          {/* Upload Queue List */}
          {queue.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs text-slate-400 px-1">
                <span>Selected Queue ({queue.length})</span>
                <span>
                  {successCount} completed • {inProgressCount} active
                </span>
              </div>

              <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                {queue.map((item) => (
                  <div
                    key={item.id}
                    className="flex items-center gap-3 p-2.5 rounded-xl bg-slate-800/40 border border-slate-800"
                  >
                    {/* Thumbnail Preview */}
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={item.previewUrl}
                      alt={item.file.name}
                      className="w-10 h-10 rounded-lg object-cover bg-slate-950"
                    />

                    {/* Details & Progress */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="font-medium text-slate-200 truncate pr-2">
                          {item.file.name}
                        </span>
                        <span className="text-[11px] text-slate-400 shrink-0">
                          {item.status === "uploading" && `Uploading ${item.progress}%`}
                          {item.status === "processing" && "Processing..."}
                          {item.status === "success" && "Uploaded ✓"}
                          {item.status === "error" && "Failed"}
                          {item.status === "pending" && "Ready"}
                        </span>
                      </div>

                      {/* Progress Bar */}
                      <div className="w-full bg-slate-950 rounded-full h-1.5 overflow-hidden">
                        <div
                          className={`h-full transition-all duration-200 ${
                            item.status === "success"
                              ? "bg-emerald-500"
                              : item.status === "error"
                              ? "bg-rose-500"
                              : "bg-cyan-500"
                          }`}
                          style={{
                            width: `${
                              item.status === "success"
                                ? 100
                                : item.status === "pending"
                                ? 0
                                : item.progress
                            }%`,
                          }}
                        />
                      </div>

                      {item.errorMessage && (
                        <p className="text-[10px] text-rose-400 mt-1 truncate">
                          {item.errorMessage}
                        </p>
                      )}
                    </div>

                    {/* Action buttons */}
                    <div className="shrink-0 flex items-center gap-1">
                      {item.status === "error" && (
                        <button
                          onClick={() => uploadItem(item)}
                          className="p-1 text-slate-400 hover:text-cyan-400"
                          title="Retry"
                        >
                          <RotateCcw className="w-4 h-4" />
                        </button>
                      )}
                      {item.status !== "uploading" && (
                        <button
                          onClick={() => removeItem(item.id)}
                          className="p-1 text-slate-400 hover:text-rose-400"
                          title="Remove"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-4 border-t border-slate-800 bg-slate-950/40 flex items-center justify-between">
          <button
            onClick={() => setQueue([])}
            disabled={queue.length === 0 || inProgressCount > 0}
            className="text-xs text-slate-400 hover:text-slate-200 disabled:opacity-40"
          >
            Clear All
          </button>

          <div className="flex items-center gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-xs font-semibold text-slate-300 hover:bg-slate-800 rounded-xl transition"
            >
              Done
            </button>
            <button
              onClick={startUploadAll}
              disabled={pendingCount === 0 || inProgressCount > 0}
              className="px-5 py-2 text-xs font-semibold bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white rounded-xl shadow-lg shadow-cyan-500/20 disabled:opacity-50 transition"
            >
              {inProgressCount > 0 ? "Uploading..." : `Upload (${pendingCount})`}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
