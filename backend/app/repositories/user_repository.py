from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User


class UserRepository:
    @staticmethod
    def get_by_id(db: Session, user_id: str) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email.lower().strip()).first()

    @staticmethod
    def create(db: Session, email: str, password_hash: str, full_name: Optional[str] = None) -> User:
        user = User(
            email=email.lower().strip(),
            password_hash=password_hash,
            full_name=full_name,
            is_active=True,
            is_superuser=False,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update(db: Session, user: User, full_name: Optional[str] = None, password_hash: Optional[str] = None) -> User:
        if full_name is not None:
            user.full_name = full_name
        if password_hash is not None:
            user.password_hash = password_hash
        db.commit()
        db.refresh(user)
        return user
