from app.core.config import settings
from app.storage.base import BaseStorageService
from app.storage.local import LocalStorageService

_storage_instance: BaseStorageService | None = None


def get_storage_service() -> BaseStorageService:
    global _storage_instance
    if _storage_instance is None:
        if settings.STORAGE_TYPE.lower() == "local":
            _storage_instance = LocalStorageService(root_dir=settings.STORAGE_LOCAL_ROOT)
        else:
            _storage_instance = LocalStorageService(root_dir=settings.STORAGE_LOCAL_ROOT)
    return _storage_instance
