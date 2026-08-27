# Control plane and workers

```text
API ingress
  -> auth and request budgets
  -> capability resolver
  -> route policy
  -> resource admission
  -> job coordinator
       -> worker manager
       -> result cache
       -> provenance recorder
       -> metrics/events
  -> response adapter
```

## Modules

API ingress provides native `/api/v1`, OpenAI-compatible `/v1`, optional MCP, uploads, request IDs/idempotency/auth/limits/schema validation. It never forwards arbitrary engine flags.

Capability registry defines semantic versions independent from models. Route resolver combines capability/profile, consumer/data policy, installed approved routes, hardware, queues/memory, compatibility and fallback permission; returns plan or explicit refusal.

Resource admission reserves budget before worker activation.

Job states: `accepted -> queued -> admitted -> loading -> running -> validating -> succeeded|failed|cancelled|expired|rejected`. Transitions are timestamped; retry is a linked new attempt.

Worker states: `stopped -> starting -> ready -> leased -> idle -> draining -> stopped`, with failed state. Lease prevents unload during active job. Lifecycle may be delegated to llama-swap while runtime keeps domain truth.

Result cache key includes input hash, capability/version, route/pipeline, model/preset, output schema and policy. Confidential payload cache is off by default.

## Workers

General LLM/VLM preferred first engine: llama.cpp server. Requires structured output, text/image where supported, embeddings/reranking where evaluated, health/metrics, controlled parallelism and explicit context/image budgets. Multimodal is version-tested.

OCR/document workers: native PDF extraction, OpenCV, Tesseract, PP-OCR, PaddleOCR layout/pipeline in separate environments.

Vector workers: ONNX/FastEmbed, llama.cpp embedding/rerank or model-specific library only when justified. Vector contract declares dimensions/normalisation.

Object/image workers: specialised detection/image embedding via bounded backend. Model family selected by benchmark.

Speech: whisper.cpp, VAD, chunking/timestamps, optional alternative ASR.

Separate processes provide dependency isolation, crash recovery, resource controls, replaceability and lazy loading. Control plane remains modular monolith until a real remote node exists.
