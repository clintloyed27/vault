import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.db.session import Base


class Album(Base):
    __tablename__ = "albums"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    cover_image_id = Column(String(36), ForeignKey("images.id", ondelete="SET NULL"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    owner = relationship("User", back_populates="albums")
    cover_image = relationship("Image", foreign_keys=[cover_image_id])
    album_images = relationship("AlbumImage", back_populates="album", cascade="all, delete-orphan")


class AlbumImage(Base):
    __tablename__ = "album_images"

    album_id = Column(String(36), ForeignKey("albums.id", ondelete="CASCADE"), primary_key=True)
    image_id = Column(String(36), ForeignKey("images.id", ondelete="CASCADE"), primary_key=True)
    added_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    album = relationship("Album", back_populates="album_images")
    image = relationship("Image", back_populates="albums")
