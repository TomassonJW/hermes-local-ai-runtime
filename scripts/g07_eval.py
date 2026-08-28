#!/usr/bin/env python3
"""G-07 loopback evaluation: embeddings + rerank. No permanent service."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from runtime.app import create_app
from runtime.config import Budget, RouteConfig, RuntimeConfig, TokenConfig
from runtime.vectors import cosine, persist_records, retrieve, space_id

SPIKE = ROOT.parent / "spike-g03"
SWAP = SPIKE / "bin" / "llama-swap"
LLAMA = SPIKE / "bin" / "llama-b10662" / "llama-server"
MODELS = SPIKE / "models"
TOKEN = "fixture-token-g07-eval"
QUERY = "Quel fournisseur d'electricite a emis cette facture ?"
DOCS = [
    ("food", "Recette de cuisine: gratin dauphinois aux pommes de terre."),
    ("invoice", "Example Energie SAS - facture d'electricite aout 2026, montant 123,45 EUR."),
    ("sport", "Le club de football a gagne le match hier soir."),
    ("contract", "Contrat de fourniture d'electricite entre Example Energie et le client."),
    ("en-invoice", "Electricity invoice from Example Energie SAS, amount 123.45 EUR."),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def swap_config(listen: str) -> str:
    host, port = listen.split(":")
    return f"""
listen: "{host}:{port}"
healthCheckTimeout: 180
models:
  embed:
    cmd: |
      {LLAMA} --model {MODELS}/qwen3-embed-0.6b-q8.gguf
      --host 127.0.0.1 --port ${{PORT}} --embedding --pooling last
      --ctx-size 2048 --threads 4 --no-webui
    ttl: 90
  rerank:
    cmd: |
      {LLAMA} --model {MODELS}/qwen3-reranker-0.6b-q8.gguf
      --host 127.0.0.1 --port ${{PORT}} --rerank --pooling rank
      --ctx-size 2048 --threads 4 --no-webui
    ttl: 90
groups:
  light:
    swap: true
    exclusive: true
    members: [embed, rerank]
"""


def wait_health(url: str, timeout: float = 120) -> None:
    deadline = time.monotonic() + timeout
    last = ""
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    return
        except Exception as exc:  # noqa: BLE001
            last = str(exc)
            time.sleep(0.5)
    raise RuntimeError(f"upstream not ready: {last}")


def runtime_config(tmp: Path, upstream: str) -> RuntimeConfig:
    embed_hash = "sha256:" + sha256(MODELS / "qwen3-embed-0.6b-q8.gguf")
    rerank_hash = "sha256:" + sha256(MODELS / "qwen3-reranker-0.6b-q8.gguf")
    return RuntimeConfig(
        listen_host="127.0.0.1",
        listen_port=8851,
        routes=(
            RouteConfig(
                id="embed-balanced@g07",
                capability="text.embed",
                capability_version="1.0.0",
                profiles=("balanced",),
                worker="openai-upstream",
                upstream_base=upstream,
                upstream_model="embed",
                engine="llama.cpp",
                engine_version="b10662",
                resource_class="light",
                memory_estimate_mib=900,
                sync_allowed=True,
                timeout_ms=180_000,
                model_artifacts=(embed_hash,),
                preset="qwen3-embed-0.6b-q8",
            ),
            RouteConfig(
                id="rerank-balanced@g07",
                capability="search.rerank",
                capability_version="1.0.0",
                profiles=("balanced",),
                worker="openai-upstream",
                upstream_base=upstream,
                upstream_model="rerank",
                engine="llama.cpp",
                engine_version="b10662",
                resource_class="light",
                memory_estimate_mib=1400,
                sync_allowed=True,
                timeout_ms=180_000,
                model_artifacts=(rerank_hash,),
                preset="qwen3-reranker-0.6b-q8",
            ),
        ),
        budget=Budget(heavy_slots=1, light_slots=1, queue_max=4, memory_floor_available_mib=0),
        tokens=(
            TokenConfig(
                name="eval",
                token=TOKEN,
                scopes=("capability:invoke:*", "job:read:self", "system:read"),
            ),
        ),
        db_path=str(tmp / "g07-eval.db"),
    )


def wait_job(client: TestClient, job_id: str, timeout: float = 180) -> dict:
    headers = {"Authorization": f"Bearer {TOKEN}"}
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        data = client.get(f"/api/v1/jobs/{job_id}", headers=headers).json()
        if data["status"] in {"succeeded", "failed", "cancelled", "rejected"}:
            return data
        time.sleep(0.2)
    raise RuntimeError(f"job {job_id} did not finish")


def submit(client: TestClient, capability: str, payload: dict) -> dict:
    headers = {"Authorization": f"Bearer {TOKEN}"}
    body = {
        "capability": capability,
        "capability_version": "1.0.0",
        "profile": "balanced",
        "input": payload,
        "policy": {
            "data_classification": "internal",
            "cloud_fallback_allowed": False,
            "retention": "none",
        },
    }
    response = client.post("/api/v1/jobs", headers=headers, json=body)
    response.raise_for_status()
    job = wait_job(client, response.json()["job_id"])
    result = client.get(f"/api/v1/jobs/{job['job_id']}/result", headers=headers).json()
    return {"job": job, "result": result}


def main() -> int:
    listen = "127.0.0.1:8870"
    report: dict = {
        "hardware_profile": "hermes-cpu-8vcpu-16gib",
        "fastembed": "measured-in-g03-not-wired",
        "shared_vector_db": False,
    }
    if not SWAP.is_file() or not (MODELS / "qwen3-embed-0.6b-q8.gguf").is_file():
        report["status"] = "skip"
        report["reason"] = "spike-g03 artefacts missing"
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    with tempfile.TemporaryDirectory(prefix="g07-eval-") as raw:
        tmp = Path(raw)
        cfg = tmp / "llama-swap.yaml"
        cfg.write_text(swap_config(listen), encoding="utf-8")
        proc = subprocess.Popen(
            [str(SWAP), "-config", str(cfg), "-listen", listen],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            wait_health(f"http://{listen}/running")
            app_config = runtime_config(tmp, f"http://{listen}")
            with TestClient(create_app(app_config)) as client:
                texts = [QUERY] + [text for _cid, text in DOCS]
                started = time.monotonic()
                embed = submit(client, "text.embed", {"texts": texts})
                embed_ms = round((time.monotonic() - started) * 1000)
                output = embed["result"]["result"]
                vectors = [item["vector"] for item in output["items"]]
                query_vec = vectors[0]
                ranked_cos = sorted(
                    (
                        {
                            "id": doc_id,
                            "score": cosine(query_vec, vectors[index + 1]),
                        }
                        for index, (doc_id, _text) in enumerate(DOCS)
                    ),
                    key=lambda item: item["score"],
                    reverse=True,
                )
                started = time.monotonic()
                rerank = submit(
                    client,
                    "search.rerank",
                    {
                        "query": QUERY,
                        "candidates": [{"id": doc_id, "text": text} for doc_id, text in DOCS],
                        "top_n": 3,
                    },
                )
                rerank_ms = round((time.monotonic() - started) * 1000)
                reranked = rerank["result"]["result"]["candidates"]
                started = time.monotonic()
                cached = submit(client, "text.embed", {"texts": texts})
                cache_ms = round((time.monotonic() - started) * 1000)
                db = tmp / "consumer.sqlite"
                records = [
                    {
                        "id": doc_id,
                        "vector": vectors[index + 1],
                        "dimensions": output["dimensions"],
                        "normalisation": output["normalisation"],
                        "space_id": output["space_id"],
                    }
                    for index, (doc_id, _text) in enumerate(DOCS)
                ]
                persist_records(db, records)
                retrieved = retrieve(db, query_vec, space_id_value=output["space_id"], top_k=3)
                dumped = json.dumps(records).lower()
                report.update(
                    {
                        "status": "measured",
                        "embed": {
                            "dimensions": output["dimensions"],
                            "normalisation": output["normalisation"],
                            "space_id": output["space_id"],
                            "latency_ms": embed_ms,
                            "cache": cached["result"]["provenance"]["cache"],
                            "cache_latency_ms": cache_ms,
                            "cosine_top": ranked_cos[0]["id"],
                            "cosine_order_ok": ranked_cos[0]["id"] in {"invoice", "contract", "en-invoice"},
                        },
                        "rerank": {
                            "latency_ms": rerank_ms,
                            "top": reranked[0]["id"] if reranked else None,
                            "ids": [item["id"] for item in reranked],
                            "top_is_invoice_family": (reranked[0]["id"] in {"invoice", "en-invoice", "contract"})
                            if reranked
                            else False,
                        },
                        "consumer": {
                            "retrieved_top": retrieved[0]["id"] if retrieved else None,
                            "no_model_filename": "gguf" not in dumped and "qwen" not in dumped,
                            "space_id": space_id("text.embed", "1.0.0", "balanced"),
                        },
                    }
                )
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=8)
            except subprocess.TimeoutExpired:
                proc.kill()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
