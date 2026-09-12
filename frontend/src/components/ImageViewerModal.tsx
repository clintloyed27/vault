"use client";

import React, { useEffect, useState, useCallback } from "react";
import { ImageItem } from "@/types";
import { api } from "@/lib/api";
import {
  X,
  ChevronLeft,
  ChevronRight,
  Download,
  Trash2,
  Info,
  ZoomIn,
  ZoomOut,
  FolderPlus,
  ShieldCheck,
  Calendar,
  HardDrive,
  FileCode,
  Hash,
} from "lucide-react";

interface ImageViewerModalProps {
  image: ImageItem | null;
  images: ImageItem[];
  currentIndex: number;
  onClose: () => void;
  onNavigate: (index: number) => void;
  onDelete: (image: ImageItem) => void;
  onAddToAlbum?: (imageId: string) => void;
}

export default function ImageViewerModal({
  image,
  images,
  currentIndex,
  onClose,
  onNavigate,
  onDelete,
  onAddToAlbum,
}: ImageViewerModalProps) {
  const [showInfo, setShowInfo] = useState(false);
  const [isZoomed, setIsZoomed] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const handlePrev = useCallback(() => {
    if (currentIndex > 0) {
      setIsZoomed(false);
      onNavigate(currentIndex - 1);
    }
  }, [currentIndex, onNavigate]);

  const handleNext = useCallback(() => {
    if (currentIndex < images.length - 1) {
      setIsZoomed(false);
      onNavigate(currentIndex + 1);
    }
  }, [currentIndex, images.length, onNavigate]);

  // Keyboard shortcut listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
      if (e.key === "ArrowLeft") handlePrev();
      if (e.key === "ArrowRight") handleNext();
      if (e.key === "i" || e.key === "I") setShowInfo((prev) => !prev);
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handlePrev, handleNext, onClose]);

  if (!image) return null;

  const fullImageUrl = api.images.getFileUrl(image.id);
  const downloadUrl = api.images.getDownloadUrl(image.id);

  const formatBytes = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString("en-US", {
      dateStyle: "medium",
      timeStyle: "short",
    });
  };

  const handleDelete = async () => {
    if (!confirm("Are you sure you want to delete this image permanently?")) return;
    try {
      setIsDeleting(true);
      await api.images.delete(image.id);
      onDelete(image);
      onClose();
    } catch (err: any) {
      alert(err.message || "Failed to delete image");
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/95 backdrop-blur-2xl select-none animate-in fade-in duration-200">
      {/* Top Action Bar */}
      <div className="absolute top-0 inset-x-0 h-16 bg-gradient-to-b from-black/80 to-transparent flex items-center justify-between px-4 sm:px-6 z-20">
        <div className="flex items-center gap-3">
          <button
            onClick={onClose}
            className="p-2 text-slate-300 hover:text-white bg-slate-900/60 hover:bg-slate-800 rounded-xl border border-slate-700/60 transition"
            title="Close (Esc)"
          >
            <X className="w-5 h-5" />
          </button>
          <div className="max-w-[200px] sm:max-w-md truncate">
            <h4 className="text-sm font-semibold text-slate-200 truncate">
              {image.original_filename}
            </h4>
            <p className="text-[11px] text-slate-400">
              {currentIndex + 1} of {images.length}
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          {/* Zoom toggle */}
          <button
            onClick={() => setIsZoomed((prev) => !prev)}
            className="p-2 text-slate-300 hover:text-cyan-400 bg-slate-900/60 hover:bg-slate-800 rounded-xl border border-slate-700/60 transition"
            title={isZoomed ? "Zoom Out" : "Zoom In"}
          >
            {isZoomed ? <ZoomOut className="w-4 h-4" /> : <ZoomIn className="w-4 h-4" />}
          </button>

          {/* Add to Album */}
          {onAddToAlbum && (
            <button
              onClick={() => onAddToAlbum(image.id)}
              className="p-2 text-slate-300 hover:text-indigo-400 bg-slate-900/60 hover:bg-slate-800 rounded-xl border border-slate-700/60 transition"
              title="Add to Album"
            >
              <FolderPlus className="w-4 h-4" />
            </button>
          )}

          {/* Download */}
          <a
            href={downloadUrl}
            download={image.original_filename}
            className="p-2 text-slate-300 hover:text-cyan-400 bg-slate-900/60 hover:bg-slate-800 rounded-xl border border-slate-700/60 transition"
            title="Download Original"
          >
            <Download className="w-4 h-4" />
          </a>

          {/* Toggle Metadata Drawer */}
          <button
            onClick={() => setShowInfo((prev) => !prev)}
            className={`p-2 rounded-xl border transition ${
              showInfo
                ? "bg-cyan-500/20 text-cyan-400 border-cyan-500/50"
                : "text-slate-300 hover:text-white bg-slate-900/60 hover:bg-slate-800 border-slate-700/60"
            }`}
            title="View Metadata (I)"
          >
            <Info className="w-4 h-4" />
          </button>

          {/* Delete */}
          <button
            onClick={handleDelete}
            disabled={isDeleting}
            className="p-2 text-slate-300 hover:text-rose-400 bg-slate-900/60 hover:bg-rose-950/40 rounded-xl border border-slate-700/60 hover:border-rose-700/60 transition"
            title="Delete from Vault"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Image Container */}
      <div className="relative w-full h-full flex items-center justify-center p-4 sm:p-12 overflow-hidden">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={fullImageUrl}
          alt={image.original_filename}
          className={`max-h-[85vh] max-w-[90vw] object-contain transition-transform duration-300 rounded-lg shadow-2xl ${
            isZoomed ? "scale-150 cursor-zoom-out" : "cursor-zoom-in"
          }`}
          onClick={() => setIsZoomed((prev) => !prev)}
        />

        {/* Left / Right Nav Arrows */}
        {currentIndex > 0 && (
          <button
            onClick={handlePrev}
            className="absolute left-4 top-1/2 -translate-y-1/2 p-3 text-slate-200 hover:text-white bg-slate-900/60 hover:bg-slate-800 rounded-2xl border border-slate-700/60 backdrop-blur-md transition shadow-xl"
            title="Previous (Left Arrow)"
          >
            <ChevronLeft className="w-6 h-6" />
          </button>
        )}

        {currentIndex < images.length - 1 && (
          <button
            onClick={handleNext}
            className="absolute right-4 top-1/2 -translate-y-1/2 p-3 text-slate-200 hover:text-white bg-slate-900/60 hover:bg-slate-800 rounded-2xl border border-slate-700/60 backdrop-blur-md transition shadow-xl"
            title="Next (Right Arrow)"
          >
            <ChevronRight className="w-6 h-6" />
          </button>
        )}
      </div>

      {/* Slide-out Metadata Drawer */}
      {showInfo && (
        <div className="absolute right-0 top-16 bottom-0 w-80 sm:w-96 bg-slate-900/95 border-l border-slate-800 backdrop-blur-2xl p-6 overflow-y-auto z-30 animate-in slide-in-from-right duration-200">
          <div className="flex items-center justify-between pb-4 border-b border-slate-800">
            <h3 className="font-semibold text-slate-200 flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-cyan-400" />
              Vault Metadata
            </h3>
            <button
              onClick={() => setShowInfo(false)}
              className="text-slate-400 hover:text-white text-xs"
            >
              Close
            </button>
          </div>

          <div className="mt-6 space-y-4 text-sm">
            <div>
              <span className="text-xs text-slate-400 block mb-1">Filename</span>
              <p className="font-medium text-slate-200 break-all">
                {image.original_filename}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3 pt-2">
              <div className="p-3 rounded-xl bg-slate-800/50 border border-slate-800">
                <span className="text-[11px] text-slate-400 flex items-center gap-1 mb-1">
                  <HardDrive className="w-3.5 h-3.5 text-cyan-400" />
                  File Size
                </span>
                <p className="font-semibold text-slate-200">
                  {formatBytes(image.file_size)}
                </p>
              </div>

              <div className="p-3 rounded-xl bg-slate-800/50 border border-slate-800">
                <span className="text-[11px] text-slate-400 flex items-center gap-1 mb-1">
                  <FileCode className="w-3.5 h-3.5 text-cyan-400" />
                  Format
                </span>
                <p className="font-semibold text-slate-200 uppercase">
                  {image.mime_type.replace("image/", "")}
                </p>
              </div>
            </div>

            {image.width && image.height && (
              <div>
                <span className="text-xs text-slate-400 block mb-1">Resolution</span>
                <p className="font-medium text-slate-200">
                  {image.width} × {image.height} pixels
                </p>
              </div>
            )}

            <div>
              <span className="text-xs text-slate-400 flex items-center gap-1 mb-1">
                <Calendar className="w-3.5 h-3.5 text-cyan-400" />
                Uploaded At
              </span>
              <p className="font-medium text-slate-300">
                {formatDate(image.created_at)}
              </p>
            </div>

            <div>
              <span className="text-xs text-slate-400 flex items-center gap-1 mb-1">
                <Hash className="w-3.5 h-3.5 text-cyan-400" />
                SHA-256 Integrity Checksum
              </span>
              <code className="text-[11px] bg-slate-950 p-2 rounded-lg border border-slate-800 font-mono text-cyan-300 block break-all">
                {image.checksum_sha256}
              </code>
            </div>

            <div className="pt-4 border-t border-slate-800/80">
              <span className="text-xs text-slate-400 block mb-2">Privacy & Isolation</span>
              <div className="p-3 rounded-xl bg-cyan-950/30 border border-cyan-800/40 text-xs text-cyan-200/90 leading-relaxed">
                ✓ Server-enforced tenancy ownership.<br />
                ✓ Internal storage keys hidden from clients.<br />
                ✓ EXIF tracking telemetry stripped.
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
