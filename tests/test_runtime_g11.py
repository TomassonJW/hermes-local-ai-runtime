from __future__ import annotations

import json
from pathlib import Path

import yaml

from installkit.release import (
    licence_inventory,
    verify_checksums,
    write_checksums,
    write_support_bundle,
)

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_CLAIMS = (
    "production-ready",
    "frontier",
    "not implemented yet",
    "runtime is not implemented",
)


def test_support_matrix_is_ubuntu_x86_only() -> None:
    matrix = yaml.safe_load((ROOT / "packaging" / "matrix.yaml").read_text(encoding="utf-8"))
    assert matrix["os"] == "ubuntu-24.04"
    assert matrix["arch"] == "x86_64"
    assert matrix["status"] == "supported"
    assert matrix["loopback_default"] == "127.0.0.1"


def test_readme_does_not_claim_frontier_or_unimplemented() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8").lower()
    french = (ROOT / "README.fr.md").read_text(encoding="utf-8").lower()
    for blob in (text, french):
        assert "not implemented yet" not in blob
        assert "n’est pas encore implémenté" not in blob
        assert "n'est pas encore implémenté" not in blob
        assert "production-ready" not in blob
        assert "frontier" not in blob


def test_checksums_and_redacted_support_bundle(tmp_path: Path) -> None:
    write_checksums(ROOT)
    assert verify_checksums(ROOT) == []
    bundle = write_support_bundle(tmp_path, ROOT)
    data = json.loads(bundle.read_text(encoding="utf-8"))
    dumped = json.dumps(data).lower()
    assert "sk-" not in dumped
    assert "token" not in dumped
    assert data["listen_default"] == "127.0.0.1"
    inventory = licence_inventory()
    assert inventory["repository"]["license"] == "Apache-2.0"
    assert inventory["production_supported"] is False
    assert inventory["frontier_parity"] is False
    names = {item["name"] for item in inventory["python_components"]}
    assert "fastapi" in names
