# G-03 engine spike report — 2026-08-28

Hardware profile: `hermes-cpu-8vcpu-16gib` (live: 10 vCPU / ~19.5 GiB / no GPU /
no swap). All servers loopback-only. All artefacts downloaded into a disposable
spike workspace outside Git; nothing installed system-wide; every process torn
down after measurement. Raw scenario outputs: spike workspace `results/*.json`
(local, public-safe aggregates reproduced here).

## Pinned artefacts

| Artefact | Version / file | SHA-256 |
| --- | --- | --- |
| llama.cpp (official ubuntu-x64 build) | `b10662` (commit `18443257a`) | archive `efccc37e…6279b` |
| llama-swap | `v251` (commit `4ec3175`) | archive `85bd7f2…7622b` |
| LocalAI container | `localai/localai:latest-cpu` = v3.0.0 (`f9b968e`) | image 3.88 GB |
| Qwen3-0.6B Q8_0 GGUF | `Qwen/Qwen3-0.6B-GGUF` | `9465e63…3bb031` |
| Qwen3-Embedding-0.6B Q8_0 | `Qwen/Qwen3-Embedding-0.6B-GGUF` | `06507c7…c3e439` |
| Qwen3-Reranker-0.6B Q8_0 | `ggml-org/Qwen3-Reranker-0.6B-Q8_0-GGUF` | `22c9979…429a48` |
| Qwen3-VL-2B Q4_K_M + mmproj Q8_0 | `Qwen/Qwen3-VL-2B-Instruct-GGUF` | `089d75c…a6c2ae` / `f9a68fa…f9c82` |
| fastembed (ONNX specialist) | 0.8.0 + `paraphrase-multilingual-MiniLM-L12-v2` | venv-local |

## llama.cpp measured results

| Surface | Model | RSS | Cold | Warm | Quality signal |
| --- | --- | ---: | ---: | ---: | --- |
| text generate | Qwen3-0.6B Q8, ctx 4k, 4 threads | 1.1 GiB | 413 ms | ~380 ms, 63–69 tok/s | correct with `/no_think`; thinking mode otherwise consumes the budget |
| structured output | idem, `json_schema` strict | — | — | ~1.1 s | 3/3 valid JSON matching schema; **French decimal comma mis-parsed (`123,45` → `123450`)** — deterministic validation layer required, exactly as the product mandates |
| embeddings | Qwen3-Embedding-0.6B Q8, pooling last | 0.94 GiB | — | 82–122 ms /batch 3 | 1024 dims; bit-deterministic per request shape; batch-composition wobble ≤ 2.8e-3 (declared in contract) |
| rerank | Qwen3-Reranker-0.6B Q8 | 1.36 GiB | 1.19 s /4 docs | — | correct top document, clean score separation |
| vision | Qwen3-VL-2B Q4_K_M + mmproj Q8 | 3.0–3.3 GiB | 3.45 s | 1.02 s | reads the synthetic dialog exactly (code E42 + disk-full message) |
| cancel | streaming abort mid-generation | — | — | — | server releases the slot, next request 132 ms |
| health/metrics | `/health` 1 ms | — | — | — | Prometheus metrics need `--metrics` flag (preset note) |

## llama-swap lifecycle results

- On-demand cold load through proxy: 1.54 s (text 0.6B), warm 495 ms (~100 ms proxy overhead).
- Heavy-group swap: text→vision 3.08 s (unloads text automatically), vision→text 1.56 s.
- TTL unload proven: 60 s idle → `/running` empty, worker process gone.
- Crash recovery proven: SIGKILL of the worker → next request transparently
  respawns and answers in 1.5 s.
- Caveats: `listen:` in YAML is ignored — loopback must be forced with the
  `-listen 127.0.0.1:PORT` CLI flag (default binds all interfaces); state API
  is `/running`; no auth of its own (must stay behind the control plane).

## G-04 resource-safety scenarios (llama-swap + bounded scopes)

| Scenario | Result |
| --- | --- |
| Baseline | 14.55 GiB available, swap 0 |
| Heavy cold/warm | 3.92 s / 0.65 s; 12.5 GiB still available |
| 1 heavy + 2 light | all complete, no error; embed coexists with vision (distinct groups) |
| Hard memory cap | `systemd-run --user --scope -p MemoryMax=500M` kills the over-budget worker in **1 s**, rc=-9, **no other service touched** |
| Queue pressure ×6 | all six serialized and completed; `/running` answers in 1 ms during load |
| VM guardrail | ≥ 4 GiB kept available throughout; no OOM outside the capped scope; no swap (none exists) |

PSI-memory spikes observed during the session were attributed to the LocalAI
container churn (see below), not to llama.cpp load — they subsided after its
teardown. Explicit admission refusal before pressure is exercised in the G-05
control-plane tests (`RESOURCE_EXHAUSTED` before worker start).

## LocalAI comparison (measured, decisive)

- Image: 3.88 GB (vs ~40 MB llama.cpp + llama-swap binaries).
- API up in ~13 s, models auto-discovered.
- **The llama-cpp backend never finished loading Qwen3-0.6B Q8 within a 10-minute
  budget** (backend process alive at low CPU, retry loop in logs), on the same
  VM where raw llama.cpp serves the same GGUF in < 4 s cold. Two container
  attempts, same behaviour.
- Verdict: rejected as execution substrate for deployment profile A. Its
  breadth (image gen, TTS, galleries) is scope the product explicitly does not
  want to operate. No further LocalAI work unless a future gate reopens it.

## Ollama

Not tested: llama.cpp + llama-swap already covers on-demand load/unload with
thinner surface and pinned upstream binaries; Ollama adds a model-registry
abstraction the product replaces with its own registry. Recorded as
`not-needed` unless the lifecycle layer fails later.

## Specialists

- **fastembed 0.8.0 (ONNX)** `paraphrase-multilingual-MiniLM-L12-v2`: 384 dims,
  **11 ms/text** (batch 30), bit-deterministic across batch compositions
  (stronger guarantee than the GGUF embedder), 4.8 s first load incl. download.
  Strong candidate for `fast` embedding profile; GGUF Qwen3-embed stays the
  `balanced` 1024-dim candidate.
- **pypdf**: image-only PDF correctly yields zero text (native-text detection
  discriminates OCR need). Full OCR/layout stack remains G-06.
- **whisper.cpp**: deferred to G-08 (no audio surface in this lot).

## Conclusions (feed ADR-0002 / ADR-0003)

1. llama.cpp official pinned builds are the general-inference engine for
   profile A: fastest, smallest, clean deps, structured output + vision +
   embeddings + rerank all proven on the target VM.
2. llama-swap is the model-lifecycle supervisor: on-demand load, group swap,
   TTL unload, crash respawn all proven; must be loopback-forced and fronted by
   the control plane (no auth of its own; runtime keeps domain truth).
3. LocalAI is rejected on measurement (unusable load times on this VM, 100×
   image weight, unwanted scope).
4. Hard memory bounding via systemd user scopes works and becomes the G-04
   enforcement mechanism per worker.
5. Small-model quality limits are real (decimal comma, occasional wrong fact
   from the 0.6B): the control plane's deterministic validation + review flags
   are load-bearing, not decorative.
