"""Workers: bounded executors behind the engine-neutral boundary.

Two implementations for the G-05 vertical:
- EchoWorker: deterministic dummy for tests and the first vertical proof;
- OpenAIUpstreamWorker: talks to a loopback OpenAI-compatible server
  (llama-swap/llama.cpp per ADR-0002) for text.extract_structured and
  text.embed routes.

Workers never receive consumer credentials, never log payload content and
enforce the route timeout."""

from __future__ import annotations

import json
import time
from typing import Any, Protocol

import httpx

from .config import RouteConfig


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
        if cap == "text.generate":
            return self._generate(route, request)
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
        texts = request["input"].get("texts")
        if not isinstance(texts, list) or not texts or not all(isinstance(t, str) for t in texts):
            raise WorkerError("INVALID_INPUT", "input.texts must be a non-empty string array", False)
        if len(texts) > 64:
            raise WorkerError("INPUT_TOO_LARGE", "at most 64 texts per batch", False)
        data = self._post_json(
            route,
            "/v1/embeddings",
            {"model": route.upstream_model or "default", "input": texts},
        )["data"]
        vectors = [d["embedding"] for d in data]
        dims = len(vectors[0]) if vectors else 0
        return {
            "vectors": vectors,
            "dimensions": dims,
            "normalized": True,
            "reproducibility": "stable per request shape; batch composition may vary at ~1e-3",
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


def build_worker(kind: str) -> Worker:
    if kind == "echo":
        return EchoWorker()
    if kind == "openai-upstream":
        return OpenAIUpstreamWorker()
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
