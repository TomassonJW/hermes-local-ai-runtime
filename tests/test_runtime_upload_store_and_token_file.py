"""Regression tests for the two UI-01 live defects.

A. The volatile upload store leaked: entries were never released, so the
   9th upload of a session failed with QUEUE_FULL and every media capability
   stayed dead until a restart.
B. The runtime could not restart unattended: the auth token was only ever
   read from the environment, so a lost shell meant a dead console.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml

from runtime.config import ConfigError, load_config
from runtime.media import UploadStore


# --- Defect A: the volatile upload store must not starve -----------------


def test_store_accepts_more_uploads_than_its_slot_count():
    """The 9th upload used to fail with QUEUE_FULL forever."""
    store = UploadStore(max_items=8, max_bytes=10 * 1024 * 1024)
    for index in range(40):
        assert store.put(f"upl_{index:016x}", b"x" * 1024) is True
    assert len(store) <= 8


def test_pinned_upload_survives_pressure_and_is_reusable_across_jobs():
    """A job's media must not be evicted under load, and a completed job's
    upload must stay reusable by a second job (vision.compare relies on it)."""
    store = UploadStore(max_items=4, max_bytes=1024 * 1024)
    store.put("upl_aaaaaaaaaaaaaaaa", b"kept")
    store.pin(["upl_aaaaaaaaaaaaaaaa"])
    for index in range(20):
        store.put(f"upl_{index:016x}", b"y" * 512)
    assert "upl_aaaaaaaaaaaaaaaa" in store
    assert store["upl_aaaaaaaaaaaaaaaa"] == b"kept"

    store.unpin(["upl_aaaaaaaaaaaaaaaa"])
    # Still present right after the job: a second job may reuse the id.
    assert "upl_aaaaaaaaaaaaaaaa" in store


def test_expired_upload_is_reclaimed():
    store = UploadStore(max_items=8, max_bytes=1024 * 1024, ttl_seconds=0.0)
    store.put("upl_bbbbbbbbbbbbbbbb", b"stale")
    assert "upl_bbbbbbbbbbbbbbbb" not in store
    assert store.stats()["items"] == 0


def test_blob_larger_than_the_whole_budget_is_refused():
    store = UploadStore(max_items=8, max_bytes=1024)
    assert store.put("upl_cccccccccccccccc", b"z" * 4096) is False


def test_pins_are_reference_counted():
    """Two jobs sharing one upload: the first finishing must not unprotect it."""
    store = UploadStore(max_items=2, max_bytes=1024 * 1024)
    store.put("upl_dddddddddddddddd", b"shared")
    store.pin(["upl_dddddddddddddddd"])
    store.pin(["upl_dddddddddddddddd"])
    store.unpin(["upl_dddddddddddddddd"])
    for index in range(10):
        store.put(f"upl_{index:016x}", b"w" * 128)
    assert "upl_dddddddddddddddd" in store


# --- Defect B: the runtime must restart without its original shell -------


def _config_doc(tmp_path: Path, token_entry: dict) -> Path:
    doc = {
        "listen": {"host": "127.0.0.1", "port": 8830},
        "db_path": str(tmp_path / "state.db"),
        "auth": {"tokens": [{"name": "local-consumer", "scopes": ["system:read"], **token_entry}]},
        "routes": [
            {
                "id": "echo@1",
                "capability": "text.generate",
                "capability_version": "1.0.0",
                "profiles": ["fast"],
                "worker": "echo",
                "engine": "dummy",
                "engine_version": "test",
                "resource_class": "light",
                "memory_estimate_mib": 1,
                "sync_allowed": True,
                "timeout_ms": 2000,
            }
        ],
    }
    path = tmp_path / "runtime.yaml"
    path.write_text(yaml.safe_dump(doc), encoding="utf-8")
    return path


def test_token_file_lets_the_runtime_start_with_an_empty_environment(tmp_path: Path):
    token_path = tmp_path / "runtime.token"
    token_path.write_text("fixture-token-value\n", encoding="utf-8")
    token_path.chmod(0o600)
    config_path = _config_doc(
        tmp_path, {"token_env": "HLAIR_ABSENT_ENV_VAR", "token_file": "runtime.token"}
    )
    os.environ.pop("HLAIR_ABSENT_ENV_VAR", None)

    config = load_config(config_path)

    assert len(config.tokens) == 1
    assert config.tokens[0].token == "fixture-token-value"


def test_environment_still_wins_over_the_token_file(tmp_path: Path):
    token_path = tmp_path / "runtime.token"
    token_path.write_text("from-file", encoding="utf-8")
    token_path.chmod(0o600)
    config_path = _config_doc(
        tmp_path, {"token_env": "HLAIR_TEST_ENV_TOKEN", "token_file": "runtime.token"}
    )
    os.environ["HLAIR_TEST_ENV_TOKEN"] = "from-environment"
    try:
        config = load_config(config_path)
    finally:
        os.environ.pop("HLAIR_TEST_ENV_TOKEN", None)

    assert config.tokens[0].token == "from-environment"


def test_group_readable_token_file_is_refused(tmp_path: Path):
    token_path = tmp_path / "runtime.token"
    token_path.write_text("leaky", encoding="utf-8")
    token_path.chmod(0o644)
    config_path = _config_doc(
        tmp_path, {"token_env": "HLAIR_ABSENT_ENV_VAR", "token_file": "runtime.token"}
    )
    os.environ.pop("HLAIR_ABSENT_ENV_VAR", None)

    with pytest.raises(ConfigError, match="readable"):
        load_config(config_path)


def test_missing_token_file_and_env_still_refuses_to_start(tmp_path: Path):
    config_path = _config_doc(
        tmp_path, {"token_env": "HLAIR_ABSENT_ENV_VAR", "token_file": "absent.token"}
    )
    os.environ.pop("HLAIR_ABSENT_ENV_VAR", None)

    with pytest.raises(ConfigError, match="refusing to start"):
        load_config(config_path)
