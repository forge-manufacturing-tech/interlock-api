from __future__ import annotations

import os

from .base import StorageProvider


def get_storage_provider() -> StorageProvider:
    provider_type = os.environ.get("STORAGE_PROVIDER", "gcs").lower()

    if provider_type == "gcs":
        from .gcs import GCSStorageProvider

        bucket_name = os.environ.get("GCS_BUCKET_NAME")
        if not bucket_name:
            raise ValueError("GCS_BUCKET_NAME environment variable is required for GCS storage provider")
        return GCSStorageProvider(bucket_name)

    # Add other providers here (e.g., S3)
    raise ValueError(f"Unsupported storage provider type: {provider_type}")


__all__ = ["StorageProvider", "get_storage_provider"]
