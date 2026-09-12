from datetime import datetime
from typing import Any, List, Optional, Tuple
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.album import AlbumImage
from app.models.image import Image


class ImageRepository:
    @staticmethod
    def get_by_id(db: Session, image_id: str, owner_id: str) -> Optional[Image]:
        """
        Fetch image strictly scoped by owner_id.
        Prevents IDOR: returns None if image belongs to another user.
        """
        return db.query(Image).filter(
            Image.id == image_id,
            Image.owner_id == owner_id
        ).first()

    @staticmethod
    def get_any_by_id(db: Session, image_id: str) -> Optional[Image]:
        """Used ONLY for internal authorization conflict detection."""
        return db.query(Image).filter(Image.id == image_id).first()

    @staticmethod
    def create(
        db: Session,
        owner_id: str,
        storage_key: str,
        original_filename: str,
        mime_type: str,
        file_size: int,
        checksum_sha256: str,
        thumbnail_key: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        metadata_json: Optional[dict[str, Any]] = None,
    ) -> Image:
        image = Image(
            owner_id=owner_id,
            storage_key=storage_key,
            thumbnail_key=thumbnail_key,
            original_filename=original_filename,
            mime_type=mime_type,
            file_size=file_size,
            checksum_sha256=checksum_sha256,
            width=width,
            height=height,
            metadata_json=metadata_json,
        )
        db.add(image)
        db.commit()
        db.refresh(image)
        return image

    @staticmethod
    def list_images(
        db: Session,
        owner_id: str,
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None,
        album_id: Optional[str] = None,
    ) -> Tuple[List[Image], int]:
        """
        Lists user images with pagination and optional search filter.
        Strictly scopes by owner_id.
        """
        query = db.query(Image).filter(Image.owner_id == owner_id)

        if album_id:
            query = query.join(AlbumImage, AlbumImage.image_id == Image.id).filter(
                AlbumImage.album_id == album_id
            )

        if search:
            query = query.filter(Image.original_filename.ilike(f"%{search.strip()}%"))

        total = query.count()
        items = (
            query.order_by(desc(Image.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total

    @staticmethod
    def update_filename(db: Session, image: Image, original_filename: str) -> Image:
        image.original_filename = original_filename.strip()
        db.commit()
        db.refresh(image)
        return image

    @staticmethod
    def delete(db: Session, image: Image) -> None:
        db.delete(image)
        db.commit()

    @staticmethod
    def get_total_storage_bytes(db: Session, owner_id: str) -> int:
        from sqlalchemy import func
        res = db.query(func.sum(Image.file_size)).filter(Image.owner_id == owner_id).scalar()
        return res or 0
