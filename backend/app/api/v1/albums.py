from typing import List
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.album import (
    AlbumCreate,
    AlbumDetailResponse,
    AlbumImageAction,
    AlbumResponse,
    AlbumUpdate,
)
from app.schemas.image import ImageResponse
from app.services.album_service import album_service

router = APIRouter()


@router.post("/", response_model=AlbumResponse, status_code=status.HTTP_201_CREATED)
def create_album(
    payload: AlbumCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new private album."""
    album = album_service.create_album(
        db=db,
        owner_id=current_user.id,
        title=payload.title,
        description=payload.description,
    )
    return AlbumResponse(
        id=album.id,
        owner_id=album.owner_id,
        title=album.title,
        description=album.description,
        cover_image_id=album.cover_image_id,
        image_count=0,
        created_at=album.created_at,
        updated_at=album.updated_at,
    )


@router.get("/", response_model=List[AlbumResponse])
def list_albums(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all private albums owned by the authenticated user."""
    results = album_service.list_albums(db=db, owner_id=current_user.id)
    return [
        AlbumResponse(
            id=album.id,
            owner_id=album.owner_id,
            title=album.title,
            description=album.description,
            cover_image_id=album.cover_image_id,
            image_count=count,
            created_at=album.created_at,
            updated_at=album.updated_at,
        )
        for album, count in results
    ]


@router.get("/{album_id}", response_model=AlbumDetailResponse)
def get_album_details(
    album_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetch album and its constituent images."""
    album, images = album_service.get_album_details(
        db=db, album_id=album_id, owner_id=current_user.id
    )
    image_responses = [ImageResponse.model_validate(img) for img in images]
    return AlbumDetailResponse(
        id=album.id,
        owner_id=album.owner_id,
        title=album.title,
        description=album.description,
        cover_image_id=album.cover_image_id,
        image_count=len(images),
        created_at=album.created_at,
        updated_at=album.updated_at,
        images=image_responses,
    )


@router.patch("/{album_id}", response_model=AlbumResponse)
def update_album(
    album_id: str,
    payload: AlbumUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update album title, description, or cover image."""
    album = album_service.update_album(
        db=db,
        album_id=album_id,
        owner_id=current_user.id,
        title=payload.title,
        description=payload.description,
        cover_image_id=payload.cover_image_id,
    )
    _, images = album_service.get_album_details(db=db, album_id=album.id, owner_id=current_user.id)
    return AlbumResponse(
        id=album.id,
        owner_id=album.owner_id,
        title=album.title,
        description=album.description,
        cover_image_id=album.cover_image_id,
        image_count=len(images),
        created_at=album.created_at,
        updated_at=album.updated_at,
    )


@router.delete("/{album_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_album(
    album_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete an album (retains the images in the vault)."""
    album_service.delete_album(db=db, album_id=album_id, owner_id=current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{album_id}/images", status_code=status.HTTP_200_OK)
def add_images_to_album(
    album_id: str,
    payload: AlbumImageAction,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Associate images with an album.
    Strictly verifies each image belongs to current_user.
    """
    count = album_service.add_images_to_album(
        db=db,
        album_id=album_id,
        owner_id=current_user.id,
        image_ids=payload.image_ids,
    )
    return {"message": f"Successfully added {count} images to album"}


@router.delete("/{album_id}/images", status_code=status.HTTP_200_OK)
def remove_images_from_album(
    album_id: str,
    payload: AlbumImageAction,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove images from an album."""
    count = album_service.remove_images_from_album(
        db=db,
        album_id=album_id,
        owner_id=current_user.id,
        image_ids=payload.image_ids,
    )
    return {"message": f"Successfully removed {count} images from album"}
