from fastapi import APIRouter, Cookie, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.exceptions import AuthenticationError
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshTokenRequest, TokenResponse
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import auth_service

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    """Register a new private user account."""
    user = auth_service.register_user(
        db=db,
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
    )
    return user


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    """Authenticate with email and password, issuing access token and secure refresh cookie."""
    user = auth_service.authenticate_user(db=db, email=payload.email, password=payload.password)
    access_token, raw_refresh, expires_in = auth_service.issue_tokens(db=db, user=user)

    # Set secure HTTPOnly refresh cookie
    response.set_cookie(
        key="vault_refresh_token",
        value=raw_refresh,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/api/v1/auth",
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
        user={
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
        },
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    response: Response,
    payload: RefreshTokenRequest = None,
    vault_refresh_token: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    """Refresh short-lived access token using secure refresh cookie or payload."""
    raw_token = (payload.refresh_token if payload else None) or vault_refresh_token
    if not raw_token:
        raise AuthenticationError("No refresh token provided")

    new_access, new_refresh, expires_in, user = auth_service.refresh_access_token(
        db=db, raw_refresh_token=raw_token
    )

    response.set_cookie(
        key="vault_refresh_token",
        value=new_refresh,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/api/v1/auth",
    )

    return TokenResponse(
        access_token=new_access,
        token_type="bearer",
        expires_in=expires_in,
        user={
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
        },
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(
    response: Response,
    vault_refresh_token: str | None = Cookie(None),
    db: Session = Depends(get_db),
):
    """Log out by invalidating active refresh token and clearing cookie."""
    if vault_refresh_token:
        auth_service.revoke_refresh_token(db=db, raw_refresh_token=vault_refresh_token)

    response.delete_cookie(key="vault_refresh_token", path="/api/v1/auth")
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Retrieve profile of authenticated user derived directly from token."""
    return current_user
