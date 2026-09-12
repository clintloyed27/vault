from typing import List, Optional, Tuple
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models.album import Album, AlbumImage
from app.models.image import Image


class AlbumRepository:
    @staticmethod
    def get_by_id(db: Session, album_id: str, owner_id: str) -> Optional[Album]:
        """Fetch album strictly scoped by owner_id."""
        return db.query(Album).filter(
            Album.id == album_id,
            Album.owner_id == owner_id
        ).first()

    @staticmethod
    def get_any_by_id(db: Session, album_id: str) -> Optional[Album]:
        """Internal lookup for authorization checks."""
        return db.query(Album).filter(Album.id == album_id).first()

    @staticmethod
    def list_albums(db: Session, owner_id: str) -> List[Tuple[Album, int]]:
        """Returns list of (Album, image_count) strictly for owner_id."""
        results = (
            db.query(Album, func.count(AlbumImage.image_id).label("image_count"))
            .outerjoin(AlbumImage, AlbumImage.album_id == Album.id)
            .filter(Album.owner_id == owner_id)
            .group_by(Album.id)
            .order_by(desc(Album.created_at))
            .all()
        )
        return results

    @staticmethod
    def create(db: Session, owner_id: str, title: str, description: Optional[str] = None) -> Album:
        album = Album(
            owner_id=owner_id,
            title=title.strip(),
            description=description.strip() if description else None,
        )
        db.add(album)
        db.commit()
        db.refresh(album)
        return album

    @staticmethod
    def update(
        db: Session,
        album: Album,
        title: Optional[str] = None,
        description: Optional[str] = None,
        cover_image_id: Optional[str] = None
    ) -> Album:
        if title is not None:
            album.title = title.strip()
        if description is not None:
            album.description = description.strip() if description else None
        if cover_image_id is not None:
            album.cover_image_id = cover_image_id
        db.commit()
        db.refresh(album)
        return album

    @staticmethod
    def delete(db: Session, album: Album) -> None:
        db.delete(album)
        db.commit()

    @staticmethod
    def add_image_to_album(db: Session, album_id: str, image_id: str) -> bool:
        exists = db.query(AlbumImage).filter(
            AlbumImage.album_id == album_id,
            AlbumImage.image_id == image_id
        ).first()
        if not exists:
            link = AlbumImage(album_id=album_id, image_id=image_id)
            db.add(link)
            db.commit()
            return True
        return False

    @staticmethod
    def remove_image_from_album(db: Session, album_id: str, image_id: str) -> bool:
        link = db.query(AlbumImage).filter(
            AlbumImage.album_id == album_id,
            AlbumImage.image_id == image_id
        ).first()
        if link:
            db.delete(link)
            db.commit()
            return True
        return False

    @staticmethod
    def get_album_images(db: Session, album_id: str, owner_id: str) -> List[Image]:
        """Fetch all images in an album, scoped by owner_id."""
        return (
            db.query(Image)
            .join(AlbumImage, AlbumImage.image_id == Image.id)
            .filter(
                AlbumImage.album_id == album_id,
                Image.owner_id == owner_id
            )
            .order_by(desc(AlbumImage.added_at))
            .all()
        )
