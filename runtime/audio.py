"""Audio inspection, energy VAD, chunking and whisper.cpp transcription."""

from __future__ import annotations

import json
import os
import shutil
import signal
import struct
import subprocess
import tempfile
import time
import wave
from pathlib import Path
from typing import Any

MAX_DURATION_S = 15 * 60
MIN_DURATION_S = 0.2
CHUNK_S = 30.0
CHUNK_OVERLAP_S = 1.0
VAD_FRAME_S = 0.03
VAD_RMS_THRESHOLD = 0.01
SUPPORTED_WAV = "audio/wav"


class AudioError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def sniff_audio(path: Path) -> str:
    header = path.read_bytes()[:12]
    if header[:4] == b"RIFF" and header[8:12] == b"WAVE":
        return "wav"
    if header[:3] == b"ID3" or header[:2] in {b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"}:
        return "mp3"
    if header[:4] == b"fLaC":
        return "flac"
    if header[:4] == b"OggS":
        return "ogg"
    raise AudioError("INVALID_INPUT", "audio format is not wav, mp3, flac or ogg")


def wav_duration_s(path: Path) -> float:
    with wave.open(str(path), "rb") as handle:
        frames = handle.getnframes()
        rate = handle.getframerate()
    if rate <= 0:
        raise AudioError("INVALID_INPUT", "wav sample rate is invalid")
    return frames / rate


def inspect_audio(path: Path, *, max_duration_s: float = MAX_DURATION_S) -> dict[str, Any]:
    kind = sniff_audio(path)
    if path.stat().st_size < 64:
        raise AudioError("INVALID_INPUT", "audio file is empty")
    duration = wav_duration_s(path) if kind == "wav" else None
    if duration is not None and duration < MIN_DURATION_S:
        return {
            "kind": kind,
            "duration_s": duration,
            "unsupported": True,
            "review_required": True,
            "warnings": [
                {
                    "code": "AUDIO_TOO_SHORT",
                    "message": "audio is shorter than 200 ms",
                }
            ],
        }
    if duration is not None and duration > max_duration_s:
        raise AudioError("INPUT_TOO_LARGE", f"audio exceeds {int(max_duration_s)} s")
    return {
        "kind": kind,
        "duration_s": duration,
        "unsupported": False,
        "review_required": False,
        "warnings": [],
    }


def decode_to_wav16(path: Path, dest: Path) -> Path:
    kind = sniff_audio(path)
    if kind == "wav":
        with wave.open(str(path), "rb") as handle:
            channels = handle.getnchannels()
            width = handle.getsampwidth()
            rate = handle.getframerate()
            if channels == 1 and width == 2 and rate == 16000:
                if dest.resolve() != path.resolve():
                    dest.write_bytes(path.read_bytes())
                return dest if dest.exists() else path
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise AudioError("MODEL_LOAD_FAILED", "ffmpeg is required to decode this audio")
    dest.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [
            ffmpeg,
            "-y",
            "-i",
            str(path),
            "-ac",
            "1",
            "-ar",
            "16000",
            "-c:a",
            "pcm_s16le",
            str(dest),
        ],
        check=False,
        capture_output=True,
        timeout=60,
    )
    if completed.returncode != 0 or not dest.is_file():
        raise AudioError("INVALID_INPUT", "audio could not be decoded")
    return dest


def _rms(frame: bytes) -> float:
    if len(frame) < 2:
        return 0.0
    count = len(frame) // 2
    samples = struct.unpack("<" + "h" * count, frame[: count * 2])
    mean = sum(sample * sample for sample in samples) / count
    return (mean ** 0.5) / 32768.0


def energy_vad(path: Path) -> dict[str, Any]:
    with wave.open(str(path), "rb") as handle:
        rate = handle.getframerate()
        width = handle.getsampwidth()
        channels = handle.getnchannels()
        if width != 2 or channels != 1:
            raise AudioError("INVALID_INPUT", "VAD requires 16-bit mono wav")
        frame_bytes = int(rate * VAD_FRAME_S) * 2
        voiced: list[tuple[float, float]] = []
        offset = 0.0
        in_speech = False
        start = 0.0
        while True:
            chunk = handle.readframes(int(rate * VAD_FRAME_S))
            if not chunk:
                break
            rms = _rms(chunk)
            if rms >= VAD_RMS_THRESHOLD:
                if not in_speech:
                    start = offset
                    in_speech = True
            elif in_speech:
                voiced.append((start, offset))
                in_speech = False
            offset += VAD_FRAME_S
            if len(chunk) < frame_bytes:
                break
        if in_speech:
            voiced.append((start, offset))
    duration = wav_duration_s(path)
    speech_s = sum(end - start for start, end in voiced)
    return {
        "segments": voiced,
        "speech_s": round(speech_s, 3),
        "has_speech": speech_s >= MIN_DURATION_S,
        "duration_s": duration,
    }


def chunk_spans(duration_s: float, speech: list[tuple[float, float]]) -> list[tuple[float, float]]:
    if not speech:
        return []
    spans: list[tuple[float, float]] = []
    start = speech[0][0]
    end = speech[0][1]
    for next_start, next_end in speech[1:]:
        if next_start - start <= CHUNK_S:
            end = max(end, next_end)
            continue
        spans.append((start, min(end, duration_s)))
        start = max(0.0, next_start - CHUNK_OVERLAP_S)
        end = next_end
    spans.append((start, min(end, duration_s)))
    return spans or [(0.0, duration_s)]


def write_wav_slice(source: Path, dest: Path, start_s: float, end_s: float) -> None:
    with wave.open(str(source), "rb") as handle:
        rate = handle.getframerate()
        start = int(start_s * rate)
        stop = int(end_s * rate)
        handle.setpos(start)
        frames = handle.readframes(max(0, stop - start))
        params = handle.getparams()
    dest.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(dest), "wb") as out:
        out.setparams(params)
        out.writeframes(frames)


def parse_whisper_json(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = payload.get("transcription") or payload.get("segments") or []
    segments: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        text = str(row.get("text") or "").strip()
        offsets = row.get("offsets") or {}
        timestamps = row.get("timestamps") or {}
        start_ms = offsets.get("from")
        end_ms = offsets.get("to")
        if start_ms is None:
            start_ms = _stamp_to_ms(timestamps.get("from"))
        if end_ms is None:
            end_ms = _stamp_to_ms(timestamps.get("to"))
        segments.append(
            {
                "start_ms": int(start_ms or 0),
                "end_ms": int(end_ms or 0),
                "text": text,
            }
        )
    return segments


def _stamp_to_ms(value: Any) -> int:
    if not isinstance(value, str):
        return 0
    cleaned = value.replace(",", ".")
    parts = cleaned.split(":")
    if len(parts) != 3:
        return 0
    hours, minutes, seconds = parts
    return int((int(hours) * 3600 + int(minutes) * 60 + float(seconds)) * 1000)


def transcribe_with_whisper(
    wav: Path,
    *,
    cli: str,
    model: str,
    language: str,
    threads: int = 4,
    timeout_s: float = 120,
) -> dict[str, Any]:
    if not Path(cli).is_file():
        raise AudioError("MODEL_LOAD_FAILED", "whisper binary is missing")
    if not Path(model).is_file():
        raise AudioError("MODEL_LOAD_FAILED", "whisper model is missing")
    out_json = Path(str(wav) + ".json")
    command = [
        cli,
        "-m",
        model,
        "-f",
        str(wav),
        "-oj",
        "-t",
        str(threads),
        "-l",
        language if language and language != "auto" else "auto",
        "-nt",
    ]
    env = os.environ.copy()
    libdir = str(Path(cli).resolve().parent)
    existing = env.get("LD_LIBRARY_PATH", "")
    env["LD_LIBRARY_PATH"] = libdir if not existing else libdir + os.pathsep + existing
    proc = subprocess.Popen(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        start_new_session=True,
        env=env,
        cwd=str(wav.parent),
    )

    def _stop(_signum: int, _frame: Any) -> None:
        if proc.poll() is None:
            os.killpg(proc.pid, signal.SIGKILL)

    previous = signal.signal(signal.SIGTERM, _stop)
    started = time.monotonic()
    try:
        try:
            proc.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired as exc:
            os.killpg(proc.pid, signal.SIGKILL)
            raise AudioError("TIMEOUT", "whisper deadline exceeded") from exc
        if proc.returncode != 0:
            raise AudioError("MODEL_LOAD_FAILED", "whisper process failed")
        if not out_json.is_file():
            raise AudioError("MODEL_LOAD_FAILED", "whisper produced no json")
        payload = json.loads(out_json.read_text(encoding="utf-8"))
        segments = parse_whisper_json(payload)
        text = " ".join(item["text"] for item in segments if item["text"]).strip()
        duration = wav_duration_s(wav)
        elapsed = time.monotonic() - started
        return {
            "text": text,
            "segments": segments,
            "language": language,
            "duration_s": round(duration, 3),
            "rtf": round(elapsed / duration, 3) if duration else None,
            "engine": "whisper.cpp",
        }
    finally:
        signal.signal(signal.SIGTERM, previous)
        out_json.unlink(missing_ok=True)
        if proc.poll() is None:
            os.killpg(proc.pid, signal.SIGKILL)


def transcribe_file(
    path: Path,
    *,
    cli: str,
    model: str,
    language: str = "auto",
    timeout_s: float = 180,
    workdir: Path | None = None,
) -> dict[str, Any]:
    info = inspect_audio(path)
    if info.get("unsupported"):
        return {
            "text": "",
            "segments": [],
            "status": "unsupported",
            "review_required": True,
            "warnings": info["warnings"],
            "engine": "whisper.cpp",
        }
    root = Path(workdir or tempfile.mkdtemp(prefix="g08-audio-"))
    root.mkdir(parents=True, exist_ok=True)
    wav = decode_to_wav16(path, root / "audio.wav")
    vad = energy_vad(wav)
    if not vad["has_speech"]:
        return {
            "text": "",
            "segments": [],
            "status": "unsupported",
            "duration_s": vad["duration_s"],
            "review_required": True,
            "warnings": [
                {
                    "code": "NO_SPEECH",
                    "message": "no voiced segment was detected",
                }
            ],
            "engine": "energy-vad",
        }
    spans = chunk_spans(vad["duration_s"], vad["segments"])
    merged: list[dict[str, Any]] = []
    started = time.monotonic()
    for index, (start, end) in enumerate(spans):
        slice_path = root / f"chunk-{index}.wav"
        write_wav_slice(wav, slice_path, start, end)
        piece = transcribe_with_whisper(
            slice_path,
            cli=cli,
            model=model,
            language=language,
            timeout_s=timeout_s,
        )
        offset_ms = int(start * 1000)
        for segment in piece["segments"]:
            merged.append(
                {
                    "start_ms": segment["start_ms"] + offset_ms,
                    "end_ms": segment["end_ms"] + offset_ms,
                    "text": segment["text"],
                }
            )
    text = " ".join(item["text"] for item in merged if item["text"]).strip()
    duration = vad["duration_s"]
    elapsed = time.monotonic() - started
    return {
        "text": text,
        "segments": merged,
        "language": language,
        "duration_s": round(duration, 3),
        "rtf": round(elapsed / duration, 3) if duration else None,
        "status": "transcribed",
        "review_required": not bool(text),
        "warnings": [],
        "engine": "whisper.cpp",
        "vad": True,
        "chunks": len(spans),
    }
