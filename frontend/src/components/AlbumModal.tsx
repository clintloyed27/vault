"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Album } from "@/types";
import { X, FolderPlus, Check, Plus } from "lucide-react";

interface AlbumModalProps {
  isOpen: boolean;
  onClose: () => void;
  imageIds: string[];
  onSuccess?: () => void;
}

export default function AlbumModal({
  isOpen,
  onClose,
  imageIds,
  onSuccess,
}: AlbumModalProps) {
  const [albums, setAlbums] = useState<Album[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAlbumId, setSelectedAlbumId] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadAlbums();
    }
  }, [isOpen]);

  const loadAlbums = async () => {
    try {
      setLoading(true);
      const res = await api.albums.list();
      setAlbums(res);
      if (res.length > 0 && !selectedAlbumId) {
        setSelectedAlbumId(res[0].id);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAndAssign = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;

    try {
      setSubmitting(true);
      const newAlbum = await api.albums.create({
        title: newTitle.trim(),
        description: newDescription.trim() || undefined,
      });

      if (imageIds.length > 0) {
        await api.albums.addImages(newAlbum.id, imageIds);
      }

      setNewTitle("");
      setNewDescription("");
      setIsCreating(false);
      if (onSuccess) onSuccess();
      onClose();
    } catch (err: any) {
      alert(err.message || "Failed to create album");
    } finally {
      setSubmitting(false);
    }
  };

  const handleAddToExisting = async () => {
    if (!selectedAlbumId || imageIds.length === 0) return;

    try {
      setSubmitting(true);
      await api.albums.addImages(selectedAlbumId, imageIds);
      if (onSuccess) onSuccess();
      onClose();
    } catch (err: any) {
      alert(err.message || "Failed to add images to album");
    } finally {
      setSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in">
      <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-indigo-950/80 border border-indigo-800/40 text-indigo-400">
              <FolderPlus className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-slate-100">
                {isCreating ? "Create New Album" : "Add to Album"}
              </h3>
              <p className="text-xs text-slate-400">
                {imageIds.length} image{imageIds.length > 1 ? "s" : ""} selected
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

        {/* Content */}
        <div className="p-6">
          {isCreating ? (
            <form onSubmit={handleCreateAndAssign} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Album Title
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Summer Archives 2026"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-sm text-slate-100 focus:outline-none focus:border-cyan-500 transition"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Description (Optional)
                </label>
                <textarea
                  rows={3}
                  placeholder="Private collection notes..."
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-sm text-slate-100 focus:outline-none focus:border-cyan-500 transition resize-none"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsCreating(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-400 hover:text-white"
                >
                  Back to List
                </button>
                <button
                  type="submit"
                  disabled={submitting || !newTitle.trim()}
                  className="px-5 py-2 text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl shadow-lg shadow-indigo-600/20 disabled:opacity-50 transition"
                >
                  {submitting ? "Saving..." : "Create & Add"}
                </button>
              </div>
            </form>
          ) : (
            <div className="space-y-4">
              <button
                type="button"
                onClick={() => setIsCreating(true)}
                className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl border border-dashed border-slate-700 hover:border-cyan-500/60 bg-slate-950/40 text-xs font-semibold text-cyan-400 transition"
              >
                <Plus className="w-4 h-4" />
                Create New Album
              </button>

              {loading ? (
                <div className="py-8 text-center text-xs text-slate-500">
                  Loading your albums...
                </div>
              ) : albums.length === 0 ? (
                <div className="py-6 text-center text-xs text-slate-400">
                  No albums found. Click above to create one.
                </div>
              ) : (
                <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                  {albums.map((album) => {
                    const isSelected = selectedAlbumId === album.id;
                    return (
                      <div
                        key={album.id}
                        onClick={() => setSelectedAlbumId(album.id)}
                        className={`flex items-center justify-between p-3 rounded-xl border cursor-pointer transition ${
                          isSelected
                            ? "bg-indigo-950/40 border-indigo-500 text-slate-100"
                            : "bg-slate-800/30 border-slate-800/70 hover:bg-slate-800/60 text-slate-300"
                        }`}
                      >
                        <div>
                          <p className="text-sm font-medium">{album.title}</p>
                          <p className="text-[11px] text-slate-500">
                            {album.image_count} items
                          </p>
                        </div>
                        {isSelected && (
                          <div className="w-5 h-5 rounded-full bg-indigo-600 flex items-center justify-center text-white">
                            <Check className="w-3.5 h-3.5 stroke-[3]" />
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}

              {albums.length > 0 && (
                <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={onClose}
                    className="px-4 py-2 text-xs font-semibold text-slate-400 hover:text-white"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={handleAddToExisting}
                    disabled={submitting || !selectedAlbumId || imageIds.length === 0}
                    className="px-5 py-2 text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl shadow-lg shadow-indigo-600/20 disabled:opacity-50 transition"
                  >
                    {submitting ? "Adding..." : "Add to Selected Album"}
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
