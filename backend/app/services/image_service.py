import mimetypes
import uuid
from typing import Any, Generator, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.core.logging import logger
from app.models.image import Image
from app.repositories.image_repository import ImageRepository
from app.services.image_validation import (
    inspect_and_process_image,
    sanitize_filename,
)
from app.storage import get_storage_service


class ImageService:
    def __init__(self):
        self.storage = get_storage_service()

    def upload_image(
        self,
        db: Session,
        owner_id: str,
        file_bytes: bytes,
        original_filename: str,
    ) -> Image:
        clean_filename = sanitize_filename(original_filename)

        # Validate, inspect magic bytes, strip EXIF, generate thumbnail
        (
            sanitized_bytes,
            thumb_bytes,
            width,
            height,
            mime_type,
            checksum,
            metadata,
        ) = inspect_and_process_image(file_bytes, clean_filename)

        # Generate unique storage keys (isolated UUIDs, not user-controllable paths)
        ext = mimetypes.guess_extension(mime_type) or ".img"
        if ext == ".jpe":
            ext = ".jpg"

        storage_uuid = str(uuid.uuid4())
        storage_key = f"{storage_uuid}{ext}"
        thumb_key = f"{storage_uuid}_thumb.webp"

        # Save to persistent storage layer under user directory
        self.storage.save_file(owner_id, storage_key, sanitized_bytes)
        self.storage.save_file(owner_id, thumb_key, thumb_bytes)

        # Record metadata in database
        image = ImageRepository.create(
            db=db,
            owner_id=owner_id,
            storage_key=storage_key,
            thumbnail_key=thumb_key,
            original_filename=clean_filename,
            mime_type=mime_type,
            file_size=len(sanitized_bytes),
            checksum_sha256=checksum,
            width=width,
            height=height,
            metadata_json=metadata,
        )

        logger.info(
            "Image uploaded successfully",
            extra={
                "event": "image_upload",
                "image_id": image.id,
                "owner_id": owner_id,
                "file_size": image.file_size,
                "mime_type": mime_type,
            },
        )
        return image

    def get_image(self, db: Session, image_id: str, owner_id: str) -> Image:
        image = ImageRepository.get_by_id(db, image_id, owner_id)
        if not image:
            # Check if image exists for another user to audit authorization failure
            other = ImageRepository.get_any_by_id(db, image_id)
            if other:
                logger.warning(
                    "Unauthorized cross-user image access attempt",
                    extra={
                        "event": "authz_violation",
                        "image_id": image_id,
                        "attempted_by": owner_id,
                        "actual_owner": other.owner_id,
                    },
                )
                raise PermissionDeniedError("Access to requested resource is forbidden")
            raise NotFoundError("Image not found")
        return image

    def get_image_stream(
        self, db: Session, image_id: str, owner_id: str
    ) -> Tuple[Generator[bytes, None, None], Image]:
        image = self.get_image(db, image_id, owner_id)
        stream = self.storage.get_file_stream(owner_id, image.storage_key)
        return stream, image

    def get_thumbnail_stream(
        self, db: Session, image_id: str, owner_id: str
    ) -> Tuple[Generator[bytes, None, None], str]:
        image = self.get_image(db, image_id, owner_id)
        if not image.thumbnail_key or not self.storage.file_exists(owner_id, image.thumbnail_key):
            # Fallback to main image
            stream = self.storage.get_file_stream(owner_id, image.storage_key)
            return stream, image.mime_type
        
        stream = self.storage.get_file_stream(owner_id, image.thumbnail_key)
        return stream, "image/webp"

    def delete_image(self, db: Session, image_id: str, owner_id: str) -> None:
        image = self.get_image(db, image_id, owner_id)

        # Delete physical files from storage
        self.storage.delete_file(owner_id, image.storage_key)
        if image.thumbnail_key:
            self.storage.delete_file(owner_id, image.thumbnail_key)

        # Delete record from database
        ImageRepository.delete(db, image)

        logger.info(
            "Image deleted successfully",
            extra={
                "event": "image_delete",
                "image_id": image_id,
                "owner_id": owner_id,
            },
        )

    def list_images(
        self,
        db: Session,
        owner_id: str,
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None,
        album_id: Optional[str] = None,
    ) -> Tuple[List[Image], int]:
        return ImageRepository.list_images(
            db=db,
            owner_id=owner_id,
            page=page,
            page_size=page_size,
            search=search,
            album_id=album_id,
        )

    def update_filename(
        self, db: Session, image_id: str, owner_id: str, new_filename: str
    ) -> Image:
        image = self.get_image(db, image_id, owner_id)
        clean_filename = sanitize_filename(new_filename)
        return ImageRepository.update_filename(db, image, clean_filename)


image_service = ImageService()
