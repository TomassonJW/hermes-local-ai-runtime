from __future__ import annotations

import ast
from pathlib import Path

from fastapi.testclient import TestClient

from benchmarks.synthetic.generate import write_suite
from consumers.client import RuntimeClient
from consumers.hermes_app import answer
from consumers.sillage_app import ingest_invoice, load_invoice
from runtime.app import create_app
from runtime.config import Budget, RouteConfig, RuntimeConfig, TokenConfig

TOKEN = "g10-consumer-token"
CONSUMERS = Path(__file__).resolve().parents[1] / "consumers"
FORBIDDEN = (
    ".gguf",
    ".onnx",
    "qwen",
    "whisper",
    "llama.cpp",
    "engine_version",
    "model_artifacts",
)


def _route(engine_version: str, *, document: bool = False) -> RouteConfig:
    if document:
        return RouteConfig(
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
        )
    return RouteConfig(
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
    )


def _config(tmp_path: Path, engine_version: str) -> RuntimeConfig:
    return RuntimeConfig(
        listen_host="127.0.0.1",
        listen_port=8090,
        routes=(_route(engine_version), _route(engine_version, document=True)),
        budget=Budget(memory_floor_available_mib=0),
        tokens=(
            TokenConfig(
                name="g10",
                token=TOKEN,
                scopes=("capability:invoke:*", "job:read:self", "system:read"),
            ),
        ),
        db_path=str(tmp_path / f"jobs-{engine_version}.db"),
    )


def _client(tmp_path: Path, engine_version: str):
    app = create_app(_config(tmp_path, engine_version))
    transport = TestClient(app)
    transport.__enter__()
    return transport, RuntimeClient(transport, TOKEN)


def test_consumers_contain_no_model_or_engine_binding() -> None:
    for path in CONSUMERS.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        dumped = ast.dump(tree).lower()
        for token in FORBIDDEN:
            assert token not in dumped, f"{path.name} mentions {token}"
            assert token not in path.read_text(encoding="utf-8").lower()


def test_two_consumers_and_engine_swap_without_consumer_change(tmp_path: Path) -> None:
    fixtures = write_suite(tmp_path / "fx")
    pdf = fixtures["invoice_native_pdf"]
    db = tmp_path / "sillage.sqlite"

    first_http, first = _client(tmp_path / "v1", "test-v1")
    assert "facture" in answer(first, "facture SYN-0042").lower()
    ingested = ingest_invoice(first, pdf, db)
    assert ingested["invoice_id"] == "SYN-0042"
    assert load_invoice(db, "SYN-0042")["invoice_id"] == "SYN-0042"
    first_prov = first.invoke("text.generate", {"text": "ping"})["provenance"]["engine_version"]
    assert first_prov == "test-v1"
    first_http.close()

    second_http, second = _client(tmp_path / "v2", "test-v2")
    assert "facture" in answer(second, "facture SYN-0042").lower()
    ingested_again = ingest_invoice(second, pdf, db)
    assert ingested_again["invoice_id"] == "SYN-0042"
    second_prov = second.invoke("text.generate", {"text": "ping"})["provenance"]["engine_version"]
    assert second_prov == "test-v2"
    assert first_prov != second_prov
    second_http.close()
