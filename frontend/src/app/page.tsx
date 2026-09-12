"use client";

import React, { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import { ImageItem } from "@/types";
import Header from "@/components/Header";
import ImageGallery from "@/components/ImageGallery";
import ImageViewerModal from "@/components/ImageViewerModal";
import UploadModal from "@/components/UploadModal";
import AlbumModal from "@/components/AlbumModal";
import { ShieldCheck, HardDrive, Image as ImageIcon } from "lucide-react";

export default function DashboardPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  const [images, setImages] = useState<ImageItem[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [storageMb, setStorageMb] = useState(0);

  // Modals state
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [activeViewerImage, setActiveViewerImage] = useState<ImageItem | null>(null);
  const [activeViewerIndex, setActiveViewerIndex] = useState<number>(0);
  const [albumModalImageIds, setAlbumModalImageIds] = useState<string[]>([]);
  const [isAlbumModalOpen, setIsAlbumModalOpen] = useState(false);

  // Redirect to login if unauthenticated
  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login");
    }
  }, [user, authLoading, router]);

  const loadData = useCallback(async (query = searchQuery) => {
    if (!user) return;
    try {
      setLoading(true);
      const [res, stats] = await Promise.all([
        api.images.list({ search: query.trim() || undefined, page_size: 100 }),
        api.users.getStats().catch(() => null),
      ]);
      setImages(res.items);
      setTotalCount(res.total);
      if (stats) {
        setStorageMb(stats.storage_used_mb);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [user, searchQuery]);

  useEffect(() => {
    if (user) {
      loadData();
    }
  }, [user, loadData]);

  const handleSearch = (q: string) => {
    setSearchQuery(q);
    loadData(q);
  };

  const handleSelectImage = (img: ImageItem, idx: number) => {
    setActiveViewerImage(img);
    setActiveViewerIndex(idx);
  };

  const handleDeleteImage = (deletedImage: ImageItem) => {
    setImages((prev) => prev.filter((i) => i.id !== deletedImage.id));
    setTotalCount((prev) => Math.max(0, prev - 1));
  };

  const handleOpenAlbumModal = (ids: string[] | string) => {
    const list = Array.isArray(ids) ? ids : [ids];
    setAlbumModalImageIds(list);
    setIsAlbumModalOpen(true);
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
      <Header
        onOpenUpload={() => setIsUploadOpen(true)}
        onSearch={handleSearch}
        storageMb={storageMb}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Clean Minimal Header */}
        <div className="flex items-baseline justify-between pb-4 mb-6 border-b border-slate-800/80">
          <div className="flex items-baseline gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-white">Photos</h1>
            <span className="text-xs text-slate-400">{totalCount} {totalCount === 1 ? "photo" : "photos"}</span>
          </div>
        </div>

        {/* Main Gallery */}
        <ImageGallery
          images={images}
          loading={loading}
          onSelectImage={handleSelectImage}
          onDeleteImage={handleDeleteImage}
          onAddToAlbum={handleOpenAlbumModal}
          onOpenUpload={() => setIsUploadOpen(true)}
        />
      </main>

      {/* Upload Modal */}
      <UploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onUploadComplete={() => {
          loadData();
        }}
      />

      {/* Fullscreen Lightbox Viewer */}
      <ImageViewerModal
        image={activeViewerImage}
        images={images}
        currentIndex={activeViewerIndex}
        onClose={() => setActiveViewerImage(null)}
        onNavigate={(idx) => {
          setActiveViewerIndex(idx);
          setActiveViewerImage(images[idx]);
        }}
        onDelete={handleDeleteImage}
        onAddToAlbum={handleOpenAlbumModal}
      />

      {/* Album Modal */}
      <AlbumModal
        isOpen={isAlbumModalOpen}
        onClose={() => setIsAlbumModalOpen(false)}
        imageIds={albumModalImageIds}
        onSuccess={() => {
          // Refresh
        }}
      />
    </div>
  );
}
