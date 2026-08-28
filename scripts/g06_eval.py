#!/usr/bin/env python3
"""G-06 loopback evaluation on synthetic fixtures. No permanent service."""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmarks.synthetic.generate import EXPECTED, write_suite
from runtime.document import extract_invoice_fields, extract_pdf_text, ocr_file
from runtime.vision_specialists import assess_image, detect_saturated_boxes, similarity

SPIKE = ROOT.parent / "spike-g03"
DEFAULT_SWAP = SPIKE / "bin" / "llama-swap"
DEFAULT_CONFIG = SPIKE / "llama-swap-config.yaml"


def _ok(flag: bool) -> str:
    return "pass" if flag else "fail"


def evaluate_specialists(suite: dict) -> dict:
    native = extract_pdf_text(suite["invoice_native_pdf"])
    scanned = extract_pdf_text(suite["invoice_image_pdf"])
    ocr = ocr_file(suite["invoice_png"])
    fields = extract_invoice_fields(ocr["text"])
    objects = detect_saturated_boxes(suite["objects"])
    near = similarity(suite["objects"], suite["objects_near"])
    far = similarity(suite["objects"], suite["unrelated"])
    tiny = assess_image(suite["ui_tiny"])
    labels = {item["label"] for item in objects["objects"]}
    return {
        "V-04-native": {
            "status": _ok("SYN-0042" in native["pages"][0]["text"] and not native["image_only"]),
            "engine": native["engine"],
            "review_required": native["review_required"],
        },
        "V-04-image-only-detection": {
            "status": _ok(scanned["image_only"]),
            "engine": scanned["engine"],
            "review_required": scanned["review_required"],
        },
        "V-04-ocr": {
            "status": _ok("SYN-0042" in ocr["text"] and ("123,45" in ocr["text"] or "123.45" in ocr["text"])),
            "engine": ocr["engine"],
            "mean_confidence": ocr.get("mean_confidence"),
            "review_required": ocr["review_required"],
        },
        "V-05-fields": {
            "status": _ok(
                fields["fields"].get("invoice_id") == EXPECTED["invoice_id"]
                and fields["fields"].get("total_eur") == EXPECTED["total_eur"]
            ),
            "fields": fields["fields"],
            "review_required": fields["review_required"],
        },
        "V-07-objects": {
            "status": _ok(labels == {"red-object", "blue-object"}),
            "labels": sorted(labels),
            "review_required": False,
        },
        "V-08-similarity": {
            "status": _ok(near["score"] > far["score"] + 0.15 and near["score"] > 0.9),
            "near": near["score"],
            "far": far["score"],
            "review_required": True,
            "note": "approved for near-duplicate only, not semantic similarity",
        },
        "V-10-tiny": {
            "status": _ok(tiny["unsupported"]),
            "review_required": True,
        },
    }


def _http_json(url: str, payload: dict | None = None, timeout: int = 180) -> dict:
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"} if payload is not None else {},
        method="GET" if payload is None else "POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def wait_health(url: str, timeout: float = 90) -> None:
    deadline = time.monotonic() + timeout
    last = ""
    while time.monotonic() < deadline:
        try:
            _http_json(url)
            return
        except Exception as exc:  # noqa: BLE001 - probe loop
            last = str(exc)
            time.sleep(0.5)
    raise RuntimeError(f"upstream not ready: {last}")


def evaluate_vlm(suite: dict, base: str, model: str) -> dict:
    png = suite["ui_error"].read_bytes()
    data_url = "data:image/png;base64," + base64.b64encode(png).decode("ascii")
    question = "What error code is visible, and what does the dialog say?"
    started = time.monotonic()
    body = _http_json(
        f"{base}/v1/chat/completions",
        {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Answer the user's question about the image. "
                                "Do not give a generic caption. "
                                f"Question: {question} /no_think"
                            ),
                        },
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
            "max_tokens": 128,
            "temperature": 0.1,
        },
        timeout=180,
    )
    elapsed_ms = round((time.monotonic() - started) * 1000)
    answer = body["choices"][0]["message"]["content"]
    hit = EXPECTED["error_code"] in answer and "full" in answer.lower()
    return {
        "V-01-V-02-vlm": {
            "status": _ok(hit),
            "engine": "llama.cpp+llama-swap",
            "model": model,
            "latency_ms": elapsed_ms,
            "answer_excerpt": answer[:240],
            "review_required": not hit,
        }
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--with-vlm", action="store_true")
    parser.add_argument("--listen", default="127.0.0.1:8860")
    args = parser.parse_args()
    dest = ROOT / "benchmarks" / "synthetic" / "generated"
    suite = write_suite(dest)
    report = {
        "hardware_profile": "hermes-cpu-8vcpu-16gib",
        "paddleocr": "not-measured",
        "private_corpus": "not-mounted",
        "families": evaluate_specialists(suite),
    }
    proc = None
    if args.with_vlm:
        if not DEFAULT_SWAP.is_file() or not DEFAULT_CONFIG.is_file():
            report["families"]["V-01-V-02-vlm"] = {
                "status": "skip",
                "reason": "spike-g03 llama-swap artefacts missing",
            }
        else:
            host, port = args.listen.split(":")
            proc = subprocess.Popen(
                [
                    str(DEFAULT_SWAP),
                    "-config",
                    str(DEFAULT_CONFIG),
                    "-listen",
                    args.listen,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            try:
                wait_health(f"http://{host}:{port}/running")
                report["families"].update(
                    evaluate_vlm(suite, f"http://{host}:{port}", "vision-2b")
                )
            finally:
                proc.terminate()
                try:
                    proc.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    proc.kill()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
