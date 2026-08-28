from __future__ import annotations

import base64
import json
import shutil
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from benchmarks.synthetic.generate import INVOICE_SCHEMA, write_suite
from runtime.app import create_app
from runtime.config import Budget, RouteConfig, RuntimeConfig, TokenConfig

TOKEN = "fixture-token-g06"
POLICY = {
    "data_classification": "internal",
    "cloud_fallback_allowed": False,
    "retention": "none",
}


def _route(**overrides) -> RouteConfig:
    base = dict(
        id="doc-native@1",
        capability="document.text_extract",
        capability_version="1.0.0",
        profiles=("balanced",),
        worker="document-native",
        upstream_base=None,
        upstream_model=None,
        engine="pdftotext",
        engine_version="poppler",
        resource_class="tiny",
        memory_estimate_mib=64,
        sync_allowed=True,
        timeout_ms=15_000,
        preset="g06",
    )
    base.update(overrides)
    return RouteConfig(**base)


def g06_config(tmp_path: Path, extra_routes: tuple[RouteConfig, ...] = ()) -> RuntimeConfig:
    routes = (
        _route(),
        _route(
            id="doc-ocr@1",
            capability="document.ocr",
            worker="document-ocr",
            engine="tesseract",
            engine_version="5",
            resource_class="medium",
            memory_estimate_mib=256,
        ),
        _route(
            id="doc-parse@1",
            capability="document.parse",
            worker="document-parse",
            engine="tesseract",
            engine_version="5",
            resource_class="medium",
            memory_estimate_mib=256,
        ),
        _route(
            id="doc-struct@1",
            capability="document.extract_structured",
            worker="document-structured",
            engine="native+ocr",
            engine_version="g06",
            resource_class="light",
            memory_estimate_mib=128,
        ),
        _route(
            id="img-embed@1",
            capability="vision.embed",
            worker="image-embed",
            engine="average-hash",
            engine_version="g06",
            resource_class="tiny",
            memory_estimate_mib=32,
        ),
        _route(
            id="img-compare@1",
            capability="vision.compare",
            worker="image-embed",
            engine="average-hash",
            engine_version="g06",
            resource_class="tiny",
            memory_estimate_mib=32,
        ),
        _route(
            id="obj-detect@1",
            capability="vision.detect_objects",
            worker="object-detect",
            engine="saturated-box",
            engine_version="g06",
            resource_class="light",
            memory_estimate_mib=64,
        ),
        *extra_routes,
    )
    return RuntimeConfig(
        listen_host="127.0.0.1",
        listen_port=8090,
        routes=routes,
        budget=Budget(memory_floor_available_mib=0),
        tokens=(
            TokenConfig(
                name="consumer-a",
                token=TOKEN,
                scopes=("capability:invoke:*", "job:read:self", "job:cancel:self", "system:read"),
            ),
        ),
        db_path=str(tmp_path / "jobs.db"),
    )


def auth() -> dict[str, str]:
    return {"Authorization": f"Bearer {TOKEN}"}


def wait_terminal(client: TestClient, job_id: str, timeout: float = 20) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        data = client.get(f"/api/v1/jobs/{job_id}", headers=auth()).json()
        if data["status"] in {"succeeded", "failed", "cancelled", "rejected"}:
            return data
        time.sleep(0.05)
    raise AssertionError(f"job {job_id} did not terminate")


def upload(client: TestClient, path: Path, content_type: str) -> str:
    response = client.post(
        "/api/v1/uploads",
        headers={**auth(), "Content-Type": content_type},
        content=path.read_bytes(),
    )
    assert response.status_code == 201, response.text
    return response.json()["upload_id"]


def submit(client: TestClient, capability: str, upload_id: str, **extra) -> dict:
    body = {
        "capability": capability,
        "capability_version": "1.0.0",
        "profile": "balanced",
        "input": {"upload_id": upload_id, **extra},
        "policy": POLICY,
    }
    if "output_schema" in extra:
        body["output_schema"] = extra.pop("output_schema")
        body["input"] = {"upload_id": upload_id, **{k: v for k, v in extra.items()}}
    response = client.post("/api/v1/jobs", headers=auth(), json=body)
    assert response.status_code == 202, response.text
    return wait_terminal(client, response.json()["job_id"])


@pytest.fixture()
def suite(tmp_path: Path) -> dict:
    return write_suite(tmp_path / "fixtures")


def test_native_pdf_extracts_ascii_invoice_and_flags_image_only(tmp_path: Path, suite: dict):
    with TestClient(create_app(g06_config(tmp_path))) as client:
        native_id = upload(client, suite["invoice_native_pdf"], "application/pdf")
        native = submit(client, "document.text_extract", native_id)
        assert native["status"] == "succeeded"
        result = client.get(f"/api/v1/jobs/{native['job_id']}/result", headers=auth()).json()
        text = result["result"]["pages"][0]["text"]
        assert "SYN-0042" in text
        assert "123.45" in text
        assert result["result"]["image_only"] is False

        image_pdf_id = upload(client, suite["invoice_image_pdf"], "application/pdf")
        scanned = submit(client, "document.text_extract", image_pdf_id)
        assert scanned["status"] == "succeeded"
        scanned_result = client.get(
            f"/api/v1/jobs/{scanned['job_id']}/result", headers=auth()
        ).json()
        assert scanned_result["result"]["image_only"] is True
        assert scanned_result["review_required"] is True


@pytest.mark.skipif(shutil.which("tesseract") is None, reason="tesseract missing")
def test_ocr_reads_french_invoice_and_extracts_schema_fields(tmp_path: Path, suite: dict):
    with TestClient(create_app(g06_config(tmp_path))) as client:
        image_id = upload(client, suite["invoice_png"], "image/png")
        ocr = submit(client, "document.ocr", image_id)
        assert ocr["status"] == "succeeded"
        payload = client.get(f"/api/v1/jobs/{ocr['job_id']}/result", headers=auth()).json()
        text = payload["result"]["text"]
        assert "SYN-0042" in text
        assert "123,45" in text or "123.45" in text
        assert payload["result"]["regions"]

        structured = client.post(
            "/api/v1/jobs",
            headers=auth(),
            json={
                "capability": "document.extract_structured",
                "capability_version": "1.0.0",
                "profile": "balanced",
                "input": {"upload_id": image_id},
                "output_schema": INVOICE_SCHEMA,
                "policy": POLICY,
            },
        )
        terminal = wait_terminal(client, structured.json()["job_id"])
        assert terminal["status"] == "succeeded"
        fields = client.get(
            f"/api/v1/jobs/{terminal['job_id']}/result", headers=auth()
        ).json()["result"]["data"]
        assert fields["invoice_id"] == "SYN-0042"
        assert fields["total_eur"] == 123.45


def test_object_detect_and_near_duplicate_hash(tmp_path: Path, suite: dict):
    with TestClient(create_app(g06_config(tmp_path))) as client:
        objects_id = upload(client, suite["objects"], "image/png")
        detected = submit(client, "vision.detect_objects", objects_id)
        assert detected["status"] == "succeeded"
        objects = client.get(
            f"/api/v1/jobs/{detected['job_id']}/result", headers=auth()
        ).json()["result"]["objects"]
        labels = {item["label"] for item in objects}
        assert "red-object" in labels
        assert "blue-object" in labels

        copy_id = upload(client, suite["objects_near"], "image/png")
        other_id = upload(client, suite["unrelated"], "image/png")
        near = client.post(
            "/api/v1/jobs",
            headers=auth(),
            json={
                "capability": "vision.compare",
                "capability_version": "1.0.0",
                "profile": "balanced",
                "input": {
                    "images": [{"upload_id": objects_id}, {"upload_id": copy_id}],
                },
                "policy": POLICY,
            },
        )
        far = client.post(
            "/api/v1/jobs",
            headers=auth(),
            json={
                "capability": "vision.compare",
                "capability_version": "1.0.0",
                "profile": "balanced",
                "input": {
                    "images": [{"upload_id": objects_id}, {"upload_id": other_id}],
                },
                "policy": POLICY,
            },
        )
        near_job = wait_terminal(client, near.json()["job_id"])
        far_job = wait_terminal(client, far.json()["job_id"])
        assert near_job["status"] == "succeeded"
        assert far_job["status"] == "succeeded"
        near_score = client.get(
            f"/api/v1/jobs/{near_job['job_id']}/result", headers=auth()
        ).json()["result"]["score"]
        far_score = client.get(
            f"/api/v1/jobs/{far_job['job_id']}/result", headers=auth()
        ).json()["result"]["score"]
        assert near_score > 0.9
        assert far_score < near_score - 0.15


def test_tiny_image_is_unsupported_and_paths_are_rejected(tmp_path: Path, suite: dict):
    vision_route = _route(
        id="vision-up@1",
        capability="vision.analyze",
        worker="openai-upstream",
        upstream_base="http://127.0.0.1:9",
        upstream_model="vision",
        engine="llama.cpp",
        engine_version="b10662",
        resource_class="heavy",
        memory_estimate_mib=3200,
        timeout_ms=5_000,
    )
    with TestClient(create_app(g06_config(tmp_path, extra_routes=(vision_route,)))) as client:
        tiny_id = upload(client, suite["ui_tiny"], "image/png")
        terminal = client.post(
            "/api/v1/jobs",
            headers=auth(),
            json={
                "capability": "vision.analyze",
                "capability_version": "1.0.0",
                "profile": "balanced",
                "input": {"upload_id": tiny_id, "question": "what error code is visible?"},
                "policy": POLICY,
            },
        )
        job = wait_terminal(client, terminal.json()["job_id"])
        assert job["status"] == "succeeded"
        payload = client.get(f"/api/v1/jobs/{job['job_id']}/result", headers=auth()).json()
        assert payload["review_required"] is True
        assert payload["result"]["status"] == "unsupported"

        denied = client.post(
            "/api/v1/jobs",
            headers=auth(),
            json={
                "capability": "document.ocr",
                "capability_version": "1.0.0",
                "profile": "balanced",
                "input": {"path": "/etc/passwd"},
                "policy": POLICY,
            },
        )
        assert denied.status_code == 400
        assert denied.json()["error"]["code"] == "INVALID_INPUT"


def test_remote_image_url_is_rejected_and_question_is_required(tmp_path: Path):
    vision_route = _route(
        id="vision-up@1",
        capability="vision.analyze",
        worker="openai-upstream",
        upstream_base="http://127.0.0.1:9",
        upstream_model="vision",
        engine="llama.cpp",
        engine_version="b10662",
        resource_class="heavy",
        memory_estimate_mib=3200,
        sync_allowed=True,
        timeout_ms=5_000,
    )
    with TestClient(create_app(g06_config(tmp_path, extra_routes=(vision_route,)))) as client:
        remote = client.post(
            "/v1/chat/completions",
            headers=auth(),
            json={
                "model": "hlair/vision-balanced",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "what is wrong?"},
                            {
                                "type": "image_url",
                                "image_url": {"url": "https://example.invalid/x.png"},
                            },
                        ],
                    }
                ],
            },
        )
        assert remote.status_code == 400
        assert remote.json()["error"]["code"] == "INVALID_INPUT"

        missing_q = client.post(
            "/api/v1/jobs",
            headers=auth(),
            json={
                "capability": "vision.analyze",
                "capability_version": "1.0.0",
                "profile": "balanced",
                "input": {"upload_id": "upl_" + "ab" * 10},
                "policy": POLICY,
            },
        )
        assert missing_q.status_code == 400


def test_openai_vision_alias_answers_the_question_not_a_caption(tmp_path: Path, suite: dict):
    captured: dict[str, object] = {}

    class VisionUpstream(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length))
            captured["body"] = body
            user = body["messages"][0]["content"]
            question = ""
            if isinstance(user, list):
                question = next(part["text"] for part in user if part["type"] == "text")
            answer = "The visible error code is E42 and the disk is full."
            if "error code" not in question.lower():
                answer = "generic caption of a window"
            payload = json.dumps({"choices": [{"message": {"content": answer}}]}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, _format, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), VisionUpstream)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        vision_route = _route(
            id="vision-up@1",
            capability="vision.analyze",
            worker="openai-upstream",
            upstream_base=f"http://127.0.0.1:{server.server_port}",
            upstream_model="vision-2b",
            engine="llama.cpp",
            engine_version="b10662",
            resource_class="heavy",
            memory_estimate_mib=3200,
            sync_allowed=True,
            timeout_ms=10_000,
        )
        with TestClient(create_app(g06_config(tmp_path, extra_routes=(vision_route,)))) as client:
            png = suite["ui_error"].read_bytes()
            data_url = "data:image/png;base64," + base64.b64encode(png).decode("ascii")
            response = client.post(
                "/v1/chat/completions",
                headers=auth(),
                json={
                    "model": "hlair/vision-balanced",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "What error code is visible?"},
                                {"type": "image_url", "image_url": {"url": data_url}},
                            ],
                        }
                    ],
                },
            )
            assert response.status_code == 200, response.text
            content = response.json()["choices"][0]["message"]["content"]
            assert "E42" in content
            assert "generic caption" not in content
            user_content = captured["body"]["messages"][0]["content"]
            assert isinstance(user_content, list)
            assert any(part.get("type") == "image_url" for part in user_content)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1)


def test_cloud_fallback_does_not_create_a_remote_route(tmp_path: Path, suite: dict):
    with TestClient(create_app(g06_config(tmp_path))) as client:
        native_id = upload(client, suite["invoice_native_pdf"], "application/pdf")
        response = client.post(
            "/api/v1/jobs",
            headers=auth(),
            json={
                "capability": "document.text_extract",
                "capability_version": "1.0.0",
                "profile": "balanced",
                "input": {"upload_id": native_id},
                "policy": {
                    "data_classification": "internal",
                    "cloud_fallback_allowed": True,
                    "allowed_remote_providers": ["openai"],
                    "retention": "none",
                },
            },
        )
        terminal = wait_terminal(client, response.json()["job_id"])
        assert terminal["status"] == "succeeded"
        result = client.get(f"/api/v1/jobs/{terminal['job_id']}/result", headers=auth()).json()
        assert result["provenance"]["engine"] == "pdftotext"


def test_task_families_are_per_family_not_a_single_badge() -> None:
    data = yaml.safe_load(Path("registry/task-families.yaml").read_text(encoding="utf-8"))
    families = {item["id"]: item["status"] for item in data["families"]}
    assert "approved" not in data.get("notice", "").lower() or "per task family" in data["notice"]
    assert families["V-01"].startswith("approved")
    assert families["V-03"] == "review"
    assert families["V-09"] == "unsupported"
    assert families["V-10"] == "approved-abstention"
    assert all(item.get("id") for item in data["families"])
