export interface User {
  id: string;
  email: string;
  full_name?: string | null;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string;
}

export interface ImageMetadata {
  format?: string;
  mode?: string;
  width?: number;
  height?: number;
  [key: string]: any;
}

export interface ImageItem {
  id: string;
  owner_id: string;
  storage_key: string;
  thumbnail_key?: string | null;
  original_filename: string;
  mime_type: string;
  file_size: number;
  width?: number | null;
  height?: number | null;
  checksum_sha256: string;
  metadata_json?: ImageMetadata | null;
  created_at: string;
  updated_at: string;
}

export interface ImageListResponse {
  items: ImageItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface Album {
  id: string;
  owner_id: string;
  title: string;
  description?: string | null;
  cover_image_id?: string | null;
  image_count: number;
  created_at: string;
  updated_at: string;
}

export interface AlbumDetail extends Album {
  images: ImageItem[];
}

export interface UserStats {
  user_id: string;
  email: string;
  storage_used_bytes: number;
  storage_used_mb: number;
  total_images: number;
  total_albums: number;
}

export interface UploadQueueItem {
  id: string;
  file: File;
  previewUrl: string;
  status: "pending" | "uploading" | "processing" | "success" | "error";
  progress: number;
  errorMessage?: string;
}
