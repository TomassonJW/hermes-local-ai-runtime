"""Release checksums, licence inventory and redacted support bundles."""

from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path

from .kit import PINNED_LICENSES

CHECKSUM_FILES = (
    "VERSION",
    "LICENSE",
    "NOTICE",
    "requirements-runtime.txt",
    "requirements-dev.txt",
    "packaging/matrix.yaml",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def write_checksums(root: Path) -> Path:
    lines = []
    for relative in CHECKSUM_FILES:
        digest = sha256_file(root / relative)
        lines.append(f"{digest}  {relative}")
    dest = root / "packaging" / "checksums.sha256"
    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return dest


def verify_checksums(root: Path) -> list[str]:
    listed = {}
    for line in (root / "packaging" / "checksums.sha256").read_text(encoding="utf-8").splitlines():
        digest, _, name = line.partition("  ")
        listed[name] = digest
    errors = []
    for relative in CHECKSUM_FILES:
        actual = sha256_file(root / relative)
        expected = listed.get(relative)
        if expected != actual:
            errors.append(relative)
    return errors


def licence_inventory() -> dict:
    components = [
        {"name": name, "version": version, "license": license_id}
        for name, (version, license_id) in PINNED_LICENSES.items()
    ]
    return {
        "repository": {"name": "hermes-local-ai-runtime", "license": "Apache-2.0"},
        "python_components": components,
        "engines_and_weights": "independent; not granted by this inventory",
        "frontier_parity": False,
        "production_supported": False,
    }


def write_support_bundle(dest: Path, root: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    payload = {
        "os": platform.system(),
        "arch": platform.machine(),
        "python": platform.python_version(),
        "version": (root / "VERSION").read_text(encoding="utf-8").strip(),
        "matrix": (root / "packaging" / "matrix.yaml").read_text(encoding="utf-8"),
        "listen_default": "127.0.0.1",
        "note": "No request payloads, credentials, hostnames or model paths.",
    }
    path = dest / "support-bundle.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path
