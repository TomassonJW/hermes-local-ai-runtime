# ADR-0002 — llama.cpp as measured general engine (confirmed)

- Status: **Accepted — confirmed by G-03 measurements**
- Date: 2026-08-27, amended 2026-08-28
- Related gates: G-03, G-04
- Evidence: `benchmarks/results/G03-ENGINE-SPIKE-2026-08-28.md`

## Context

CPU-only x86_64 and limited VM RAM need quantised text/vision, structured output, embeddings/reranking where useful, HTTP/metrics and future accelerator backends.

## Decision

llama.cpp pinned official builds (spike: `b10662`) are the general-inference engine for deployment profile A, supervised by llama-swap (spike: `v251`) for on-demand load, group swap, idle TTL and crash respawn. Capability contracts stay engine-neutral. Specialised OCR/vector/audio remain separate workers; ONNX/fastembed is the fast-profile embedding candidate.

Measured on the target VM: text 0.6B Q8 cold 413 ms / 63–69 tok/s; vision 2B Q4_K_M cold 3.5 s, warm 1.0 s, RSS ≤ 3.3 GiB; strict `json_schema` output valid 3/3; rerank correct; stream cancel releases the slot; TTL unload and SIGKILL respawn proven; hard per-worker memory caps enforced via systemd user scopes (kill in 1 s, no collateral).

## Operational constraints recorded

- llama-swap must be started with `-listen 127.0.0.1:PORT` (YAML `listen` ignored) and always fronted by the control plane (it has no auth).
- Prometheus metrics require the `--metrics` server flag.
- Qwen3 presets for bounded tasks must disable thinking mode (`/no_think`).
- Small-model output needs the deterministic validation layer (French decimal comma mis-parse observed); `review_required` semantics are load-bearing.

## Falsification

Demote if a future gate shows unacceptable lifecycle, memory, vision, packaging, cancellation or observability on the target VM compared with a thinner alternative.
