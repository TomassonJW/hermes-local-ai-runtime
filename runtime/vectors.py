"""Embedding and rerank contracts: dimensions, space ids, no model filenames."""

from __future__ import annotations

import hashlib
import json
import math
import sqlite3
from pathlib import Path
from typing import Any

MAX_EMBED_BATCH = 64
MAX_RERANK_CANDIDATES = 100


def space_id(capability: str, version: str, profile: str) -> str:
    return f"{capability}@{version}/{profile}"


def l2_normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return list(vector)
    return [value / norm for value in vector]


def cosine(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    num = sum(a * b for a, b in zip(left, right))
    den = math.sqrt(sum(a * a for a in left)) * math.sqrt(sum(b * b for b in right))
    if den == 0:
        return 0.0
    return num / den


def parse_embed_items(inp: dict[str, Any]) -> list[dict[str, str]]:
    items = inp.get("items")
    if isinstance(items, list) and items:
        parsed: list[dict[str, str]] = []
        for index, item in enumerate(items):
            if not isinstance(item, dict) or not isinstance(item.get("text"), str):
                raise ValueError("items must be objects with text")
            parsed.append({"id": str(item.get("id") or f"t{index}"), "text": item["text"]})
        return parsed
    texts = inp.get("texts")
    if isinstance(texts, list) and texts and all(isinstance(text, str) for text in texts):
        return [{"id": f"t{index}", "text": text} for index, text in enumerate(texts)]
    raise ValueError("input.texts or input.items is required")


def parse_rerank_request(inp: dict[str, Any]) -> tuple[str, list[dict[str, str]], int]:
    query = inp.get("query")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query is required")
    raw_candidates = inp.get("candidates")
    if raw_candidates is None and isinstance(inp.get("documents"), list):
        raw_candidates = [
            {"id": f"d{index}", "text": text}
            for index, text in enumerate(inp["documents"])
            if isinstance(text, str)
        ]
    if not isinstance(raw_candidates, list) or not raw_candidates:
        raise ValueError("candidates are required")
    if len(raw_candidates) > MAX_RERANK_CANDIDATES:
        raise ValueError(f"at most {MAX_RERANK_CANDIDATES} candidates are accepted")
    candidates: list[dict[str, str]] = []
    for index, item in enumerate(raw_candidates):
        if isinstance(item, str):
            candidates.append({"id": f"d{index}", "text": item})
            continue
        if not isinstance(item, dict) or not isinstance(item.get("text"), str):
            raise ValueError("each candidate needs text")
        candidates.append({"id": str(item.get("id") or f"d{index}"), "text": item["text"]})
    top_n = inp.get("top_n", len(candidates))
    if not isinstance(top_n, int) or isinstance(top_n, bool) or top_n < 1:
        top_n = len(candidates)
    return query.strip(), candidates, min(top_n, len(candidates))


def consumer_record(
    item_id: str,
    vector: list[float],
    *,
    dimensions: int,
    normalisation: str,
    space_id_value: str,
) -> dict[str, Any]:
    return {
        "id": item_id,
        "vector": vector,
        "dimensions": dimensions,
        "normalisation": normalisation,
        "space_id": space_id_value,
    }


def cache_key(route_id: str, capability: str, request: dict[str, Any]) -> str | None:
    policy = request.get("policy") or {}
    if policy.get("data_classification") in {"confidential", "restricted"}:
        return None
    payload = {
        "route": route_id,
        "capability": capability,
        "input": request.get("input"),
        "profile": request.get("profile"),
        "capability_version": request.get("capability_version"),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


FORBIDDEN_CONSUMER_KEYS = {
    "model",
    "model_artifacts",
    "checkpoint",
    "gguf",
    "engine",
    "upstream_model",
}


def persist_records(db_path: Path, records: list[dict[str, Any]]) -> None:
    """Consumer-owned sqlite. The runtime never opens this file."""
    for record in records:
        forbidden = FORBIDDEN_CONSUMER_KEYS.intersection(record)
        if forbidden:
            raise ValueError(f"consumer record must not store {sorted(forbidden)}")
        dumped = json.dumps(record).lower()
        if "gguf" in dumped or ".onnx" in dumped:
            raise ValueError("consumer record must not store a model filename")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as con:
        con.execute(
            "CREATE TABLE IF NOT EXISTS vectors "
            "(id TEXT NOT NULL, space_id TEXT NOT NULL, dimensions INTEGER NOT NULL, "
            "normalisation TEXT NOT NULL, vector TEXT NOT NULL, PRIMARY KEY (id, space_id))"
        )
        for record in records:
            con.execute(
                "INSERT OR REPLACE INTO vectors "
                "(id, space_id, dimensions, normalisation, vector) VALUES (?, ?, ?, ?, ?)",
                (
                    record["id"],
                    record["space_id"],
                    record["dimensions"],
                    record["normalisation"],
                    json.dumps(record["vector"]),
                ),
            )


def retrieve(
    db_path: Path, query: list[float], *, space_id_value: str, top_k: int = 5
) -> list[dict[str, Any]]:
    with sqlite3.connect(db_path) as con:
        rows = con.execute(
            "SELECT id, vector FROM vectors WHERE space_id = ?",
            (space_id_value,),
        ).fetchall()
    scored = [
        {"id": item_id, "score": cosine(query, json.loads(blob))}
        for item_id, blob in rows
    ]
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:top_k]
