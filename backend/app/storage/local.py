import os
from typing import Generator
from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.storage.base import BaseStorageService


class LocalStorageService(BaseStorageService):
    def __init__(self, root_dir: str = "/data/images"):
        self.root_dir = os.path.abspath(root_dir)
        os.makedirs(self.root_dir, exist_ok=True)

    def _get_secure_path(self, user_id: str, file_key: str) -> str:
        # Prevent directory traversal attacks
        if ".." in user_id or ".." in file_key or "/" in file_key or "\\" in file_key:
            raise PermissionDeniedError("Invalid file path or potential directory traversal attack")

        target_dir = os.path.abspath(os.path.join(self.root_dir, user_id))
        target_path = os.path.abspath(os.path.join(target_dir, file_key))

        if not target_path.startswith(self.root_dir):
            raise PermissionDeniedError("Path traversal attack detected")

        return target_path

    def save_file(self, user_id: str, file_key: str, data: bytes) -> str:
        file_path = self._get_secure_path(user_id, file_key)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(data)
        # Non-executable secure permissions
        try:
            os.chmod(file_path, 0o600)
        except Exception:
            pass
        return file_path

    def get_file_bytes(self, user_id: str, file_key: str) -> bytes:
        file_path = self._get_secure_path(user_id, file_key)
        if not os.path.exists(file_path):
            raise NotFoundError("File not found in storage")
        with open(file_path, "rb") as f:
            return f.read()

    def get_file_stream(self, user_id: str, file_key: str) -> Generator[bytes, None, None]:
        file_path = self._get_secure_path(user_id, file_key)
        if not os.path.exists(file_path):
            raise NotFoundError("File not found in storage")

        def iterfile():
            with open(file_path, "rb") as f:
                while chunk := f.read(65536):
                    yield chunk

        return iterfile()

    def delete_file(self, user_id: str, file_key: str) -> bool:
        file_path = self._get_secure_path(user_id, file_key)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False

    def file_exists(self, user_id: str, file_key: str) -> bool:
        file_path = self._get_secure_path(user_id, file_key)
        return os.path.exists(file_path)

    def get_file_size(self, user_id: str, file_key: str) -> int:
        file_path = self._get_secure_path(user_id, file_key)
        if not os.path.exists(file_path):
            raise NotFoundError("File not found in storage")
        return os.path.getsize(file_path)
