"""Workers: bounded executors behind the engine-neutral boundary.

Two implementations for the G-05 vertical:
- EchoWorker: deterministic dummy for tests and the first vertical proof;
- OpenAIUpstreamWorker: talks to a loopback OpenAI-compatible server
  (llama-swap/llama.cpp per ADR-0002) for text.extract_structured and
  text.embed routes.

Workers never receive consumer credentials, never log payload content and
enforce the route timeout."""

from __future__ import annotations

import base64
import json
import os
import time
from pathlib import Path
from typing import Any, Protocol

import httpx

from .audio import AudioError, transcribe_file
from .config import RouteConfig
from .document import DocumentError, extract_invoice_fields, extract_pdf_text, ocr_file
from .vectors import (
    MAX_EMBED_BATCH,
    l2_normalize,
    parse_embed_items,
    parse_rerank_request,
    space_id,
)
from .vision_specialists import assess_image, average_hash, detect_saturated_boxes, similarity


class WorkerError(RuntimeError):
    def __init__(self, code: str, message: str, retryable: bool):
        super().__init__(message)
        self.code = code
        self.retryable = retryable


class Worker(Protocol):
    def execute(self, route: RouteConfig, request: dict) -> dict: ...


class EchoWorker:
    """Deterministic worker: validates shape, echoes bounded input back.
    Used by tests and as the 'dummy worker' the mission requires."""

    def execute(self, route: RouteConfig, request: dict) -> dict:
        inp = request.get("input", {})
        text = str(inp.get("text", ""))
        if len(text) > route.max_input_chars:
            raise WorkerError("INPUT_TOO_LARGE", "input exceeds route limit", False)
        time.sleep(float(inp.get("simulate_work_s", 0)))
        if inp.get("simulate_crash"):
            raise WorkerError("WORKER_CRASHED", "simulated crash", True)
        synthetic_bytes = int(inp.get("synthetic_result_bytes", 0))
        if synthetic_bytes:
            if not 1 <= synthetic_bytes <= 2_000_000:
                raise WorkerError("INVALID_INPUT", "synthetic result size is invalid", False)
            return {"blob": "x" * synthetic_bytes}
        return {"echo": text[:2000], "length": len(text)}


class OpenAIUpstreamWorker:
    """Bounded adapter to a loopback OpenAI-compatible upstream."""

    def __init__(self, timeout_extra_s: float = 30.0):
        self._timeout_extra = timeout_extra_s

    def _client(self, route: RouteConfig) -> httpx.Client:
        assert route.upstream_base, "route missing upstream_base"
        return httpx.Client(
            base_url=route.upstream_base,
            timeout=route.timeout_ms / 1000 + self._timeout_extra,
            trust_env=False,
        )

    def execute(self, route: RouteConfig, request: dict) -> dict:
        cap = route.capability
        if cap == "text.extract_structured":
            return self._extract_structured(route, request)
        if cap == "text.embed":
            return self._embed(route, request)
        if cap == "search.rerank":
            return self._rerank(route, request)
        if cap == "text.generate":
            return self._generate(route, request)
        if cap in {"vision.analyze", "vision.extract_structured", "vision.classify"}:
            return self._vision(route, request)
        raise WorkerError("CAPABILITY_UNAVAILABLE", f"no upstream mapping for {cap}", False)

    def _post_json(self, route: RouteConfig, path: str, payload: dict) -> dict:
        with self._client(route) as client:
            try:
                with client.stream("POST", path, json=payload) as resp:
                    if resp.status_code != 200:
                        raise WorkerError(
                            "MODEL_LOAD_FAILED",
                            f"upstream status {resp.status_code}",
                            True,
                        )
                    content = bytearray()
                    for chunk in resp.iter_bytes():
                        if len(content) + len(chunk) > route.max_upstream_response_bytes:
                            raise WorkerError(
                                "OUTPUT_TOO_LARGE",
                                "upstream response exceeds the byte limit",
                                False,
                            )
                        content.extend(chunk)
            except httpx.TimeoutException as exc:
                raise WorkerError("TIMEOUT", "upstream timed out", True) from exc
            except httpx.HTTPError as exc:
                raise WorkerError("MODEL_LOAD_FAILED", "upstream unreachable", True) from exc
        try:
            decoded = json.loads(content)
        except json.JSONDecodeError as exc:
            raise WorkerError("MODEL_LOAD_FAILED", "upstream response is not JSON", True) from exc
        if not isinstance(decoded, dict):
            raise WorkerError("MODEL_LOAD_FAILED", "upstream response is invalid", True)
        return decoded

    def _extract_structured(self, route: RouteConfig, request: dict) -> dict:
        inp = request["input"]
        text = str(inp.get("text", ""))
        schema = request.get("output_schema") or inp.get("schema")
        if not text:
            raise WorkerError("INVALID_INPUT", "input.text is required", False)
        if not isinstance(schema, dict):
            raise WorkerError("INVALID_INPUT", "output_schema is required", False)
        if len(text) > route.max_input_chars:
            raise WorkerError("INPUT_TOO_LARGE", "input exceeds route limit", False)
        payload = {
            "model": route.upstream_model or "default",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Extract the requested fields from the document."
                        " Reply only with JSON. /no_think"
                    ),
                },
                {"role": "user", "content": text},
            ],
            "max_tokens": 512,
            "temperature": 0,
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "extraction", "schema": schema, "strict": True},
            },
        }
        raw = self._post_json(route, "/v1/chat/completions", payload)["choices"][0][
            "message"
        ]["content"]
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise WorkerError("OUTPUT_SCHEMA_FAILED", "model output is not JSON", True) from exc
        return {"data": parsed}

    def _embed(self, route: RouteConfig, request: dict) -> dict:
        try:
            items = parse_embed_items(request.get("input") or {})
        except ValueError as exc:
            raise WorkerError("INVALID_INPUT", str(exc), False) from exc
        if len(items) > MAX_EMBED_BATCH:
            raise WorkerError("INPUT_TOO_LARGE", "at most 64 texts per batch", False)
        for item in items:
            if len(item["text"]) > route.max_input_chars:
                raise WorkerError("INPUT_TOO_LARGE", "input exceeds route limit", False)
        texts = [item["text"] for item in items]
        data = self._post_json(
            route,
            "/v1/embeddings",
            {"model": route.upstream_model or "default", "input": texts},
        )["data"]
        try:
            vectors = [l2_normalize([float(value) for value in row["embedding"]]) for row in data]
        except (KeyError, TypeError, ValueError) as exc:
            raise WorkerError("MODEL_LOAD_FAILED", "upstream embeddings are invalid", True) from exc
        if len(vectors) != len(items):
            raise WorkerError("MODEL_LOAD_FAILED", "embedding count mismatch", True)
        dims = len(vectors[0]) if vectors else 0
        if any(len(vector) != dims for vector in vectors):
            raise WorkerError("MODEL_LOAD_FAILED", "embedding dimensions mismatch", True)
        profile = str(request.get("profile") or route.profiles[0])
        return {
            "items": [
                {"id": item["id"], "vector": vector}
                for item, vector in zip(items, vectors)
            ],
            "dimensions": dims,
            "normalisation": "l2",
            "space_id": space_id(route.capability, route.capability_version, profile),
            "reproducibility": (
                "stable per request shape; batch composition may vary at ~1e-3"
            ),
        }

    def _rerank(self, route: RouteConfig, request: dict) -> dict:
        try:
            query, candidates, top_n = parse_rerank_request(request.get("input") or {})
        except ValueError as exc:
            raise WorkerError("INVALID_INPUT", str(exc), False) from exc
        if len(query) > route.max_input_chars or any(
            len(item["text"]) > route.max_input_chars for item in candidates
        ):
            raise WorkerError("INPUT_TOO_LARGE", "input exceeds route limit", False)
        body = self._post_json(
            route,
            "/v1/rerank",
            {
                "model": route.upstream_model or "default",
                "query": query,
                "documents": [item["text"] for item in candidates],
                "top_n": top_n,
            },
        )
        ranked: list[dict[str, Any]] = []
        seen: set[str] = set()
        for row in body.get("results") or []:
            if not isinstance(row, dict):
                continue
            index = row.get("index")
            if not isinstance(index, int) or index < 0 or index >= len(candidates):
                continue
            candidate_id = candidates[index]["id"]
            if candidate_id in seen:
                continue
            seen.add(candidate_id)
            ranked.append(
                {
                    "id": candidate_id,
                    "score": float(row.get("relevance_score", 0)),
                }
            )
        ranked.sort(key=lambda item: item["score"], reverse=True)
        profile = str(request.get("profile") or route.profiles[0])
        return {
            "candidates": [
                {"id": item["id"], "score": item["score"], "rank": rank}
                for rank, item in enumerate(ranked[:top_n], start=1)
            ],
            "space_id": space_id(route.capability, route.capability_version, profile),
        }

    def _generate(self, route: RouteConfig, request: dict) -> dict:
        inp = request["input"]
        prompt = str(inp.get("prompt", ""))
        if not prompt:
            raise WorkerError("INVALID_INPUT", "input.prompt is required", False)
        if len(prompt) > route.max_input_chars:
            raise WorkerError("INPUT_TOO_LARGE", "input exceeds route limit", False)
        max_tokens = int(
            (request.get("constraints") or {}).get("max_output_tokens", 256)
        )
        response = self._post_json(
            route,
            "/v1/chat/completions",
            {
                "model": route.upstream_model or "default",
                "messages": [{"role": "user", "content": prompt + " /no_think"}],
                "max_tokens": min(max_tokens, 2048),
                "temperature": 0.2,
            },
        )
        return {"text": response["choices"][0]["message"]["content"]}

    def _vision(self, route: RouteConfig, request: dict) -> dict:
        files = request.get("media_files") or []
        if not files:
            raise WorkerError("INVALID_INPUT", "image upload is required", False)
        path = Path(files[0]["path"])
        header = path.read_bytes()[:5]
        if header == b"%PDF-":
            raise WorkerError("INVALID_INPUT", "vision route requires an image, not a PDF", False)
        quality = assess_image(path)
        if quality.get("unsupported"):
            return {
                "answer": None,
                "status": "unsupported",
                "review_required": True,
                "warnings": quality["warnings"],
            }
        question = str((request.get("input") or {}).get("question") or "").strip()
        if not question:
            raise WorkerError("INVALID_INPUT", "question is required", False)
        prompt = (
            "Answer the user's question about the image. "
            "Do not give a generic caption. If a detail is unreadable, say so. "
            f"Question: {question} /no_think"
        )
        raw = path.read_bytes()
        mime = "image/png" if raw.startswith(b"\x89PNG") else "image/jpeg"
        parts: list[dict[str, Any]] = [
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime};base64,{base64.b64encode(raw).decode('ascii')}"
                },
            },
        ]
        payload: dict[str, Any] = {
            "model": route.upstream_model or "default",
            "messages": [{"role": "user", "content": parts}],
            "max_tokens": int((request.get("constraints") or {}).get("max_output_tokens", 512)),
            "temperature": 0.1,
        }
        schema = request.get("output_schema")
        if route.capability == "vision.extract_structured":
            if not isinstance(schema, dict):
                raise WorkerError("INVALID_INPUT", "output_schema is required", False)
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "extraction", "schema": schema, "strict": True},
            }
        response = self._post_json(route, "/v1/chat/completions", payload)
        content = response["choices"][0]["message"]["content"]
        if route.capability == "vision.extract_structured":
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError as exc:
                raise WorkerError("OUTPUT_SCHEMA_FAILED", "model output is not JSON", True) from exc
            return {"data": parsed, "review_required": False, "warnings": []}
        return {
            "answer": content,
            "status": "answered",
            "review_required": False,
            "warnings": [],
        }


def _media_path(request: dict) -> Path:
    files = request.get("media_files") or []
    if not files:
        raise WorkerError("INVALID_INPUT", "upload_id is required", False)
    return Path(files[0]["path"])


def _wrap_document(exc: DocumentError) -> WorkerError:
    return WorkerError(exc.code, exc.message, False)


class DocumentNativeWorker:
    def execute(self, route: RouteConfig, request: dict) -> dict:
        try:
            return extract_pdf_text(_media_path(request))
        except DocumentError as exc:
            raise _wrap_document(exc) from exc


class DocumentOcrWorker:
    def execute(self, route: RouteConfig, request: dict) -> dict:
        try:
            return ocr_file(_media_path(request))
        except DocumentError as exc:
            raise _wrap_document(exc) from exc


class DocumentParseWorker:
    def execute(self, route: RouteConfig, request: dict) -> dict:
        try:
            ocr = ocr_file(_media_path(request))
        except DocumentError as exc:
            raise _wrap_document(exc) from exc
        return {
            "pages": ocr["pages"],
            "regions": ocr["regions"],
            "reading_order": [region["text"] for region in ocr["regions"]],
            "engine": ocr["engine"],
            "review_required": ocr["review_required"],
            "warnings": ocr["warnings"],
        }


class DocumentStructuredWorker:
    def execute(self, route: RouteConfig, request: dict) -> dict:
        path = _media_path(request)
        try:
            header = path.read_bytes()[:5]
            if header == b"%PDF-":
                native = extract_pdf_text(path)
                text = native["pages"][0]["text"]
                warnings = list(native["warnings"])
                review = bool(native["review_required"])
                if native["image_only"]:
                    ocr = ocr_file(path)
                    text = ocr["text"]
                    warnings.extend(ocr["warnings"])
                    review = review or ocr["review_required"]
            else:
                ocr = ocr_file(path)
                text = ocr["text"]
                warnings = list(ocr["warnings"])
                review = bool(ocr["review_required"])
        except DocumentError as exc:
            raise _wrap_document(exc) from exc
        extracted = extract_invoice_fields(text)
        fields = extracted["fields"]
        schema = request.get("output_schema")
        if isinstance(schema, dict):
            allowed = set((schema.get("properties") or {}).keys())
            if allowed:
                fields = {key: value for key, value in fields.items() if key in allowed}
        return {
            "data": fields,
            "missing": extracted["missing"],
            "review_required": review or extracted["review_required"],
            "warnings": warnings,
            "evidence": extracted["evidence"],
        }


class ImageEmbedWorker:
    def execute(self, route: RouteConfig, request: dict) -> dict:
        files = request.get("media_files") or []
        if len(files) >= 2:
            return similarity(Path(files[0]["path"]), Path(files[1]["path"]))
        if not files:
            raise WorkerError("INVALID_INPUT", "upload_id is required", False)
        digest = average_hash(Path(files[0]["path"]))
        return {
            "hash": digest,
            "dimensions": 64,
            "normalisation": "none",
            "engine": "average-hash",
            "warnings": [
                {
                    "code": "HASH_NOT_SEMANTIC",
                    "message": "perceptual hash is not a semantic embedding",
                }
            ],
        }


class ObjectDetectWorker:
    def execute(self, route: RouteConfig, request: dict) -> dict:
        path = _media_path(request)
        quality = assess_image(path)
        if quality.get("unsupported"):
            return {
                "objects": [],
                "review_required": True,
                "warnings": quality["warnings"],
            }
        return detect_saturated_boxes(path)


class WhisperCppWorker:
    def execute(self, route: RouteConfig, request: dict) -> dict:
        path = _media_path(request)
        language = str((request.get("input") or {}).get("language") or "auto")
        cli = route.worker_binary or os.environ.get("HERMES_WHISPER_CLI") or ""
        model = route.upstream_model or os.environ.get("HERMES_WHISPER_MODEL") or ""
        try:
            return transcribe_file(
                path,
                cli=cli,
                model=model,
                language=language,
                timeout_s=max(5.0, route.timeout_ms / 1000),
                workdir=path.parent / "decode",
            )
        except AudioError as exc:
            retryable = exc.code in {"TIMEOUT", "MODEL_LOAD_FAILED"}
            raise WorkerError(exc.code, str(exc), retryable) from exc


def build_worker(kind: str) -> Worker:
    if kind == "echo":
        return EchoWorker()
    if kind == "openai-upstream":
        return OpenAIUpstreamWorker()
    if kind == "document-native":
        return DocumentNativeWorker()
    if kind == "document-ocr":
        return DocumentOcrWorker()
    if kind == "document-parse":
        return DocumentParseWorker()
    if kind == "document-structured":
        return DocumentStructuredWorker()
    if kind == "image-embed":
        return ImageEmbedWorker()
    if kind == "object-detect":
        return ObjectDetectWorker()
    if kind == "whisper-cpp":
        return WhisperCppWorker()
    raise ValueError(f"unknown worker kind: {kind}")


def run_worker_process(route: RouteConfig, request: dict, result_queue: Any) -> None:
    """Child-process entrypoint. Only bounded result/error metadata crosses
    back to the control plane; unexpected exceptions never expose payloads."""
    try:
        output = build_worker(route.worker).execute(route, request)
        result_queue.put({"ok": True, "output": output})
    except WorkerError as exc:
        result_queue.put(
            {
                "ok": False,
                "code": exc.code,
                "message": str(exc),
                "retryable": exc.retryable,
            }
        )
    except BaseException:
        result_queue.put(
            {
                "ok": False,
                "code": "WORKER_CRASHED",
                "message": "worker process failed",
                "retryable": True,
            }
        )


def validate_against_schema(data: Any, schema: dict) -> list[str]:
    """Deterministic output validation. Returns a list of violations."""
    import jsonschema

    validator = jsonschema.Draft202012Validator(schema)
    return [f"{'/'.join(map(str, e.path)) or '<root>'}: {e.message}" for e in validator.iter_errors(data)]
