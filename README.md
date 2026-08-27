# Hermes Local AI Runtime

A local-first, resource-aware AI capability runtime for Hermes and other applications.

> **Status:** product and engineering bootstrap `0.1.0`. The runtime is not implemented yet. This repository is the development authority that Hermes will take over.

Hermes Local AI Runtime is intended to become the shared local AI kernel for a Hermes environment: one stable place where applications can request OCR, document understanding, structured extraction, embeddings, reranking, general vision, object and image analysis, speech recognition, and—later—larger local language models.

The project does **not** make applications depend on model names. Consumers request versioned capabilities such as `vision.analyze`, `document.ocr`, `text.extract_structured`, `text.embed`, `search.rerank`, or `audio.transcribe`. The runtime selects an approved engine, model, preset, worker, and execution target under explicit resource and privacy policies.

## Why this project exists

Without a shared runtime, each application tends to rebuild model downloads, inference servers, prompts, quantization settings, resource limits, observability, fallbacks, and security boundaries. That duplication becomes expensive and unreliable.

This repository defines a reusable control plane around existing open-source inference engines. It will not reimplement inference, OCR, tokenization, or speech recognition.

## Product principles

- **Capabilities before models.** Applications depend on stable contracts, not a particular checkpoint.
- **Local-first, not local-only dogma.** A bounded local attempt may fall back only when policy explicitly permits it.
- **Specialists before giant generalists.** OCR, detection, embeddings, reranking, and speech use purpose-built engines when they are better or cheaper.
- **Resource admission before execution.** An AI job must never silently consume the whole Hermes server.
- **Evidence before promotion.** A model becomes `approved` only after compatibility, quality, latency, memory, licence, and regression gates.
- **No hidden writes.** The runtime computes and returns results; consumer applications own their databases and business decisions.
- **Open standards and replaceable engines.** The native capability API is complemented by OpenAI-compatible endpoints and optional MCP integration.
- **Future GPU without a rewrite.** CPU workers are the first deployment profile; GPU and remote workers use the same contracts later.

## Initial target environment

The first real deployment is the existing Hermes Ubuntu VM:

- 8 virtual CPU cores on an AMD Ryzen 9 7900 host;
- 16 GiB RAM assigned to the VM;
- no GPU;
- other Hermes applications and services already running in the same VM;
- local or tailnet-only access; no public listener by default.

The initial profile therefore permits one heavy generative inference at a time, keeps strict memory headroom for the rest of Hermes, loads larger models lazily, and treats swap thrashing as a failed admission decision rather than normal operation.

## Intended architecture

```text
Hermes / applications / SDKs / MCP clients
                    |
          Capability API + OpenAI facade
                    |
       policy, routing, jobs, admission control
                    |
     registry, presets, cache, provenance, metrics
                    |
     +--------------+---------------+--------------+
     |              |               |              |
 llama.cpp       OCR/layout      ONNX/vector    speech workers
 llama-swap      PaddleOCR       embed/rerank   whisper.cpp
     |              |               |              |
     +----------- CPU workers first; GPU workers later --------+
```

`llama.cpp` is the preferred first general inference engine, with `llama-swap` evaluated for on-demand process and model lifecycle management. LocalAI remains a required comparison candidate: if it meets the gates with less custom code, the architecture must be allowed to become thinner.

## Capability roadmap

The baseline covers these capability families:

1. health, discovery, jobs, routing, registry, resource governance, and provenance;
2. general image understanding and Hermes auxiliary vision;
3. OCR, document layout, classification, and structured extraction;
4. embeddings, semantic retrieval support, and reranking;
5. object detection and image similarity through specialised workers;
6. speech-to-text with `whisper.cpp`, then alternative ASR candidates;
7. later: text generation, coding models, TTS, image generation, video, GPU and distributed workers.

“Covered” means architected and gated, not already implemented.

## Start here

Agents and contributors must read in this order:

1. [`AGENTS.md`](AGENTS.md)
2. [`provenance/COMPILATION-MANIFEST.yml`](provenance/COMPILATION-MANIFEST.yml)
3. [`product/00-index.md`](product/00-index.md)
4. [`architecture/00-index.md`](architecture/00-index.md)
5. [`GATES.md`](GATES.md)
6. [`STATE.md`](STATE.md)
7. [`HANDOFF.md`](HANDOFF.md)

The first implementation lot is **UI-00**, a truthful operations shell with simulated data only. It must stop for Thomas's visible-product verdict before runtime backend work begins. Technical read-only probes and benchmark planning may be prepared during preflight, but no permanent service or host mutation is authorised by the bootstrap alone.

## Language

English is the canonical repository language. A maintained French overview is available in [`README.fr.md`](README.fr.md). Code identifiers, API paths, model IDs, command names, and configuration keys remain in English.

## Licence

The repository's original code and documentation are licensed under Apache License 2.0. Downloaded models, runtimes, datasets, fonts, and other third-party components keep their own licences. A model is not approved merely because this repository can download or execute it.

See [`LICENSE`](LICENSE), [`NOTICE`](NOTICE), and [`registry/LICENSE-POLICY.md`](registry/LICENSE-POLICY.md).
