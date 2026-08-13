"""
Evidence file storage abstraction.

Development: local secure directory (gitignored).
Production: S3-compatible object storage (S3 API clients may be added when
credentials are configured; the interface below is storage-agnostic).

The backend returns evidence IDs and metadata, never raw filesystem paths.
"""

import shutil
from pathlib import Path

from app.core.config import settings
from app.core.exceptions import StorageError
from app.core.logging import get_logger

logger = get_logger("storage")


class StorageProvider:
    """Minimal storage interface: put/get/delete by key."""

    def put(self, key: str, source_path: str) -> None: ...

    def get(self, key: str, dest_path: str) -> bool: ...

    def delete(self, key: str) -> None: ...

    def exists(self, key: str) -> bool: ...


class LocalStorage(StorageProvider):
    """Local-directory storage for development."""

    def __init__(self, base_dir: str | None = None) -> None:
        self._root = Path(base_dir or settings.LOCAL_STORAGE_DIR).resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, key: str) -> Path:
        # Reject path traversal attempts.
        if ".." in key.split("/") or key.startswith("/") or ":" in key:
            raise StorageError(f"Invalid storage key: {key!r}")
        path = (self._root / key).resolve()
        if not str(path).startswith(str(self._root)):
            raise StorageError(f"Storage key escapes root: {key!r}")
        return path

    def put(self, key: str, source_path: str) -> None:
        dest = self._resolve(key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(source_path, dest)
        except OSError as exc:
            raise StorageError(f"Failed to store file {key}: {exc}")

    def get(self, key: str, dest_path: str) -> bool:
        src = self._resolve(key)
        if not src.exists():
            return False
        try:
            shutil.copy2(src, dest_path)
            return True
        except OSError as exc:
            raise StorageError(f"Failed to retrieve file {key}: {exc}")

    def delete(self, key: str) -> None:
        path = self._resolve(key)
        if path.exists():
            path.unlink(missing_ok=True)

    def exists(self, key: str) -> bool:
        return self._resolve(key).exists()


# Future: S3Storage(StorageProvider) using boto3/minio, activated when
# STORAGE_ENDPOINT is configured.


def get_storage() -> StorageProvider:
    """Return the active storage provider instance."""
    if settings.STORAGE_ENDPOINT:
        # Placeholder: swap to S3 client when credentials are configured.
        logger.warning("STORAGE_ENDPOINT set but S3 storage not yet enabled; using local storage.")
        return _local_storage()
    return _local_storage()


_local: LocalStorage | None = None


def _local_storage() -> LocalStorage:
    global _local
    if _local is None:
        _local = LocalStorage()
    return _local