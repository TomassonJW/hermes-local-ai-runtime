#!/usr/bin/env python3
"""G-10 two-consumer proof. No permanent service, no Hermes config change."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from benchmarks.synthetic.generate import write_suite
from consumers.client import RuntimeClient
from consumers.hermes_app import answer
from consumers.sillage_app import ingest_invoice
from runtime.app import create_app
from runtime.config import Budget, RouteConfig, RuntimeConfig, TokenConfig

TOKEN = "g10-eval-token"


def _config(db: Path, engine_version: str) -> RuntimeConfig:
    return RuntimeConfig(
        listen_host="127.0.0.1",
        listen_port=8090,
        routes=(
            RouteConfig(
                id=f"echo-text@{engine_version}",
                capability="text.generate",
                capability_version="1.0.0",
                profiles=("balanced",),
                worker="echo",
                upstream_base=None,
                upstream_model=None,
                engine="dummy",
                engine_version=engine_version,
                resource_class="light",
                memory_estimate_mib=1,
                sync_allowed=True,
                timeout_ms=5_000,
            ),
            RouteConfig(
                id=f"doc-struct@{engine_version}",
                capability="document.extract_structured",
                capability_version="1.0.0",
                profiles=("balanced",),
                worker="document-structured",
                upstream_base=None,
                upstream_model=None,
                engine="pdf-native",
                engine_version=engine_version,
                resource_class="light",
                memory_estimate_mib=64,
                sync_allowed=True,
                timeout_ms=15_000,
            ),
        ),
        budget=Budget(memory_floor_available_mib=0),
        tokens=(
            TokenConfig(
                name="g10",
                token=TOKEN,
                scopes=("capability:invoke:*", "job:read:self", "system:read"),
            ),
        ),
        db_path=str(db),
    )


def run_pair(tmp: Path, engine_version: str, pdf: Path, sillage_db: Path) -> dict:
    with TestClient(create_app(_config(tmp / f"{engine_version}.db", engine_version))) as http:
        client = RuntimeClient(http, TOKEN)
        text = answer(client, "facture SYN-0042")
        invoice = ingest_invoice(client, pdf, sillage_db)
        provenance = client.invoke("text.generate", {"text": "ping"})["provenance"]
        return {
            "engine_version": provenance["engine_version"],
            "hermes_echo": text,
            "sillage_invoice": invoice["invoice_id"],
        }


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="hlair-g10-") as raw:
        tmp = Path(raw)
        pdf = write_suite(tmp / "fx")["invoice_native_pdf"]
        db = tmp / "sillage.sqlite"
        first = run_pair(tmp / "v1", "test-v1", pdf, db)
        second = run_pair(tmp / "v2", "test-v2", pdf, db)
        report = {
            "consumers": ["hermes_app", "sillage_app"],
            "first": first,
            "second": second,
            "engine_changed": first["engine_version"] != second["engine_version"],
            "sillage_stable": first["sillage_invoice"] == second["sillage_invoice"] == "SYN-0042",
            "hermes_config_mutated": False,
            "permanent_service": False,
        }
        print(json.dumps(report, indent=2))
        if not report["engine_changed"] or not report["sillage_stable"]:
            return 1
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
