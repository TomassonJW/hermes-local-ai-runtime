from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


def test_validator_passes() -> None:
    subprocess.run(
        [sys.executable, "scripts/validate_bootstrap.py"],
        cwd=ROOT,
        check=True,
    )


def test_json_schemas_are_draft_2020_12() -> None:
    for path in sorted((ROOT / "schemas").glob("*.json")):
        schema = json.loads(path.read_text(encoding="utf-8"))
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        Draft202012Validator.check_schema(schema)


def test_candidate_registry_contains_no_approved_model() -> None:
    registry = yaml.safe_load(
        (ROOT / "registry/candidates.yaml").read_text(encoding="utf-8")
    )
    statuses = [
        item["status"]
        for section in ("engines", "model_families")
        for item in registry.get(section, [])
    ]
    assert "approved" not in statuses


def test_runtime_defaults_disable_public_and_cloud() -> None:
    config = yaml.safe_load(
        (ROOT / "config/runtime.example.yaml").read_text(encoding="utf-8")
    )
    assert config["runtime"]["bind_host"] == "127.0.0.1"
    assert config["runtime"]["public_access"] is False
    assert config["security"]["cloud_fallback_default"] is False
    assert config["models"]["auto_download"] is False
    assert config["models"]["auto_promote"] is False


def test_initial_profile_is_bounded() -> None:
    profile = yaml.safe_load(
        (
            ROOT
            / "config/hardware-profiles/hermes-cpu-8vcpu-16gib.yaml"
        ).read_text(encoding="utf-8")
    )
    policy = profile["resource_policy"]
    assert profile["hardware"]["cpu"]["allocated_vcpu"] == 8
    assert profile["hardware"]["memory"]["allocated_gib"] == 16
    assert policy["hard_memory_gib"] <= 10
    assert policy["heavy_concurrency"] == 1
    assert policy["queue_max_jobs"] <= 8
