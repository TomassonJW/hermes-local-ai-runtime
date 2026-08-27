#!/usr/bin/env python3
"""Validate the public bootstrap without requiring runtime implementation."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = {
    "README.md",
    "README.fr.md",
    "AGENTS.md",
    "VERSION",
    "CHANGELOG.md",
    "LICENSE",
    "NOTICE",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "GATES.md",
    "ROADMAP.md",
    "BACKLOG.md",
    "STATE.md",
    "HANDOFF.md",
    "product/00-index.md",
    "architecture/00-index.md",
    "provenance/COMPILATION-MANIFEST.yml",
    "provenance/SOURCE-MAP.md",
    "contracts/openapi.yaml",
    "contracts/capabilities.v1.yaml",
    "schemas/job-request.schema.json",
    "schemas/job-result.schema.json",
    "schemas/model-manifest.schema.json",
    "schemas/route.schema.json",
    "config/hardware-profiles/hermes-cpu-8vcpu-16gib.yaml",
    "registry/candidates.yaml",
    "registry/LICENSE-POLICY.md",
    "ui/LOCAL-UI-CONTRACT.md",
    "ui/UI-00-ACCEPTANCE.md",
    "integration/hermes/skill/hermes-local-ai-runtime/SKILL.md",
}

MODEL_EXTENSIONS = {".gguf", ".safetensors", ".onnx", ".pt", ".pth"}
SECRET_PATTERNS = {
    "OpenAI-style key": re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    "Google API key": re.compile(r"\bAIza[A-Za-z0-9_-]{30,}\b"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
}

LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
BASELINE_RE = re.compile(r"Baseline commit:\s*`([0-9a-f]{40})`")


class Validation:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def load_yaml(path: Path, validation: Validation) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - validation should collect all failures
        validation.error(f"Invalid YAML {path.relative_to(ROOT)}: {exc}")
        return None


def validate_required_files(validation: Validation, allow_pending_baseline: bool) -> None:
    required = set(REQUIRED_FILES)
    if not allow_pending_baseline:
        required.add("BASELINE.md")
    for rel in sorted(required):
        if not (ROOT / rel).exists():
            validation.error(f"Missing required file: {rel}")


def validate_yaml_and_json(validation: Validation) -> None:
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or any(part.startswith(".git") for part in path.parts):
            continue
        if path.suffix in {".yaml", ".yml"}:
            load_yaml(path, validation)
        elif path.suffix == ".json":
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
                if path.parent.name == "schemas":
                    Draft202012Validator.check_schema(value)
            except Exception as exc:  # noqa: BLE001
                validation.error(f"Invalid JSON/schema {path.relative_to(ROOT)}: {exc}")


def normalise_link(raw: str) -> str:
    value = raw.strip().split(" ", 1)[0].strip("<>")
    return value.split("#", 1)[0]


def validate_internal_links(validation: Validation) -> None:
    for path in sorted(ROOT.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        for match in LINK_RE.finditer(text):
            target = normalise_link(match.group(1))
            if not target or target.startswith(("#", "http://", "https://", "mailto:")):
                continue
            candidate = (path.parent / target).resolve()
            try:
                candidate.relative_to(ROOT.resolve())
            except ValueError:
                validation.error(
                    f"Link escapes repository: {path.relative_to(ROOT)} -> {target}"
                )
                continue
            if not candidate.exists():
                validation.error(
                    f"Broken internal link: {path.relative_to(ROOT)} -> {target}"
                )


def validate_skill(validation: Validation) -> None:
    path = ROOT / "integration/hermes/skill/hermes-local-ai-runtime/SKILL.md"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        validation.error("Hermes skill must start with YAML frontmatter at byte zero")
        return
    try:
        _, frontmatter, body = text.split("---\n", 2)
        data = yaml.safe_load(frontmatter)
    except Exception as exc:  # noqa: BLE001
        validation.error(f"Invalid Hermes skill frontmatter: {exc}")
        return
    if not isinstance(data, dict):
        validation.error("Hermes skill frontmatter must be a mapping")
        return
    for field in ("name", "description"):
        if not data.get(field):
            validation.error(f"Hermes skill missing {field}")
    description = str(data.get("description", ""))
    if len(description) > 60:
        validation.error(
            f"Hermes skill description is {len(description)} chars; maximum is 60"
        )
    if not body.strip():
        validation.error("Hermes skill body is empty")


def validate_versions_and_pins(validation: Validation) -> None:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    manifest = load_yaml(ROOT / "provenance/COMPILATION-MANIFEST.yml", validation)
    ui = (ROOT / "ui/LOCAL-UI-CONTRACT.md").read_text(encoding="utf-8")

    if f"`{version}`" not in readme:
        validation.error("README does not contain VERSION")
    if isinstance(manifest, dict):
        manifest_version = str(manifest.get("project", {}).get("version", ""))
        if manifest_version != version:
            validation.error(
                f"Manifest version {manifest_version!r} differs from VERSION {version!r}"
            )
        if not manifest.get("authority", {}).get("repository_is_self_contained"):
            validation.error("Manifest must declare repository_is_self_contained: true")

    required_pins = {
        "agentic canon version": "0.5.0",
        "agentic canon commit": "460d3ef07b740c12f82baa89a0614efe8fe4ccbb",
        "UI canon version": "1.3.0",
        "UI canon commit": "4d720bf20f3c89e9a9d71072f0b76d55d225cb62",
    }
    combined = (
        (ROOT / "provenance/COMPILATION-MANIFEST.yml").read_text(encoding="utf-8")
        + "\n"
        + ui
    )
    for label, value in required_pins.items():
        if value not in combined:
            validation.error(f"Missing {label}: {value}")


def validate_invariants(validation: Validation) -> None:
    corpus = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in ROOT.rglob("*")
        if path.is_file()
        and path.suffix.lower() in {".md", ".yaml", ".yml", ".json", ".toml", ""}
        and ".git" not in path.parts
    )
    invariants = {
        "UI-00 stop": "UI-00",
        "cloud fallback off": "cloud_fallback_default: false",
        "consumer database boundary": "does not hold consumer database credentials",
        "resource admission": "resource admission",
        "future GPU": "Future GPU",
    }
    lower = corpus.lower()
    for label, phrase in invariants.items():
        if phrase.lower() not in lower:
            validation.error(f"Missing invariant: {label} ({phrase})")


def validate_public_safety(validation: Validation) -> None:
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or ".git" in path.parts:
            continue
        if path.suffix.lower() in MODEL_EXTENSIONS:
            validation.error(f"Model artefact committed: {path.relative_to(ROOT)}")
        if path.stat().st_size > 2_000_000:
            validation.warn(f"Large file: {path.relative_to(ROOT)}")
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for name, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                validation.error(f"Possible {name} in {path.relative_to(ROOT)}")


def validate_candidate_registry(validation: Validation) -> None:
    data = load_yaml(ROOT / "registry/candidates.yaml", validation)
    if not isinstance(data, dict):
        return
    for section in ("engines", "model_families"):
        for item in data.get(section, []) or []:
            if item.get("status") == "approved":
                validation.error(
                    f"Public candidate registry cannot pre-approve {item.get('id')}"
                )


def validate_openapi(validation: Validation) -> None:
    data = load_yaml(ROOT / "contracts/openapi.yaml", validation)
    if not isinstance(data, dict):
        return
    if data.get("openapi") != "3.1.0":
        validation.error("OpenAPI contract must declare 3.1.0")
    for required in ("/healthz", "/readyz", "/api/v1/jobs", "/v1/chat/completions"):
        if required not in data.get("paths", {}):
            validation.error(f"OpenAPI missing path {required}")


def validate_baseline(validation: Validation, allow_pending: bool) -> None:
    path = ROOT / "BASELINE.md"
    if not path.exists():
        if not allow_pending:
            validation.error("BASELINE.md is missing")
        return
    match = BASELINE_RE.search(path.read_text(encoding="utf-8"))
    if not match:
        if allow_pending:
            validation.warn("Baseline commit pending")
        else:
            validation.error("BASELINE.md must contain a 40-character commit SHA")
        return
    if set(match.group(1)) == {"0"} and not allow_pending:
        validation.error("Baseline commit cannot be all zeroes")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--allow-pending-baseline",
        action="store_true",
        help="Permit local compilation validation before the Git baseline exists.",
    )
    args = parser.parse_args()

    validation = Validation()
    validate_required_files(validation, args.allow_pending_baseline)
    validate_yaml_and_json(validation)
    validate_internal_links(validation)
    validate_skill(validation)
    validate_versions_and_pins(validation)
    validate_invariants(validation)
    validate_public_safety(validation)
    validate_candidate_registry(validation)
    validate_openapi(validation)
    validate_baseline(validation, args.allow_pending_baseline)

    for warning in validation.warnings:
        print(f"WARNING: {warning}")
    for error in validation.errors:
        print(f"ERROR: {error}", file=sys.stderr)

    if validation.errors:
        print(f"Bootstrap validation failed: {len(validation.errors)} error(s).")
        return 1

    print("Bootstrap validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
