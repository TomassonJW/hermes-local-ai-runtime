# ADR-0002 — llama.cpp as preferred first general engine

- Status: Accepted as spike default, not lock-in
- Date: 2026-08-27
- Related gates: G-03, G-04

## Context

CPU-only x86_64 and limited VM RAM need quantised text/vision, structured output, embeddings/reranking where useful, HTTP/metrics and future accelerator backends.

## Decision

Use llama.cpp as first measured general-engine candidate and evaluate llama-swap for lifecycle. Keep capability contracts engine-neutral. Specialised OCR/vector/audio remain separate.

## Consequences

GGUF and engine-version compatibility enter registry; multimodal needs explicit tests; architecture may switch/thin after LocalAI comparison.

## Falsification

Demote if target VM shows unacceptable lifecycle, memory, vision, packaging, cancellation or observability compared with thinner alternative.
