"""FastAPI control plane for G-05.

The native capability API is normative. The OpenAI-compatible surface is a
thin adapter; it cannot select engine flags or bypass admission. Request
content is never logged by this module.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import threading
import time
import uuid
from contextlib import asynccontextmanager
from contextvars import ContextVar
from typing import Annotated, Any, Literal

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Request, Response, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, ConfigDict, Field

from . import RUNTIME_VERSION
from .config import RuntimeConfig
from .coordinator import (
    CapabilityUnavailable,
    InputTooLarge,
    InvalidJobInput,
    JobCoordinator,
    QueueFull,
)
from .store import IdempotencyConflict, JobRow, JobStore

REQUEST_ID: ContextVar[str] = ContextVar("request_id", default="req_unavailable")

ERROR_HTTP_STATUS = {
    "INVALID_INPUT": 400,
    "INPUT_TOO_LARGE": 413,
    "CAPABILITY_UNAVAILABLE": 503,
    "RESOURCE_EXHAUSTED": 503,
    "TIMEOUT": 504,
    "CANCELLED": 409,
    "MODEL_LOAD_FAILED": 503,
    "WORKER_CRASHED": 503,
    "OUTPUT_SCHEMA_FAILED": 422,
    "OUTPUT_TOO_LARGE": 422,
    "INTERNAL_ERROR": 500,
}


class JobPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data_classification: Literal["public", "internal", "confidential", "restricted"]
    cloud_fallback_allowed: bool
    allowed_remote_providers: list[str] = Field(default_factory=list)
    retention: Literal["none", "job_ttl", "consumer_policy"]
    human_confirmation_for_remote: bool = True


class JobConstraints(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timeout_ms: int | None = Field(default=None, ge=100, le=3_600_000)
    max_output_tokens: int | None = Field(default=None, ge=1, le=65_536)
    priority: Literal["interactive", "normal", "batch"] | None = None
    allow_degraded_route: bool = False


class JobRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capability: str = Field(pattern="^[a-z][a-z0-9_]*(\\.[a-z][a-z0-9_]*)+$")
    capability_version: str = Field(min_length=1)
    profile: str = Field(pattern="^(fast|balanced|accurate)$")
    input: dict[str, Any]
    output_schema: dict[str, Any] | None = None
    constraints: JobConstraints | None = None
    policy: JobPolicy


class OpenAITextPart(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["text"]
    text: str = Field(min_length=1, max_length=200_000)


class OpenAIImageUrl(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str = Field(min_length=8, max_length=6_000_000)


class OpenAIImagePart(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["image_url"]
    image_url: OpenAIImageUrl


class OpenAIMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["system", "user", "assistant", "tool"]
    content: str | list[OpenAITextPart | OpenAIImagePart] = Field(min_length=1)


class OpenAIChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str = Field(min_length=1, max_length=100)
    messages: list[OpenAIMessage] = Field(min_length=1, max_length=128)
    max_tokens: int = Field(default=256, ge=1, le=2048)
    stream: bool = False


class OpenAIEmbeddingsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str = Field(min_length=1, max_length=100)
    input: str | list[str]


class OpenAIRerankRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str = Field(min_length=1, max_length=100)
    query: str = Field(min_length=1, max_length=200_000)
    documents: list[str] = Field(min_length=1, max_length=100)
    top_n: int | None = Field(default=None, ge=1, le=100)


class Principal(BaseModel):
    name: str
    scopes: tuple[str, ...]


def error_response(
    code: str,
    message: str,
    http_status: int,
    *,
    retryable: bool = False,
    retry_after_seconds: int | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {
        "error": {
            "code": code,
            "message": message,
            "retryable": retryable,
            "request_id": REQUEST_ID.get(),
        }
    }
    if retry_after_seconds is not None:
        body["error"]["retry_after_seconds"] = retry_after_seconds
    headers = (
        {"Retry-After": str(retry_after_seconds)}
        if retry_after_seconds is not None
        else None
    )
    return JSONResponse(body, status_code=http_status, headers=headers)


def _has_scope(principal: Principal, wanted: str) -> bool:
    if wanted in principal.scopes:
        return True
    family = wanted.split(":")
    wildcard = ":".join(family[:-1] + ["*"])
    return wildcard in principal.scopes


def create_app(config: RuntimeConfig, *, max_upload_bytes: int = 20 * 1024 * 1024) -> FastAPI:
    store = JobStore(config.db_path)
    counters = {"requests": 0, "auth_failures": 0, "uploads": 0}
    upload_lock = threading.Lock()
    uploads: dict[str, bytes] = {}
    coordinator = JobCoordinator(config, store, media_store=uploads)
    max_upload_store_bytes = max_upload_bytes * 2
    openai_profiles = sorted(
        {
            profile
            for route in config.routes
            if route.capability == "text.generate" and route.sync_allowed
            for profile in route.profiles
        }
    )
    openai_aliases = {f"local-{profile}": profile for profile in openai_profiles}
    embed_aliases: dict[str, str] = {}
    rerank_aliases: dict[str, str] = {}
    transcribe_aliases: dict[str, str] = {}
    for route in config.routes:
        for profile in route.profiles:
            if route.sync_allowed:
                if route.capability == "text.embed":
                    embed_aliases[f"hlair/embed-{profile}"] = profile
                    embed_aliases[f"local-embed-{profile}"] = profile
                if route.capability == "search.rerank":
                    rerank_aliases[f"hlair/rerank-{profile}"] = profile
                    rerank_aliases[f"local-rerank-{profile}"] = profile
            if route.capability == "audio.transcribe":
                transcribe_aliases[f"hlair/transcribe-{profile}"] = profile
                transcribe_aliases[f"local-transcribe-{profile}"] = profile

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        coordinator.start()
        app.state.store = store
        app.state.coordinator = coordinator
        app.state.uploads = uploads
        try:
            yield
        finally:
            coordinator.stop()
            with upload_lock:
                uploads.clear()

    app = FastAPI(
        title="Hermes Local AI Runtime",
        version=RUNTIME_VERSION,
        lifespan=lifespan,
        openapi_url=None,
        docs_url=None,
        redoc_url=None,
    )

    @app.middleware("http")
    async def count_requests(request: Request, call_next):
        counters["requests"] += 1
        request_id = f"req_{uuid.uuid4().hex[:20]}"
        context_token = REQUEST_ID.set(request_id)
        try:
            if request.method == "POST" and request.url.path in {
                "/api/v1/jobs",
                "/v1/chat/completions",
            }:
                content_length = request.headers.get("content-length")
                if content_length is not None:
                    try:
                        if int(content_length) > config.budget.request_max_bytes:
                            return error_response(
                                "INPUT_TOO_LARGE", "request exceeds the byte limit", 413
                            )
                    except ValueError:
                        return error_response("INVALID_INPUT", "invalid Content-Length", 400)
                content = bytearray()
                async for chunk in request.stream():
                    content.extend(chunk)
                    if len(content) > config.budget.request_max_bytes:
                        return error_response(
                            "INPUT_TOO_LARGE", "request exceeds the byte limit", 413
                        )
                request._body = bytes(content)
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            REQUEST_ID.reset(context_token)

    @app.exception_handler(RequestValidationError)
    async def validation_error(_request: Request, exc: RequestValidationError):
        # Exclude submitted values: validation diagnostics must not echo payloads.
        details = [
            {"location": list(e["loc"]), "message": e["msg"], "type": e["type"]}
            for e in exc.errors()
        ]
        return JSONResponse(
            {
                "error": {
                    "code": "INVALID_INPUT",
                    "message": "request validation failed",
                    "retryable": False,
                    "request_id": REQUEST_ID.get(),
                    "details": details,
                }
            },
            status_code=400,
        )

    async def principal(
        authorization: Annotated[str | None, Header()] = None,
    ) -> Principal:
        if config.dev_mode and not config.tokens:
            return Principal(
                name="dev-loopback",
                scopes=("capability:invoke:*", "job:read:self", "job:cancel:self", "system:read"),
            )
        if not authorization or not authorization.startswith("Bearer "):
            counters["auth_failures"] += 1
            raise HTTPException(status_code=401, detail="AUTH_REQUIRED")
        candidate = authorization[7:]
        for token in config.tokens:
            if hmac.compare_digest(candidate, token.token):
                return Principal(name=token.name, scopes=token.scopes)
        counters["auth_failures"] += 1
        raise HTTPException(status_code=401, detail="AUTH_REQUIRED")

    @app.exception_handler(HTTPException)
    async def http_error(_request: Request, exc: HTTPException):
        code = str(exc.detail)
        if code not in {
            "AUTH_REQUIRED",
            "SCOPE_DENIED",
            "NOT_FOUND",
            "CAPABILITY_UNAVAILABLE",
        }:
            code = "INTERNAL_ERROR"
        messages = {
            "AUTH_REQUIRED": "a valid bearer token is required",
            "SCOPE_DENIED": "the token does not have the required scope",
            "NOT_FOUND": "resource not found",
            "CAPABILITY_UNAVAILABLE": "no approved route matches the request",
            "INTERNAL_ERROR": "request failed",
        }
        return error_response(code, messages[code], exc.status_code)

    def require_scope(p: Principal, scope: str) -> None:
        if not _has_scope(p, scope):
            raise HTTPException(status_code=403, detail="SCOPE_DENIED")

    def owned_job(job_id: str, p: Principal, scope: str) -> JobRow:
        require_scope(p, scope)
        job = store.get(job_id)
        # Deliberately hide cross-consumer existence.
        if job is None or job.consumer != p.name:
            raise HTTPException(status_code=404, detail="NOT_FOUND")
        return job

    @app.get("/healthz")
    async def healthz() -> dict:
        return {"status": "ok"}

    @app.get("/readyz")
    async def readyz() -> dict:
        # SQLite was opened at construction and coordinator is created. No route
        # readiness claim is inferred from a process merely existing.
        return {
            "status": "ready",
            "control_plane": True,
            "approved_routes": len(config.routes),
        }

    @app.get("/api/v1/system")
    async def system(p: Principal = Depends(principal)) -> dict:
        require_scope(p, "system:read")
        return {
            "runtime": "hermes-local-ai-runtime",
            "version": RUNTIME_VERSION,
            "listen_policy": "loopback-only",
            "cloud_fallback": False,
            "request_content_logging": False,
            "hardware_profile": "hermes-cpu-8vcpu-16gib",
            "recovered_jobs_at_start": coordinator.recovered_jobs,
            "admission": coordinator.admission.snapshot(),
        }

    @app.get("/api/v1/capabilities")
    async def capabilities(p: Principal = Depends(principal)) -> dict:
        require_scope(p, "system:read")
        by_key: dict[tuple[str, str], dict] = {}
        for route in config.routes:
            key = (route.capability, route.capability_version)
            entry = by_key.setdefault(
                key,
                {
                    "id": route.capability,
                    "version": route.capability_version,
                    "profiles": [],
                    "sync_allowed": route.sync_allowed,
                    "status": "available",
                },
            )
            for profile in route.profiles:
                if profile not in entry["profiles"]:
                    entry["profiles"].append(profile)
        return {"capabilities": list(by_key.values())}

    @app.post("/api/v1/jobs")
    async def submit_job(
        body: JobRequest,
        p: Principal = Depends(principal),
        idempotency_key: Annotated[str | None, Header()] = None,
    ) -> Response:
        require_scope(p, f"capability:invoke:{body.capability.split('.')[0]}")
        if idempotency_key is not None and not (8 <= len(idempotency_key) <= 128):
            return error_response("INVALID_INPUT", "invalid Idempotency-Key", 400)
        request_data = body.model_dump(exclude_none=True)
        try:
            submission = coordinator.submit(p.name, request_data, idempotency_key)
        except CapabilityUnavailable:
            return error_response(
                "CAPABILITY_UNAVAILABLE", "no approved route matches the request", 503
            )
        except IdempotencyConflict:
            return error_response(
                "IDEMPOTENCY_CONFLICT",
                "the idempotency key was already used with a different request",
                409,
            )
        except InputTooLarge:
            return error_response("INPUT_TOO_LARGE", "request exceeds the byte limit", 413)
        except InvalidJobInput as exc:
            return error_response("INVALID_INPUT", str(exc), 400)
        except QueueFull as exc:
            return error_response(
                "QUEUE_FULL",
                str(exc),
                429,
                retryable=True,
                retry_after_seconds=exc.retry_after_seconds,
            )
        payload = job_view(submission.job)
        payload["status_url"] = f"/api/v1/jobs/{submission.job.job_id}"
        payload["result_url"] = f"/api/v1/jobs/{submission.job.job_id}/result"
        return JSONResponse(
            payload,
            status_code=202 if submission.created else 200,
            headers={"Location": payload["status_url"]} if submission.created else None,
        )

    @app.get("/api/v1/jobs/{job_id}")
    async def get_job(job_id: str, p: Principal = Depends(principal)) -> dict:
        return job_view(owned_job(job_id, p, "job:read:self"))

    @app.get("/api/v1/jobs/{job_id}/result")
    async def get_result(
        job_id: str, p: Principal = Depends(principal)
    ) -> Response:
        job = owned_job(job_id, p, "job:read:self")
        result = coordinator.result(job_id)
        if job.status != "succeeded" or result is None:
            return error_response(
                "RESULT_NOT_READY", f"result is not available (status: {job.status})", 409
            )
        return JSONResponse(
            {
                "job_id": job.job_id,
                "status": job.status,
                **result,
                "timing": job.timing,
            }
        )

    @app.post("/api/v1/jobs/{job_id}/cancel")
    async def cancel_job(
        job_id: str, p: Principal = Depends(principal)
    ) -> Response:
        job = owned_job(job_id, p, "job:cancel:self")
        if job.status in {"succeeded", "failed", "cancelled", "expired", "rejected"}:
            return JSONResponse(job_view(job), status_code=200)
        store.request_cancel(job_id)
        current = store.get(job_id)
        return JSONResponse(job_view(current or job), status_code=202)

    @app.post("/api/v1/uploads")
    async def upload(
        request: Request,
        p: Principal = Depends(principal),
        content_type: Annotated[str | None, Header(alias="Content-Type")] = None,
        content_length: Annotated[int | None, Header(alias="Content-Length")] = None,
    ) -> Response:
        require_scope(p, "capability:invoke:*")
        if content_length is not None and content_length > max_upload_bytes:
            return error_response("INPUT_TOO_LARGE", "upload exceeds the byte limit", 413)
        upload_id = f"upl_{uuid.uuid4().hex[:20]}"
        size = 0
        digest = hashlib.sha256()
        content = bytearray()
        try:
            async for chunk in request.stream():
                size += len(chunk)
                if size > max_upload_bytes:
                    raise UploadTooLarge
                digest.update(chunk)
                content.extend(chunk)
        except UploadTooLarge:
            return error_response("INPUT_TOO_LARGE", "upload exceeds the byte limit", 413)
        with upload_lock:
            stored_bytes = sum(len(value) for value in uploads.values())
            if len(uploads) >= 8 or stored_bytes + size > max_upload_store_bytes:
                return error_response(
                    "QUEUE_FULL", "volatile upload store is full", 429, retryable=True
                )
            uploads[upload_id] = bytes(content)
        counters["uploads"] += 1
        return JSONResponse(
            {
                "upload_id": upload_id,
                "size_bytes": size,
                "sha256": digest.hexdigest(),
                "media_type": content_type or "application/octet-stream",
            },
            status_code=201,
        )

    @app.get("/metrics", response_class=PlainTextResponse)
    async def metrics(p: Principal = Depends(principal)) -> str:
        require_scope(p, "system:read")
        status_counts = store.counts_by_status()
        admission = coordinator.admission.snapshot()
        lines = [
            "# HELP hermes_runtime_requests_total HTTP requests received.",
            "# TYPE hermes_runtime_requests_total counter",
            f"hermes_runtime_requests_total {counters['requests']}",
            "# HELP hermes_runtime_auth_failures_total Authentication failures.",
            "# TYPE hermes_runtime_auth_failures_total counter",
            f"hermes_runtime_auth_failures_total {counters['auth_failures']}",
            "# HELP hermes_runtime_jobs Jobs by bounded status label.",
            "# TYPE hermes_runtime_jobs gauge",
        ]
        for job_status, count in sorted(status_counts.items()):
            lines.append(f'hermes_runtime_jobs{{status="{job_status}"}} {count}')
        lines.extend(
            [
                f"hermes_runtime_queue_depth {admission['queued']}",
                f"hermes_runtime_memory_available_mib {admission['mem_available_mib']}",
            ]
        )
        return "\n".join(lines) + "\n"

    @app.post("/v1/chat/completions")
    async def openai_chat(
        body: OpenAIChatRequest,
        p: Principal = Depends(principal),
    ) -> Response:
        if body.stream:
            return error_response(
                "CAPABILITY_UNAVAILABLE", "streaming is not implemented in G-05", 501
            )
        vision_profile = {
            "hlair/vision-balanced": "balanced",
            "hlair/vision-fast": "fast",
            "hlair/vision-accurate": "accurate",
            "local-vision": "balanced",
        }.get(body.model)
        if vision_profile is not None:
            require_scope(p, "capability:invoke:vision")
            texts: list[str] = []
            upload_ids: list[str] = []
            for message in body.messages:
                if isinstance(message.content, str):
                    texts.append(message.content)
                    continue
                for part in message.content:
                    if isinstance(part, OpenAITextPart):
                        texts.append(part.text)
                    else:
                        url = part.image_url.url
                        if not url.startswith("data:") or "," not in url:
                            return error_response(
                                "INVALID_INPUT", "only data: image URLs are accepted", 400
                            )
                        header, payload = url.split(",", 1)
                        if ";base64" not in header:
                            return error_response(
                                "INVALID_INPUT", "image URL must be base64", 400
                            )
                        try:
                            raw = base64.b64decode(payload, validate=True)
                        except Exception:
                            return error_response("INVALID_INPUT", "invalid image data", 400)
                        if len(raw) > max_upload_bytes:
                            return error_response(
                                "INPUT_TOO_LARGE", "upload exceeds the byte limit", 413
                            )
                        upload_id = f"upl_{uuid.uuid4().hex[:20]}"
                        with upload_lock:
                            uploads[upload_id] = raw
                        upload_ids.append(upload_id)
            question = "\n".join(texts).strip()
            if not question:
                return error_response("INVALID_INPUT", "question is required", 400)
            if not upload_ids:
                return error_response("INVALID_INPUT", "image is required", 400)
            route = config.route_for("vision.analyze", "1.0.0", vision_profile)
            if route is None or not route.sync_allowed:
                return error_response(
                    "CAPABILITY_UNAVAILABLE", "no synchronous vision route", 503
                )
            request_data = {
                "capability": "vision.analyze",
                "capability_version": "1.0.0",
                "profile": vision_profile,
                "input": {
                    "question": question,
                    "upload_id": upload_ids[0],
                    "images": [{"upload_id": item} for item in upload_ids],
                },
                "constraints": {
                    "timeout_ms": route.timeout_ms,
                    "max_output_tokens": body.max_tokens,
                    "priority": "interactive",
                    "allow_degraded_route": False,
                },
                "policy": {
                    "data_classification": "internal",
                    "cloud_fallback_allowed": False,
                    "retention": "none",
                },
            }
        else:
            require_scope(p, "capability:invoke:text")
            profile = openai_aliases.get(body.model)
            if profile is None:
                raise HTTPException(status_code=404, detail="NOT_FOUND")
            if any(not isinstance(message.content, str) for message in body.messages):
                return error_response(
                    "INVALID_INPUT", "text aliases accept string content only", 400
                )
            route = config.route_for("text.generate", "1.0.0", profile)
            if route is None or not route.sync_allowed:
                return error_response(
                    "CAPABILITY_UNAVAILABLE", "no synchronous text route", 503
                )
            prompt = "\n".join(f"{m.role}: {m.content}" for m in body.messages)
            request_data = {
                "capability": "text.generate",
                "capability_version": "1.0.0",
                "profile": profile,
                "input": {"text": body.messages[-1].content, "prompt": prompt},
                "constraints": {
                    "timeout_ms": route.timeout_ms,
                    "max_output_tokens": body.max_tokens,
                    "priority": "interactive",
                    "allow_degraded_route": False,
                },
                "policy": {
                    "data_classification": "internal",
                    "cloud_fallback_allowed": False,
                    "retention": "none",
                },
            }
        try:
            submission = coordinator.submit(p.name, request_data, None)
        except CapabilityUnavailable:
            return error_response(
                "CAPABILITY_UNAVAILABLE", "no approved route", 503
            )
        except InvalidJobInput as exc:
            return error_response("INVALID_INPUT", str(exc), 400)
        except QueueFull as exc:
            return error_response(
                "QUEUE_FULL",
                str(exc),
                429,
                retryable=True,
                retry_after_seconds=exc.retry_after_seconds,
            )
        job = await asyncio.to_thread(
            coordinator.wait,
            submission.job.job_id,
            route.timeout_ms / 1000 + 1,
        )
        if job is None or job.status not in {"succeeded", "failed", "rejected", "cancelled"}:
            store.request_cancel(submission.job.job_id)
            return error_response("TIMEOUT", "job did not complete in time", 504, retryable=True)
        result = coordinator.result(job.job_id)
        if job.status != "succeeded" or result is None:
            err = job.error or {"code": "INTERNAL_ERROR", "message": "job failed"}
            return error_response(
                err["code"],
                err["message"],
                ERROR_HTTP_STATUS.get(err["code"], 500),
                retryable=bool(err.get("retryable")),
            )
        output = result["result"]
        content = output.get(
            "answer", output.get("text", output.get("echo", json.dumps(output)))
        )
        if not isinstance(content, str):
            content = json.dumps(content)
        created = int(time.time())
        return JSONResponse(
            {
                "id": f"chatcmpl-{job.job_id[4:]}",
                "object": "chat.completion",
                "created": created,
                "model": body.model,
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": content},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                "hermes_provenance": result["provenance"],
            }
        )

    @app.get("/v1/models")
    async def openai_models(p: Principal = Depends(principal)) -> dict:
        require_scope(p, "system:read")
        models = [
            {"id": f"local-{profile}", "object": "model", "owned_by": "local-runtime"}
            for profile in openai_profiles
        ]
        if any(
            route.capability == "vision.analyze" and route.sync_allowed
            for route in config.routes
        ):
            models.append(
                {
                    "id": "hlair/vision-balanced",
                    "object": "model",
                    "owned_by": "local-runtime",
                }
            )
        for alias in sorted(set(embed_aliases) | set(rerank_aliases) | set(transcribe_aliases)):
            models.append({"id": alias, "object": "model", "owned_by": "local-runtime"})
        return {"object": "list", "data": models}

    @app.post("/v1/embeddings")
    async def openai_embeddings(
        body: OpenAIEmbeddingsRequest, p: Principal = Depends(principal)
    ):
        require_scope(p, "capability:invoke:text")
        profile = embed_aliases.get(body.model)
        if profile is None:
            raise HTTPException(status_code=404, detail="NOT_FOUND")
        route = config.route_for("text.embed", "1.0.0", profile)
        if route is None or not route.sync_allowed:
            return error_response(
                "CAPABILITY_UNAVAILABLE", "no synchronous embed route", 503
            )
        texts = [body.input] if isinstance(body.input, str) else body.input
        if not texts or not all(isinstance(item, str) for item in texts):
            return error_response("INVALID_INPUT", "input must be a string or string array", 400)
        request_data = {
            "capability": "text.embed",
            "capability_version": "1.0.0",
            "profile": profile,
            "input": {"texts": texts},
            "constraints": {
                "timeout_ms": route.timeout_ms,
                "priority": "interactive",
                "allow_degraded_route": False,
            },
            "policy": {
                "data_classification": "internal",
                "cloud_fallback_allowed": False,
                "retention": "none",
            },
        }
        try:
            submission = coordinator.submit(p.name, request_data, None)
        except CapabilityUnavailable:
            return error_response("CAPABILITY_UNAVAILABLE", "no approved route", 503)
        except InvalidJobInput as exc:
            return error_response("INVALID_INPUT", str(exc), 400)
        except QueueFull as exc:
            return error_response(
                "QUEUE_FULL",
                str(exc),
                429,
                retryable=True,
                retry_after_seconds=exc.retry_after_seconds,
            )
        job = await asyncio.to_thread(
            coordinator.wait,
            submission.job.job_id,
            route.timeout_ms / 1000 + 1,
        )
        if job is None or job.status not in {"succeeded", "failed", "rejected", "cancelled"}:
            store.request_cancel(submission.job.job_id)
            return error_response("TIMEOUT", "job did not complete in time", 504, retryable=True)
        result = coordinator.result(job.job_id)
        if job.status != "succeeded" or result is None:
            err = job.error or {"code": "INTERNAL_ERROR", "message": "job failed"}
            return error_response(
                err["code"],
                err["message"],
                ERROR_HTTP_STATUS.get(err["code"], 500),
                retryable=bool(err.get("retryable")),
            )
        items = result["result"]["items"]
        return JSONResponse(
            {
                "object": "list",
                "model": body.model,
                "data": [
                    {
                        "object": "embedding",
                        "index": index,
                        "embedding": item["vector"],
                    }
                    for index, item in enumerate(items)
                ],
                "usage": {"prompt_tokens": 0, "total_tokens": 0},
                "hermes_space_id": result["result"]["space_id"],
                "hermes_provenance": result["provenance"],
            }
        )

    @app.post("/v1/rerank")
    async def openai_rerank(body: OpenAIRerankRequest, p: Principal = Depends(principal)):
        require_scope(p, "capability:invoke:search")
        profile = rerank_aliases.get(body.model)
        if profile is None:
            raise HTTPException(status_code=404, detail="NOT_FOUND")
        route = config.route_for("search.rerank", "1.0.0", profile)
        if route is None or not route.sync_allowed:
            return error_response(
                "CAPABILITY_UNAVAILABLE", "no synchronous rerank route", 503
            )
        request_data = {
            "capability": "search.rerank",
            "capability_version": "1.0.0",
            "profile": profile,
            "input": {
                "query": body.query,
                "documents": body.documents,
                "top_n": body.top_n or len(body.documents),
            },
            "constraints": {
                "timeout_ms": route.timeout_ms,
                "priority": "interactive",
                "allow_degraded_route": False,
            },
            "policy": {
                "data_classification": "internal",
                "cloud_fallback_allowed": False,
                "retention": "none",
            },
        }
        try:
            submission = coordinator.submit(p.name, request_data, None)
        except CapabilityUnavailable:
            return error_response("CAPABILITY_UNAVAILABLE", "no approved route", 503)
        except InvalidJobInput as exc:
            return error_response("INVALID_INPUT", str(exc), 400)
        except QueueFull as exc:
            return error_response(
                "QUEUE_FULL",
                str(exc),
                429,
                retryable=True,
                retry_after_seconds=exc.retry_after_seconds,
            )
        job = await asyncio.to_thread(
            coordinator.wait,
            submission.job.job_id,
            route.timeout_ms / 1000 + 1,
        )
        if job is None or job.status not in {"succeeded", "failed", "rejected", "cancelled"}:
            store.request_cancel(submission.job.job_id)
            return error_response("TIMEOUT", "job did not complete in time", 504, retryable=True)
        result = coordinator.result(job.job_id)
        if job.status != "succeeded" or result is None:
            err = job.error or {"code": "INTERNAL_ERROR", "message": "job failed"}
            return error_response(
                err["code"],
                err["message"],
                ERROR_HTTP_STATUS.get(err["code"], 500),
                retryable=bool(err.get("retryable")),
            )
        id_to_index = {f"d{index}": index for index in range(len(body.documents))}
        return JSONResponse(
            {
                "model": body.model,
                "results": [
                    {
                        "index": id_to_index.get(item["id"], 0),
                        "relevance_score": item["score"],
                    }
                    for item in result["result"]["candidates"]
                ],
                "hermes_provenance": result["provenance"],
            }
        )

    @app.post("/v1/audio/transcriptions")
    async def openai_transcriptions(
        p: Principal = Depends(principal),
        file: UploadFile = File(...),
        model: str = Form(...),
        language: str | None = Form(None),
    ):
        require_scope(p, "capability:invoke:audio")
        profile = transcribe_aliases.get(model)
        if profile is None:
            raise HTTPException(status_code=404, detail="NOT_FOUND")
        route = config.route_for("audio.transcribe", "1.0.0", profile)
        if route is None:
            return error_response("CAPABILITY_UNAVAILABLE", "no transcription route", 503)
        raw = await file.read()
        if len(raw) > max_upload_bytes:
            return error_response("INPUT_TOO_LARGE", "upload exceeds the byte limit", 413)
        upload_id = f"upl_{uuid.uuid4().hex[:20]}"
        with upload_lock:
            uploads[upload_id] = raw
        request_data = {
            "capability": "audio.transcribe",
            "capability_version": "1.0.0",
            "profile": profile,
            "input": {"upload_id": upload_id, "language": language or "auto"},
            "constraints": {
                "timeout_ms": route.timeout_ms,
                "priority": "batch",
                "allow_degraded_route": False,
            },
            "policy": {
                "data_classification": "internal",
                "cloud_fallback_allowed": False,
                "retention": "none",
            },
        }
        try:
            submission = coordinator.submit(p.name, request_data, None)
        except CapabilityUnavailable:
            return error_response("CAPABILITY_UNAVAILABLE", "no approved route", 503)
        except InvalidJobInput as exc:
            return error_response("INVALID_INPUT", str(exc), 400)
        except QueueFull as exc:
            return error_response(
                "QUEUE_FULL",
                str(exc),
                429,
                retryable=True,
                retry_after_seconds=exc.retry_after_seconds,
            )
        job = await asyncio.to_thread(
            coordinator.wait,
            submission.job.job_id,
            route.timeout_ms / 1000 + 1,
        )
        if job is None or job.status not in {"succeeded", "failed", "rejected", "cancelled"}:
            store.request_cancel(submission.job.job_id)
            return error_response("TIMEOUT", "job did not complete in time", 504, retryable=True)
        result = coordinator.result(job.job_id)
        if job.status != "succeeded" or result is None:
            err = job.error or {"code": "INTERNAL_ERROR", "message": "job failed"}
            return error_response(
                err["code"],
                err["message"],
                ERROR_HTTP_STATUS.get(err["code"], 500),
                retryable=bool(err.get("retryable")),
            )
        output = result["result"]
        return JSONResponse(
            {
                "text": output.get("text") or "",
                "model": model,
                "language": output.get("language"),
                "duration": output.get("duration_s"),
                "segments": output.get("segments") or [],
                "hermes_provenance": result["provenance"],
            }
        )

    return app


def job_view(job: JobRow) -> dict:
    data: dict[str, Any] = {
        "job_id": job.job_id,
        "capability": job.capability,
        "capability_version": job.capability_version,
        "profile": job.profile,
        "status": job.status,
        "route_id": job.route_id,
    }
    if job.error is not None:
        data["error"] = job.error
    if job.timing:
        data["timing"] = job.timing
    return data


class UploadTooLarge(RuntimeError):
    pass
