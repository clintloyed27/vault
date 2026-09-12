from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.image import ImageResponse


class AlbumBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)


class AlbumCreate(AlbumBase):
    pass


class AlbumUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    cover_image_id: Optional[str] = None


class AlbumResponse(AlbumBase):
    id: str
    owner_id: str
    cover_image_id: Optional[str] = None
    image_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlbumDetailResponse(AlbumResponse):
    images: List[ImageResponse] = []


class AlbumImageAction(BaseModel):
    image_ids: List[str]
