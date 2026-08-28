from __future__ import annotations

import asyncio
import json
import multiprocessing
import sqlite3
import stat
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import jsonschema
import httpx
import pytest
import yaml
from fastapi.testclient import TestClient

from runtime.admission import Admission
from runtime.app import create_app
from runtime.config import Budget, ConfigError, RouteConfig, RuntimeConfig, TokenConfig, load_config
from runtime.coordinator import InputTooLarge, JobCoordinator
from runtime.store import JobStore
from runtime.workers import OpenAIUpstreamWorker, WorkerError

TOKEN_A = "fixture-token-a"
TOKEN_B = "fixture-token-b"
POLICY = {
    "data_classification": "internal",
    "cloud_fallback_allowed": False,
    "retention": "none",
}


def config(
    tmp_path: Path,
    *,
    floor_mib: int = 0,
    queue_max: int = 8,
    result_max_count: int = 64,
    request_max_bytes: int = 512 * 1024,
    result_max_bytes: int = 4 * 1024 * 1024,
    result_store_max_bytes: int = 16 * 1024 * 1024,
) -> RuntimeConfig:
    routes = (
        RouteConfig(
            id="echo-text@1",
            capability="text.generate",
            capability_version="1.0.0",
            profiles=("fast", "balanced"),
            worker="echo",
            upstream_base=None,
            upstream_model=None,
            engine="dummy",
            engine_version="test-v1",
            resource_class="light",
            memory_estimate_mib=1,
            sync_allowed=True,
            timeout_ms=2_000,
            preset="test",
        ),
        RouteConfig(
            id="echo-heavy@1",
            capability="vision.analyze",
            capability_version="1.0.0",
            profiles=("balanced",),
            worker="echo",
            upstream_base=None,
            upstream_model=None,
            engine="dummy",
            engine_version="test-v1",
            resource_class="heavy",
            memory_estimate_mib=1,
            sync_allowed=False,
            timeout_ms=2_000,
            preset="test-heavy",
        ),
    )
    return RuntimeConfig(
        listen_host="127.0.0.1",
        listen_port=8090,
        routes=routes,
        budget=Budget(
            heavy_slots=1,
            light_slots=2,
            queue_max=queue_max,
            memory_floor_available_mib=floor_mib,
            result_max_count=result_max_count,
            request_max_bytes=request_max_bytes,
            result_max_bytes=result_max_bytes,
            result_store_max_bytes=result_store_max_bytes,
        ),
        tokens=(
            TokenConfig(
                name="consumer-a",
                token=TOKEN_A,
                scopes=("capability:invoke:*", "job:read:self", "job:cancel:self", "system:read"),
            ),
            TokenConfig(
                name="consumer-b",
                token=TOKEN_B,
                scopes=("capability:invoke:*", "job:read:self", "job:cancel:self", "system:read"),
            ),
        ),
        db_path=str(tmp_path / "jobs.db"),
    )


def auth(token: str = TOKEN_A) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def submit(client: TestClient, text: str = "bonjour", **input_extra) -> dict:
    body = {
        "capability": "text.generate",
        "capability_version": "1.0.0",
        "profile": "balanced",
        "input": {"text": text, **input_extra},
        "policy": POLICY,
    }
    response = client.post("/api/v1/jobs", headers=auth(), json=body)
    assert response.status_code == 202, response.text
    return response.json()


def wait_terminal(client: TestClient, job_id: str, timeout: float = 3) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        data = client.get(f"/api/v1/jobs/{job_id}", headers=auth()).json()
        if data["status"] in {"succeeded", "failed", "cancelled", "rejected"}:
            return data
        time.sleep(0.02)
    raise AssertionError(f"job {job_id} did not terminate")


def test_health_is_public_but_control_plane_requires_auth(tmp_path: Path):
    with TestClient(create_app(config(tmp_path))) as client:
        assert client.get("/healthz").json() == {"status": "ok"}
        assert client.get("/readyz").status_code == 200
        denied = client.get("/api/v1/system")
        assert denied.status_code == 401
        assert denied.json()["error"]["code"] == "AUTH_REQUIRED"
        assert denied.json()["error"]["request_id"].startswith("req_")
        assert denied.headers["X-Request-ID"] == denied.json()["error"]["request_id"]
        assert client.get("/api/v1/system", headers=auth()).status_code == 200


def test_capabilities_are_route_based_and_do_not_expose_engine_flags(tmp_path: Path):
    with TestClient(create_app(config(tmp_path))) as client:
        response = client.get("/api/v1/capabilities", headers=auth())
        assert response.status_code == 200
        capability = response.json()["capabilities"][0]
        assert capability["id"] == "text.generate"
        assert capability["profiles"] == ["fast", "balanced"]
        assert "upstream_model" not in capability
        assert "engine" not in capability


def test_job_runs_end_to_end_and_returns_provenance(tmp_path: Path):
    request_body = {
        "capability": "text.generate",
        "capability_version": "1.0.0",
        "profile": "balanced",
        "input": {"text": "bonjour"},
        "constraints": {
            "timeout_ms": 10_000,
            "max_output_tokens": 64,
            "priority": "interactive",
            "allow_degraded_route": False,
        },
        "policy": POLICY,
    }
    jsonschema.validate(
        request_body,
        json.loads(Path("schemas/job-request.schema.json").read_text()),
    )
    with TestClient(create_app(config(tmp_path))) as client:
        response = client.post(
            "/api/v1/jobs",
            headers=auth(),
            json=request_body,
        )
        assert response.status_code == 202
        accepted = response.json()
        assert response.headers["Location"] == f"/api/v1/jobs/{accepted['job_id']}"
        terminal = wait_terminal(client, accepted["job_id"])
        assert terminal["status"] == "succeeded"
        result = client.get(
            f"/api/v1/jobs/{accepted['job_id']}/result", headers=auth()
        )
        assert result.status_code == 200
        payload = result.json()
        schema = json.loads(Path("schemas/job-result.schema.json").read_text())
        jsonschema.validate(payload, schema)
        assert payload["result"]["echo"] == "bonjour"
        assert payload["evidence"] == []
        assert payload["warnings"] == []
        assert payload["provenance"]["route"] == "echo-text@1"
        assert payload["provenance"]["capability"] == "text.generate"
        assert payload["provenance"]["runtime_version"]
        assert payload["provenance"]["engine"] == "dummy"
        assert payload["provenance"]["engine_version"] == "test-v1"
        assert payload["provenance"]["profile"] == "balanced"
        assert payload["timing"]["total_ms"] >= 0


def test_native_job_requires_canonical_policy(tmp_path: Path):
    body = {
        "capability": "text.generate",
        "capability_version": "1.0.0",
        "profile": "balanced",
        "input": {"text": "no policy"},
    }
    with TestClient(create_app(config(tmp_path))) as client:
        response = client.post("/api/v1/jobs", headers=auth(), json=body)
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "INVALID_INPUT"


def test_native_job_accepts_every_canonical_policy_field_and_version_shape(tmp_path: Path):
    request_body = {
        "capability": "text.generate",
        "capability_version": "stable",
        "profile": "balanced",
        "input": {},
        "policy": {
            "data_classification": "internal",
            "cloud_fallback_allowed": False,
            "allowed_remote_providers": [],
            "retention": "job_ttl",
            "human_confirmation_for_remote": True,
        },
    }
    jsonschema.validate(
        request_body,
        json.loads(Path("schemas/job-request.schema.json").read_text()),
    )
    app_config = config(tmp_path)
    app_config = RuntimeConfig(
        **{
            **app_config.__dict__,
            "routes": (
                RouteConfig(
                    **{**app_config.routes[0].__dict__, "capability_version": "stable"}
                ),
            ),
        }
    )
    with TestClient(create_app(app_config)) as client:
        response = client.post("/api/v1/jobs", headers=auth(), json=request_body)
        assert response.status_code == 202, response.text


def test_idempotency_replays_same_job_and_rejects_payload_change(tmp_path: Path):
    with TestClient(create_app(config(tmp_path))) as client:
        headers = {**auth(), "Idempotency-Key": "idem-001"}
        body = {
            "capability": "text.generate",
            "capability_version": "1.0.0",
            "profile": "balanced",
            "input": {"text": "one"},
            "policy": POLICY,
        }
        first = client.post("/api/v1/jobs", headers=headers, json=body)
        replay = client.post("/api/v1/jobs", headers=headers, json=body)
        conflict = client.post(
            "/api/v1/jobs", headers=headers, json={**body, "input": {"text": "two"}}
        )
        assert first.status_code == 202
        assert replay.status_code == 200
        assert replay.json()["job_id"] == first.json()["job_id"]
        assert conflict.status_code == 409
        assert conflict.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"
        short = client.post(
            "/api/v1/jobs",
            headers={**auth(), "Idempotency-Key": "short"},
            json=body,
        )
        assert short.status_code == 400


def test_idempotency_is_atomic_across_store_instances(tmp_path: Path):
    db_path = tmp_path / "jobs.db"
    stores = [JobStore(db_path) for _ in range(8)]
    barrier = threading.Barrier(len(stores))
    results: list[tuple[str, bool]] = []
    errors: list[BaseException] = []
    result_lock = threading.Lock()
    request = {
        "capability": "text.generate",
        "capability_version": "1.0.0",
        "profile": "balanced",
    }

    def create(store: JobStore) -> None:
        barrier.wait()
        try:
            row, created = store.create(
                "consumer-a", request, "echo-text@1", "shared-key", "same-hash"
            )
            with result_lock:
                results.append((row.job_id, created))
        except BaseException as exc:
            with result_lock:
                errors.append(exc)

    threads = [threading.Thread(target=create, args=(store,)) for store in stores]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=3)

    assert errors == []
    assert len(results) == len(stores)
    assert sum(created for _, created in results) == 1
    assert len({job_id for job_id, _ in results}) == 1

def test_consumer_cannot_read_another_consumers_job(tmp_path: Path):
    with TestClient(create_app(config(tmp_path))) as client:
        job_id = submit(client)["job_id"]
        response = client.get(
            f"/api/v1/jobs/{job_id}", headers=auth(TOKEN_B)
        )
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "NOT_FOUND"


def test_queued_or_running_job_can_be_cancelled(tmp_path: Path):
    with TestClient(create_app(config(tmp_path))) as client:
        job_id = submit(client, simulate_work_s=1.0)["job_id"]
        deadline = time.monotonic() + 1
        while time.monotonic() < deadline:
            current = client.get(f"/api/v1/jobs/{job_id}", headers=auth()).json()
            if current["status"] == "running":
                break
            time.sleep(0.01)
        assert current["status"] == "running"
        cancelled_at = time.monotonic()
        response = client.post(f"/api/v1/jobs/{job_id}/cancel", headers=auth())
        assert response.status_code == 202
        terminal = wait_terminal(client, job_id)
        assert terminal["status"] == "cancelled"
        assert time.monotonic() - cancelled_at < 0.4


def test_shutdown_terminates_and_joins_active_worker_children(tmp_path: Path):
    app_config = config(tmp_path)
    with TestClient(create_app(app_config)) as client:
        job_id = submit(client, simulate_work_s=5.0)["job_id"]
        deadline = time.monotonic() + 1
        while time.monotonic() < deadline:
            current = client.get(f"/api/v1/jobs/{job_id}", headers=auth()).json()
            if current["status"] == "running":
                break
            time.sleep(0.01)
        assert current["status"] == "running"
    survivors = [
        child
        for child in multiprocessing.active_children()
        if child.name.startswith("worker-job_") and child.is_alive()
    ]
    assert survivors == []
    assert JobStore(app_config.db_path).get(job_id).status == "cancelled"


def test_admission_refuses_before_memory_floor_is_crossed(tmp_path: Path):
    app_config = config(tmp_path, floor_mib=10**9)
    with TestClient(create_app(app_config)) as client:
        terminal = wait_terminal(client, submit(client)["job_id"])
        assert terminal["status"] == "rejected"
        assert terminal["error"]["code"] == "RESOURCE_EXHAUSTED"


def test_queue_is_hard_bounded():
    admission = Admission(Budget(queue_max=2, memory_floor_available_mib=0))
    assert admission.try_enqueue().admitted
    assert admission.try_enqueue().admitted
    third = admission.try_enqueue()
    assert not third.admitted
    assert third.code == "QUEUE_FULL"


def test_one_heavy_and_two_light_jobs_execute_concurrently(tmp_path: Path):
    with TestClient(create_app(config(tmp_path))) as client:
        requests = [
            {
                "capability": "vision.analyze",
                "capability_version": "1.0.0",
                "profile": "balanced",
                "input": {"text": "heavy", "simulate_work_s": 0.3},
                "policy": POLICY,
            },
            {
                "capability": "text.generate",
                "capability_version": "1.0.0",
                "profile": "balanced",
                "input": {"text": "light-1", "simulate_work_s": 0.3},
                "policy": POLICY,
            },
            {
                "capability": "text.generate",
                "capability_version": "1.0.0",
                "profile": "balanced",
                "input": {"text": "light-2", "simulate_work_s": 0.3},
                "policy": POLICY,
            },
        ]
        started = time.monotonic()
        job_ids = []
        for body in requests:
            response = client.post("/api/v1/jobs", headers=auth(), json=body)
            assert response.status_code == 202
            job_ids.append(response.json()["job_id"])
        terminal = [wait_terminal(client, job_id) for job_id in job_ids]
        elapsed = time.monotonic() - started
        assert all(job["status"] == "succeeded" for job in terminal)
        assert elapsed < 0.65


def test_second_heavy_job_waits_instead_of_being_rejected(tmp_path: Path):
    body = {
        "capability": "vision.analyze",
        "capability_version": "1.0.0",
        "profile": "balanced",
        "input": {"text": "heavy", "simulate_work_s": 0.2},
        "policy": POLICY,
    }
    with TestClient(create_app(config(tmp_path))) as client:
        first = client.post("/api/v1/jobs", headers=auth(), json=body).json()["job_id"]
        second = client.post("/api/v1/jobs", headers=auth(), json=body).json()["job_id"]
        terminal = [wait_terminal(client, first), wait_terminal(client, second)]
        assert [job["status"] for job in terminal] == ["succeeded", "succeeded"]


def test_restart_converges_incomplete_jobs_to_failed(tmp_path: Path):
    store = JobStore(tmp_path / "restart.db")
    request = {
        "capability": "text.generate",
        "capability_version": "1.0.0",
        "profile": "balanced",
        "input": {"text": "x"},
        "policy": POLICY,
    }
    row, _ = store.create("consumer-a", request, "echo-text@1", None, "hash")
    store.set_status(row.job_id, "running")
    assert store.recover_incomplete() == 1
    recovered = store.get(row.job_id)
    assert recovered is not None
    assert recovered.status == "failed"
    assert recovered.error["code"] == "WORKER_CRASHED"


def test_cancel_wins_atomic_race_against_success_publication(tmp_path: Path):
    store = JobStore(tmp_path / "atomic" / "jobs.db")
    request = {
        "capability": "text.generate",
        "capability_version": "1.0.0",
        "profile": "balanced",
        "input": {"text": "x"},
        "policy": POLICY,
    }
    row, _ = store.create("consumer-a", request, "echo-text@1", None, "hash")
    store.set_status(row.job_id, "running")
    store.request_cancel(row.job_id)
    published = store.complete_success_if_not_cancelled(
        row.job_id,
        {"queued_ms": 0, "load_ms": 0, "inference_ms": 1, "validation_ms": 0, "total_ms": 1},
    )
    assert not published
    assert store.get(row.job_id).status == "cancelled"


def test_cancel_wins_atomic_race_against_failure_publication(tmp_path: Path):
    store = JobStore(tmp_path / "atomic-failure" / "jobs.db")
    request = {
        "capability": "text.generate",
        "capability_version": "1.0.0",
        "profile": "balanced",
        "input": {"text": "x"},
        "policy": POLICY,
    }
    row, _ = store.create("consumer-a", request, "echo-text@1", None, "hash")
    store.set_status(row.job_id, "running")
    store.request_cancel(row.job_id)
    published = store.complete_failure_if_not_cancelled(
        row.job_id,
        {"code": "TIMEOUT", "message": "late timeout", "retryable": True},
        {"total_ms": 10},
    )
    assert not published
    terminal = store.get(row.job_id)
    assert terminal.status == "cancelled"
    assert terminal.error is None


def test_sqlite_is_private_metadata_only_and_contains_no_payload(tmp_path: Path):
    marker = "confidential-marker-never-persist"
    app_config = config(tmp_path / "private-state")
    with TestClient(create_app(app_config)) as client:
        job_id = submit(client, marker)["job_id"]
        assert wait_terminal(client, job_id)["status"] == "succeeded"
    db_path = Path(app_config.db_path)
    assert stat.S_IMODE(db_path.stat().st_mode) == 0o600
    assert stat.S_IMODE(db_path.parent.stat().st_mode) == 0o700
    assert marker.encode() not in db_path.read_bytes()
    with sqlite3.connect(db_path) as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(jobs)")}
    assert "request_json" not in columns
    assert "result_json" not in columns


def test_schema_v1_migrates_without_payload_columns_and_accepts_new_jobs(tmp_path: Path):
    db_path = tmp_path / "legacy.db"
    with sqlite3.connect(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            INSERT INTO meta VALUES('schema_version', '1');
            CREATE TABLE jobs (
              job_id TEXT PRIMARY KEY, consumer TEXT NOT NULL,
              capability TEXT NOT NULL, capability_version TEXT NOT NULL,
              profile TEXT NOT NULL, route_id TEXT, status TEXT NOT NULL,
              request_json TEXT NOT NULL, result_json TEXT, error_json TEXT,
              idempotency_key TEXT, request_hash TEXT, created_at REAL NOT NULL,
              updated_at REAL NOT NULL, queued_ms INTEGER, load_ms INTEGER,
              inference_ms INTEGER, validation_ms INTEGER, total_ms INTEGER,
              cancel_requested INTEGER NOT NULL DEFAULT 0
            );
            INSERT INTO jobs VALUES(
              'job_legacy','consumer-a','text.generate','1.0.0','balanced',
              'echo-text@1','succeeded','{"input":{"text":"legacy-secret"}}',
              '{"result":"legacy-secret"}',NULL,NULL,'legacy-hash',1,1,
              NULL,NULL,NULL,NULL,NULL,0
            );
            """
        )
    db_path.chmod(0o600)
    store = JobStore(db_path)
    created, is_new = store.create(
        "consumer-a",
        {
            "capability": "text.generate",
            "capability_version": "1.0.0",
            "profile": "balanced",
            "input": {"text": "new-secret"},
            "policy": POLICY,
        },
        "echo-text@1",
        None,
        "new-hash",
    )
    assert is_new
    assert created.status == "queued"
    with sqlite3.connect(db_path) as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(jobs)")}
        assert connection.execute(
            "SELECT status FROM jobs WHERE job_id='job_legacy'"
        ).fetchone() == ("succeeded",)
    assert "request_json" not in columns
    assert "result_json" not in columns
    raw = db_path.read_bytes()
    assert b"legacy-secret" not in raw
    assert b"new-secret" not in raw


def test_large_child_result_is_drained_without_pipe_deadlock(tmp_path: Path):
    with TestClient(create_app(config(tmp_path))) as client:
        job_id = submit(client, "large", synthetic_result_bytes=1_000_000)["job_id"]
        terminal = wait_terminal(client, job_id, timeout=5)
        assert terminal["status"] == "succeeded"
        result = client.get(f"/api/v1/jobs/{job_id}/result", headers=auth()).json()
        assert len(result["result"]["blob"]) == 1_000_000


def test_single_volatile_result_is_rejected_at_serialized_byte_limit(tmp_path: Path):
    with TestClient(create_app(config(tmp_path, result_max_bytes=1024))) as client:
        job_id = submit(client, "large", synthetic_result_bytes=2000)["job_id"]
        terminal = wait_terminal(client, job_id)
        assert terminal["status"] == "failed"
        assert terminal["error"]["code"] == "OUTPUT_TOO_LARGE"
        assert client.get(f"/api/v1/jobs/{job_id}/result", headers=auth()).status_code == 409


def test_single_result_cannot_exceed_aggregate_store_budget(tmp_path: Path):
    app_config = config(
        tmp_path,
        result_max_bytes=4096,
        result_store_max_bytes=1024,
    )
    with TestClient(create_app(app_config)) as client:
        job_id = submit(client, "large", synthetic_result_bytes=2000)["job_id"]
        terminal = wait_terminal(client, job_id)
        assert terminal["status"] == "failed"
        assert terminal["error"]["code"] == "OUTPUT_TOO_LARGE"


def test_upstream_response_is_stopped_before_json_decode_at_byte_limit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    route = RouteConfig(
        **{
            **config(tmp_path).routes[0].__dict__,
            "worker": "openai-upstream",
            "upstream_base": "http://127.0.0.1:8840",
            "upstream_model": "synthetic",
        }
    )

    def oversized(_request: httpx.Request) -> httpx.Response:
        content = json.dumps(
            {"choices": [{"message": {"content": "x" * (5 * 1024 * 1024)}}]}
        ).encode()
        return httpx.Response(200, content=content)

    monkeypatch.setattr(
        OpenAIUpstreamWorker,
        "_client",
        lambda _self, _route: httpx.Client(
            transport=httpx.MockTransport(oversized), base_url="http://test"
        ),
    )
    with pytest.raises(WorkerError, match="byte limit") as raised:
        OpenAIUpstreamWorker().execute(
            route,
            {
                "input": {"prompt": "hello"},
                "constraints": {"max_output_tokens": 8},
            },
        )
    assert raised.value.code == "OUTPUT_TOO_LARGE"


def test_loopback_upstream_ignores_environment_http_proxy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    proxy_hits = 0

    class RecordingProxy(BaseHTTPRequestHandler):
        def do_POST(self):
            nonlocal proxy_hits
            proxy_hits += 1
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"choices":[{"message":{"content":"intercepted"}}]}')

        def log_message(self, _format, *args):
            pass

    proxy = ThreadingHTTPServer(("127.0.0.1", 0), RecordingProxy)
    proxy_thread = threading.Thread(target=proxy.serve_forever, daemon=True)
    proxy_thread.start()
    try:
        for name in ("NO_PROXY", "no_proxy", "HTTPS_PROXY", "https_proxy", "http_proxy"):
            monkeypatch.delenv(name, raising=False)
        monkeypatch.setenv("HTTP_PROXY", f"http://127.0.0.1:{proxy.server_port}")
        route = RouteConfig(
            **{
                **config(tmp_path).routes[0].__dict__,
                "worker": "openai-upstream",
                "upstream_base": "http://127.0.0.1:1",
                "upstream_model": "synthetic",
            }
        )

        with pytest.raises(WorkerError) as exc:
            OpenAIUpstreamWorker(timeout_extra_s=0).execute(
                route, {"input": {"prompt": "private payload"}}
            )

        assert exc.value.code == "MODEL_LOAD_FAILED"
        assert proxy_hits == 0
    finally:
        proxy.shutdown()
        proxy.server_close()
        proxy_thread.join(timeout=1)


def test_volatile_result_store_evicts_oldest_entry_at_bound(tmp_path: Path):
    with TestClient(create_app(config(tmp_path, result_max_count=2))) as client:
        job_ids = []
        for text in ("one", "two", "three"):
            job_id = submit(client, text)["job_id"]
            assert wait_terminal(client, job_id)["status"] == "succeeded"
            job_ids.append(job_id)
        evicted = client.get(f"/api/v1/jobs/{job_ids[0]}/result", headers=auth())
        newest = client.get(f"/api/v1/jobs/{job_ids[-1]}/result", headers=auth())
        assert evicted.status_code == 409
        assert newest.status_code == 200


def test_volatile_result_store_evicts_oldest_entry_at_aggregate_byte_bound(tmp_path: Path):
    app_config = config(
        tmp_path,
        result_max_count=64,
        result_max_bytes=4096,
        result_store_max_bytes=2500,
    )
    with TestClient(create_app(app_config)) as client:
        first = submit(client, "one", synthetic_result_bytes=1200)["job_id"]
        assert wait_terminal(client, first)["status"] == "succeeded"
        second = submit(client, "two", synthetic_result_bytes=1200)["job_id"]
        assert wait_terminal(client, second)["status"] == "succeeded"
        assert client.get(f"/api/v1/jobs/{first}/result", headers=auth()).status_code == 409
        assert client.get(f"/api/v1/jobs/{second}/result", headers=auth()).status_code == 200


def test_raw_upload_is_bounded_and_returns_only_metadata(tmp_path: Path):
    with TestClient(create_app(config(tmp_path), max_upload_bytes=16)) as client:
        ok = client.post(
            "/api/v1/uploads",
            headers={**auth(), "Content-Type": "text/plain"},
            content=b"synthetic",
        )
        assert ok.status_code == 201
        assert ok.json()["size_bytes"] == 9
        assert "content" not in ok.json()
        too_large = client.post(
            "/api/v1/uploads",
            headers={**auth(), "Content-Type": "application/octet-stream"},
            content=b"x" * 17,
        )
        assert too_large.status_code == 413
        assert too_large.json()["error"]["code"] == "INPUT_TOO_LARGE"
    assert not list((tmp_path / ".runtime-uploads").glob("upl_*"))


def test_validation_error_does_not_echo_submitted_content(tmp_path: Path):
    marker = "private-payload-marker"
    with TestClient(create_app(config(tmp_path))) as client:
        response = client.post(
            "/api/v1/jobs",
            headers=auth(),
            json={
                "capability": "text.generate",
                "capability_version": "1.0.0",
                "profile": "unsupported-profile",
                "input": {"text": marker},
                "policy": POLICY,
            },
        )
        assert response.status_code == 400
        assert marker not in response.text


def test_native_request_body_is_rejected_before_job_creation_at_byte_limit(tmp_path: Path):
    app_config = config(tmp_path, request_max_bytes=1024)
    body = {
        "capability": "text.generate",
        "capability_version": "1.0.0",
        "profile": "balanced",
        "input": {"unused": "x" * 2000},
        "policy": POLICY,
    }
    with TestClient(create_app(app_config)) as client:
        response = client.post("/api/v1/jobs", headers=auth(), json=body)
        assert response.status_code == 413
        assert response.json()["error"]["code"] == "INPUT_TOO_LARGE"
        assert app_config.db_path and client.app.state.store.counts_by_status() == {}


def test_coordinator_rejects_oversized_request_before_retaining_state(tmp_path: Path):
    app_config = config(tmp_path, request_max_bytes=1024)
    store = JobStore(app_config.db_path)
    coordinator = JobCoordinator(app_config, store)
    request = {
        "capability": "text.generate",
        "capability_version": "1.0.0",
        "profile": "balanced",
        "input": {"unused": "x" * 2000},
        "policy": POLICY,
    }

    with pytest.raises(InputTooLarge):
        coordinator.submit("consumer-a", request, None)

    with sqlite3.connect(app_config.db_path) as con:
        assert con.execute("SELECT count(*) FROM jobs").fetchone()[0] == 0
    assert coordinator._queue.empty()
    admission = coordinator.admission.snapshot()
    assert admission["queued"] == 0
    assert admission["light_leases"] == 0
    assert admission["heavy_leases"] == 0
    assert coordinator._requests == {}


def test_openai_chat_adapter_uses_capability_job_contract(tmp_path: Path):
    with TestClient(create_app(config(tmp_path))) as client:
        response = client.post(
            "/v1/chat/completions",
            headers=auth(),
            json={
                "model": "local-balanced",
                "messages": [{"role": "user", "content": "bonjour"}],
                "max_tokens": 16,
            },
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["object"] == "chat.completion"
        assert data["choices"][0]["message"]["content"] == "bonjour"
        assert data["model"] == "local-balanced"


def test_openai_adapter_rejects_unknown_alias_and_engine_flags(tmp_path: Path):
    with TestClient(create_app(config(tmp_path))) as client:
        unknown = client.post(
            "/v1/chat/completions",
            headers=auth(),
            json={
                "model": "unknown-model",
                "messages": [{"role": "user", "content": "bonjour"}],
            },
        )
        assert unknown.status_code == 404
        assert unknown.json()["error"]["code"] == "NOT_FOUND"
        flag = client.post(
            "/v1/chat/completions",
            headers=auth(),
            json={
                "model": "local-balanced",
                "messages": [{"role": "user", "content": "bonjour"}],
                "n_ctx": 999999,
            },
        )
        assert flag.status_code == 400
        assert flag.json()["error"]["code"] == "INVALID_INPUT"


def test_openai_timeout_returns_504_and_leaves_no_worker_child(tmp_path: Path):
    class SlowUpstream(BaseHTTPRequestHandler):
        def do_POST(self):
            time.sleep(0.5)
            try:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(
                    b'{"choices":[{"message":{"content":"too late"}}]}'
                )
            except BrokenPipeError:
                pass

        def log_message(self, _format, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), SlowUpstream)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    try:
        base = config(tmp_path)
        route = RouteConfig(
            **{
                **base.routes[0].__dict__,
                "worker": "openai-upstream",
                "upstream_base": f"http://127.0.0.1:{server.server_port}",
                "upstream_model": "synthetic",
                "timeout_ms": 100,
            }
        )
        app_config = RuntimeConfig(**{**base.__dict__, "routes": (route,)})
        with TestClient(create_app(app_config)) as client:
            response = client.post(
                "/v1/chat/completions",
                headers=auth(),
                json={
                    "model": "local-balanced",
                    "messages": [{"role": "user", "content": "bonjour"}],
                },
            )
            assert response.status_code == 504, response.text
            assert response.json()["error"]["code"] == "TIMEOUT"
        assert not [
            child
            for child in multiprocessing.active_children()
            if child.name.startswith("worker-job_") and child.is_alive()
        ]
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=1)


def test_openai_wait_does_not_block_health_on_the_event_loop(tmp_path: Path):
    class SlowUpstream(BaseHTTPRequestHandler):
        def do_POST(self):
            time.sleep(0.4)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"choices":[{"message":{"content":"done"}}]}')

        def log_message(self, _format, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), SlowUpstream)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    try:
        base = config(tmp_path)
        route = RouteConfig(
            **{
                **base.routes[0].__dict__,
                "worker": "openai-upstream",
                "upstream_base": f"http://127.0.0.1:{server.server_port}",
                "upstream_model": "synthetic",
                "timeout_ms": 1000,
            }
        )
        app = create_app(RuntimeConfig(**{**base.__dict__, "routes": (route,)}))

        async def exercise() -> None:
            transport = httpx.ASGITransport(app=app)
            async with app.router.lifespan_context(app):
                async with httpx.AsyncClient(
                    transport=transport, base_url="http://runtime.test"
                ) as client:
                    started = time.monotonic()
                    chat = asyncio.create_task(
                        client.post(
                            "/v1/chat/completions",
                            headers=auth(),
                            json={
                                "model": "local-balanced",
                                "messages": [{"role": "user", "content": "bonjour"}],
                            },
                        )
                    )
                    await asyncio.sleep(0.05)
                    health = await client.get("/healthz")
                    assert time.monotonic() - started < 0.25
                    assert health.status_code == 200
                    assert (await chat).status_code == 200

        asyncio.run(exercise())
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=1)


def test_native_job_enforces_consumer_timeout_below_route_timeout(tmp_path: Path):
    base = config(tmp_path)
    route = RouteConfig(**{**base.routes[0].__dict__, "timeout_ms": 1000})
    app_config = RuntimeConfig(**{**base.__dict__, "routes": (route,)})
    body = {
        "capability": "text.generate",
        "capability_version": "1.0.0",
        "profile": "balanced",
        "input": {"text": "slow", "simulate_work_s": 0.4},
        "constraints": {"timeout_ms": 100},
        "policy": POLICY,
    }
    with TestClient(create_app(app_config)) as client:
        job_id = client.post("/api/v1/jobs", headers=auth(), json=body).json()["job_id"]
        terminal = wait_terminal(client, job_id)
        assert terminal["status"] == "failed"
        assert terminal["error"]["code"] == "TIMEOUT"
        assert terminal["timing"]["total_ms"] < route.timeout_ms


def test_secret_token_never_appears_in_system_or_job_response(tmp_path: Path):
    with TestClient(create_app(config(tmp_path))) as client:
        system = client.get("/api/v1/system", headers=auth()).text
        job = submit(client)
        assert TOKEN_A not in system
        assert TOKEN_A not in str(job)


def test_exposed_routes_equal_openapi_routes_marked_implemented(tmp_path: Path):
    app = create_app(config(tmp_path))
    exposed = {
        (route.path, method.lower())
        for route in app.routes
        for method in route.methods
        if method not in {"HEAD", "OPTIONS"}
    }
    contract = yaml.safe_load(Path("contracts/openapi.yaml").read_text())
    implemented = {
        (path, method)
        for path, path_item in contract["paths"].items()
        for method, operation in path_item.items()
        if isinstance(operation, dict)
        and operation.get("x-implementation-status")
        in {"implemented-g05", "implemented-g07", "implemented-g08"}
    }
    assert exposed == implemented


@pytest.mark.parametrize(
    ("host", "upstream"),
    [
        ("0.0.0.0", "http://127.0.0.1:8840"),
        ("127.0.0.1", "https://remote.example.invalid"),
    ],
)
def test_config_rejects_non_loopback_listeners_and_upstreams(
    tmp_path: Path, host: str, upstream: str
):
    config_path = tmp_path / "runtime.yaml"
    config_path.write_text(
        f"""
listen: {{host: {host}, port: 8850}}
db_path: {tmp_path / 'jobs.db'}
dev_mode: true
routes:
  - id: bounded-route
    capability: text.generate
    capability_version: 1.0.0
    profiles: [balanced]
    worker: openai-upstream
    upstream_base: {upstream}
    upstream_model: synthetic
    engine: synthetic
    engine_version: test
    resource_class: light
    memory_estimate_mib: 1
    sync_allowed: true
    timeout_ms: 1000
""",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError):
        load_config(config_path)


@pytest.mark.parametrize(
    ("second_name", "second_value"),
    [
        ("consumer-a", TOKEN_B),
        ("consumer-b", TOKEN_A),
    ],
)
def test_config_rejects_duplicate_principal_names_and_token_values(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    second_name: str,
    second_value: str,
):
    monkeypatch.setenv("TOKEN_ONE", TOKEN_A)
    monkeypatch.setenv("TOKEN_TWO", second_value)
    config_path = tmp_path / "runtime.yaml"
    config_path.write_text(
        f"""
listen: {{host: 127.0.0.1, port: 8850}}
db_path: {tmp_path / 'jobs.db'}
auth:
  tokens:
    - name: consumer-a
      token_env: TOKEN_ONE
      scopes: [job:read:self]
    - name: {second_name}
      token_env: TOKEN_TWO
      scopes: [job:read:self]
routes: []
""",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="unique"):
        load_config(config_path)
