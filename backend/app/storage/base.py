import abc
from typing import Generator


class BaseStorageService(abc.ABC):
    @abc.abstractmethod
    def save_file(self, user_id: str, file_key: str, data: bytes) -> str:
        pass

    @abc.abstractmethod
    def get_file_bytes(self, user_id: str, file_key: str) -> bytes:
        pass

    @abc.abstractmethod
    def get_file_stream(self, user_id: str, file_key: str) -> Generator[bytes, None, None]:
        pass

    @abc.abstractmethod
    def delete_file(self, user_id: str, file_key: str) -> bool:
        pass

    @abc.abstractmethod
    def file_exists(self, user_id: str, file_key: str) -> bool:
        pass

    @abc.abstractmethod
    def get_file_size(self, user_id: str, file_key: str) -> int:
        pass
