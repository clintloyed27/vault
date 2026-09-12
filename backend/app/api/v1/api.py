from fastapi import APIRouter

from app.api.v1.albums import router as albums_router
from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.api.v1.images import router as images_router
from app.api.v1.users import router as users_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["Health"])
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(images_router, prefix="/images", tags=["Images"])
api_router.include_router(albums_router, prefix="/albums", tags=["Albums"])
api_router.include_router(users_router, prefix="/users", tags=["Users"])
