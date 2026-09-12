from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from app.models.refresh_token import RefreshToken


class TokenRepository:
    @staticmethod
    def create(db: Session, user_id: str, token_hash: str, expires_at: datetime) -> RefreshToken:
        token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            is_revoked=False,
        )
        db.add(token)
        db.commit()
        db.refresh(token)
        return token

    @staticmethod
    def get_valid_by_hash(db: Session, token_hash: str) -> Optional[RefreshToken]:
        now = datetime.now(timezone.utc)
        return db.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.is_revoked == False,
            RefreshToken.expires_at > now
        ).first()

    @staticmethod
    def revoke(db: Session, token: RefreshToken) -> None:
        token.is_revoked = True
        db.commit()

    @staticmethod
    def revoke_all_for_user(db: Session, user_id: str) -> int:
        count = (
            db.query(RefreshToken)
            .filter(RefreshToken.user_id == user_id, RefreshToken.is_revoked == False)
            .update({"is_revoked": True})
        )
        db.commit()
        return count
