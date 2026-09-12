from fastapi import APIRouter, Depends, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.exceptions import AuthenticationError
from app.core.security import get_password_hash, verify_password
from app.db.session import get_db
from app.models.album import Album
from app.models.image import Image
from app.models.user import User
from app.repositories.image_repository import ImageRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserPasswordUpdate, UserResponse, UserUpdate

router = APIRouter()


@router.patch("/me", response_model=UserResponse)
def update_profile(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update user profile metadata."""
    updated = UserRepository.update(db, current_user, full_name=payload.full_name)
    return updated


@router.post("/me/password", status_code=status.HTTP_200_OK)
def change_password(
    payload: UserPasswordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update account password after verifying current password."""
    if not verify_password(payload.current_password, current_user.password_hash):
        raise AuthenticationError("Current password does not match")

    new_hash = get_password_hash(payload.new_password)
    UserRepository.update(db, current_user, password_hash=new_hash)
    return {"message": "Password updated successfully"}


@router.get("/me/stats")
def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns storage usage and resource counts strictly for the authenticated tenant."""
    total_bytes = ImageRepository.get_total_storage_bytes(db, current_user.id)
    image_count = db.query(Image).filter(Image.owner_id == current_user.id).count()
    album_count = db.query(Album).filter(Album.owner_id == current_user.id).count()

    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "storage_used_bytes": total_bytes,
        "storage_used_mb": round(total_bytes / (1024 * 1024), 2),
        "total_images": image_count,
        "total_albums": album_count,
    }
