#!/usr/bin/env python3
"""Exercise every declared capability of the local runtime end to end.

Loopback only, console cookie auth. No request content is persisted here
beyond the transient fixtures this script generates itself.
"""
from __future__ import annotations

import io
import json
import struct
import sys
import time
import urllib.error
import urllib.request
import wave
import zlib
from http.cookiejar import CookieJar

BASE = "http://127.0.0.1:8830"
POLICY = {
    "data_classification": "internal",
    "cloud_fallback_allowed": False,
    "retention": "none",
}

opener = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(CookieJar())
)


def call(method, path, body=None, ctype="application/json", raw=None, timeout=240):
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    req = urllib.request.Request(BASE + path, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", ctype)
    try:
        with opener.open(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        raw_body = e.read().decode()
        try:
            return e.code, json.loads(raw_body or "{}")
        except json.JSONDecodeError:
            return e.code, {"_raw": raw_body[:200]}
    except Exception as e:  # noqa: BLE001
        return 0, {"_transport_error": f"{type(e).__name__}: {e}"}


def png(width=64, height=64, color=(220, 40, 40), box=None):
    rows = []
    for y in range(height):
        row = bytearray([0])
        for x in range(width):
            c = color
            if box and box[0] <= x < box[2] and box[1] <= y < box[3]:
                c = (250, 250, 40)
            row.extend(c)
        rows.append(bytes(row))
    raw = b"".join(rows)

    def chunk(tag, payload):
        d = tag + payload
        return struct.pack(">I", len(payload)) + d + struct.pack(">I", zlib.crc32(d))

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


def pdf(text="Facture 2026-08 total 120,00 EUR"):
    stream = f"BT /F1 12 Tf 60 700 Td ({text}) Tj ET".encode()
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, o in enumerate(objs, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + o + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs)+1}\n".encode() + b"0000000000 65535 f \n"
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += (
        f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref}\n".encode()
        + b"%%EOF\n"
    )
    return bytes(out)


def wav(seconds=1.0, freq=440.0, rate=16000):
    import math

    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        frames = bytearray()
        for i in range(int(rate * seconds)):
            v = int(12000 * math.sin(2 * math.pi * freq * i / rate))
            frames += struct.pack("<h", v)
        w.writeframes(bytes(frames))
    return buf.getvalue()


def upload(blob, ctype):
    st, body = call("POST", "/api/v1/uploads", raw=blob, ctype=ctype)
    if st != 201:
        raise RuntimeError(f"upload failed {st} {body}")
    return body["upload_id"]


def run(name, capability, profile, inp, extra=None, timeout=260):
    body = {
        "capability": capability,
        "capability_version": "1.0.0",
        "profile": profile,
        "input": inp,
        "policy": POLICY,
    }
    if extra:
        body.update(extra)
    t0 = time.time()
    st, sub = call("POST", "/api/v1/jobs", body)
    if st not in (200, 202):
        return {
            "name": name, "verdict": "FAIL", "stage": "submit",
            "http": st, "detail": sub, "secs": round(time.time() - t0, 1),
        }
    job_id = sub["job_id"]
    status = sub.get("status")
    deadline = time.time() + timeout
    while status not in {"succeeded", "failed", "cancelled", "expired", "rejected"}:
        if time.time() > deadline:
            return {
                "name": name, "verdict": "FAIL", "stage": "timeout",
                "detail": {"last_status": status}, "secs": round(time.time() - t0, 1),
            }
        time.sleep(1.0)
        st, cur = call("GET", f"/api/v1/jobs/{job_id}")
        status = cur.get("status")
        last = cur
    secs = round(time.time() - t0, 1)
    if status != "succeeded":
        return {
            "name": name, "verdict": "FAIL", "stage": status,
            "detail": last.get("error") or last, "secs": secs,
        }
    st, res = call("GET", f"/api/v1/jobs/{job_id}/result")
    if st != 200:
        return {"name": name, "verdict": "FAIL", "stage": "result",
                "http": st, "detail": res, "secs": secs}
    return {"name": name, "verdict": "OK", "secs": secs,
            "sample": summarise(res.get("result") or res)}


def summarise(res):
    if not isinstance(res, dict):
        return str(res)[:120]
    out = {}
    for k, v in res.items():
        if k in {"vector", "items", "objects", "regions", "pages", "results"} and isinstance(v, list):
            if v and isinstance(v[0], dict) and "vector" in v[0]:
                out[k] = f"{len(v)} item(s), dim={len(v[0]['vector'])}"
            else:
                out[k] = f"{len(v)} entry(ies)"
        elif isinstance(v, str):
            out[k] = v[:90]
        elif isinstance(v, (int, float, bool)) or v is None:
            out[k] = v
        elif isinstance(v, list):
            out[k] = f"[{len(v)}]"
        elif isinstance(v, dict):
            out[k] = "{" + ",".join(list(v)[:4]) + "}"
    return out


def main():
    st, sess = call("GET", "/api/v1/console/session")
    if st != 200:
        print(f"console session failed: {st} {sess}")
        return 1
    st, caps = call("GET", "/api/v1/capabilities")
    declared = [(c["id"], p) for c in caps["capabilities"] for p in c["profiles"]]
    print(f"declared capability/profile pairs: {len(declared)}\n")

    img = upload(png(box=(10, 10, 40, 40)), "image/png")
    img2 = upload(png(color=(30, 30, 210)), "image/png")
    doc = upload(pdf(), "application/pdf")
    aud = upload(wav(), "audio/wav")

    results = []
    results.append(run("text.generate / fast (dummy echo)", "text.generate", "fast",
                       {"text": "bonjour"}))
    results.append(run("text.generate / balanced (qwen3-0.6b)", "text.generate", "balanced",
                       {"prompt": "Reponds en un mot: capitale de la France?"},
                       {"constraints": {"max_output_tokens": 32}}))
    results.append(run("text.embed / balanced (qwen3-embed)", "text.embed", "balanced",
                       {"texts": ["facture d'electricite", "recette de tarte"]}))
    results.append(run("search.rerank / balanced (qwen3-reranker)", "search.rerank", "balanced",
                       {"query": "facture energie",
                        "documents": ["facture EDF octobre", "photo de vacances",
                                      "releve de consommation gaz"], "top_n": 2}))
    results.append(run("document.text_extract / fast (pdftotext)", "document.text_extract",
                       "fast", {"upload_id": doc}))
    results.append(run("document.ocr / balanced (tesseract)", "document.ocr", "balanced",
                       {"upload_id": doc}))
    results.append(run("document.parse / balanced (tesseract)", "document.parse", "balanced",
                       {"upload_id": doc}))
    results.append(run("document.extract_structured / balanced", "document.extract_structured",
                       "balanced", {"upload_id": doc},
                       {"output_schema": {"type": "object",
                                          "properties": {"total": {"type": "string"}}}}))
    results.append(run("vision.detect_objects / fast", "vision.detect_objects", "fast",
                       {"upload_id": img}))
    results.append(run("vision.compare / fast", "vision.compare", "fast",
                       {"images": [{"upload_id": img}, {"upload_id": img2}]}))
    results.append(run("vision.analyze / balanced (qwen3vl-2b)", "vision.analyze", "balanced",
                       {"upload_id": img, "question": "Quelle couleur domine?"}))
    results.append(run("audio.transcribe / fast (whisper tiny)", "audio.transcribe", "fast",
                       {"upload_id": aud}))
    aud2 = upload(wav(), "audio/wav")
    results.append(run("audio.transcribe / balanced (whisper base)", "audio.transcribe",
                       "balanced", {"upload_id": aud2}))

    ok = sum(1 for r in results if r["verdict"] == "OK")
    print(f"{'CAPABILITY':<46} {'VERDICT':<7} {'SECS':>6}")
    print("-" * 64)
    for r in results:
        print(f"{r['name']:<46} {r['verdict']:<7} {r['secs']:>6}")
    print("-" * 64)
    print(f"{ok}/{len(results)} OK\n")
    print("=== DETAIL ===")
    for r in results:
        print(json.dumps(r, ensure_ascii=False)[:600])
    return 0


if __name__ == "__main__":
    sys.exit(main())
