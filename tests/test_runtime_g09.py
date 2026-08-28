from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
import yaml

from installkit.kit import (
    FORBIDDEN_PREFIXES,
    InstallError,
    backup,
    install,
    load_manifest,
    model_store_quota,
    model_store_register,
    plan,
    rollback,
    uninstall,
    upgrade,
)
from runtime.config import load_config

REPO = Path(__file__).resolve().parents[1]


def test_plan_is_dry_and_loopback(tmp_path: Path) -> None:
    prefix = tmp_path / "hlair"
    document = plan(source_root=REPO, prefix=prefix)
    assert prefix.exists() is False
    assert document["listen_host"] == "127.0.0.1"
    assert document["enable_service"] is False
    assert document["download_models"] is False
    assert any("pve" in p for p in document["forbidden_prefixes"])


def test_install_refuses_proxmox_and_usr() -> None:
    for forbidden in ("/etc/pve/hlair", "/usr/local/hlair", "/var/lib/pve/hlair"):
        with pytest.raises(InstallError, match="forbidden"):
            install(source_root=REPO, prefix=Path(forbidden))


def test_install_loopback_layout_notices_sbom_and_no_service(tmp_path: Path) -> None:
    prefix = tmp_path / "opt" / "hlair"
    manifest = install(source_root=REPO, prefix=prefix)
    assert manifest["listen_host"] == "127.0.0.1"
    assert manifest["service_enabled"] is False
    assert (prefix / "etc" / "runtime.yaml").is_file()
    assert (prefix / "share" / "notices" / "NOTICE").is_file()
    assert (prefix / "share" / "notices" / "THIRD-PARTY.txt").is_file()
    assert (prefix / "share" / "sbom" / "sbom.json").is_file()
    assert (prefix / "share" / "systemd" / "hermes-local-ai-runtime.user.service").is_file()
    assert (prefix / "var" / "models" / "blobs" / "sha256").is_dir()
    raw = yaml.safe_load((prefix / "etc" / "runtime.yaml").read_text(encoding="utf-8"))
    assert raw["listen"]["host"] == "127.0.0.1"
    os.environ["HERMES_LOCAL_AI_TOKEN"] = "g09-unit-token"
    cfg = load_config(prefix / "etc" / "runtime.yaml")
    assert cfg.listen_host == "127.0.0.1"
    sbom = json.loads((prefix / "share" / "sbom" / "sbom.json").read_text(encoding="utf-8"))
    names = {c["name"] for c in sbom["components"]}
    assert "fastapi" in names
    assert "Apache-2.0" in (prefix / "share" / "notices" / "THIRD-PARTY.txt").read_text(
        encoding="utf-8"
    )
    unit = (prefix / "share" / "systemd" / "hermes-local-ai-runtime.user.service").read_text(
        encoding="utf-8"
    )
    assert "127.0.0.1" in unit
    assert "WantedBy" in unit
    # Unit is shipped, never enabled by install.
    assert not (Path.home() / ".config/systemd/user/hermes-local-ai-runtime.service").exists() or True
    user_unit = Path.home() / ".config/systemd/user/hermes-local-ai-runtime.service"
    assert not user_unit.exists()


def test_install_refuses_non_loopback_override(tmp_path: Path) -> None:
    with pytest.raises(InstallError, match="loopback"):
        install(
            source_root=REPO,
            prefix=tmp_path / "hlair",
            listen_host="0.0.0.0",
        )


def test_model_store_register_quota_and_no_auto_download(tmp_path: Path) -> None:
    prefix = tmp_path / "hlair"
    install(source_root=REPO, prefix=prefix, model_store_quota_bytes=2048)
    blob = tmp_path / "toy.bin"
    blob.write_bytes(b"model-bytes")
    record = model_store_register(prefix, blob, artefact_id="toy-v1")
    assert record["sha256"]
    stored = prefix / "var" / "models" / "blobs" / "sha256" / record["sha256"]
    assert stored.is_file()
    assert stored.read_bytes() == b"model-bytes"
    usage = model_store_quota(prefix)
    assert usage["used_bytes"] == 11
    assert usage["quota_bytes"] == 2048
    too_big = tmp_path / "huge.bin"
    too_big.write_bytes(b"x" * 3000)
    with pytest.raises(InstallError, match="quota"):
        model_store_register(prefix, too_big, artefact_id="huge")


def test_backup_upgrade_rollback_uninstall(tmp_path: Path) -> None:
    prefix = tmp_path / "hlair"
    install(source_root=REPO, prefix=prefix)
    first = load_manifest(prefix)
    checkpoint = backup(prefix)
    assert Path(checkpoint).is_dir()
    (prefix / "etc" / "runtime.yaml").write_text("listen:\n  host: 127.0.0.1\n  port: 1\n", encoding="utf-8")
    upgrade(source_root=REPO, prefix=prefix)
    restored = rollback(prefix)
    assert restored["listen_port"] == first["listen_port"]
    yaml.safe_load((prefix / "etc" / "runtime.yaml").read_text(encoding="utf-8"))
    blob = tmp_path / "keep.bin"
    blob.write_bytes(b"keep")
    model_store_register(prefix, blob, artefact_id="keep")
    uninstall(prefix, keep_models=True)
    assert not (prefix / "etc").exists()
    assert (prefix / "var" / "models" / "blobs").exists()
    uninstall(prefix, keep_models=False, purge=True)
    assert not prefix.exists()


def test_forbidden_prefixes_cover_proxmox() -> None:
    joined = " ".join(FORBIDDEN_PREFIXES)
    assert "/etc/pve" in joined
    assert "/var/lib/pve" in joined
