# G-07 embeddings and rerank report — 2026-08-28

Hardware profile: `hermes-cpu-8vcpu-16gib` (live: 10 vCPU / ~19.5 GiB / no GPU /
no swap). Control plane loopback-only. llama-swap started for this evaluation
and stopped after it.

Engine: llama.cpp b10662 via llama-swap. Models remain outside Git in
`spike-g03/models`.

## Measured

| Family | Route | Result |
| --- | --- | --- |
| Embed | `text.embed@1.0.0/balanced` Qwen3-Embedding-0.6B Q8 | 1024-d, L2, 2038 ms for 6 texts |
| Cache | same request, internal classification | `hit`, 226 ms, no second upstream call |
| Cosine retrieve | French electricity-invoice query | top = `contract` (invoice family) |
| Rerank | `search.rerank@1.0.0/balanced` Qwen3-Reranker-0.6B Q8 | 3452 ms including model swap; top 3 = en-invoice, invoice, contract |
| Consumer persist | sqlite helper | no GGUF/Qwen filename in records |

`space_id` is `text.embed@1.0.0/balanced`. Changing profile or version requires
re-embed.

## Not measured, not approved

- FastEmbed/ONNX as a G-07 worker (G-03 measured 384-d MiniLM; not wired here)
- Private retrieval corpora
- Shared runtime vector database (forbidden)
- Cross-space mixing of 1024-d and 384-d vectors

## Honesty

A French query ranked the English invoice first, then the French invoice, then
the contract. That is invoice-family success, not French-only ranking. Do not
claim a universal multilingual retriever.

## Rollback

Remove embed/rerank routes and `/v1/embeddings` plus `/v1/rerank` adapters.
G-05/G-06 stay. No permanent service was installed.
