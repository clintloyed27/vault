from datetime import datetime, timezone
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AuthenticationError, ConflictError
from app.core.logging import logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    hash_token,
    verify_password,
)
from app.models.user import User
from app.repositories.token_repository import TokenRepository
from app.repositories.user_repository import UserRepository


class AuthService:
    @staticmethod
    def register_user(
        db: Session, email: str, password: str, full_name: Optional[str] = None
    ) -> User:
        existing = UserRepository.get_by_email(db, email)
        if existing:
            raise ConflictError("A user with this email address already exists")

        pw_hash = get_password_hash(password)
        user = UserRepository.create(db, email=email, password_hash=pw_hash, full_name=full_name)
        
        logger.info(
            "User registered successfully",
            extra={"event": "user_register", "user_id": user.id, "email": user.email},
        )
        return user

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> User:
        user = UserRepository.get_by_email(db, email)
        if not user:
            logger.warning(
                "Authentication failed: User not found",
                extra={"event": "auth_failure", "email": email},
            )
            raise AuthenticationError("Incorrect email or password")

        if not verify_password(password, user.password_hash):
            logger.warning(
                "Authentication failed: Invalid password",
                extra={"event": "auth_failure", "email": email, "user_id": user.id},
            )
            raise AuthenticationError("Incorrect email or password")

        if not user.is_active:
            raise AuthenticationError("User account is inactive")

        logger.info(
            "User authenticated successfully",
            extra={"event": "auth_success", "user_id": user.id, "email": user.email},
        )
        return user

    @staticmethod
    def issue_tokens(db: Session, user: User) -> Tuple[str, str, int]:
        """
        Creates short-lived JWT access token and records persistent refresh token.
        Returns: (access_token, raw_refresh_token, expires_in_seconds)
        """
        access_token = create_access_token(subject=user.id)
        raw_refresh, token_hash, expires_at = create_refresh_token(subject=user.id)
        
        TokenRepository.create(db, user_id=user.id, token_hash=token_hash, expires_at=expires_at)
        expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        return access_token, raw_refresh, expires_in

    @staticmethod
    def refresh_access_token(db: Session, raw_refresh_token: str) -> Tuple[str, str, int, User]:
        """Validates refresh token, rotates it, and issues new token pair."""
        token_hash = hash_token(raw_refresh_token)
        stored_token = TokenRepository.get_valid_by_hash(db, token_hash)
        if not stored_token:
            raise AuthenticationError("Invalid or expired refresh token")

        # Invalidate old refresh token (token rotation defense)
        TokenRepository.revoke(db, stored_token)

        user = UserRepository.get_by_id(db, stored_token.user_id)
        if not user or not user.is_active:
            raise AuthenticationError("User is no longer active")

        # Issue new token pair
        new_access_token, new_refresh_token, expires_in = AuthService.issue_tokens(db, user)
        return new_access_token, new_refresh_token, expires_in, user

    @staticmethod
    def revoke_refresh_token(db: Session, raw_refresh_token: str) -> None:
        token_hash = hash_token(raw_refresh_token)
        stored = TokenRepository.get_valid_by_hash(db, token_hash)
        if stored:
            TokenRepository.revoke(db, stored)

    @staticmethod
    def revoke_all_user_sessions(db: Session, user_id: str) -> int:
        return TokenRepository.revoke_all_for_user(db, user_id)


auth_service = AuthService()
