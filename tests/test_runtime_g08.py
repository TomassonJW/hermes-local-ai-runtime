from __future__ import annotations

import json
import os
import struct
import time
import wave
from pathlib import Path

from fastapi.testclient import TestClient

from runtime.app import create_app
from runtime.audio import energy_vad, inspect_audio, sniff_audio
from runtime.config import Budget, RouteConfig, RuntimeConfig, TokenConfig

TOKEN = "fixture-token-g08"
POLICY = {
    "data_classification": "internal",
    "cloud_fallback_allowed": False,
    "retention": "none",
}


def pcm_wav(path: Path, seconds: float = 1.0, amplitude: int = 8000, rate: int = 16000) -> Path:
    frames = int(seconds * rate)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        samples = []
        for index in range(frames):
            value = int(amplitude * (1 if (index // 40) % 2 == 0 else -1))
            samples.append(struct.pack("<h", value))
        handle.writeframes(b"".join(samples))
    return path


def silent_wav(path: Path, seconds: float = 1.0) -> Path:
    return pcm_wav(path, seconds=seconds, amplitude=0)


def fake_whisper(path: Path) -> Path:
    script = path / "fake-whisper"
    script.write_text(
        "#!/usr/bin/env python3\n"
        "import json, sys\n"
        "from pathlib import Path\n"
        "args = sys.argv[1:]\n"
        "wav = Path(args[args.index('-f') + 1])\n"
        "payload = {\n"
        "  'transcription': [{\n"
        "    'offsets': {'from': 0, 'to': 800},\n"
        "    'text': 'facture SYN-0042'\n"
        "  }]\n"
        "}\n"
        "wav.with_name(wav.name + '.json').write_text(json.dumps(payload))\n"
        "sys.exit(0)\n",
        encoding="utf-8",
    )
    script.chmod(0o700)
    model = path / "dummy-model.bin"
    model.write_bytes(b"whisper-dummy")
    return script


def _route(**overrides) -> RouteConfig:
    base = dict(
        id="audio-transcribe@1",
        capability="audio.transcribe",
        capability_version="1.0.0",
        profiles=("balanced", "fast"),
        worker="whisper-cpp",
        upstream_base=None,
        upstream_model=None,
        engine="whisper.cpp",
        engine_version="b4938",
        resource_class="heavy",
        memory_estimate_mib=512,
        sync_allowed=True,
        timeout_ms=30_000,
        preset="whisper-cpu-baseline-v1",
        worker_binary=None,
    )
    base.update(overrides)
    return RouteConfig(**base)


def g08_config(tmp_path: Path, cli: Path, model: Path) -> RuntimeConfig:
    return RuntimeConfig(
        listen_host="127.0.0.1",
        listen_port=8090,
        routes=(_route(worker_binary=str(cli), upstream_model=str(model)),),
        budget=Budget(heavy_slots=1, light_slots=1, queue_max=4, memory_floor_available_mib=0),
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


def wait_terminal(client: TestClient, job_id: str, timeout: float = 5) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        data = client.get(f"/api/v1/jobs/{job_id}", headers=auth()).json()
        if data["status"] in {"succeeded", "failed", "cancelled", "rejected"}:
            return data
        time.sleep(0.02)
    raise AssertionError(f"job {job_id} did not terminate")


def test_sniff_and_short_audio(tmp_path: Path) -> None:
    wav = pcm_wav(tmp_path / "ok.wav", seconds=1.0)
    assert sniff_audio(wav) == "wav"
    short = pcm_wav(tmp_path / "short.wav", seconds=0.05)
    info = inspect_audio(short)
    assert info["unsupported"] is True


def test_vad_rejects_silence(tmp_path: Path) -> None:
    quiet = silent_wav(tmp_path / "quiet.wav", seconds=1.0)
    voiced = pcm_wav(tmp_path / "voice.wav", seconds=1.0)
    assert energy_vad(quiet)["has_speech"] is False
    assert energy_vad(voiced)["has_speech"] is True


def test_transcribe_job_returns_segments_and_no_path(tmp_path: Path) -> None:
    cli = fake_whisper(tmp_path)
    wav = pcm_wav(tmp_path / "speech.wav", seconds=1.0)
    with TestClient(create_app(g08_config(tmp_path, cli, tmp_path / "dummy-model.bin"))) as client:
        uploaded = client.post(
            "/api/v1/uploads",
            headers={**auth(), "Content-Type": "audio/wav"},
            content=wav.read_bytes(),
        )
        assert uploaded.status_code == 201, uploaded.text
        upload_id = uploaded.json()["upload_id"]
        submitted = client.post(
            "/api/v1/jobs",
            headers=auth(),
            json={
                "capability": "audio.transcribe",
                "capability_version": "1.0.0",
                "profile": "balanced",
                "input": {"upload_id": upload_id, "language": "fr"},
                "policy": POLICY,
            },
        )
        assert submitted.status_code == 202, submitted.text
        job = wait_terminal(client, submitted.json()["job_id"])
        assert job["status"] == "succeeded"
        result = client.get(
            f"/api/v1/jobs/{job['job_id']}/result", headers=auth()
        ).json()
        assert "SYN-0042" in result["result"]["text"]
        assert result["result"]["segments"][0]["text"]
        dumped = json.dumps(result["result"])
        assert str(wav) not in dumped
        assert "ggml" not in dumped.lower()


def test_silence_is_unsupported_not_invented(tmp_path: Path) -> None:
    cli = fake_whisper(tmp_path)
    wav = silent_wav(tmp_path / "silence.wav", seconds=1.0)
    with TestClient(create_app(g08_config(tmp_path, cli, tmp_path / "dummy-model.bin"))) as client:
        uploaded = client.post(
            "/api/v1/uploads",
            headers={**auth(), "Content-Type": "audio/wav"},
            content=wav.read_bytes(),
        )
        upload_id = uploaded.json()["upload_id"]
        submitted = client.post(
            "/api/v1/jobs",
            headers=auth(),
            json={
                "capability": "audio.transcribe",
                "capability_version": "1.0.0",
                "profile": "balanced",
                "input": {"upload_id": upload_id},
                "policy": POLICY,
            },
        )
        job = wait_terminal(client, submitted.json()["job_id"])
        result = client.get(
            f"/api/v1/jobs/{job['job_id']}/result", headers=auth()
        ).json()
        assert result["result"]["status"] == "unsupported"
        assert result["result"]["text"] == ""
        assert result["review_required"] is True


def test_path_input_is_rejected(tmp_path: Path) -> None:
    cli = fake_whisper(tmp_path)
    with TestClient(create_app(g08_config(tmp_path, cli, tmp_path / "dummy-model.bin"))) as client:
        response = client.post(
            "/api/v1/jobs",
            headers=auth(),
            json={
                "capability": "audio.transcribe",
                "capability_version": "1.0.0",
                "profile": "balanced",
                "input": {"path": "/etc/passwd"},
                "policy": POLICY,
            },
        )
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "INVALID_INPUT"


def test_openai_transcription_adapter(tmp_path: Path) -> None:
    cli = fake_whisper(tmp_path)
    wav = pcm_wav(tmp_path / "speech.wav", seconds=1.0)
    with TestClient(create_app(g08_config(tmp_path, cli, tmp_path / "dummy-model.bin"))) as client:
        response = client.post(
            "/v1/audio/transcriptions",
            headers=auth(),
            files={"file": ("speech.wav", wav.read_bytes(), "audio/wav")},
            data={"model": "hlair/transcribe-balanced", "language": "fr"},
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert "SYN-0042" in body["text"]
        assert body["model"] == "hlair/transcribe-balanced"
        assert "ggml" not in json.dumps(body).lower()


def test_unknown_format_is_rejected(tmp_path: Path) -> None:
    cli = fake_whisper(tmp_path)
    with TestClient(create_app(g08_config(tmp_path, cli, tmp_path / "dummy-model.bin"))) as client:
        uploaded = client.post(
            "/api/v1/uploads",
            headers={**auth(), "Content-Type": "application/octet-stream"},
            content=b"not-audio",
        )
        upload_id = uploaded.json()["upload_id"]
        submitted = client.post(
            "/api/v1/jobs",
            headers=auth(),
            json={
                "capability": "audio.transcribe",
                "capability_version": "1.0.0",
                "profile": "balanced",
                "input": {"upload_id": upload_id},
                "policy": POLICY,
            },
        )
        job = wait_terminal(client, submitted.json()["job_id"])
        assert job["status"] == "failed"
        assert job["error"]["code"] == "INVALID_INPUT"
