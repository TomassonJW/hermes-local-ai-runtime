"""Resolve job media from volatile upload ids. Never open consumer paths."""

from __future__ import annotations

import re
import threading
import time
from pathlib import Path
from typing import Any, Iterator

UPLOAD_ID_RE = re.compile(r"^upl_[a-f0-9]{16,32}$")
FORBIDDEN_PATH_KEYS = {"path", "file_path", "filepath", "filename", "file"}
MAX_MEDIA_ITEMS = 4
UPLOAD_TTL_SECONDS = 900.0


class InvalidJobInput(ValueError):
    """Caller input is structurally unusable before admission."""


class UploadStore:
    """Volatile, bounded, self-expiring media store.

    Uploads are transient job inputs, never durable consumer data. An entry
    that is never claimed by a job used to occupy a slot until process exit,
    which starved the store and made every media capability fail with
    QUEUE_FULL. Entries therefore expire on a TTL and the oldest entry is
    evicted when the store is at capacity, so a stale upload can never block
    a live request. Reuse across jobs stays possible inside the TTL.

    Exposes the read-only mapping surface the coordinator relies on
    (``in``, ``[]``, ``len``) so it substitutes for the previous plain dict.
    """

    def __init__(
        self,
        *,
        max_items: int = 8,
        max_bytes: int = 40 * 1024 * 1024,
        ttl_seconds: float = UPLOAD_TTL_SECONDS,
    ) -> None:
        self._max_items = max_items
        self._max_bytes = max_bytes
        self._ttl = ttl_seconds
        self._lock = threading.Lock()
        self._blobs: dict[str, bytes] = {}
        self._deadlines: dict[str, float] = {}
        self._pins: dict[str, int] = {}

    def _purge_expired_locked(self, now: float) -> None:
        expired = [
            key
            for key, deadline in self._deadlines.items()
            if deadline <= now and not self._pins.get(key)
        ]
        for key in expired:
            self._blobs.pop(key, None)
            self._deadlines.pop(key, None)

    def _evict_oldest_locked(self) -> bool:
        candidates = {
            key: deadline
            for key, deadline in self._deadlines.items()
            if not self._pins.get(key)
        }
        if not candidates:
            return False
        oldest = min(candidates, key=candidates.__getitem__)
        self._blobs.pop(oldest, None)
        self._deadlines.pop(oldest, None)
        return True

    def pin(self, upload_ids: list[str]) -> None:
        """Protect ids an accepted job still needs from TTL and eviction."""
        with self._lock:
            for upload_id in upload_ids:
                self._pins[upload_id] = self._pins.get(upload_id, 0) + 1

    def unpin(self, upload_ids: list[str]) -> None:
        """Release the protection once a job reached a terminal state. The
        blob stays available for reuse until its TTL or an eviction."""
        with self._lock:
            for upload_id in upload_ids:
                remaining = self._pins.get(upload_id, 0) - 1
                if remaining > 0:
                    self._pins[upload_id] = remaining
                else:
                    self._pins.pop(upload_id, None)

    def put(self, upload_id: str, blob: bytes) -> bool:
        """Store one upload. Returns False only when the blob alone exceeds
        the whole byte budget, which no amount of eviction can fix."""
        size = len(blob)
        if size > self._max_bytes:
            return False
        now = time.monotonic()
        with self._lock:
            self._purge_expired_locked(now)
            while (
                len(self._blobs) >= self._max_items
                or sum(map(len, self._blobs.values())) + size > self._max_bytes
            ):
                if not self._evict_oldest_locked():
                    break
            self._blobs[upload_id] = blob
            self._deadlines[upload_id] = now + self._ttl
        return True

    def discard(self, upload_ids: list[str]) -> None:
        """Release ids a terminal job no longer needs."""
        with self._lock:
            for upload_id in upload_ids:
                self._blobs.pop(upload_id, None)
                self._deadlines.pop(upload_id, None)

    def clear(self) -> None:
        with self._lock:
            self._blobs.clear()
            self._deadlines.clear()
            self._pins.clear()

    def stats(self) -> dict[str, int]:
        now = time.monotonic()
        with self._lock:
            self._purge_expired_locked(now)
            return {
                "items": len(self._blobs),
                "bytes": sum(map(len, self._blobs.values())),
                "max_items": self._max_items,
                "max_bytes": self._max_bytes,
            }

    def __contains__(self, upload_id: object) -> bool:
        now = time.monotonic()
        with self._lock:
            self._purge_expired_locked(now)
            return upload_id in self._blobs

    def __getitem__(self, upload_id: str) -> bytes:
        now = time.monotonic()
        with self._lock:
            self._purge_expired_locked(now)
            return self._blobs[upload_id]

    def __len__(self) -> int:
        now = time.monotonic()
        with self._lock:
            self._purge_expired_locked(now)
            return len(self._blobs)

    def __iter__(self) -> Iterator[str]:
        with self._lock:
            return iter(list(self._blobs))


def collect_upload_ids(inp: dict[str, Any]) -> list[str]:
    found: list[str] = []
    raw = inp.get("upload_id")
    if isinstance(raw, str):
        found.append(raw)
    for key in ("images", "pages", "documents", "audio"):
        items = inp.get(key)
        if not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, dict) and isinstance(item.get("upload_id"), str):
                found.append(item["upload_id"])
    unique: list[str] = []
    seen: set[str] = set()
    for upload_id in found:
        if upload_id not in seen:
            unique.append(upload_id)
            seen.add(upload_id)
    return unique


def reject_path_keys(inp: dict[str, Any]) -> None:
    extra = FORBIDDEN_PATH_KEYS.intersection(inp)
    if extra:
        raise InvalidJobInput("filesystem paths are not accepted as job input")
    for key in ("images", "pages", "documents", "audio"):
        items = inp.get(key)
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict) and FORBIDDEN_PATH_KEYS.intersection(item):
                    raise InvalidJobInput("filesystem paths are not accepted as job input")


def validate_upload_ids(
    ids: list[str],
    media_store: dict[str, bytes] | None,
) -> None:
    if len(ids) > MAX_MEDIA_ITEMS:
        raise InvalidJobInput(f"at most {MAX_MEDIA_ITEMS} media items are accepted")
    store = media_store or {}
    for upload_id in ids:
        if not UPLOAD_ID_RE.match(upload_id):
            raise InvalidJobInput("upload_id is malformed")
        if upload_id not in store:
            raise InvalidJobInput("unknown upload_id")


def materialize(
    job_id: str,
    ids: list[str],
    media_store: dict[str, bytes],
    root: Path,
) -> list[dict[str, str]]:
    job_dir = root / job_id
    job_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    files: list[dict[str, str]] = []
    for upload_id in ids:
        blob = media_store[upload_id]
        path = job_dir / upload_id
        path.write_bytes(blob)
        path.chmod(0o600)
        files.append({"upload_id": upload_id, "path": str(path)})
    return files


def cleanup(job_id: str, root: Path) -> None:
    job_dir = root / job_id
    if not job_dir.is_dir():
        return
    for child in job_dir.iterdir():
        if child.is_dir():
            for nested in child.iterdir():
                nested.unlink(missing_ok=True)
            child.rmdir()
        else:
            child.unlink(missing_ok=True)
    job_dir.rmdir()
