from __future__ import annotations

import datetime
from typing import BinaryIO

from google.cloud import storage

from .base import StorageProvider


class GCSStorageProvider(StorageProvider):
    def __init__(self, bucket_name: str):
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)

    def upload_file(self, file_path: str, data: BinaryIO, content_type: str | None = None) -> str:
        blob = self.bucket.blob(file_path)
        blob.upload_from_file(data, content_type=content_type)
        return file_path

    def download_file(self, file_path: str) -> bytes:
        blob = self.bucket.blob(file_path)
        return blob.download_as_bytes()

    def get_signed_url(self, file_path: str, expiration: int = 3600) -> str:
        import os

        blob = self.bucket.blob(file_path)

        kwargs = {
            "version": "v4",
            "expiration": datetime.timedelta(seconds=expiration),
            "method": "GET",
        }

        sa_email = os.environ.get("SERVICE_ACCOUNT_EMAIL")
        if sa_email:
            import google.auth
            from google.auth.transport.requests import Request

            # Fetch local ADC tokens
            credentials, _ = google.auth.default()
            credentials.refresh(Request())

            kwargs["service_account_email"] = sa_email
            kwargs["access_token"] = credentials.token

        return blob.generate_signed_url(**kwargs)

    def delete_file(self, file_path: str) -> None:
        blob = self.bucket.blob(file_path)
        blob.delete()
