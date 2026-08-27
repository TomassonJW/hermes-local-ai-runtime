# Mission 02 — Runtime engine spike

## Goal

Select the thinnest execution substrate that satisfies the product boundaries on the actual CPU VM.

## Preconditions

- UI-00 explicitly accepted;
- G-02 live profile current;
- installation/rollback plan accepted;
- model-store quota and temporary paths defined;
- no unrelated service degradation.

## Spike matrix

### General inference

- pinned llama.cpp build;
- text structured output with a small text candidate;
- Qwen3-VL 2B image question with exact GGUF/projector artefacts;
- context, image, KV F16/Q8/Q4 comparison;
- cold/warm latency and memory;
- cancellation and crash.

### Lifecycle

- direct process management baseline;
- llama-swap candidate;
- load, lease, idle TTL, drain, unload, pressure unload;
- metrics and health.

### Alternative platform

Configure equivalent bounded text, vision, embedding/rerank, and audio surfaces in LocalAI where feasible.

### Specialists

- native PDF extraction;
- PP-OCR/Paddle candidate;
- ONNX embedding/reranking candidate;
- whisper.cpp smoke test.

## Evidence

- exact source revisions and hashes;
- public-safe commands/config;
- hardware profile;
- install and cleanup;
- result contract compatibility;
- idle and peak resources;
- failure and recovery;
- licence/notice impact;
- maintenance assessment.

## Decisions

Update ADR-0002 and ADR-0003. Select:

- engine adapters;
- process supervisor/lifecycle;
- dependency isolation;
- packaging direction;
- metrics interface.

## Stop

Do not build the production gateway until G-03 and G-04 pass.
