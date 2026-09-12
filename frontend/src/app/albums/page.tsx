"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import { Album, AlbumDetail, ImageItem } from "@/types";
import Header from "@/components/Header";
import ImageGallery from "@/components/ImageGallery";
import ImageViewerModal from "@/components/ImageViewerModal";
import AlbumModal from "@/components/AlbumModal";
import {
  FolderLock,
  Plus,
  ArrowLeft,
  Trash2,
  Image as ImageIcon,
  FolderOpen,
} from "lucide-react";

export default function AlbumsPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  const [albums, setAlbums] = useState<Album[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeAlbum, setActiveAlbum] = useState<AlbumDetail | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  // Lightbox
  const [activeViewerImage, setActiveViewerImage] = useState<ImageItem | null>(null);
  const [activeViewerIndex, setActiveViewerIndex] = useState<number>(0);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login");
    }
  }, [user, authLoading, router]);

  const loadAlbums = async () => {
    try {
      setLoading(true);
      const res = await api.albums.list();
      setAlbums(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
      loadAlbums();
    }
  }, [user]);

  const openAlbumDetail = async (albumId: string) => {
    try {
      setLoading(true);
      const res = await api.albums.get(albumId);
      setActiveAlbum(res);
    } catch (err: any) {
      alert(err.message || "Failed to load album");
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAlbum = async (albumId: string) => {
    if (!confirm("Delete this album? Images inside will remain safely in your vault."))
      return;
    try {
      await api.albums.delete(albumId);
      setActiveAlbum(null);
      loadAlbums();
    } catch (err: any) {
      alert(err.message || "Failed to delete album");
    }
  };

  if (authLoading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#070a12] text-cyan-400">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#070a12] text-slate-100 flex flex-col">
      <Header />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeAlbum ? (
          /* Album Detail View */
          <div>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 mb-6 border-b border-slate-800">
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setActiveAlbum(null)}
                  className="p-2 text-slate-400 hover:text-white bg-slate-900 border border-slate-800 rounded-xl transition"
                >
                  <ArrowLeft className="w-5 h-5" />
                </button>
                <div>
                  <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                    <FolderOpen className="w-6 h-6 text-indigo-400" />
                    {activeAlbum.title}
                  </h1>
                  {activeAlbum.description && (
                    <p className="text-xs text-slate-400 mt-1">
                      {activeAlbum.description}
                    </p>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-3">
                <span className="text-xs text-slate-400 bg-slate-900 px-3 py-1.5 rounded-xl border border-slate-800">
                  {activeAlbum.images.length} images
                </span>
                <button
                  onClick={() => handleDeleteAlbum(activeAlbum.id)}
                  className="p-2 text-slate-400 hover:text-rose-400 bg-slate-900 hover:bg-rose-950/40 border border-slate-800 rounded-xl transition"
                  title="Delete Album"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Render Album Images */}
            <ImageGallery
              images={activeAlbum.images}
              loading={loading}
              onSelectImage={(img, idx) => {
                setActiveViewerImage(img);
                setActiveViewerIndex(idx);
              }}
              onDeleteImage={(img) => {
                setActiveAlbum((prev) =>
                  prev ? { ...prev, images: prev.images.filter((i) => i.id !== img.id) } : null
                );
              }}
            />
          </div>
        ) : (
          /* Albums Grid */
          <div>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 mb-8 border-b border-slate-800">
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
                  <FolderLock className="w-6 h-6 text-indigo-400" />
                  Private Collections
                </h1>
                <p className="text-xs text-slate-400 mt-1">
                  Organize your private images into distinct, protected albums.
                </p>
              </div>

              <button
                onClick={() => setIsCreateModalOpen(true)}
                className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold px-4 py-2 rounded-xl shadow-lg shadow-indigo-600/20 transition self-start sm:self-auto"
              >
                <Plus className="w-4 h-4" />
                New Album
              </button>
            </div>

            {loading ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6 animate-pulse">
                {Array.from({ length: 4 }).map((_, i) => (
                  <div
                    key={i}
                    className="h-48 rounded-3xl bg-slate-800/40 border border-slate-800"
                  />
                ))}
              </div>
            ) : albums.length === 0 ? (
              <div className="text-center py-20 rounded-3xl border border-dashed border-slate-800 bg-slate-900/30">
                <FolderLock className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                <h3 className="text-lg font-semibold text-slate-200">
                  No Albums Created Yet
                </h3>
                <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1 mb-6">
                  Create collections to group memories, documents, and private photos.
                </p>
                <button
                  onClick={() => setIsCreateModalOpen(true)}
                  className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold px-4 py-2 rounded-xl shadow-lg shadow-indigo-600/20 transition"
                >
                  Create Your First Album
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                {albums.map((album) => (
                  <div
                    key={album.id}
                    onClick={() => openAlbumDetail(album.id)}
                    className="group vault-glass-card rounded-3xl p-5 cursor-pointer flex flex-col justify-between"
                  >
                    <div>
                      <div className="w-12 h-12 rounded-2xl bg-indigo-950/80 border border-indigo-800/40 flex items-center justify-center text-indigo-400 mb-4 group-hover:scale-110 transition duration-300">
                        <FolderLock className="w-6 h-6" />
                      </div>
                      <h3 className="text-base font-semibold text-slate-100 group-hover:text-cyan-300 transition truncate">
                        {album.title}
                      </h3>
                      {album.description && (
                        <p className="text-xs text-slate-400 mt-1 line-clamp-2">
                          {album.description}
                        </p>
                      )}
                    </div>

                    <div className="mt-6 pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-500">
                      <span className="flex items-center gap-1">
                        <ImageIcon className="w-3.5 h-3.5" />
                        {album.image_count} items
                      </span>
                      <span className="text-indigo-400 font-medium group-hover:translate-x-1 transition">
                        View →
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>

      {/* Album Creation Modal */}
      <AlbumModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        imageIds={[]}
        onSuccess={loadAlbums}
      />

      {/* Viewer Modal */}
      {activeAlbum && (
        <ImageViewerModal
          image={activeViewerImage}
          images={activeAlbum.images}
          currentIndex={activeViewerIndex}
          onClose={() => setActiveViewerImage(null)}
          onNavigate={(idx) => {
            setActiveViewerIndex(idx);
            setActiveViewerImage(activeAlbum.images[idx]);
          }}
          onDelete={(deleted) => {
            setActiveAlbum((prev) =>
              prev
                ? { ...prev, images: prev.images.filter((i) => i.id !== deleted.id) }
                : null
            );
          }}
        />
      )}
    </div>
  );
}
