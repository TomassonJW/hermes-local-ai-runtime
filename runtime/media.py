"""Resolve job media from volatile upload ids. Never open consumer paths."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

UPLOAD_ID_RE = re.compile(r"^upl_[a-f0-9]{16,32}$")
FORBIDDEN_PATH_KEYS = {"path", "file_path", "filepath", "filename", "file"}
MAX_MEDIA_ITEMS = 4


class InvalidJobInput(ValueError):
    """Caller input is structurally unusable before admission."""


def collect_upload_ids(inp: dict[str, Any]) -> list[str]:
    found: list[str] = []
    raw = inp.get("upload_id")
    if isinstance(raw, str):
        found.append(raw)
    for key in ("images", "pages", "documents"):
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
    for key in ("images", "pages", "documents"):
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
        child.unlink(missing_ok=True)
    job_dir.rmdir()
