#!/usr/bin/env python3
"""G-09 prefix install evaluation. No systemd enable, no model download."""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from installkit.kit import backup, install, model_store_register, plan, uninstall, upgrade
from runtime.config import load_config


def main() -> int:
    prefix = Path(tempfile.mkdtemp(prefix="hlair-g09-"))
    os.environ["HERMES_LOCAL_AI_TOKEN"] = "g09-eval-token"
    try:
        document = plan(ROOT, prefix)
        assert document["enable_service"] is False
        assert document["listen_host"] == "127.0.0.1"
        manifest = install(ROOT, prefix)
        cfg = load_config(prefix / "etc" / "runtime.yaml")
        toy = prefix / "var" / "tmp" / "toy.bin"
        toy.write_bytes(b"g09-toy")
        record = model_store_register(prefix, toy, "g09-toy")
        checkpoint = backup(prefix)
        upgrade(ROOT, prefix)
        report = {
            "prefix": str(prefix),
            "listen_host": manifest["listen_host"],
            "service_enabled": manifest["service_enabled"],
            "config_host": cfg.listen_host,
            "notices": (prefix / "share" / "notices" / "THIRD-PARTY.txt").is_file(),
            "sbom": (prefix / "share" / "sbom" / "sbom.json").is_file(),
            "unit_shipped": (
                prefix / "share" / "systemd" / "hermes-local-ai-runtime.user.service"
            ).is_file(),
            "model_sha256": record["sha256"],
            "backup": str(checkpoint),
            "user_unit_enabled": (
                Path.home() / ".config/systemd/user/hermes-local-ai-runtime.service"
            ).exists(),
        }
        print(json.dumps(report, indent=2))
        if report["listen_host"] != "127.0.0.1":
            raise SystemExit("listen is not loopback")
        if report["service_enabled"] or report["user_unit_enabled"]:
            raise SystemExit("systemd unit was enabled")
        return 0
    finally:
        uninstall(prefix, keep_models=False, purge=True)
        if prefix.exists():
            shutil.rmtree(prefix, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
