# G-07 embeddings and rerank core — 2026-08-28

Lot authorised by explicit `GO G-07`. Reuses the G-05 job core. No permanent
runtime service, no live UI wiring, no Hermes `config.yaml` mutation, no
production model promotion.

## Delivered

- `text.embed` and `search.rerank` workers on OpenAI-compatible llama.cpp
- declared `dimensions`, `normalisation=l2`, opaque `space_id`
- rerank bound of 100 candidates
- in-process result cache off for confidential/restricted
- `/v1/embeddings` and `/v1/rerank` adapters
- Python/TypeScript consumer examples that persist without model filenames
- ADR-0011

## Evidence

- Tests: `tests/test_runtime_g07.py`
- Loopback eval: `scripts/g07_eval.py`
- Report: `benchmarks/results/G07-EMBEDDINGS-RERANK-2026-08-28.md`

## Limits

FastEmbed is not a G-07 worker. No shared vector DB. Consumer owns the index.
