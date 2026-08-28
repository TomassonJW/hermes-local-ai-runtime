"""Prefix installer, model store, notices, SBOM, backup and rollback."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import time
from pathlib import Path
from typing import Any

import yaml

MANIFEST_NAME = "INSTALL-MANIFEST.json"
DEFAULT_LISTEN_HOST = "127.0.0.1"
DEFAULT_LISTEN_PORT = 8850
DEFAULT_QUOTA_BYTES = 30 * 1024 * 1024 * 1024
FORBIDDEN_PREFIXES = (
    "/etc/pve",
    "/var/lib/pve",
    "/var/lib/vz",
    "/usr",
    "/bin",
    "/sbin",
    "/lib",
    "/lib64",
    "/boot",
    "/root",
)

PINNED_LICENSES = {
    "fastapi": ("0.129.0", "MIT"),
    "uvicorn": ("0.41.0", "BSD-3-Clause"),
    "pydantic": ("2.12.5", "MIT"),
    "httpx": ("0.28.1", "BSD-3-Clause"),
    "PyYAML": ("6.0.3", "MIT"),
    "jsonschema": ("4.25.1", "MIT"),
    "pytest": ("8.4.2", "MIT"),
    "pillow": ("11.3.0", "HPND"),
    "python-multipart": ("0.0.32", "Apache-2.0"),
}

COPY_TREES = ("runtime", "contracts", "schemas")
COPY_FILES = (
    "LICENSE",
    "NOTICE",
    "VERSION",
    "requirements-runtime.txt",
    "requirements-dev.txt",
)


class InstallError(RuntimeError):
    pass


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve(prefix: Path) -> Path:
    return prefix.expanduser().resolve()


def assert_allowed_prefix(prefix: Path) -> Path:
    target = _resolve(prefix)
    text = str(target)
    for forbidden in FORBIDDEN_PREFIXES:
        if text == forbidden or text.startswith(forbidden + "/"):
            raise InstallError(f"forbidden install prefix: {target}")
    return target


def _layout(prefix: Path) -> dict[str, Path]:
    return {
        "etc": prefix / "etc",
        "lib": prefix / "lib",
        "share": prefix / "share",
        "var_lib": prefix / "var" / "lib",
        "models": prefix / "var" / "models",
        "backups": prefix / "var" / "backups",
        "log": prefix / "var" / "log",
        "tmp": prefix / "var" / "tmp",
        "notices": prefix / "share" / "notices",
        "sbom": prefix / "share" / "sbom",
        "systemd": prefix / "share" / "systemd",
    }


def plan(
    source_root: Path,
    prefix: Path,
    listen_host: str = DEFAULT_LISTEN_HOST,
    listen_port: int = DEFAULT_LISTEN_PORT,
    model_store_quota_bytes: int = DEFAULT_QUOTA_BYTES,
) -> dict[str, Any]:
    source_root = source_root.resolve()
    return {
        "source_root": str(source_root),
        "prefix": str(_resolve(prefix) if prefix.exists() else prefix),
        "listen_host": listen_host,
        "listen_port": listen_port,
        "enable_service": False,
        "download_models": False,
        "model_store_quota_bytes": model_store_quota_bytes,
        "forbidden_prefixes": list(FORBIDDEN_PREFIXES),
        "owned_trees": ["etc", "lib", "share", "var"],
        "rollback": "installkit backup then uninstall --keep-models",
    }


def _write_runtime_yaml(path: Path, source_root: Path, prefix: Path, host: str, port: int) -> None:
    if host not in {"127.0.0.1", "::1"}:
        raise InstallError("only loopback listen is permitted")
    example = source_root / "config" / "g05-runtime.example.yaml"
    raw = yaml.safe_load(example.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise InstallError("example runtime config is invalid")
    raw["listen"] = {"host": host, "port": port}
    raw["db_path"] = str(prefix / "var" / "lib" / "runtime.db")
    raw["dev_mode"] = False
    path.write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")
    path.chmod(0o600)


def _write_unit(path: Path, prefix: Path, host: str, port: int) -> None:
    python = shutil.which("python3") or "/usr/bin/python3"
    body = f"""[Unit]
Description=Hermes Local AI Runtime (user, loopback)
After=network.target
ConditionPathExists={prefix}/INSTALL-MANIFEST.json

[Service]
Type=simple
WorkingDirectory={prefix}
Environment=PYTHONPATH={prefix}/lib
Environment=HLAIR_PREFIX={prefix}
ExecStart={python} -m uvicorn runtime.app:app --app-dir {prefix}/lib --host {host} --port {port}
Restart=on-failure
MemoryMax=10G
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ReadWritePaths={prefix}/var {prefix}/etc
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6

[Install]
WantedBy=default.target
"""
    path.write_text(body, encoding="utf-8")


def _write_notices(dest: Path, source_root: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_root / "NOTICE", dest / "NOTICE")
    shutil.copy2(source_root / "LICENSE", dest / "LICENSE")
    lines = [
        "Third-party Python pins copied with this installation.",
        "Engine/model licences are independent and are not granted by this list.",
        "",
    ]
    for name, (version, license_id) in PINNED_LICENSES.items():
        lines.append(f"{name}=={version}  {license_id}")
    lines.append("")
    lines.append("Original runtime code: Apache-2.0")
    (dest / "THIRD-PARTY.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_sbom(dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    components = []
    for name, (version, license_id) in PINNED_LICENSES.items():
        components.append(
            {
                "type": "library",
                "name": name,
                "version": version,
                "licenses": [{"license": {"id": license_id}}],
            }
        )
    payload = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "components": components,
    }
    (dest / "sbom.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _copy_payload(source_root: Path, lib: Path) -> list[str]:
    owned: list[str] = []
    for tree in COPY_TREES:
        src = source_root / tree
        dst = lib / tree
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        owned.append(str(dst))
    for name in COPY_FILES:
        src = source_root / name
        if not src.is_file():
            continue
        dst = lib / name
        shutil.copy2(src, dst)
        owned.append(str(dst))
    return owned


def _checksums(prefix: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for path in sorted(prefix.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(prefix).as_posix()
        if rel.startswith("var/models/blobs/") or rel.startswith("var/backups/"):
            continue
        out[rel] = _sha256_file(path)
    return out


def _write_manifest(prefix: Path, payload: dict[str, Any]) -> dict[str, Any]:
    payload["checksums"] = _checksums(prefix)
    path = prefix / MANIFEST_NAME
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def load_manifest(prefix: Path) -> dict[str, Any]:
    path = _resolve(prefix) / MANIFEST_NAME
    if not path.is_file():
        raise InstallError(f"missing {MANIFEST_NAME}")
    return json.loads(path.read_text(encoding="utf-8"))


def install(
    source_root: Path,
    prefix: Path,
    listen_host: str = DEFAULT_LISTEN_HOST,
    listen_port: int = DEFAULT_LISTEN_PORT,
    model_store_quota_bytes: int = DEFAULT_QUOTA_BYTES,
    enable_service: bool = False,
) -> dict[str, Any]:
    if enable_service:
        raise InstallError("refusing to enable a systemd service without an explicit later decision")
    if listen_host not in {"127.0.0.1", "::1"}:
        raise InstallError("only loopback listen is permitted")
    source_root = source_root.resolve()
    prefix = assert_allowed_prefix(prefix)
    layout = _layout(prefix)
    for path in layout.values():
        path.mkdir(parents=True, exist_ok=True)
    for sub in ("blobs/sha256", "manifests", "aliases", "staging", "quarantine", "notices"):
        (layout["models"] / sub).mkdir(parents=True, exist_ok=True)
    owned = _copy_payload(source_root, layout["lib"])
    _write_runtime_yaml(
        layout["etc"] / "runtime.yaml",
        source_root,
        prefix,
        listen_host,
        listen_port,
    )
    _write_notices(layout["notices"], source_root)
    _write_sbom(layout["sbom"])
    _write_unit(
        layout["systemd"] / "hermes-local-ai-runtime.user.service",
        prefix,
        listen_host,
        listen_port,
    )
    store_meta = {
        "quota_bytes": model_store_quota_bytes,
        "download_models": False,
    }
    (layout["models"] / "STORE.json").write_text(
        json.dumps(store_meta, indent=2) + "\n", encoding="utf-8"
    )
    version = (source_root / "VERSION").read_text(encoding="utf-8").strip()
    manifest = {
        "product": "hermes-local-ai-runtime",
        "version": version,
        "source_root": str(source_root),
        "prefix": str(prefix),
        "listen_host": listen_host,
        "listen_port": listen_port,
        "service_enabled": False,
        "download_models": False,
        "model_store_quota_bytes": model_store_quota_bytes,
        "owned_paths": owned + [str(layout["etc"]), str(layout["share"]), str(layout["var_lib"])],
        "created_unix": int(time.time()),
    }
    os.chmod(prefix, stat.S_IRWXU)
    return _write_manifest(prefix, manifest)


def backup(prefix: Path) -> Path:
    prefix = _resolve(prefix)
    manifest = load_manifest(prefix)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    dest = prefix / "var" / "backups" / stamp
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(prefix / MANIFEST_NAME, dest / MANIFEST_NAME)
    etc = prefix / "etc"
    if etc.exists():
        shutil.copytree(etc, dest / "etc", dirs_exist_ok=True)
    store = prefix / "var" / "models" / "STORE.json"
    if store.is_file():
        shutil.copy2(store, dest / "STORE.json")
    (dest / "checkpoint.json").write_text(
        json.dumps({"prefix": str(prefix), "version": manifest.get("version")}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    return dest


def _latest_backup(prefix: Path) -> Path:
    root = prefix / "var" / "backups"
    if not root.is_dir():
        raise InstallError("no backup checkpoint")
    children = sorted([p for p in root.iterdir() if p.is_dir()])
    if not children:
        raise InstallError("no backup checkpoint")
    return children[-1]


def rollback(prefix: Path) -> dict[str, Any]:
    prefix = _resolve(prefix)
    checkpoint = _latest_backup(prefix)
    etc_src = checkpoint / "etc"
    if etc_src.is_dir():
        etc_dst = prefix / "etc"
        if etc_dst.exists():
            shutil.rmtree(etc_dst)
        shutil.copytree(etc_src, etc_dst)
    man_src = checkpoint / MANIFEST_NAME
    if man_src.is_file():
        shutil.copy2(man_src, prefix / MANIFEST_NAME)
    return load_manifest(prefix)


def upgrade(source_root: Path, prefix: Path) -> dict[str, Any]:
    prefix = assert_allowed_prefix(prefix)
    backup(prefix)
    current = load_manifest(prefix)
    return install(
        source_root=source_root,
        prefix=prefix,
        listen_host=str(current.get("listen_host", DEFAULT_LISTEN_HOST)),
        listen_port=int(current.get("listen_port", DEFAULT_LISTEN_PORT)),
        model_store_quota_bytes=int(
            current.get("model_store_quota_bytes", DEFAULT_QUOTA_BYTES)
        ),
    )


def uninstall(prefix: Path, keep_models: bool = True, purge: bool = False) -> None:
    prefix = _resolve(prefix)
    if not prefix.exists():
        return
    models = prefix / "var" / "models"
    preserved = None
    if keep_models and models.exists() and not purge:
        tmp = prefix.parent / f".{prefix.name}-models-keep"
        if tmp.exists():
            shutil.rmtree(tmp)
        shutil.move(str(models), str(tmp))
        preserved = tmp
    shutil.rmtree(prefix)
    if preserved is not None:
        prefix.mkdir(parents=True)
        shutil.move(str(preserved), str(prefix / "var" / "models"))


def model_store_quota(prefix: Path) -> dict[str, int]:
    prefix = _resolve(prefix)
    meta = json.loads((prefix / "var" / "models" / "STORE.json").read_text(encoding="utf-8"))
    blob_root = prefix / "var" / "models" / "blobs" / "sha256"
    used = 0
    if blob_root.is_dir():
        for path in blob_root.iterdir():
            if path.is_file():
                used += path.stat().st_size
    return {"used_bytes": used, "quota_bytes": int(meta["quota_bytes"])}


def model_store_register(prefix: Path, source: Path, artefact_id: str) -> dict[str, Any]:
    prefix = _resolve(prefix)
    source = source.resolve()
    if not source.is_file():
        raise InstallError("model source is not a file")
    digest = _sha256_file(source)
    size = source.stat().st_size
    usage = model_store_quota(prefix)
    dest = prefix / "var" / "models" / "blobs" / "sha256" / digest
    additional = 0 if dest.exists() else size
    if usage["used_bytes"] + additional > usage["quota_bytes"]:
        raise InstallError("model-store quota exceeded")
    if not dest.exists():
        shutil.copy2(source, dest)
        dest.chmod(0o444)
    record = {
        "id": artefact_id,
        "sha256": digest,
        "bytes": size,
        "source_name": source.name,
        "promoted": False,
    }
    man = prefix / "var" / "models" / "manifests" / f"{artefact_id}.json"
    man.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record
