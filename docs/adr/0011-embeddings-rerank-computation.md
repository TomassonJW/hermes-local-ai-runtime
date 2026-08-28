# ADR-0011 — Embeddings and reranking as computation, not a vector database

- Status: Accepted
- Date: 2026-08-28
- Decision owners: Hermes (implementation), Thomas Jankowski (lot GO)
- Related gates: G-07
- Evidence: `operations/G07-EMBEDDINGS-RERANK-2026-08-28.md`

## Context

G-07 must give consumers stable vectors and bounded reranking without taking
ownership of their indexes. ADR-0009 already forbids a shared vector store.

G-03 measured two embedding families on this VM: Qwen3-Embedding-0.6B GGUF
(1024-d, llama.cpp) and FastEmbed MiniLM multilingual ONNX (384-d,
bit-stable across batch shapes). Qwen3-Reranker-0.6B ordered French
candidates correctly.

## Options considered

1. Runtime-hosted vector DB - rejected by ADR-0009.
2. Computation-only routes on the G-05 job core - reversible, consumer-owned
   persistence.
3. Hardcoded FastEmbed in-process in the control plane - couples ONNX deps
   to the API process.

## Decision

`text.embed` and `search.rerank` are G-05 jobs.

- `balanced` embeddings: llama.cpp OpenAI `/v1/embeddings` (Qwen3-0.6B).
- `fast` embeddings: ONNX/FastEmbed when a disposable worker is configured;
  otherwise the balanced route is the only approved one.
- Rerank: llama.cpp `/v1/rerank`, max 100 candidates.
- Result cache is metadata-keyed and off for confidential/restricted data.
- Consumer records store `id`, `vector`, `dimensions`, `normalisation`,
  `space_id`. They never store a model filename. A different `space_id`
  means re-embed.

## Consequences

Consumers can persist and replace embedding spaces without coupling to GGUF
names. The runtime never sees a consumer database.

Limits: GGUF batch composition can wobble at ~1e-3; FastEmbed was measured
in G-03 but is not a CI dependency.

## Validation

Falsify if a consumer record contains a model artefact name, if rerank
accepts more than 100 candidates, if confidential jobs are cached, or if
French mixed retrieval puts an unrelated document first on the synthetic
suite.

## Rollback

Remove embed/rerank routes and adapters. G-05/G-06 workers stay.
