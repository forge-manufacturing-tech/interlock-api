# Storage Package

Abstract blob storage provider for Interlock.

## Usage

```python
from storage import get_storage_provider

storage = get_storage_provider()
storage.upload_file("path/to/file.txt", data, content_type="text/plain")
```

## Configuration

Set the following environment variables:
- `STORAGE_PROVIDER`: "gcs" (default)
- `GCS_BUCKET_NAME`: The name of the GCS bucket.
