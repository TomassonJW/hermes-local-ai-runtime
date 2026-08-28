"""UI-01 console: cookie session, job list, resources, prefix strip."""

from __future__ import annotations

from fastapi.testclient import TestClient

from runtime.app import create_app
from tests.test_runtime_g05 import POLICY, TOKEN_A, config


def test_console_cookie_can_read_system_without_bearer(tmp_path):
    app = create_app(config(tmp_path))
    with TestClient(app) as client:
        denied = client.get("/api/v1/system")
        assert denied.status_code == 401
        session = client.get("/api/v1/console/session")
        assert session.status_code == 200
        assert session.json()["principal"] == "console"
        system = client.get("/api/v1/system")
        assert system.status_code == 200
        assert system.json()["listen_policy"] == "loopback-only"
        assert "admission" in system.json()


def test_console_lists_own_jobs_and_hides_foreign(tmp_path):
    app = create_app(config(tmp_path))
    with TestClient(app) as client:
        client.get("/api/v1/console/session")
        created = client.post(
            "/api/v1/jobs",
            json={
                "capability": "text.generate",
                "capability_version": "1.0.0",
                "profile": "fast",
                "input": {"prompt": "ping"},
                "policy": POLICY,
            },
        )
        assert created.status_code in {200, 202}
        job_id = created.json()["job_id"]
        listed = client.get("/api/v1/jobs")
        assert listed.status_code == 200
        ids = [row["job_id"] for row in listed.json()["jobs"]]
        assert job_id in ids
        foreign = client.get(
            "/api/v1/jobs",
            headers={"Authorization": f"Bearer {TOKEN_A}"},
        )
        assert foreign.status_code == 200
        assert job_id not in [row["job_id"] for row in foreign.json()["jobs"]]


def test_resources_snapshot_is_live_not_fixture(tmp_path):
    app = create_app(config(tmp_path))
    with TestClient(app) as client:
        client.get("/api/v1/console/session")
        payload = client.get("/api/v1/resources").json()
        assert "admission" in payload
        assert payload["admission"]["mem_available_mib"] > 0
        assert payload["budget"]["heavy_slots"] == 1
        assert len(payload["loadavg"]) == 3


def test_hub_prefix_is_stripped_for_api(tmp_path):
    app = create_app(config(tmp_path))
    with TestClient(app) as client:
        health = client.get("/apps/local-ai-runtime/healthz")
        assert health.status_code == 200
        assert health.json() == {"status": "ok"}


def test_capabilities_expose_engine_not_filenames(tmp_path):
    app = create_app(config(tmp_path))
    with TestClient(app) as client:
        client.get("/api/v1/console/session")
        caps = client.get("/api/v1/capabilities").json()["capabilities"]
        text = next(item for item in caps if item["id"] == "text.generate")
        assert "fast" in text["profiles"]
        engines = {route["engine"] for route in text["routes"]}
        assert "dummy" in engines
        blob = str(caps)
        assert ".gguf" not in blob
        assert "qwen" not in blob.lower()
