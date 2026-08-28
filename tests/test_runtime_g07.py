from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from runtime.app import create_app
from runtime.config import Budget, RouteConfig, RuntimeConfig, TokenConfig
from runtime.vectors import (
    MAX_RERANK_CANDIDATES,
    consumer_record,
    persist_records,
    retrieve,
    space_id,
)

TOKEN = "fixture-token-g07"
POLICY = {
    "data_classification": "internal",
    "cloud_fallback_allowed": False,
    "retention": "none",
}


def _route(**overrides) -> RouteConfig:
    base = dict(
        id="embed-balanced@1",
        capability="text.embed",
        capability_version="1.0.0",
        profiles=("balanced",),
        worker="openai-upstream",
        upstream_base="http://127.0.0.1:9",
        upstream_model="embed",
        engine="llama.cpp",
        engine_version="b10662",
        resource_class="light",
        memory_estimate_mib=64,
        sync_allowed=True,
        timeout_ms=5_000,
        preset="g07",
        model_artifacts=("sha256:embed-fixture",),
    )
    base.update(overrides)
    return RouteConfig(**base)


def g07_config(tmp_path: Path, upstream: str) -> RuntimeConfig:
    return RuntimeConfig(
        listen_host="127.0.0.1",
        listen_port=8090,
        routes=(
            _route(upstream_base=upstream),
            _route(
                id="embed-fast@1",
                profiles=("fast",),
                upstream_base=upstream,
                upstream_model="embed-fast",
                model_artifacts=("sha256:embed-fast-fixture",),
            ),
            _route(
                id="rerank-balanced@1",
                capability="search.rerank",
                profiles=("balanced",),
                upstream_base=upstream,
                upstream_model="rerank",
                model_artifacts=("sha256:rerank-fixture",),
            ),
        ),
        budget=Budget(
            heavy_slots=1,
            light_slots=2,
            queue_max=8,
            memory_floor_available_mib=0,
            result_max_count=64,
            request_max_bytes=512 * 1024,
            result_max_bytes=4 * 1024 * 1024,
            result_store_max_bytes=16 * 1024 * 1024,
        ),
        tokens=(
            TokenConfig(
                name="consumer-a",
                token=TOKEN,
                scopes=(
                    "capability:invoke:*",
                    "job:read:self",
                    "job:cancel:self",
                    "system:read",
                ),
            ),
        ),
        db_path=str(tmp_path / "jobs.db"),
    )


def auth() -> dict[str, str]:
    return {"Authorization": f"Bearer {TOKEN}"}


def wait_terminal(client: TestClient, job_id: str, timeout: float = 4) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        data = client.get(f"/api/v1/jobs/{job_id}", headers=auth()).json()
        if data["status"] in {"succeeded", "failed", "cancelled", "rejected"}:
            return data
        time.sleep(0.02)
    raise AssertionError(f"job {job_id} did not terminate")


def _vector_for(text: str) -> list[float]:
    lowered = text.lower()
    if "facture" in lowered or "invoice" in lowered or "électricité" in lowered:
        return [1.0, 0.0, 0.0, 0.0]
    if "football" in lowered or "match" in lowered:
        return [0.0, 1.0, 0.0, 0.0]
    if "gratin" in lowered or "cuisine" in lowered:
        return [0.0, 0.0, 1.0, 0.0]
    return [0.0, 0.0, 0.0, 1.0]


class CountingUpstream(BaseHTTPRequestHandler):
    hits = 0
    lock = threading.Lock()

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(length) or b"{}")
        with self.lock:
            type(self).hits += 1
        if self.path == "/v1/embeddings":
            texts = body["input"]
            if isinstance(texts, str):
                texts = [texts]
            payload = {
                "data": [
                    {"embedding": _vector_for(text), "index": index}
                    for index, text in enumerate(texts)
                ]
            }
        elif self.path == "/v1/rerank":
            query = body["query"]
            docs = body["documents"]
            results = []
            for index, doc in enumerate(docs):
                score = 0.1
                if "facture" in doc.lower() or "électricité" in doc.lower():
                    score = 0.9
                if "contrat" in doc.lower() and "électricité" in query.lower():
                    score = 0.7
                results.append({"index": index, "relevance_score": score})
            payload = {"results": results}
        else:
            self.send_response(404)
            self.end_headers()
            return
        raw = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


@pytest.fixture
def upstream():
    CountingUpstream.hits = 0
    server = ThreadingHTTPServer(("127.0.0.1", 0), CountingUpstream)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    yield f"http://{host}:{port}"
    server.shutdown()
    thread.join(timeout=2)


def test_embed_declares_space_and_hides_model_filename(tmp_path: Path, upstream: str) -> None:
    with TestClient(create_app(g07_config(tmp_path, upstream))) as client:
        response = client.post(
            "/api/v1/jobs",
            headers=auth(),
            json={
                "capability": "text.embed",
                "capability_version": "1.0.0",
                "profile": "balanced",
                "input": {
                    "items": [
                        {"id": "a", "text": "Facture d'électricité SYN-0042"},
                        {"id": "b", "text": "Le club de football a gagné"},
                    ]
                },
                "policy": POLICY,
            },
        )
        assert response.status_code == 202, response.text
        job = wait_terminal(client, response.json()["job_id"])
        assert job["status"] == "succeeded"
        result = client.get(f"/api/v1/jobs/{job['job_id']}/result", headers=auth()).json()
        output = result["result"]
        assert output["dimensions"] == 4
        assert output["normalisation"] == "l2"
        assert output["space_id"] == "text.embed@1.0.0/balanced"
        ids = [item["id"] for item in output["items"]]
        assert ids == ["a", "b"]
        dumped = json.dumps(output)
        assert "gguf" not in dumped.lower()
        assert "qwen" not in dumped.lower()
        assert "embed-fixture" not in dumped
        assert result["provenance"]["model_artifacts"] == ["sha256:embed-fixture"]


def test_rerank_preserves_ids_and_rejects_over_bound(tmp_path: Path, upstream: str) -> None:
    with TestClient(create_app(g07_config(tmp_path, upstream))) as client:
        response = client.post(
            "/api/v1/jobs",
            headers=auth(),
            json={
                "capability": "search.rerank",
                "capability_version": "1.0.0",
                "profile": "balanced",
                "input": {
                    "query": "Quelle facture d'électricité ?",
                    "candidates": [
                        {"id": "food", "text": "Recette de cuisine: gratin dauphinois."},
                        {"id": "invoice", "text": "Example Energie - facture d'électricité."},
                        {"id": "sport", "text": "Le club de football a gagné le match."},
                    ],
                    "top_n": 2,
                },
                "policy": POLICY,
            },
        )
        job = wait_terminal(client, response.json()["job_id"])
        assert job["status"] == "succeeded"
        ranked = client.get(
            f"/api/v1/jobs/{job['job_id']}/result", headers=auth()
        ).json()["result"]["candidates"]
        assert [item["id"] for item in ranked] == ["invoice", "food"] or ranked[0]["id"] == "invoice"
        assert ranked[0]["id"] == "invoice"
        assert len(ranked) == 2

        too_many = client.post(
            "/api/v1/jobs",
            headers=auth(),
            json={
                "capability": "search.rerank",
                "capability_version": "1.0.0",
                "profile": "balanced",
                "input": {
                    "query": "x",
                    "candidates": [{"id": str(i), "text": "doc"} for i in range(MAX_RERANK_CANDIDATES + 1)],
                },
                "policy": POLICY,
            },
        )
        assert too_many.status_code in {400, 202}
        if too_many.status_code == 202:
            failed = wait_terminal(client, too_many.json()["job_id"])
            assert failed["status"] == "failed"
            assert failed["error"]["code"] == "INVALID_INPUT"


def test_result_cache_hits_internal_and_bypasses_confidential(
    tmp_path: Path, upstream: str
) -> None:
    with TestClient(create_app(g07_config(tmp_path, upstream))) as client:
        body = {
            "capability": "text.embed",
            "capability_version": "1.0.0",
            "profile": "balanced",
            "input": {"texts": ["Le chat dort sur le canapé."]},
            "policy": POLICY,
        }
        first = client.post("/api/v1/jobs", headers=auth(), json=body)
        wait_terminal(client, first.json()["job_id"])
        hits_after_first = CountingUpstream.hits
        second = client.post("/api/v1/jobs", headers=auth(), json=body)
        job = wait_terminal(client, second.json()["job_id"])
        result = client.get(
            f"/api/v1/jobs/{job['job_id']}/result", headers=auth()
        ).json()
        assert result["provenance"]["cache"] == "hit"
        assert CountingUpstream.hits == hits_after_first

        confidential = dict(body)
        confidential["policy"] = {
            **POLICY,
            "data_classification": "confidential",
        }
        third = client.post("/api/v1/jobs", headers=auth(), json=confidential)
        job = wait_terminal(client, third.json()["job_id"])
        result = client.get(
            f"/api/v1/jobs/{job['job_id']}/result", headers=auth()
        ).json()
        assert result["provenance"]["cache"] == "bypass"
        assert CountingUpstream.hits == hits_after_first + 1


def test_consumer_persist_has_no_model_filename_and_space_replacement(
    tmp_path: Path, upstream: str
) -> None:
    with TestClient(create_app(g07_config(tmp_path, upstream))) as client:
        def embed(profile: str, item_id: str, text: str) -> dict:
            response = client.post(
                "/api/v1/jobs",
                headers=auth(),
                json={
                    "capability": "text.embed",
                    "capability_version": "1.0.0",
                    "profile": profile,
                    "input": {"items": [{"id": item_id, "text": text}]},
                    "policy": POLICY,
                },
            )
            job = wait_terminal(client, response.json()["job_id"])
            output = client.get(
                f"/api/v1/jobs/{job['job_id']}/result", headers=auth()
            ).json()["result"]
            item = output["items"][0]
            return consumer_record(
                item["id"],
                item["vector"],
                dimensions=output["dimensions"],
                normalisation=output["normalisation"],
                space_id_value=output["space_id"],
            )

        balanced = embed("balanced", "doc-1", "Facture atelier")
        fast = embed("fast", "doc-1", "Facture atelier")
        db = tmp_path / "consumer.sqlite"
        persist_records(db, [balanced])
        dumped = json.dumps(balanced)
        assert "gguf" not in dumped
        assert "qwen" not in dumped.lower()
        assert balanced["space_id"] != fast["space_id"]
        assert balanced["space_id"] == space_id("text.embed", "1.0.0", "balanced")
        hits = retrieve(db, balanced["vector"], space_id_value=fast["space_id"])
        assert hits == []


def test_french_mixed_retrieval_then_rerank(tmp_path: Path, upstream: str) -> None:
    docs = [
        {"id": "invoice", "text": "Facture d'électricité Example Energie, 123,45 EUR."},
        {"id": "sport", "text": "The football club won the match last night."},
        {"id": "food", "text": "Recette de cuisine: gratin dauphinois."},
    ]
    with TestClient(create_app(g07_config(tmp_path, upstream))) as client:
        embed = client.post(
            "/api/v1/jobs",
            headers=auth(),
            json={
                "capability": "text.embed",
                "capability_version": "1.0.0",
                "profile": "balanced",
                "input": {
                    "items": docs + [{"id": "q", "text": "fournisseur d'électricité facture"}]
                },
                "policy": POLICY,
            },
        )
        job = wait_terminal(client, embed.json()["job_id"])
        items = {
            item["id"]: item["vector"]
            for item in client.get(
                f"/api/v1/jobs/{job['job_id']}/result", headers=auth()
            ).json()["result"]["items"]
        }
        from runtime.vectors import cosine

        ranked = sorted(
            (doc_id for doc_id in ("invoice", "sport", "food")),
            key=lambda doc_id: cosine(items["q"], items[doc_id]),
            reverse=True,
        )
        assert ranked[0] == "invoice"
        rerank = client.post(
            "/api/v1/jobs",
            headers=auth(),
            json={
                "capability": "search.rerank",
                "capability_version": "1.0.0",
                "profile": "balanced",
                "input": {
                    "query": "Quel fournisseur d'électricité a émis cette facture ?",
                    "candidates": docs,
                },
                "policy": POLICY,
            },
        )
        job = wait_terminal(client, rerank.json()["job_id"])
        top = client.get(
            f"/api/v1/jobs/{job['job_id']}/result", headers=auth()
        ).json()["result"]["candidates"][0]["id"]
        assert top == "invoice"


def test_openai_embeddings_adapter_uses_alias_not_checkpoint(
    tmp_path: Path, upstream: str
) -> None:
    with TestClient(create_app(g07_config(tmp_path, upstream))) as client:
        response = client.post(
            "/v1/embeddings",
            headers=auth(),
            json={"model": "hlair/embed-balanced", "input": ["bonjour"]},
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["object"] == "list"
        assert data["model"] == "hlair/embed-balanced"
        assert "gguf" not in json.dumps(data).lower()
        flag = client.post(
            "/v1/embeddings",
            headers=auth(),
            json={"model": "hlair/embed-balanced", "input": ["bonjour"], "n_ctx": 999},
        )
        assert flag.status_code == 400
        models = client.get("/v1/models", headers=auth()).json()["data"]
        ids = {item["id"] for item in models}
        assert "hlair/embed-balanced" in ids
        assert "hlair/rerank-balanced" in ids
        rerank = client.post(
            "/v1/rerank",
            headers=auth(),
            json={
                "model": "hlair/rerank-balanced",
                "query": "facture électricité",
                "documents": ["gratin", "facture d'électricité", "football"],
            },
        )
        assert rerank.status_code == 200, rerank.text
        assert rerank.json()["results"][0]["index"] == 1
