"""Object storage abstraction.

Phase 1 ships a local-filesystem implementation. The Storage protocol is the
seam where an S3/R2 backend plugs in later.

# TODO(phase2): add S3Storage implementing the Storage protocol (boto3),
# selected via settings.environment / a STORAGE_BACKEND env var.
"""
import uuid
from pathlib import Path
from typing import Protocol

from app.config import settings


class Storage(Protocol):
    def save(self, data: bytes, ext: str) -> str:
        """Persist bytes and return a storage key (relative path)."""

    def url_for(self, key: str) -> str:
        """Return a URL the frontend can use to fetch the object."""

    def abspath(self, key: str) -> str:
        """Return a local filesystem path for the object (Phase 1 vision read)."""


class LocalStorage:
    """Stores files under settings.storage_path, served via /storage mount."""

    def __init__(self, base_path: str | None = None) -> None:
        self.base = Path(base_path or settings.storage_path)
        self.base.mkdir(parents=True, exist_ok=True)

    def save(self, data: bytes, ext: str) -> str:
        ext = ext.lstrip(".").lower()
        key = f"{uuid.uuid4().hex}.{ext}"
        (self.base / key).write_bytes(data)
        return key

    def url_for(self, key: str) -> str:
        # Matches the StaticFiles mount in app.main ("/storage").
        return f"/storage/{key}"

    def abspath(self, key: str) -> str:
        return str(self.base / key)


def get_storage() -> Storage:
    return LocalStorage()
