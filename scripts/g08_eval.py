#!/usr/bin/env python3
"""G-08 loopback evaluation: whisper.cpp transcription. No permanent service."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.app import create_app
from runtime.config import Budget, RouteConfig, RuntimeConfig, TokenConfig

SPIKE = ROOT.parent / "spike-g03"
WHISPER_CLI = SPIKE / "whisper" / "whisper-bin-ubuntu-x64" / "whisper-cli"
MODELS = {
    "tiny": SPIKE / "models" / "ggml-tiny.bin",
    "base": SPIKE / "models" / "ggml-base.bin",
    "small": SPIKE / "models" / "ggml-small.bin",
}
TOKEN = "fixture-token-g08-eval"
PHRASE = "La facture SYN-0042 s'eleve a cent vingt-trois euros."


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def make_speech_wav(dest: Path) -> dict:
    espeak = shutil.which("espeak-ng") or shutil.which("espeak")
    if espeak:
        subprocess.run(
            [espeak, "-v", "fr", "-s", "140", "-w", str(dest), PHRASE],
            check=True,
            capture_output=True,
        )
        return {"engine": Path(espeak).name, "text": PHRASE}
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("neither espeak-ng nor ffmpeg is available")
    # Fallback: not speech. Eval will mark French quality as not-measured.
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=2",
            "-ac",
            "1",
            "-ar",
            "16000",
            str(dest),
        ],
        check=True,
        capture_output=True,
    )
    return {"engine": "ffmpeg-sine", "text": None}


def make_silence_wav(dest: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=16000:cl=mono",
            "-t",
            "1",
            str(dest),
        ],
        check=True,
        capture_output=True,
    )


def runtime_config(tmp: Path, model: Path) -> RuntimeConfig:
    return RuntimeConfig(
        listen_host="127.0.0.1",
        listen_port=8090,
        routes=(
            RouteConfig(
                id="audio-transcribe@1",
                capability="audio.transcribe",
                capability_version="1.0.0",
                profiles=("balanced", "fast"),
                worker="whisper-cpp",
                upstream_base=None,
                upstream_model=str(model),
                engine="whisper.cpp",
                engine_version="b4938",
                resource_class="heavy",
                memory_estimate_mib=512,
                sync_allowed=True,
                timeout_ms=180_000,
                preset="whisper-cpu-baseline-v1",
                worker_binary=str(WHISPER_CLI),
                model_artifacts=(f"sha256:{sha256(model)}",),
            ),
        ),
        budget=Budget(heavy_slots=1, light_slots=1, queue_max=4, memory_floor_available_mib=0),
        tokens=(
            TokenConfig(
                name="eval",
                token=TOKEN,
                scopes=("capability:invoke:*", "job:read:self", "job:cancel:self", "system:read"),
            ),
        ),
        db_path=str(tmp / "jobs.db"),
    )


def transcribe(client: TestClient, wav: Path, language: str = "fr") -> dict:
    headers = {"Authorization": f"Bearer {TOKEN}"}
    uploaded = client.post(
        "/api/v1/uploads",
        headers={**headers, "Content-Type": "audio/wav"},
        content=wav.read_bytes(),
    )
    upload_id = uploaded.json()["upload_id"]
    started = time.monotonic()
    submitted = client.post(
        "/api/v1/jobs",
        headers=headers,
        json={
            "capability": "audio.transcribe",
            "capability_version": "1.0.0",
            "profile": "balanced",
            "input": {"upload_id": upload_id, "language": language},
            "policy": {
                "data_classification": "internal",
                "cloud_fallback_allowed": False,
                "retention": "none",
            },
        },
    )
    job_id = submitted.json()["job_id"]
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        job = client.get(f"/api/v1/jobs/{job_id}", headers=headers).json()
        if job["status"] in {"succeeded", "failed", "rejected", "cancelled"}:
            result = client.get(f"/api/v1/jobs/{job_id}/result", headers=headers).json()
            return {
                "status": job["status"],
                "elapsed_ms": round((time.monotonic() - started) * 1000),
                "job": job,
                "result": result.get("result") if result else None,
                "error": job.get("error"),
            }
        time.sleep(0.05)
    return {"status": "timeout"}


def main() -> int:
    if not WHISPER_CLI.is_file():
        print(json.dumps({"status": "skip", "reason": "whisper-cli missing"}))
        return 0
    report: dict = {
        "hardware_profile": "hermes-cpu-8vcpu-16gib",
        "engine": "whisper.cpp",
        "engine_version": "b4938",
        "qwen3_asr": "not-packaged",
        "streaming": "not-implemented",
        "shared_service": False,
        "variants": {},
    }
    with tempfile.TemporaryDirectory(prefix="g08-eval-") as raw:
        tmp = Path(raw)
        speech = tmp / "fr.wav"
        source = make_speech_wav(speech)
        report["fixture"] = source
        silence = tmp / "silence.wav"
        make_silence_wav(silence)
        for name, model in MODELS.items():
            if not model.is_file():
                report["variants"][name] = {"status": "skip", "reason": "model missing"}
                continue
            cfg_dir = tmp / name
            cfg_dir.mkdir()
            with TestClient(create_app(runtime_config(cfg_dir, model))) as client:
                spoken = transcribe(client, speech, "fr")
                quiet = transcribe(client, silence, "fr")
            text = ((spoken.get("result") or {}).get("text") or "").lower()
            hits = source["text"] is not None and all(
                token in text for token in ("facture", "0042")
            )
            report["variants"][name] = {
                "status": "measured",
                "sha256": sha256(model),
                "bytes": model.stat().st_size,
                "speech": {
                    "job_status": spoken.get("status"),
                    "text": (spoken.get("result") or {}).get("text"),
                    "rtf": (spoken.get("result") or {}).get("rtf"),
                    "duration_s": (spoken.get("result") or {}).get("duration_s"),
                    "elapsed_ms": spoken.get("elapsed_ms"),
                    "chunks": (spoken.get("result") or {}).get("chunks"),
                    "french_tokens_ok": hits,
                },
                "silence": {
                    "status": (quiet.get("result") or {}).get("status"),
                    "text": (quiet.get("result") or {}).get("text"),
                },
            }
    print(json.dumps(report, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
