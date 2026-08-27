# Mission 05 — Embeddings and reranking

## Goal

Provide stable vector computation and candidate reordering while consumers retain their own indexes and data.

## Explanation

Embedding converts text or an image into a numerical vector so approximate search can retrieve plausible candidates quickly.

Reranking is the second stage: it reads the query together with each of the top retrieved candidates and reorders them more precisely. It is more expensive per candidate but operates on a small set.

## Work

- compare compact ONNX/FastEmbed families with Qwen3 embedding/reranker candidates;
- declare dimensions, normalisation, maximum input, and language coverage;
- implement batching and cache;
- implement bounded rerank candidates;
- return original candidate IDs, order, score, and optional evidence;
- provide Python/TypeScript examples;
- test French and mixed-language retrieval;
- test model replacement compatibility.

## Non-goal

No shared vector database, document ingestion platform, or RAG framework.

## Acceptance

G-07 passes and a synthetic consumer can persist vectors and use reranking without knowing model artefacts.
