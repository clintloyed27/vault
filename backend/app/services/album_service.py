from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, PermissionDeniedError
from app.core.logging import logger
from app.models.album import Album
from app.models.image import Image
from app.repositories.album_repository import AlbumRepository
from app.repositories.image_repository import ImageRepository


class AlbumService:
    @staticmethod
    def create_album(
        db: Session, owner_id: str, title: str, description: Optional[str] = None
    ) -> Album:
        album = AlbumRepository.create(db, owner_id, title, description)
        logger.info(
            "Album created",
            extra={"event": "album_create", "album_id": album.id, "owner_id": owner_id},
        )
        return album

    @staticmethod
    def get_album(db: Session, album_id: str, owner_id: str) -> Album:
        album = AlbumRepository.get_by_id(db, album_id, owner_id)
        if not album:
            other = AlbumRepository.get_any_by_id(db, album_id)
            if other:
                logger.warning(
                    "Unauthorized cross-user album access attempt",
                    extra={
                        "event": "authz_violation",
                        "album_id": album_id,
                        "attempted_by": owner_id,
                    },
                )
                raise PermissionDeniedError("Access to requested album is forbidden")
            raise NotFoundError("Album not found")
        return album

    @staticmethod
    def list_albums(db: Session, owner_id: str) -> List[Tuple[Album, int]]:
        return AlbumRepository.list_albums(db, owner_id)

    @staticmethod
    def get_album_details(
        db: Session, album_id: str, owner_id: str
    ) -> Tuple[Album, List[Image]]:
        album = AlbumService.get_album(db, album_id, owner_id)
        images = AlbumRepository.get_album_images(db, album_id, owner_id)
        return album, images

    @staticmethod
    def update_album(
        db: Session,
        album_id: str,
        owner_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        cover_image_id: Optional[str] = None,
    ) -> Album:
        album = AlbumService.get_album(db, album_id, owner_id)
        if cover_image_id:
            # Verify cover image belongs to user
            cover = ImageRepository.get_by_id(db, cover_image_id, owner_id)
            if not cover:
                raise PermissionDeniedError("Cover image must belong to the album owner")

        return AlbumRepository.update(
            db, album, title=title, description=description, cover_image_id=cover_image_id
        )

    @staticmethod
    def delete_album(db: Session, album_id: str, owner_id: str) -> None:
        album = AlbumService.get_album(db, album_id, owner_id)
        AlbumRepository.delete(db, album)
        logger.info(
            "Album deleted",
            extra={"event": "album_delete", "album_id": album_id, "owner_id": owner_id},
        )

    @staticmethod
    def add_images_to_album(
        db: Session, album_id: str, owner_id: str, image_ids: List[str]
    ) -> int:
        album = AlbumService.get_album(db, album_id, owner_id)
        added_count = 0
        for image_id in image_ids:
            # Strictly verify image ownership
            img = ImageRepository.get_by_id(db, image_id, owner_id)
            if not img:
                logger.warning(
                    "Attempted to add foreign or nonexistent image to album",
                    extra={
                        "event": "authz_violation",
                        "album_id": album_id,
                        "image_id": image_id,
                        "user_id": owner_id,
                    },
                )
                raise PermissionDeniedError(
                    f"Image {image_id} does not exist or does not belong to you"
                )
            if AlbumRepository.add_image_to_album(db, album.id, img.id):
                added_count += 1

        return added_count

    @staticmethod
    def remove_images_from_album(
        db: Session, album_id: str, owner_id: str, image_ids: List[str]
    ) -> int:
        album = AlbumService.get_album(db, album_id, owner_id)
        removed_count = 0
        for image_id in image_ids:
            if AlbumRepository.remove_image_from_album(db, album.id, image_id):
                removed_count += 1
        return removed_count


album_service = AlbumService()
