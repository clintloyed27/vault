import math
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Query, Response, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.image import ImageListResponse, ImageResponse, ImageUpdate
from app.services.image_service import image_service

router = APIRouter()


@router.post("/upload", response_model=List[ImageResponse], status_code=status.HTTP_201_CREATED)
async def upload_images(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload one or multiple images into the authenticated user's private vault.
    Strictly validates MIME type, magic bytes, strips sensitive EXIF, and creates thumbnails.
    """
    uploaded_images = []
    for upload in files:
        contents = await upload.read()
        image = image_service.upload_image(
            db=db,
            owner_id=current_user.id,
            file_bytes=contents,
            original_filename=upload.filename or "image.jpg",
        )
        uploaded_images.append(image)

    return uploaded_images


@router.get("/", response_model=ImageListResponse)
def list_images(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: Optional[str] = Query(None),
    album_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List images belonging exclusively to the current user.
    Never returns images from other users.
    """
    items, total = image_service.list_images(
        db=db,
        owner_id=current_user.id,
        page=page,
        page_size=page_size,
        search=search,
        album_id=album_id,
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return ImageListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{image_id}", response_model=ImageResponse)
def get_image_details(
    image_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetch image metadata. Returns 404/403 if image belongs to another tenant."""
    return image_service.get_image(db=db, image_id=image_id, owner_id=current_user.id)


@router.get("/{image_id}/file")
def view_image_file(
    image_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Streams full-resolution image binary.
    Zero direct filesystem exposure - strictly mediated via authenticated stream.
    """
    stream, image = image_service.get_image_stream(
        db=db, image_id=image_id, owner_id=current_user.id
    )
    headers = {
        "Content-Disposition": f'inline; filename="{image.original_filename}"',
        "Content-Length": str(image.file_size),
        "Cache-Control": "private, max-age=3600",
        "X-Content-Type-Options": "nosniff",
    }
    return StreamingResponse(stream, media_type=image.mime_type, headers=headers)


@router.get("/{image_id}/thumbnail")
def view_thumbnail_file(
    image_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Streams optimized WebP thumbnail binary with caching headers."""
    stream, media_type = image_service.get_thumbnail_stream(
        db=db, image_id=image_id, owner_id=current_user.id
    )
    headers = {
        "Cache-Control": "private, max-age=86400",
        "X-Content-Type-Options": "nosniff",
    }
    return StreamingResponse(stream, media_type=media_type, headers=headers)


@router.get("/{image_id}/download")
def download_image(
    image_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Downloads original image file as an attachment."""
    stream, image = image_service.get_image_stream(
        db=db, image_id=image_id, owner_id=current_user.id
    )
    headers = {
        "Content-Disposition": f'attachment; filename="{image.original_filename}"',
        "Content-Length": str(image.file_size),
        "X-Content-Type-Options": "nosniff",
    }
    return StreamingResponse(stream, media_type=image.mime_type, headers=headers)


@router.patch("/{image_id}", response_model=ImageResponse)
def update_image(
    image_id: str,
    payload: ImageUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Rename original filename."""
    if not payload.original_filename:
        return image_service.get_image(db=db, image_id=image_id, owner_id=current_user.id)

    return image_service.update_filename(
        db=db,
        image_id=image_id,
        owner_id=current_user.id,
        new_filename=payload.original_filename,
    )


@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_image(
    image_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Permanently delete an image and its physical storage files."""
    image_service.delete_image(db=db, image_id=image_id, owner_id=current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
