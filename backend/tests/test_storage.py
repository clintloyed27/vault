import tempfile
import pytest
from app.core.exceptions import PermissionDeniedError
from app.storage.local import LocalStorageService


def test_storage_path_traversal_rejection():
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = LocalStorageService(root_dir=tmpdir)

        # Attempt path traversal via user_id
        with pytest.raises(PermissionDeniedError):
            storage.save_file("../malicious", "file.jpg", b"data")

        # Attempt path traversal via file_key
        with pytest.raises(PermissionDeniedError):
            storage.save_file("valid_user", "../../etc/passwd", b"data")


def test_storage_save_and_retrieve():
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = LocalStorageService(root_dir=tmpdir)
        user_id = "user_123"
        file_key = "test_image.jpg"
        payload = b"\x00\x01\x02\x03\x04"

        path = storage.save_file(user_id, file_key, payload)
        assert storage.file_exists(user_id, file_key) is True
        assert storage.get_file_size(user_id, file_key) == 5

        read_bytes = storage.get_file_bytes(user_id, file_key)
        assert read_bytes == payload

        # Delete
        assert storage.delete_file(user_id, file_key) is True
        assert storage.file_exists(user_id, file_key) is False
