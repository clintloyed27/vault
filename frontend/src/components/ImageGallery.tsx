"use client";

import React, { useState } from "react";
import { ImageItem } from "@/types";
import { api } from "@/lib/api";
import {
  ShieldAlert,
  Check,
  Trash2,
  FolderPlus,
  Maximize2,
  FileImage,
} from "lucide-react";

interface ImageGalleryProps {
  images: ImageItem[];
  loading: boolean;
  onSelectImage: (image: ImageItem, index: number) => void;
  onDeleteImage?: (image: ImageItem) => void;
  onAddToAlbum?: (selectedIds: string[]) => void;
  onOpenUpload?: () => void;
}

export default function ImageGallery({
  images,
  loading,
  onSelectImage,
  onDeleteImage,
  onAddToAlbum,
  onOpenUpload,
}: ImageGalleryProps) {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [selectionMode, setSelectionMode] = useState(false);

  const toggleSelect = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const next = new Set(selectedIds);
    if (next.has(id)) {
      next.delete(id);
    } else {
      next.add(id);
    }
    setSelectedIds(next);
    if (next.size === 0) {
      setSelectionMode(false);
    } else {
      setSelectionMode(true);
    }
  };

  const handleSelectAll = () => {
    if (selectedIds.size === images.length) {
      setSelectedIds(new Set());
      setSelectionMode(false);
    } else {
      setSelectedIds(new Set(images.map((i) => i.id)));
      setSelectionMode(true);
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  if (loading) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 animate-pulse">
        {Array.from({ length: 12 }).map((_, i) => (
          <div
            key={i}
            className="aspect-square rounded-2xl bg-slate-800/40 border border-slate-800/60"
          />
        ))}
      </div>
    );
  }

  if (images.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[55vh] text-center p-8 rounded-3xl border border-dashed border-slate-800 bg-slate-900/30">
        <div className="w-16 h-16 rounded-2xl bg-slate-800/80 border border-slate-700/80 flex items-center justify-center mb-4 text-cyan-400">
          <FileImage className="w-8 h-8 opacity-80" />
        </div>
        <h3 className="text-xl font-semibold text-slate-200 mb-1">
          Your Vault is Empty
        </h3>
        <p className="text-sm text-slate-400 max-w-sm mb-6">
          Encrypted private storage with server-enforced zero-knowledge isolation.
          No unauthorized access, guaranteed.
        </p>
        {onOpenUpload && (
          <button
            onClick={onOpenUpload}
            className="bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white font-medium px-5 py-2.5 rounded-xl shadow-lg shadow-cyan-500/20 transition"
          >
            Upload Images Now
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Batch Selection Action Bar */}
      {selectionMode && (
        <div className="sticky top-20 z-30 flex items-center justify-between bg-slate-900/90 border border-cyan-500/30 backdrop-blur-xl px-4 py-2.5 rounded-2xl shadow-xl shadow-cyan-950/40 animate-in fade-in slide-in-from-top-2">
          <div className="flex items-center gap-3">
            <button
              onClick={handleSelectAll}
              className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-slate-800 text-slate-200 hover:bg-slate-700 transition"
            >
              {selectedIds.size === images.length ? "Deselect All" : "Select All"}
            </button>
            <span className="text-sm text-cyan-300 font-medium">
              {selectedIds.size} image{selectedIds.size > 1 ? "s" : ""} selected
            </span>
          </div>

          <div className="flex items-center gap-2">
            {onAddToAlbum && (
              <button
                onClick={() => onAddToAlbum(Array.from(selectedIds))}
                className="flex items-center gap-1.5 text-xs font-semibold bg-indigo-600/80 hover:bg-indigo-600 text-white px-3 py-1.5 rounded-xl transition"
              >
                <FolderPlus className="w-3.5 h-3.5" />
                Add to Album
              </button>
            )}
            <button
              onClick={() => {
                setSelectedIds(new Set());
                setSelectionMode(false);
              }}
              className="text-xs text-slate-400 hover:text-slate-200 px-2 py-1"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Grid Layout */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3 sm:gap-4">
        {images.map((image, idx) => {
          const isSelected = selectedIds.has(image.id);
          const thumbUrl = api.images.getThumbnailUrl(image.id);

          return (
            <div
              key={image.id}
              onClick={() => {
                if (selectionMode) {
                  toggleSelect(image.id, {} as any);
                } else {
                  onSelectImage(image, idx);
                }
              }}
              className={`group relative aspect-square rounded-2xl overflow-hidden bg-slate-900 border cursor-pointer transition-all duration-300 select-none ${
                isSelected
                  ? "border-cyan-400 ring-2 ring-cyan-400/40 scale-[0.98]"
                  : "border-slate-800/80 hover:border-slate-600 hover:shadow-lg hover:shadow-cyan-950/20"
              }`}
            >
              {/* Image thumbnail */}
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={thumbUrl}
                alt={image.original_filename}
                loading="lazy"
                className="w-full h-full object-cover object-center group-hover:scale-105 transition duration-500"
              />

              {/* Top Selector Checkbox */}
              <button
                onClick={(e) => toggleSelect(image.id, e)}
                className={`absolute top-2 left-2 w-6 h-6 rounded-lg flex items-center justify-center transition ${
                  isSelected
                    ? "bg-cyan-500 text-white shadow-md shadow-cyan-500/50"
                    : "bg-black/50 backdrop-blur-md border border-white/20 text-transparent opacity-0 group-hover:opacity-100 hover:border-white/60"
                }`}
              >
                <Check className="w-3.5 h-3.5 stroke-[3]" />
              </button>

              {/* Bottom Metadata Overlay */}
              <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent p-2.5 pt-6 flex flex-col justify-end opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                <p className="text-xs font-medium text-slate-200 truncate drop-shadow">
                  {image.original_filename}
                </p>
                <div className="flex items-center justify-between text-[10px] text-slate-400 mt-0.5">
                  <span>{formatBytes(image.file_size)}</span>
                  {image.width && image.height && (
                    <span>
                      {image.width}×{image.height}
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
