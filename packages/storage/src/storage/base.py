from __future__ import annotations

from abc import ABC, abstractmethod
from typing import BinaryIO


class StorageProvider(ABC):
    @abstractmethod
    def upload_file(self, file_path: str, data: BinaryIO, content_type: str | None = None) -> str:
        """Uploads a file and returns the storage path."""
        pass

    @abstractmethod
    def download_file(self, file_path: str) -> bytes:
        """Downloads a file."""
        pass

    @abstractmethod
    def get_signed_url(self, file_path: str, expiration: int = 3600) -> str:
        """Generates a signed URL for a file."""
        pass

    @abstractmethod
    def delete_file(self, file_path: str) -> None:
        """Deletes a file."""
        pass
