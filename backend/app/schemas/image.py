from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ImageBase(BaseModel):
    original_filename: str
    mime_type: str
    file_size: int
    width: Optional[int] = None
    height: Optional[int] = None


class ImageUpdate(BaseModel):
    original_filename: Optional[str] = Field(None, max_length=255)


class ImageResponse(ImageBase):
    id: str
    owner_id: str
    storage_key: str
    thumbnail_key: Optional[str] = None
    checksum_sha256: str
    metadata_json: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ImageListResponse(BaseModel):
    items: List[ImageResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
